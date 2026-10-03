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
    GBB_INVALID_ROM,
    GBB_OUT_OF_MEMORY
} gbb_error;

typedef enum {
    GBB_STOP_BUDGET = 0,
    GBB_STOP_UNSUPPORTED_OPCODE,
    GBB_STOP_TRACE_FULL,
    GBB_STOP_INVALID_STATE
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
} gbb_run_result;

gbb_error gbb_create(gbb_profile profile, gbb_instance **out_instance);
void gbb_destroy(gbb_instance *instance);
gbb_error gbb_load_rom(gbb_instance *instance, const uint8_t *rom, size_t rom_size);
gbb_run_result gbb_run(gbb_instance *instance, uint64_t budget_half_dots,
                       gbb_trace_record *trace, size_t trace_capacity);
uint8_t gbb_peek_ram(const gbb_instance *instance, uint16_t address);

#ifdef __cplusplus
}
#endif
#endif
