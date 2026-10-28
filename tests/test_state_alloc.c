/* Instrument the real core in one translation unit so allocator calls and the
 * private SHA observer remain attributable to each public state operation. */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void *gbb_state_test_malloc(size_t size);
void *gbb_state_test_calloc(size_t count, size_t size);
void *gbb_state_test_realloc(void *pointer, size_t size);
void gbb_state_test_free(void *pointer);

#define malloc gbb_state_test_malloc
#define calloc gbb_state_test_calloc
#define realloc gbb_state_test_realloc
#define free gbb_state_test_free
#define GBB_TEST_STATE_HASH_COUNTER 1
#ifndef GBB_CORE_SOURCE_PATH
#define GBB_CORE_SOURCE_PATH "../src/core/gabbaboy.c"
#endif
#include GBB_CORE_SOURCE_PATH
#undef malloc
#undef calloc
#undef realloc
#undef free

#ifndef GBB_STATE_SOURCE_REV
#define GBB_STATE_SOURCE_REV "unknown"
#endif

typedef struct {
    size_t heap_calls;
    size_t request_bytes;
    size_t largest_request;
} heap_probe;

static int heap_probe_active;
static heap_probe current_heap_probe;

static void record_heap_call(size_t requested_bytes) {
    if (!heap_probe_active) return;
    ++current_heap_probe.heap_calls;
    if (requested_bytes > SIZE_MAX - current_heap_probe.request_bytes)
        current_heap_probe.request_bytes = SIZE_MAX;
    else
        current_heap_probe.request_bytes += requested_bytes;
    if (requested_bytes > current_heap_probe.largest_request)
        current_heap_probe.largest_request = requested_bytes;
}

void *gbb_state_test_malloc(size_t size) {
    record_heap_call(size);
    return malloc(size);
}

void *gbb_state_test_calloc(size_t count, size_t size) {
    const size_t bytes = count != 0u && size > SIZE_MAX / count ? SIZE_MAX : count * size;
    record_heap_call(bytes);
    return calloc(count, size);
}

void *gbb_state_test_realloc(void *pointer, size_t size) {
    record_heap_call(size);
    return realloc(pointer, size);
}

void gbb_state_test_free(void *pointer) {
    record_heap_call(0u);
    free(pointer);
}

static void probe_begin(void) {
    memset(&current_heap_probe, 0, sizeof(current_heap_probe));
    state_sha256_test_calls = 0u;
    heap_probe_active = 1;
}

static heap_probe probe_end(uint64_t *hash_calls) {
    heap_probe_active = 0;
    *hash_calls = state_sha256_test_calls;
    return current_heap_probe;
}

static int probe_is_pure(const char *operation, heap_probe heap, uint64_t hashes) {
    if (heap.heap_calls == 0u && heap.request_bytes == 0u && hashes == 0u &&
        heap.largest_request <= GBB_STATE_MAX_BODY_BYTES + GBB_STATE_HEADER_BYTES)
        return 1;
    fprintf(stderr,
        "state_purity failure: operation=%s heap_calls=%zu request_bytes=%zu largest=%zu hashes=%llu\n",
        operation, heap.heap_calls, heap.request_bytes, heap.largest_request,
        (unsigned long long)hashes);
    return 0;
}

typedef struct {
    gbb_instance raw;
    uint8_t *rom;
    uint8_t *ram;
} state_alloc_snapshot;

static int snapshot_init(state_alloc_snapshot *snapshot, const gbb_instance *instance) {
    memset(snapshot, 0, sizeof(*snapshot));
    snapshot->rom = instance->rom_size == 0u ? NULL : malloc(instance->rom_size);
    snapshot->ram = instance->cartridge_ram_size == 0u ? NULL :
                    malloc(instance->cartridge_ram_size);
    if ((instance->rom_size != 0u && snapshot->rom == NULL) ||
        (instance->cartridge_ram_size != 0u && snapshot->ram == NULL)) {
        free(snapshot->rom);
        free(snapshot->ram);
        memset(snapshot, 0, sizeof(*snapshot));
        return 0;
    }
    return 1;
}

static void snapshot_capture(state_alloc_snapshot *snapshot,
                             const gbb_instance *instance) {
    memcpy(&snapshot->raw, instance, sizeof(*instance));
    if (instance->rom_size != 0u) memcpy(snapshot->rom, instance->rom, instance->rom_size);
    if (instance->cartridge_ram_size != 0u)
        memcpy(snapshot->ram, instance->cartridge_ram, instance->cartridge_ram_size);
}

static int snapshot_matches(const state_alloc_snapshot *snapshot,
                            const gbb_instance *instance) {
    return memcmp(&snapshot->raw, instance, sizeof(*instance)) == 0 &&
           (instance->rom_size == 0u ||
            memcmp(snapshot->rom, instance->rom, instance->rom_size) == 0) &&
           (instance->cartridge_ram_size == 0u ||
            memcmp(snapshot->ram, instance->cartridge_ram,
                   instance->cartridge_ram_size) == 0);
}

static void snapshot_destroy(state_alloc_snapshot *snapshot) {
    free(snapshot->rom);
    free(snapshot->ram);
    memset(snapshot, 0, sizeof(*snapshot));
}

static void fix_header_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void build_rom(uint8_t rom[32768]) {
    memset(rom, 0, 32768u);
    rom[0x147u] = 0x10u; /* MBC3 timer + RAM + battery. */
    rom[0x149u] = 0x02u;
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    rom[0x200u] = 0x18u;
    rom[0x201u] = 0xFEu;
    fix_header_checksum(rom);
}

static gbb_instance *new_machine(const uint8_t rom[32768]) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768u) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static int state_purity_controls(void) {
    uint8_t digest[32];
    probe_begin();
    void *allocation = gbb_state_test_malloc(7u);
    gbb_state_test_free(allocation);
    state_sha256((const uint8_t *)"purity-control", 14u, digest);
    uint64_t hashes = 0u;
    const heap_probe heap = probe_end(&hashes);
    if (allocation == NULL || heap.heap_calls != 2u || heap.request_bytes != 7u ||
        heap.largest_request != 7u || hashes != 1u) {
        fprintf(stderr, "state_purity_controls failed allocator/hash hooks calls=%zu bytes=%zu hashes=%llu\n",
                heap.heap_calls, heap.request_bytes, (unsigned long long)hashes);
        return 1;
    }
    puts("state_purity_controls pass allocator=live hash=live");
    return 0;
}

static int state_purity(void) {
    const char *operation = "setup";
    uint8_t rom[32768];
    build_rom(rom);
    gbb_instance *source = new_machine(rom);
    gbb_instance *target_a = new_machine(rom);
    gbb_instance *target_b = new_machine(rom);
    gbb_instance *empty = NULL;
    if (source == NULL || target_a == NULL || target_b == NULL ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &empty) != GBB_OK) {
        gbb_destroy(empty); gbb_destroy(target_b); gbb_destroy(target_a); gbb_destroy(source);
        fputs("state_purity setup failed\n", stderr);
        return 1;
    }
    for (size_t i = 0u; i < source->cartridge_ram_size; ++i) {
        source->cartridge_ram[i] = (uint8_t)(0x29u + i * 11u);
        target_a->cartridge_ram[i] = (uint8_t)(0x91u + i * 7u);
        target_b->cartridge_ram[i] = (uint8_t)(0xE3u + i * 3u);
    }
    target_a->battery_generation = 5u;
    target_b->battery_generation = 73u;
    target_a->cart.rumble_changes = 11u;
    target_b->cart.rumble_changes = 137u;

    size_t size = 0u;
    if (gbb_state_size(source, &size) != GBB_OK) {
        fputs("state_purity setup size failed\n", stderr);
        gbb_destroy(empty); gbb_destroy(target_b); gbb_destroy(target_a); gbb_destroy(source);
        return 1;
    }
    uint8_t *state = malloc(size + 16u);
    uint8_t *invalid = malloc(size);
    uint8_t *valid_state = malloc(size);
    state_alloc_snapshot source_snapshot, a_snapshot, b_snapshot, empty_snapshot;
    int initialized = state != NULL && invalid != NULL && valid_state != NULL &&
        snapshot_init(&source_snapshot, source) && snapshot_init(&a_snapshot, target_a) &&
        snapshot_init(&b_snapshot, target_b) && snapshot_init(&empty_snapshot, empty);
    if (!initialized) {
        fputs("state_purity setup buffers failed\n", stderr);
        free(state); free(invalid); free(valid_state);
        gbb_destroy(empty); gbb_destroy(target_b); gbb_destroy(target_a); gbb_destroy(source);
        return 1;
    }
    memset(state, 0xA6u, size + 16u);
    snapshot_capture(&source_snapshot, source);
    operation = "size_success";
    probe_begin();
    size_t observed_size = 0u;
    const gbb_error size_result = gbb_state_size(source, &observed_size);
    uint64_t hashes = 0u;
    heap_probe heap = probe_end(&hashes);
    if (size_result != GBB_OK || observed_size != size ||
        !probe_is_pure("size_success", heap, hashes) ||
        !snapshot_matches(&source_snapshot, source)) goto fail;

    snapshot_capture(&source_snapshot, source);
    operation = "save_success";
    probe_begin();
    const gbb_error save_result = gbb_save_state(source, state, size + 16u);
    heap = probe_end(&hashes);
    if (save_result != GBB_OK || !probe_is_pure("save_success", heap, hashes) ||
        !snapshot_matches(&source_snapshot, source)) goto fail;
    memcpy(valid_state, state, size);
    for (size_t i = size; i < size + 16u; ++i)
        if (state[i] != 0xA6u) {
            fputs("state_purity failure: save tail modified\n", stderr);
            goto fail;
        }

    memset(state, 0x5Cu, size + 16u);
    snapshot_capture(&source_snapshot, source);
    operation = "save_short";
    probe_begin();
    const gbb_error short_result = gbb_save_state(source, state, size - 1u);
    heap = probe_end(&hashes);
    if (short_result != GBB_BUFFER_TOO_SMALL || !probe_is_pure("save_short", heap, hashes) ||
        !snapshot_matches(&source_snapshot, source)) goto fail;
    for (size_t i = 0u; i < size + 16u; ++i)
        if (state[i] != 0x5Cu) {
            fputs("state_purity failure: short save output modified\n", stderr);
            goto fail;
        }

    memcpy(invalid, valid_state, size);
    invalid[60] ^= 1u;
    snapshot_capture(&a_snapshot, target_a);
    snapshot_capture(&b_snapshot, target_b);
    operation = "load_success";
    probe_begin();
    const gbb_error load_result = gbb_load_state(target_a, valid_state, size);
    heap = probe_end(&hashes);
    if (load_result != GBB_OK || !probe_is_pure("load_success", heap, hashes) ||
        !snapshot_matches(&b_snapshot, target_b)) goto fail;

    snapshot_capture(&a_snapshot, target_a);
    operation = "load_invalid";
    probe_begin();
    const gbb_error invalid_result = gbb_load_state(target_a, invalid, size);
    heap = probe_end(&hashes);
    if (invalid_result != GBB_STATE_CORRUPT ||
        !probe_is_pure("load_invalid", heap, hashes) ||
        !snapshot_matches(&a_snapshot, target_a)) goto fail;

    operation = "size_error";
    probe_begin();
    const gbb_error null_size = gbb_state_size(source, NULL);
    heap = probe_end(&hashes);
    if (null_size != GBB_INVALID_ARGUMENT || !probe_is_pure("size_error", heap, hashes)) goto fail;
    operation = "save_error";
    operation = "load_error";
    probe_begin();
    const gbb_error null_save = gbb_save_state(source, NULL, size);
    heap = probe_end(&hashes);
    if (null_save != GBB_INVALID_ARGUMENT || !probe_is_pure("save_error", heap, hashes)) goto fail;
    probe_begin();
    const gbb_error null_load = gbb_load_state(target_a, NULL, size);
    heap = probe_end(&hashes);
    if (null_load != GBB_INVALID_ARGUMENT || !probe_is_pure("load_error", heap, hashes)) goto fail;

    snapshot_capture(&empty_snapshot, empty);
    operation = "size_no_rom";
    probe_begin();
    const gbb_error empty_size = gbb_state_size(empty, &observed_size);
    heap = probe_end(&hashes);
    if (empty_size != GBB_STATE_NO_ROM || !probe_is_pure("size_no_rom", heap, hashes) ||
        !snapshot_matches(&empty_snapshot, empty)) goto fail;
    operation = "save_no_rom";
    operation = "load_no_rom";
    probe_begin();
    const gbb_error empty_save = gbb_save_state(empty, state, size + 16u);
    heap = probe_end(&hashes);
    if (empty_save != GBB_STATE_NO_ROM || !probe_is_pure("save_no_rom", heap, hashes) ||
        !snapshot_matches(&empty_snapshot, empty)) goto fail;
    probe_begin();
    const gbb_error empty_load = gbb_load_state(empty, valid_state, size);
    heap = probe_end(&hashes);
    if (empty_load != GBB_STATE_NO_ROM || !probe_is_pure("load_no_rom", heap, hashes) ||
        !snapshot_matches(&empty_snapshot, empty)) goto fail;

    snapshot_destroy(&empty_snapshot); snapshot_destroy(&b_snapshot);
    snapshot_destroy(&a_snapshot); snapshot_destroy(&source_snapshot);
    free(valid_state); free(invalid); free(state);
    gbb_destroy(empty); gbb_destroy(target_b); gbb_destroy(target_a); gbb_destroy(source);
    puts("state_purity pass public_calls=success_and_error heap=0 hashes=0 size_save=observationally-pure instances=independent");
    return 0;

fail:
    fprintf(stderr, "state_purity failure: operation=%s result_or_snapshot\n", operation);
    snapshot_destroy(&empty_snapshot); snapshot_destroy(&b_snapshot);
    snapshot_destroy(&a_snapshot); snapshot_destroy(&source_snapshot);
    free(valid_state); free(invalid); free(state);
    gbb_destroy(empty); gbb_destroy(target_b); gbb_destroy(target_a); gbb_destroy(source);
    return 1;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--source-revision") == 0) {
        printf("source_revision=%s\n", GBB_STATE_SOURCE_REV);
        return 0;
    }
    if (argc != 2) return 2;
    if (strcmp(argv[1], "state_purity") == 0) return state_purity();
    if (strcmp(argv[1], "state_purity_controls") == 0) return state_purity_controls();
    fprintf(stderr, "unknown state allocation case: %s\n", argv[1]);
    return 2;
}
