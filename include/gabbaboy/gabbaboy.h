#ifndef GABBABOY_GABBABOY_H
#define GABBABOY_GABBABOY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct gbb_instance gbb_instance;

typedef enum {
    GBB_PROFILE_DMG_CPU_B = 1
} gbb_profile;

typedef enum {
    GBB_OK = 0,
    GBB_INVALID_ARGUMENT,
    GBB_UNSUPPORTED_PROFILE,
    GBB_INVALID_ROM,          /* malformed header or header checksum */
    GBB_ROM_TRUNCATED,        /* image ends before header or declared ROM size */
    GBB_ROM_TOO_LARGE,        /* actual image exceeds the 8 MiB hard limit */
    GBB_ROM_SIZE_MISMATCH,    /* actual image is longer than its declared ROM size */
    GBB_UNSUPPORTED_CARTRIDGE,/* cartridge type is not ROM-only */
    GBB_UNSUPPORTED_ROM_SIZE, /* header declares an unsupported ROM size code */
    GBB_UNSUPPORTED_RAM_SIZE, /* cartridge header declares external RAM */
    GBB_OUT_OF_MEMORY         /* allocation failed; live instance is unchanged */
} gbb_error;

typedef enum {
    GBB_STOP_BUDGET = 0,
    GBB_STOP_UNSUPPORTED_OPCODE,
    GBB_STOP_TRACE_FULL,
    GBB_STOP_INVALID_STATE,
    GBB_STOP_UNSUPPORTED_BUS,
    GBB_STOP_LOCKUP
} gbb_stop_reason;

typedef struct {
    uint64_t time_half_dots;
    uint16_t pc;
    uint8_t opcode[3];
    uint8_t opcode_size;
    uint8_t a, f, b, c, d, e, h, l;
    uint16_t sp;
} gbb_trace_record;

typedef struct {
    uint64_t consumed_half_dots;
    gbb_stop_reason reason;
    size_t trace_count;
    uint16_t lockup_pc;
    uint8_t lockup_opcode;
} gbb_run_result;

/* The opaque instance owns its mutable state and a private copy of a loaded ROM.
 * Create/load may allocate; run/reset/peek do not. Each instance may be called
 * by one thread at a time. Separate instances have no shared mutable state.
 * The only implemented model is bootless DMG-CPU-B deterministic post-boot. */
gbb_error gbb_create(gbb_profile profile, gbb_instance **out_instance);
void gbb_destroy(gbb_instance *instance);
/* Reset restores the documented post-boot CPU/profile state, clears guest RAM
 * and emulated time, and retains the currently loaded ROM. */
gbb_error gbb_reset(gbb_instance *instance);
/* ROM bytes are copied on success; caller storage may be released immediately.
 * A failed replacement leaves the current ROM and machine state unchanged.
 * Supports only exact-size 32 KiB ROM-only images with no cartridge RAM. */
gbb_error gbb_load_rom(gbb_instance *instance, const uint8_t *rom, size_t rom_size);
/* Runs only whole supported instructions. Budget/consumed values are uint64
 * half-dot ticks. An instruction is preflighted and won't start unless its
 * full cost fits. Trace records are optional caller-owned storage; the core
 * writes no more than capacity, allocates nothing, and never overwrites prior
 * records. trace=NULL is valid only with capacity=0. Trace bytes are snapshots
 * at instruction boundaries and remain owned by the caller. */
gbb_run_result gbb_run(gbb_instance *instance, uint64_t budget_half_dots,
                       gbb_trace_record *trace, size_t trace_capacity);
/* Side-effect-free debug read of WRAM (C000-DFFF and its E000-FDFF echo) or
 * HRAM (FF80-FFFE). Other addresses and a null instance return 0xFF. No
 * pointer into instance storage is exposed. */
uint8_t gbb_peek_ram(const gbb_instance *instance, uint16_t address);

#ifdef __cplusplus
}
#endif
#endif
