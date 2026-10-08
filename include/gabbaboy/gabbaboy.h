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
    GBB_ROM_TOO_LARGE,        /* actual image exceeds the 2 MiB hard limit */
    GBB_ROM_SIZE_MISMATCH,    /* actual image is longer than its declared ROM size */
    GBB_UNSUPPORTED_CARTRIDGE,/* cartridge type is outside the supported matrix */
    GBB_UNSUPPORTED_CARTRIDGE_VARIANT, /* recognized MBC1M wiring is unsupported */
    GBB_UNSUPPORTED_ROM_SIZE, /* header declares an unsupported ROM size code */
    GBB_UNSUPPORTED_RAM_SIZE, /* cartridge header declares external RAM */
    GBB_NO_BATTERY,           /* loaded cartridge has no battery-backed RAM */
    GBB_BUFFER_TOO_SMALL,     /* caller output buffer cannot hold all battery RAM */
    GBB_BATTERY_SIZE_MISMATCH,/* battery import is not the exact cartridge RAM size */
    GBB_OUT_OF_MEMORY,        /* allocation failed; live instance is unchanged */
    GBB_EVENT_QUEUE_FULL,
    GBB_INVALID_EVENT,
    GBB_FRAME_NOT_READY
} gbb_error;

typedef enum {
    GBB_STOP_BUDGET = 0,
    GBB_STOP_UNSUPPORTED_OPCODE,
    GBB_STOP_TRACE_FULL,
    GBB_STOP_INVALID_STATE,
    GBB_STOP_UNSUPPORTED_BUS,
    GBB_STOP_LOCKUP,
    GBB_STOP_HALTED_IDLE,    /* eligible idle ticks advanced; machine remains halted */
    GBB_STOP_STOPPED,        /* STOP entered; oscillator remains paused until modeled wake */
    GBB_STOP_NO_PROGRESS,
    GBB_STOP_OUTPUT_FULL = GBB_STOP_TRACE_FULL
} gbb_stop_reason;

typedef enum {
    GBB_INPUT_STOP_WAKE = 1,
    GBB_INPUT_SERIAL_EDGE = 2,
    GBB_INPUT_BUTTON_PRESS = 3,
    GBB_INPUT_BUTTON_RELEASE = 4
} gbb_input_event_kind;

typedef enum {
    GBB_BUTTON_RIGHT = 0,
    GBB_BUTTON_LEFT = 1,
    GBB_BUTTON_UP = 2,
    GBB_BUTTON_DOWN = 3,
    GBB_BUTTON_A = 4,
    GBB_BUTTON_B = 5,
    GBB_BUTTON_SELECT = 6,
    GBB_BUTTON_START = 7
} gbb_button;

typedef struct {
    uint64_t at_half_dots;
    gbb_input_event_kind kind;
    uint8_t value;
} gbb_input_event;

typedef struct {
    uint64_t time_half_dots;
    uint16_t pc;
    uint8_t opcode[3];
    uint8_t opcode_size;
    uint8_t a, f, b, c, d, e, h, l;
    uint16_t sp;
} gbb_trace_record;

typedef enum {
    GBB_DIAGNOSTIC_INSTRUCTION = 1,
    GBB_DIAGNOSTIC_BUS_READ,
    GBB_DIAGNOSTIC_BUS_WRITE,
    GBB_DIAGNOSTIC_TIMER
} gbb_diagnostic_kind;

typedef struct {
    uint64_t time_half_dots;
    gbb_diagnostic_kind kind;
    uint16_t pc;
    uint8_t opcode;
    uint16_t address;
    uint8_t value;
    uint8_t timer_state;
} gbb_diagnostic_record;

typedef struct {
    uint64_t consumed_half_dots;
    gbb_stop_reason reason;
    size_t trace_count;
    size_t diagnostic_count;
    uint16_t lockup_pc;
    uint8_t lockup_opcode;
} gbb_run_result;

typedef struct {
    int16_t left;
    int16_t right;
} gbb_audio_frame;

typedef struct {
    uint32_t width;
    uint32_t height;
    uint64_t generation;
    uint64_t completion_half_dots;
} gbb_frame_info;

/* The opaque instance owns its mutable state and a private copy of a loaded ROM.
 * Create/load may allocate; run/reset/peek do not. Each instance may be called
 * by one thread at a time. Separate instances have no shared mutable state.
 * The only implemented model is bootless DMG-CPU-B deterministic post-boot. */
gbb_error gbb_create(gbb_profile profile, gbb_instance **out_instance);
void gbb_destroy(gbb_instance *instance);
/* Reset restores the documented post-boot CPU/profile state, clears work RAM
 * and emulated time, and retains the loaded ROM and cartridge RAM. */
gbb_error gbb_reset(gbb_instance *instance);
/* ROM bytes are copied on success; caller storage may be released immediately.
 * A failed replacement leaves the current ROM and machine state unchanged.
 * Supports 32 KiB ROM-only images and standard MBC1 types $01-$03, ROM-size
 * codes $00-$06, and the documented no-RAM/8-KiB/32-KiB header matrix. 32-KiB
 * RAM is accepted only through 512 KiB ROM; larger MBC1 images may declare
 * only 8-KiB RAM. The conservative, recognized MBC1M logo/header candidate
 * returns GBB_UNSUPPORTED_CARTRIDGE_VARIANT; this does not identify every
 * special-wiring image. New cartridge RAM starts at $FF as deterministic
 * software policy, not a hardware power-on claim. */
gbb_error gbb_load_rom(gbb_instance *instance, const uint8_t *rom, size_t rom_size);
/* Battery RAM is available only for supported battery-backed cartridges.
 * Query the exact size, then copy/import through caller-owned buffers. No core
 * filesystem access or mutable instance pointer is exposed. A successful
 * import validates its full exact size before changing live RAM; it advances
 * the generation once only when at least one byte changes. Changed guest
 * writes advance the generation once per changed byte; unchanged writes do
 * not. Reset preserves RAM and generation, while successful ROM replacement
 * starts a fresh $FF image with generation zero. On errors, output values and
 * live RAM remain unchanged. */
gbb_error gbb_battery_size(const gbb_instance *instance, size_t *out_size);
gbb_error gbb_copy_battery(const gbb_instance *instance, uint8_t *out_bytes,
                           size_t capacity_bytes);
gbb_error gbb_import_battery(gbb_instance *instance, const uint8_t *bytes,
                             size_t size_bytes);
gbb_error gbb_battery_generation(const gbb_instance *instance,
                                 uint64_t *out_generation);
/* Copies events into a fixed 64-event per-instance queue. Timestamps are
 * absolute half-dot ticks and must be nondecreasing within the batch and no
 * earlier than the instance's current time. Equal timestamps keep caller
 * order. STOP_WAKE value 1 is a separate modeled STOP wake; SERIAL_EDGE value
 * is the input bit sampled by the disconnected serial endpoint;
 * BUTTON_PRESS/RELEASE value is a gbb_button identifier. Button events are
 * consumed by active-low FF00 row polling; JOYP IF generation is not modeled
 * while its DMG-CPU-B evidence gate remains open. STOP_WAKE does not imply a
 * JOYP interrupt, and this is not a host wall-clock input API. Admission is
 * atomic: an invalid top-level pointer returns GBB_INVALID_ARGUMENT; empty
 * batches, including NULL/0, succeed. For nonempty batches with valid pointers,
 * remaining capacity is checked before event contents, so an over-capacity
 * batch returns GBB_EVENT_QUEUE_FULL even if an entry is malformed. Otherwise,
 * malformed, past or unordered events return GBB_INVALID_EVENT. Rejected
 * batches append nothing. Consumed events free queue capacity. */
gbb_error gbb_queue_events(gbb_instance *instance, const gbb_input_event *events, size_t count);
/* Copies the latest completed 160x144 frame as one byte per pixel. Each byte
 * is a DMG shade index in [0,3]. pitch_bytes is the destination row stride;
 * capacity_bytes must cover (height-1)*pitch_bytes + width bytes. The entire
 * capacity_bytes range must not overlap out_info. Output remains caller-owned,
 * the core allocates nothing, and no pointer into instance storage is exposed.
 * Checked arithmetic, pointers, pitch, capacity, and overlap are validated
 * before either output is written. Invalid ranges return GBB_INVALID_ARGUMENT;
 * GBB_FRAME_NOT_READY is returned only after valid arguments are established.
 * Reset invalidates the completed frame. On every error, pixels and out_info
 * remain unchanged. */
gbb_error gbb_copy_frame(const gbb_instance *instance, uint8_t *pixels,
                         size_t capacity_bytes, size_t pitch_bytes,
                         gbb_frame_info *out_info);
/* Runs whole supported instructions. GBB_STOP_HALTED_IDLE means the run has
 * consumed eligible idle ticks and the CPU remains halted; GBB_STOP_STOPPED
 * means STOP is waiting for a modeled wake event. A positive STOP wait can
 * consume master timeline ticks while CPU, divider, timer and internal serial
 * oscillator work remains frozen. An accepted wake is applied at its timestamp
 * before another CPU fetch. The caller's budget bounds all idle progression.
 * Budget/consumed values are uint64 half-dot ticks. An instruction is
 * preflighted and won't start unless its full cost fits. GBB_STOP_NO_PROGRESS
 * is distinct from STOPPED, HALTED_IDLE, LOCKUP, UNSUPPORTED_BUS,
 * INVALID_STATE, OUTPUT_FULL and normal GBB_STOP_BUDGET completion. Trace
 * records are optional caller-owned storage; the core
 * writes no more than capacity, allocates nothing, and never overwrites prior
 * records. trace=NULL is valid only with capacity=0. Trace bytes are snapshots
 * at instruction boundaries and remain owned by the caller. */
gbb_run_result gbb_run(gbb_instance *instance, uint64_t budget_half_dots,
                       gbb_trace_record *trace, size_t trace_capacity);
/* Extended run with optional caller-owned diagnostics. Both output buffers
 * remain owned by the caller. NULL is valid only with zero capacity; capacity
 * is measured in records, records are chronological, and actual written
 * counts are returned. The core allocates/formats nothing. Diagnostics reserve
 * a complete operation before it mutates state; an insufficient reserve stops
 * with GBB_STOP_OUTPUT_FULL and writes no record for that operation. Trace and
 * diagnostic counts report records written by this call. */
gbb_run_result gbb_run_ex(gbb_instance *instance, uint64_t budget_half_dots,
                          gbb_trace_record *trace, size_t trace_capacity,
                          gbb_diagnostic_record *diagnostics,
                          size_t diagnostic_capacity);
/* Audio-aware run. Emits 48 kHz signed 16-bit stereo into caller-owned
 * storage; the core allocates nothing. A NULL buffer is valid only with zero
 * capacity. If the next whole instruction could exceed capacity, it stops
 * before mutating guest state with GBB_STOP_OUTPUT_FULL. out_frame_count is
 * always written when non-NULL. Legacy gbb_run/gbb_run_ex are explicitly
 * muted runs. */
gbb_run_result gbb_run_audio(gbb_instance *instance, uint64_t budget_half_dots,
                             gbb_audio_frame *frames, size_t frame_capacity,
                             size_t *out_frame_count);
/* Side-effect-free debug read of WRAM (C000-DFFF and its E000-FDFF echo) or
 * HRAM (FF80-FFFE). Other addresses and a null instance return 0xFF. No
 * pointer into instance storage is exposed. */
uint8_t gbb_peek_ram(const gbb_instance *instance, uint16_t address);

#ifdef __cplusplus
}
#endif
#endif
