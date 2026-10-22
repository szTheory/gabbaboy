#include "gbb_accept.h"
#include "../core/gbb_accept_input.h"

#include <string.h>

/* Longest DMG instruction is 6 M-cycles = 48 half-dots. A zero-consume call
 * with no more than this remaining cannot start another instruction. */
#define MAX_INSTRUCTION_HALF_DOTS UINT64_C(48)

void gbb_accept_stepper_init(gbb_accept_stepper *stepper, gbb_instance *instance,
                             gbb_accept_pcm_sink sink, void *sink_context) {
    memset(stepper, 0, sizeof(*stepper));
    stepper->instance = instance;
    stepper->sink = sink;
    stepper->sink_context = sink_context;
    stepper->last_stop = GBB_STOP_BUDGET;
}

bool gbb_accept_stop_resumable(const gbb_accept_input_span *span, uint64_t deadline,
                               uint64_t consumed_half_dots, uint64_t budget_half_dots) {
    return span != NULL && *span->cursor < span->count &&
           span->events[*span->cursor].at_half_dots <= deadline &&
           consumed_half_dots < budget_half_dots;
}

enum gbb_accept_step_status gbb_accept_diag_advance(
    gbb_instance *instance, uint64_t *actual_half_dots, uint64_t deadline,
    const gbb_accept_input_span *span, gbb_trace_record *trace, size_t trace_capacity,
    gbb_diagnostic_record *diagnostics, size_t diagnostic_capacity,
    gbb_accept_diag_visit_fn visit, void *visit_context, uint64_t guard_origin_half_dots) {
    /* The guard base is the caller's logical time, not the actual counter: a carried instruction makes
     * them differ and the diagnostic pass has always sized its guard from logical time. */
    uint64_t guard = (deadline - guard_origin_half_dots) / 4u + 1024u;
    while (*actual_half_dots < deadline) {
        if (guard-- == 0) return GBB_ACCEPT_STEP_GUARD;
        uint64_t budget = deadline - *actual_half_dots;
        gbb_run_result r = gbb_accept_run_diagnostic(instance, budget, span, trace, trace_capacity,
                                                      diagnostics, diagnostic_capacity);
        if (visit != NULL && (r.trace_count != 0 || r.diagnostic_count != 0)) {
            visit(visit_context, trace, r.trace_count, diagnostics, r.diagnostic_count);
        }
        *actual_half_dots += r.consumed_half_dots;
        switch (r.reason) {
        case GBB_STOP_BUDGET:
            if (r.consumed_half_dots == 0 && budget <= MAX_INSTRUCTION_HALF_DOTS) {
                return GBB_ACCEPT_STEP_OK; /* carried */
            }
            continue;
        case GBB_STOP_OUTPUT_FULL:
        case GBB_STOP_HALTED_IDLE:
            continue;
        case GBB_STOP_STOPPED:
            if (gbb_accept_stop_resumable(span, deadline, r.consumed_half_dots, budget)) continue; /* replay: same STOP rule as advance_to_span */
            return GBB_ACCEPT_STEP_STOPPED;
        default:
            return GBB_ACCEPT_STEP_STOPPED;
        }
    }
    return GBB_ACCEPT_STEP_OK;
}

static enum gbb_accept_step_status advance_to_span(gbb_accept_stepper *s, uint64_t deadline,
                                                   const gbb_accept_input_span *span) {
    if (s->actual_half_dots >= deadline) return GBB_ACCEPT_STEP_OK;
    uint64_t guard = (deadline - s->actual_half_dots) / 4u + 1024u;
    while (s->actual_half_dots < deadline) {
        if (guard-- == 0) return GBB_ACCEPT_STEP_GUARD;
        uint64_t budget = deadline - s->actual_half_dots;
        size_t written = 0;
        gbb_run_result r = span == NULL
            ? gbb_run_audio(s->instance, budget, s->frames, GBB_ACCEPT_PCM_FRAMES, &written)
            : gbb_accept_run_audio(s->instance, budget, span, s->frames, GBB_ACCEPT_PCM_FRAMES,
                                   &written);
        s->actual_half_dots += r.consumed_half_dots;
        s->last_stop = r.reason;
        if (written != 0 && s->sink != NULL) s->sink(s->sink_context, s->frames, written);
        switch (r.reason) {
        case GBB_STOP_BUDGET:
            /* Normal completion; a zero-consume call this close to the
             * deadline reaches it logically and the remainder is carried. */
            if (r.consumed_half_dots == 0 && budget <= MAX_INSTRUCTION_HALF_DOTS) {
                return GBB_ACCEPT_STEP_OK;
            }
            break;
        case GBB_STOP_OUTPUT_FULL: /* PCM buffer filled; frames already sunk */
        case GBB_STOP_HALTED_IDLE: /* eligible idle ticks advanced; keep going */
            break;
        case GBB_STOP_STOPPED:
            if (gbb_accept_stop_resumable(span, deadline, r.consumed_half_dots, budget)) {
                break; /* resume stopped time only when the borrowed stream has a deadline */
            }
            return GBB_ACCEPT_STEP_STOPPED;
        default:
            return GBB_ACCEPT_STEP_STOPPED;
        }
    }
    return GBB_ACCEPT_STEP_OK;
}

enum gbb_accept_step_status gbb_accept_advance_to(gbb_accept_stepper *stepper, uint64_t deadline) {
    return advance_to_span(stepper, deadline, NULL);
}

static uint8_t peek_instance(void *context, uint16_t address) {
    return gbb_peek_ram((const gbb_instance *)context, address);
}

void gbb_accept_drive(const gbb_accept_drive_config *cfg, gbb_accept_drive_result *result) {
    memset(result, 0, sizeof(*result));
    result->status = GBB_ACCEPT_DRIVE_INVALID_CONFIG;
    if (cfg == NULL || cfg->stepper == NULL || cfg->script == NULL || cfg->predicate == NULL ||
        cfg->max_batch == 0 || cfg->max_batch > 64u) {
        return;
    }
    gbb_accept_stepper *stepper = cfg->stepper;
    const gbb_accept_script *script = cfg->script;
    gbb_accept_track track;
    gbb_accept_track_init(&track);

    uint64_t logical = stepper->actual_half_dots;
    size_t next_event = 0, next_mark = 0;
    gbb_accept_input_span input_span = {script->events, script->event_count, &next_event};
    uint64_t boundary_k = logical / GBB_ACCEPT_HALF_DOTS_PER_FRAME + 1u;

    for (;;) {
        uint64_t limit = cfg->budget_half_dots;
        if (track.hit && track.t_hit <= UINT64_MAX - cfg->tail_half_dots &&
            track.t_hit + cfg->tail_half_dots < limit) {
            limit = track.t_hit + cfg->tail_half_dots;
        }
        if (logical >= limit) break;

        /* Merge frame boundaries, script marks and the script end into the
         * next window end. */
        uint64_t deadline = limit;
        uint64_t boundary = boundary_k * GBB_ACCEPT_HALF_DOTS_PER_FRAME;
        if (boundary < deadline) deadline = boundary;
        while (next_mark < script->mark_count && script->marks[next_mark].at_half_dots <= logical) {
            next_mark++;
        }
        if (next_mark < script->mark_count && script->marks[next_mark].at_half_dots < deadline) {
            deadline = script->marks[next_mark].at_half_dots;
        }
        if (script->end_half_dots > logical && script->end_half_dots < deadline) {
            deadline = script->end_half_dots;
        }

        /* Custom adopters keep their bounded delivery callback. The default
         * acceptance path lends the immutable span to the core per run call,
         * where due events are copied through the existing 64-entry queue. */
        if (cfg->deliver != NULL) {
            size_t batch_end = next_event;
            while (batch_end < script->event_count &&
                   script->events[batch_end].at_half_dots <= deadline &&
                   batch_end - next_event < cfg->max_batch) {
                batch_end++;
            }
            if (batch_end < script->event_count && batch_end - next_event == cfg->max_batch &&
                script->events[batch_end].at_half_dots <= deadline) {
                deadline = script->events[batch_end - 1u].at_half_dots;
            }
            if (batch_end > next_event) {
                const gbb_input_event *events = script->events + next_event;
                size_t count = batch_end - next_event;
                if (!cfg->deliver(cfg->context, events, count)) {
                    result->status = GBB_ACCEPT_DRIVE_DELIVER_FAILED;
                    result->end_half_dots = logical;
                    return;
                }
                next_event = batch_end;
            }
        }

        if (deadline > logical) {
            enum gbb_accept_step_status st = advance_to_span(stepper, deadline,
                                                              cfg->deliver == NULL ? &input_span : NULL);
            if (st != GBB_ACCEPT_STEP_OK) {
                result->status = st == GBB_ACCEPT_STEP_GUARD ? GBB_ACCEPT_DRIVE_GUARD
                                                             : GBB_ACCEPT_DRIVE_STOPPED;
                result->stop_reason = stepper->last_stop;
                result->end_half_dots = logical;
                return;
            }
            logical = deadline;
            if (cfg->after_step != NULL) {
                cfg->after_step(cfg->context, stepper->instance, stepper->actual_half_dots);
            }
        }

        if (deadline == boundary) {
            bool value = gbb_accept_predicate_eval(cfg->predicate, peek_instance,
                                                   stepper->instance, cfg->expect_hw);
            if (cfg->at_boundary != NULL) {
                cfg->at_boundary(cfg->context, stepper->instance, boundary, value);
            }
            gbb_accept_predicate_track(&track, boundary, value);
            boundary_k++;
        }
    }

    result->end_half_dots = logical;
    result->stop_reason = stepper->last_stop;
    if (track.hit) {
        result->status = GBB_ACCEPT_DRIVE_HIT;
        result->t_hit_half_dots = track.t_hit;
    } else {
        result->status = GBB_ACCEPT_DRIVE_NOT_REACHED;
    }
}
