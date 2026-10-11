#include "gbb_accept.h"

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

enum gbb_accept_step_status gbb_accept_advance_to(gbb_accept_stepper *s, uint64_t deadline) {
    if (s->actual_half_dots >= deadline) return GBB_ACCEPT_STEP_OK;
    uint64_t guard = (deadline - s->actual_half_dots) / 4u + 1024u;
    while (s->actual_half_dots < deadline) {
        if (guard-- == 0) return GBB_ACCEPT_STEP_GUARD;
        uint64_t budget = deadline - s->actual_half_dots;
        size_t written = 0;
        gbb_run_result r = gbb_run_audio(s->instance, budget, s->frames, GBB_ACCEPT_PCM_FRAMES,
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
        default:
            return GBB_ACCEPT_STEP_STOPPED;
        }
    }
    return GBB_ACCEPT_STEP_OK;
}

static uint8_t peek_instance(void *context, uint16_t address) {
    return gbb_peek_ram((const gbb_instance *)context, address);
}

static bool queue_on_instance(gbb_instance *instance, const gbb_input_event *events, size_t count) {
    return gbb_queue_events(instance, events, count) == GBB_OK;
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

        /* Deliver pending events that fall in this window, at most max_batch
         * at a time; a fuller window is shortened to the last batched event. */
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
            bool ok = cfg->deliver != NULL ? cfg->deliver(cfg->context, events, count)
                                           : queue_on_instance(stepper->instance, events, count);
            if (!ok) {
                result->status = GBB_ACCEPT_DRIVE_DELIVER_FAILED;
                result->end_half_dots = logical;
                return;
            }
            next_event = batch_end;
        }

        if (deadline > logical) {
            enum gbb_accept_step_status st = gbb_accept_advance_to(stepper, deadline);
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
