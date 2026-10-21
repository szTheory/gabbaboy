#ifndef GBB_ACCEPT_INPUT_H
#define GBB_ACCEPT_INPUT_H

/* Private acceptance-run seam. The caller owns both the immutable event array
 * and cursor. A span is borrowed for exactly one core run call; the core never
 * retains it after returning. This is not part of the installed API. */

#include "gabbaboy/gabbaboy.h"

#include <stddef.h>

#define GBB_ACCEPT_INPUT_SPAN_MAX_EVENTS 16384u

typedef struct {
    const gbb_input_event *events;
    size_t count;
    size_t *cursor;
} gbb_accept_input_span;

gbb_run_result gbb_accept_run_audio(gbb_instance *instance, uint64_t budget_half_dots,
                                    const gbb_accept_input_span *span,
                                    gbb_audio_frame *frames, size_t frame_capacity,
                                    size_t *out_frame_count);

gbb_run_result gbb_accept_run_diagnostic(gbb_instance *instance, uint64_t budget_half_dots,
                                         const gbb_accept_input_span *span,
                                         gbb_trace_record *trace, size_t trace_capacity,
                                         gbb_diagnostic_record *diagnostics,
                                         size_t diagnostic_capacity);

#endif
