/* Pure flush cadence for host mode (Phase 18, D-11).
 *
 * The state machine reads no clock, performs no I/O and allocates nothing: the caller passes the frame
 * number and the battery generation it just observed and acts on the returned action. That keeps the
 * thresholds provable by boundary tables instead of by waiting thousands of frames.
 *
 * Declared loss windows: a guest SRAM write is flushed after at most 300 frames plus one write; an
 * RTC-only drift, which does not bump the generation, after at most 3,600 frames. */
#include "gbb_host.h"

/* Frames from `mark` to `frame`. A mark ahead of the frame (a reset or a stale value) reads as zero so
 * unsigned subtraction can never wrap into a huge age. */
static uint64_t elapsed(uint64_t frame, uint64_t mark) {
    return frame >= mark ? frame - mark : 0u;
}

void host_cadence_reset(host_cadence *cadence, uint64_t generation, uint64_t frame) {
    cadence->dirty = false;
    cadence->observed_generation = generation;
    cadence->flushed_generation = generation;
    cadence->first_dirty_frame = frame;
    cadence->last_change_frame = frame;
    cadence->last_compare_frame = frame;
    cadence->retry_after_frame = 0u;
}

host_cadence_action host_cadence_step(host_cadence *cadence, uint64_t frame, uint64_t generation) {
    /* Any difference counts, including a decrease: a state load or an import may move the counter
     * backwards, and a guest write after it must still be noticed. */
    if (generation != cadence->observed_generation) {
        cadence->observed_generation = generation;
        if (!cadence->dirty) {
            cadence->dirty = true;
            cadence->first_dirty_frame = frame;
        }
        cadence->last_change_frame = frame;
    }
    if (frame < cadence->retry_after_frame) return HOST_CADENCE_NONE; /* back off after a failed flush */
    if (cadence->dirty &&
        (elapsed(frame, cadence->last_change_frame) >= GBB_HOST_QUIET_FRAMES ||
         elapsed(frame, cadence->first_dirty_frame) >= GBB_HOST_MAX_DIRTY_FRAMES))
        return HOST_CADENCE_FLUSH;
    if (elapsed(frame, cadence->last_compare_frame) >= GBB_HOST_RTC_COMPARE_FRAMES)
        return HOST_CADENCE_EXPORT_COMPARE;
    return HOST_CADENCE_NONE;
}

void host_cadence_flushed(host_cadence *cadence, uint64_t generation, uint64_t frame) {
    cadence->dirty = false;
    cadence->flushed_generation = generation;
    cadence->last_compare_frame = frame;
    cadence->retry_after_frame = 0u;
}

void host_cadence_flush_failed(host_cadence *cadence, uint64_t frame) {
    /* D-11 says only "retried at the next cadence point". A 16-frame back-off is the recorded
     * discretion choice: it retries within about a quarter second but cannot spin on a full disk. */
    if (!cadence->dirty) {
        cadence->dirty = true; /* an RTC-compare write failed: the unwritten image is still pending */
        cadence->first_dirty_frame = frame;
        cadence->last_change_frame = frame;
    }
    cadence->retry_after_frame = frame + GBB_HOST_QUIET_FRAMES;
}
