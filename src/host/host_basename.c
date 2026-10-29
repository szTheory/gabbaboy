/* D-07: derive the `.sav` stem from a ROM path. Pure; no feature macros are needed because nothing
 * here touches the filesystem or a POSIX call. */
#include "gbb_host.h"

#include <string.h>

/* Strict UTF-8 (RFC 3629): no C0/C1 leads, overlongs, surrogates (ED A0..BF), code points above
 * U+10FFFF (F4 90.. and F5..FF) or truncated sequences. Returns false on the first defect. */
static bool utf8_valid(const unsigned char *s, size_t n) {
    size_t i = 0u;
    while (i < n) {
        const unsigned char c = s[i];
        size_t extra;
        unsigned char lo = 0x80u, hi = 0xBFu; /* range of the first continuation byte */
        if (c <= 0x7Fu) { ++i; continue; }
        if (c >= 0xC2u && c <= 0xDFu) extra = 1u;
        else if (c == 0xE0u) { extra = 2u; lo = 0xA0u; }         /* no overlong 3-byte */
        else if (c == 0xEDu) { extra = 2u; hi = 0x9Fu; }         /* no surrogates */
        else if (c >= 0xE1u && c <= 0xEFu) extra = 2u;
        else if (c == 0xF0u) { extra = 3u; lo = 0x90u; }         /* no overlong 4-byte */
        else if (c == 0xF4u) { extra = 3u; hi = 0x8Fu; }         /* nothing above U+10FFFF */
        else if (c >= 0xF1u && c <= 0xF3u) extra = 3u;
        else return false;                                       /* 80..C1 and F5..FF */
        if (i + extra >= n) return false; /* truncated: the last continuation byte would be past the end */
        if (s[i + 1u] < lo || s[i + 1u] > hi) return false;
        for (size_t k = 2u; k <= extra; ++k)
            if (s[i + k] < 0x80u || s[i + k] > 0xBFu) return false;
        i += extra + 1u;
    }
    return true;
}

static bool ascii_alnum(unsigned char c) {
    return (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
}

host_stem_status host_stem(const char *rom_path, char *out, size_t cap) {
    if (rom_path == NULL || out == NULL) return HOST_STEM_EMPTY;
    const char *slash = strrchr(rom_path, '/');
    const unsigned char *comp = (const unsigned char *)(slash != NULL ? slash + 1 : rom_path);
    size_t len = strlen((const char *)comp);
    if (len == 0u) return HOST_STEM_EMPTY; /* a trailing slash names a directory, not a ROM */

    /* Strip a final `.ext` of 1-8 ASCII alphanumerics. A dot at byte 0 never separates an extension
     * (Playstead deletingPathExtension: `.gb` keeps its whole name). */
    for (size_t d = len; d-- > 1u;) {
        if (comp[d] != '.') continue;
        const size_t ext = len - d - 1u;
        bool ok = ext >= 1u && ext <= 8u;
        for (size_t k = d + 1u; ok && k < len; ++k) ok = ascii_alnum(comp[k]);
        if (ok) len = d;
        break; /* only the last dot is a candidate */
    }

    if (len == 0u) return HOST_STEM_EMPTY;
    if (comp[0] == '.') return HOST_STEM_LEADING_DOT;
    for (size_t i = 0u; i < len; ++i) if (comp[i] < 0x20u) return HOST_STEM_CONTROL;
    for (size_t i = 0u; i < len; ++i) if (comp[i] == 0x7Fu) return HOST_STEM_DEL;
    for (size_t i = 0u; i < len; ++i) if (comp[i] == '\\') return HOST_STEM_BACKSLASH;
    if (!utf8_valid(comp, len)) return HOST_STEM_BAD_UTF8;
    if (len > GBB_HOST_STEM_MAX_BYTES || len + 1u > cap) return HOST_STEM_TOO_LONG;

    memcpy(out, comp, len);
    out[len] = '\0';
    return HOST_STEM_OK;
}

const char *host_stem_reason(host_stem_status status) {
    switch (status) {
    case HOST_STEM_OK: return "stem-ok";
    case HOST_STEM_EMPTY: return "stem-empty";
    case HOST_STEM_LEADING_DOT: return "stem-leading-dot";
    case HOST_STEM_CONTROL: return "stem-control";
    case HOST_STEM_DEL: return "stem-del";
    case HOST_STEM_BACKSLASH: return "stem-backslash";
    case HOST_STEM_BAD_UTF8: return "stem-bad-utf8";
    case HOST_STEM_TOO_LONG: return "stem-too-long";
    }
    return "stem-unknown";
}
