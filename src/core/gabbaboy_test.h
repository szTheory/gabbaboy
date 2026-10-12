#ifndef GBB_CORE_TEST_H
#define GBB_CORE_TEST_H

/* Private test seams of the core. Not public ABI and not installed: the in-tree runner and tests
 * include this header so a signature change fails to compile instead of mis-linking. */

#include "gabbaboy/gabbaboy.h"

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* The address the core LAST refused (D-26 evidence). A failed read pre-flight records its address; every
 * deferred or serial write overwrites it. An instruction that issues two refused writes (PUSH or CALL
 * with SP just above FF77, or the interrupt-entry push) therefore reports the later one, which
 * cgb_visibility_deferred_latch_interrupt pins. A caller comparing against one declared address must
 * expect that. The value is cleared when the stop is reported. Read-only; runs no guest code. */
uint16_t gbb_test_last_unsupported_address(const gbb_instance *m);

#ifdef __cplusplus
}
#endif

#endif
