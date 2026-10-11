#include "gbb_accept.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* gbinput 1 parser (D-10..D-12). The whole script is validated before any
 * guest work: a failure frees everything and leaves the output zeroed. Time
 * arithmetic is checked against the 600 s ceiling, so no intermediate value
 * can wrap a uint64. */

typedef struct {
    gbb_input_event *events;
    size_t event_count;
    size_t event_capacity;
    gbb_accept_mark *marks;
    size_t mark_count;
    size_t mark_capacity;
    uint64_t cursor;
    uint8_t held;            /* bit per gbb_button */
    size_t press_line[8];
    bool version_seen;
} parse_state;

typedef struct {
    size_t line;
    const char *reason;
    int code;                /* 1 invalid script, 2 out of memory */
} parse_error;

static const char *const button_names[8] = {"RIGHT", "LEFT", "UP", "DOWN",
                                            "A", "B", "SELECT", "START"};

static void fail(parse_error *e, size_t line, const char *reason) {
    e->line = line;
    e->reason = reason;
    e->code = 1;
}

static void fail_oom(parse_error *e, size_t line) {
    e->line = line;
    e->reason = "out of memory";
    e->code = 2;
}

static int parse_button(const char *token, uint8_t *out) {
    for (uint8_t i = 0; i < 8; i++) {
        if (strcmp(token, button_names[i]) == 0) {
            *out = i;
            return 1;
        }
    }
    return 0;
}

/* Decimal digits plus hd/f/s suffix; every multiply and add is checked. */
static int parse_duration(const char *token, uint64_t *out, const char **reason) {
    size_t digits = 0;
    uint64_t value = 0;
    while (token[digits] >= '0' && token[digits] <= '9') {
        unsigned d = (unsigned)(token[digits] - '0');
        if (value > (UINT64_MAX - d) / 10u) {
            *reason = "time overflow";
            return 0;
        }
        value = value * 10u + d;
        digits++;
    }
    if (digits == 0) {
        *reason = "malformed time";
        return 0;
    }
    const char *suffix = token + digits;
    uint64_t unit;
    if (strcmp(suffix, "hd") == 0) unit = 1;
    else if (strcmp(suffix, "f") == 0) unit = GBB_ACCEPT_HALF_DOTS_PER_FRAME;
    else if (strcmp(suffix, "s") == 0) unit = GBB_ACCEPT_HALF_DOTS_PER_SECOND;
    else {
        *reason = "malformed time suffix";
        return 0;
    }
    if (value > UINT64_MAX / unit) {
        *reason = "time overflow";
        return 0;
    }
    *out = value * unit;
    return 1;
}

static int push_event(parse_state *st, parse_error *e, size_t line, uint64_t at,
                      gbb_input_event_kind kind, uint8_t button) {
    if (st->event_count >= GBB_ACCEPT_SCRIPT_MAX_EVENTS) {
        fail(e, line, "too many events");
        return 0;
    }
    if (st->event_count == st->event_capacity) {
        size_t capacity = st->event_capacity ? st->event_capacity * 2u : 64u;
        if (capacity > GBB_ACCEPT_SCRIPT_MAX_EVENTS) capacity = GBB_ACCEPT_SCRIPT_MAX_EVENTS;
        gbb_input_event *grown = realloc(st->events, capacity * sizeof(*grown));
        if (grown == NULL) {
            fail_oom(e, line);
            return 0;
        }
        st->events = grown;
        st->event_capacity = capacity;
    }
    st->events[st->event_count].at_half_dots = at;
    st->events[st->event_count].kind = kind;
    st->events[st->event_count].value = button;
    st->event_count++;
    return 1;
}

static int advance(parse_state *st, parse_error *e, size_t line, uint64_t delta) {
    if (delta > GBB_ACCEPT_MAX_SCRIPT_HALF_DOTS - st->cursor) {
        fail(e, line, "time exceeds 600 s ceiling");
        return 0;
    }
    st->cursor += delta;
    return 1;
}

static int valid_label(const char *s) {
    size_t n = strlen(s);
    if (n == 0 || n > GBB_ACCEPT_SCRIPT_MAX_LABEL) return 0;
    for (size_t i = 0; i < n; i++) {
        if (!((s[i] >= 'a' && s[i] <= 'z') || (s[i] >= '0' && s[i] <= '9') || s[i] == '_')) return 0;
    }
    return 1;
}

/* Splits a comment-stripped line in place into at most 3 tokens. Returns the
 * count, or -1 when there are more. */
static int tokenize(char *line, char *tokens[3]) {
    int count = 0;
    char *p = line;
    for (;;) {
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '\0') break;
        if (count == 3) return -1;
        tokens[count++] = p;
        while (*p != '\0' && *p != ' ' && *p != '\t') p++;
        if (*p == '\0') break;
        *p++ = '\0';
    }
    return count;
}

static int handle_line(parse_state *st, parse_error *e, size_t line_no, char *text) {
    char *hash = strchr(text, '#');
    if (hash != NULL) *hash = '\0';
    char *tokens[3];
    int count = tokenize(text, tokens);
    if (count == 0) return 1;
    if (count < 0) {
        fail(e, line_no, "too many arguments");
        return 0;
    }
    if (!st->version_seen) {
        if (count != 2 || strcmp(tokens[0], "gbinput") != 0) {
            fail(e, line_no, "missing gbinput version line");
            return 0;
        }
        if (strcmp(tokens[1], "1") != 0) {
            fail(e, line_no, "unsupported gbinput version");
            return 0;
        }
        st->version_seen = true;
        return 1;
    }
    const char *verb = tokens[0];
    const char *reason = NULL;
    uint8_t button = 0;
    uint64_t t = 0;
    if (strcmp(verb, "wait") == 0) {
        if (count != 2) { fail(e, line_no, "wait takes one time"); return 0; }
        if (!parse_duration(tokens[1], &t, &reason)) { fail(e, line_no, reason); return 0; }
        return advance(st, e, line_no, t);
    }
    if (strcmp(verb, "press") == 0 || strcmp(verb, "release") == 0) {
        int press = verb[0] == 'p';
        if (count != 2) { fail(e, line_no, "press/release takes one button"); return 0; }
        if (!parse_button(tokens[1], &button)) { fail(e, line_no, "unknown button"); return 0; }
        uint8_t bit = (uint8_t)(1u << button);
        if (press) {
            if (st->held & bit) { fail(e, line_no, "button already pressed"); return 0; }
            if (!push_event(st, e, line_no, st->cursor, GBB_INPUT_BUTTON_PRESS, button)) return 0;
            st->held |= bit;
            st->press_line[button] = line_no;
        } else {
            if (!(st->held & bit)) { fail(e, line_no, "release without press"); return 0; }
            if (!push_event(st, e, line_no, st->cursor, GBB_INPUT_BUTTON_RELEASE, button)) return 0;
            st->held &= (uint8_t)~bit;
        }
        return 1;
    }
    if (strcmp(verb, "tap") == 0) {
        if (count != 3) { fail(e, line_no, "tap takes a button and a time"); return 0; }
        if (!parse_button(tokens[1], &button)) { fail(e, line_no, "unknown button"); return 0; }
        if (!parse_duration(tokens[2], &t, &reason)) { fail(e, line_no, reason); return 0; }
        uint8_t bit = (uint8_t)(1u << button);
        if (st->held & bit) { fail(e, line_no, "button already pressed"); return 0; }
        uint64_t press_at = st->cursor;
        if (!advance(st, e, line_no, t)) return 0;
        if (!push_event(st, e, line_no, press_at, GBB_INPUT_BUTTON_PRESS, button)) return 0;
        return push_event(st, e, line_no, st->cursor, GBB_INPUT_BUTTON_RELEASE, button);
    }
    if (strcmp(verb, "mark") == 0) {
        if (count != 2) { fail(e, line_no, "mark takes one label"); return 0; }
        if (!valid_label(tokens[1])) { fail(e, line_no, "invalid label"); return 0; }
        for (size_t i = 0; i < st->mark_count; i++) {
            if (strcmp(st->marks[i].label, tokens[1]) == 0) {
                fail(e, line_no, "duplicate label");
                return 0;
            }
        }
        if (st->mark_count == st->mark_capacity) {
            size_t capacity = st->mark_capacity ? st->mark_capacity * 2u : 8u;
            gbb_accept_mark *grown = realloc(st->marks, capacity * sizeof(*grown));
            if (grown == NULL) { fail_oom(e, line_no); return 0; }
            st->marks = grown;
            st->mark_capacity = capacity;
        }
        strcpy(st->marks[st->mark_count].label, tokens[1]);
        st->marks[st->mark_count].at_half_dots = st->cursor;
        st->mark_count++;
        return 1;
    }
    fail(e, line_no, "unknown verb");
    return 0;
}

static int run_parse(const uint8_t *bytes, size_t length, parse_state *st, parse_error *e) {
    if (length > GBB_ACCEPT_SCRIPT_MAX_BYTES) {
        fail(e, 0, "file exceeds 65536 bytes");
        return 0;
    }
    size_t pos = 0, line_no = 0;
    char buffer[GBB_ACCEPT_SCRIPT_MAX_LINE_BYTES + 1u];
    while (pos < length) {
        size_t end = pos;
        while (end < length && bytes[end] != '\n') end++;
        line_no++;
        if (line_no > GBB_ACCEPT_SCRIPT_MAX_LINES) {
            fail(e, line_no, "too many lines");
            return 0;
        }
        size_t content = end - pos;
        if (content > 0 && bytes[end - 1u] == '\r' && end > pos) content--;
        if (content > GBB_ACCEPT_SCRIPT_MAX_LINE_BYTES) {
            fail(e, line_no, "line exceeds 128 bytes");
            return 0;
        }
        for (size_t i = 0; i < content; i++) {
            uint8_t b = bytes[pos + i];
            if (b == 0) { fail(e, line_no, "NUL byte"); return 0; }
            if (b > 0x7e) { fail(e, line_no, "non-ASCII byte"); return 0; }
            if (b < 0x20 && b != '\t') { fail(e, line_no, "control byte"); return 0; }
            buffer[i] = (char)b;
        }
        buffer[content] = '\0';
        if (!handle_line(st, e, line_no, buffer)) return 0;
        pos = end < length ? end + 1u : end;
    }
    if (!st->version_seen) {
        fail(e, line_no ? line_no : 1u, "missing gbinput version line");
        return 0;
    }
    for (uint8_t b = 0; b < 8; b++) {
        if (st->held & (1u << b)) {
            fail(e, st->press_line[b], "button still held at end of script");
            return 0;
        }
    }
    return 1;
}

int gbb_accept_script_parse(const uint8_t *bytes, size_t length, gbb_accept_script *out,
                            char *err, size_t err_capacity) {
    if (out == NULL || (bytes == NULL && length != 0)) {
        if (err != NULL && err_capacity != 0) snprintf(err, err_capacity, "invalid-script: line 0: invalid argument");
        return 1;
    }
    memset(out, 0, sizeof(*out));
    parse_state st;
    memset(&st, 0, sizeof(st));
    parse_error e = {0, "", 0};
    if (!run_parse(bytes, length, &st, &e)) {
        free(st.events);
        free(st.marks);
        if (err != NULL && err_capacity != 0) {
            snprintf(err, err_capacity, "invalid-script: line %zu: %s", e.line, e.reason);
        }
        return e.code;
    }
    out->events = st.events;
    out->event_count = st.event_count;
    out->marks = st.marks;
    out->mark_count = st.mark_count;
    out->end_half_dots = st.cursor;
    if (err != NULL && err_capacity != 0) err[0] = '\0';
    return 0;
}

void gbb_accept_script_free(gbb_accept_script *script) {
    if (script == NULL) return;
    free(script->events);
    free(script->marks);
    memset(script, 0, sizeof(*script));
}
