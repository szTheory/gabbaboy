#include "gabbaboy/gabbaboy.h"

#include <stdbool.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static atomic_bool watching_allocations;
static atomic_uint allocation_calls;

static void record_allocator_call(void) {
    if (atomic_load_explicit(&watching_allocations, memory_order_relaxed))
        atomic_fetch_add_explicit(&allocation_calls, 1u, memory_order_relaxed);
}

void *gbb_test_malloc(size_t size) {
    record_allocator_call();
    return malloc(size);
}

void *gbb_test_calloc(size_t count, size_t size) {
    record_allocator_call();
    return calloc(count, size);
}

void *gbb_test_realloc(void *pointer, size_t size) {
    record_allocator_call();
    return realloc(pointer, size);
}

void gbb_test_free(void *pointer) {
    record_allocator_call();
    free(pointer);
}

static void begin_measurement(void) {
    atomic_store_explicit(&allocation_calls, 0u, memory_order_relaxed);
    atomic_store_explicit(&watching_allocations, true, memory_order_relaxed);
}

static unsigned end_measurement(void) {
    atomic_store_explicit(&watching_allocations, false, memory_order_relaxed);
    return atomic_load_explicit(&allocation_calls, memory_order_relaxed);
}

static void fix_header_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

int main(void) {
    static const uint8_t pulse_program[] = {
        0x3Eu, 0xF0u, 0xEAu, 0x12u, 0xFFu,
        0x3Eu, 0x80u, 0xEAu, 0x11u, 0xFFu,
        0x3Eu, 0xF0u, 0xEAu, 0x13u, 0xFFu,
        0x3Eu, 0x87u, 0xEAu, 0x14u, 0xFFu,
        0x18u, 0xFEu
    };
    uint8_t rom[32768] = {0};
    memcpy(rom + 0x100u, pulse_program, sizeof(pulse_program));
    fix_header_checksum(rom);

    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        fputs("could not prepare the authored pulse guest\n", stderr);
        return 1;
    }

    gbb_audio_frame frames[804] = {{0}};
    size_t frame_count = 0u;
    begin_measurement();
    const gbb_run_result result = gbb_run_audio(machine, 140448u, frames,
                                                 804u, &frame_count);
    const unsigned successful_run_allocations = end_measurement();
    if (result.reason != GBB_STOP_BUDGET || result.consumed_half_dots != 140448u ||
        frame_count != 803u || successful_run_allocations != 0u) {
        fprintf(stderr, "audio run reason=%d elapsed=%llu frames=%zu allocations=%u\n",
                result.reason, (unsigned long long)result.consumed_half_dots,
                frame_count, successful_run_allocations);
        gbb_destroy(machine);
        return 1;
    }

    size_t rejected_count = 0u;
    begin_measurement();
    const gbb_run_result rejected = gbb_run_audio(machine, 400u, NULL, 0u,
                                                   &rejected_count);
    const unsigned rejected_run_allocations = end_measurement();
    if (rejected.reason != GBB_STOP_OUTPUT_FULL || rejected_count != 0u ||
        rejected_run_allocations != 0u) {
        fprintf(stderr, "capacity run reason=%d frames=%zu allocations=%u\n",
                rejected.reason, rejected_count, rejected_run_allocations);
        gbb_destroy(machine);
        return 1;
    }

    gbb_destroy(machine);
    puts("audio_no_alloc: successful PCM and output-full runs made no heap calls");
    return 0;
}
