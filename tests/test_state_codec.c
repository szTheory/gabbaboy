/* Public state-API identity and continuation matrix. This translation unit includes
 * the core so the test-only SHA observer can count exact ROM hashing work and
 * semantic fixtures can produce checksum-correct hostile state buffers. */
#define GBB_TEST_STATE_HASH_COUNTER 1
#include "../src/core/gabbaboy.c"

#include <stdio.h>

#define REQUIRE_CASE(name, condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", (name), __LINE__, #condition); \
        return 1; \
    } \
} while (0)

#define TEST_ROM_BYTES 0x8000u
#define TEST_STATE_HEADER_BYTES 64u

static int same_run_result(gbb_run_result a, gbb_run_result b);

static void test_header_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void test_build_rom(uint8_t *rom, uint8_t cartridge_type, uint8_t cgb_flag) {
    memset(rom, 0, TEST_ROM_BYTES);
    static const uint8_t title[] = "GBB STATE MATRIX";
    memcpy(rom + 0x134u, title, sizeof(title) - 1u);
    rom[0x143u] = cgb_flag;
    rom[0x147u] = cartridge_type;
    rom[0x148u] = 0u; /* 32 KiB, two ROM banks. */
    switch (cartridge_type) {
        case 0x03u: /* MBC1 + RAM + battery */
        case 0x10u: /* MBC3 + timer + RAM + battery */
        case 0x1Eu: /* MBC5 + rumble + RAM + battery */
            rom[0x149u] = 0x02u; /* 8 KiB RAM */
            break;
        default:
            rom[0x149u] = 0u;
            break;
    }
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x00u; rom[0x102u] = 0x02u;
    static const uint8_t sound_loop[] = {
        0x3Eu, 0xF0u, 0xEAu, 0x12u, 0xFFu,
        0x3Eu, 0x80u, 0xEAu, 0x11u, 0xFFu,
        0x3Eu, 0xF0u, 0xEAu, 0x13u, 0xFFu,
        0x3Eu, 0x87u, 0xEAu, 0x14u, 0xFFu,
        0x18u, 0xFEu
    };
    memcpy(rom + 0x200u, sound_loop, sizeof(sound_loop));
    test_header_checksum(rom);
}

static int test_hex_matches(const uint8_t digest[32], const char *hex) {
    static const char digits[] = "0123456789abcdef";
    for (size_t i = 0u; i < 32u; ++i) {
        if (digits[digest[i] >> 4] != hex[i * 2u] ||
            digits[digest[i] & 0x0Fu] != hex[i * 2u + 1u]) return 0;
    }
    return hex[64] == '\0';
}

static int test_hex_check(const char *name, const uint8_t digest[32], const char *hex) {
    if (test_hex_matches(digest, hex)) return 1;
    fprintf(stderr, "SHA vector %s actual=", name);
    for (size_t i = 0u; i < 32u; ++i) fprintf(stderr, "%02x", digest[i]);
    fputc('\n', stderr);
    return 0;
}

static int test_sha_vectors(void) {
    uint8_t digest[32];
    static const char empty_hex[] =
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
    static const char abc_hex[] =
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    static const char multi_hex[] =
        "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1";
    static const char thousand_a_hex[] =
        "41edece42d63e8d9bf515a9ba6932e1c20cbc9f5a5d134645adb5db1b9737ea3";
    static const uint8_t multi_message[] =
        "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
    uint8_t thousand_a[1000];
    memset(thousand_a, 'a', sizeof(thousand_a));
    state_sha256(NULL, 0u, digest);
    if (!test_hex_check("empty", digest, empty_hex)) return 0;
    state_sha256((const uint8_t *)"abc", 3u, digest);
    if (!test_hex_check("abc", digest, abc_hex)) return 0;
    state_sha256(multi_message, sizeof(multi_message) - 1u, digest);
    if (!test_hex_check("multi", digest, multi_hex)) return 0;
    state_sha256(thousand_a, sizeof(thousand_a), digest);
    return test_hex_check("thousand_a", digest, thousand_a_hex);
}

/* Find a deterministic 40-bit null vector of the 32-bit CRC map for a five-byte
 * suffix. The construction is bounded (exactly 40 columns) and avoids a
 * probabilistic birthday search; both images remain identical through the ROM
 * header, title and size metadata. */
static int test_crc_collision_pair(const uint8_t *first, uint8_t *second,
                                   size_t rom_size) {
    enum { SUFFIX_BYTES = 5, VARIABLE_BITS = SUFFIX_BYTES * 8 };
    if (rom_size < SUFFIX_BYTES) return 0;
    uint32_t columns[VARIABLE_BITS];
    uint8_t variant[TEST_ROM_BYTES];
    if (rom_size > sizeof(variant)) return 0;
    memcpy(second, first, rom_size);
    const uint32_t baseline = state_crc32(first, rom_size);
    for (unsigned bit = 0u; bit < VARIABLE_BITS; ++bit) {
        memcpy(variant, first, rom_size);
        variant[rom_size - SUFFIX_BYTES + bit / 8u] ^=(uint8_t)(1u << (bit % 8u));
        columns[bit] = state_crc32(variant, rom_size) ^ baseline;
    }
    uint32_t basis[32] = {0};
    uint64_t basis_combination[32] = {0};
    uint64_t dependency = 0u;
    for (unsigned column = 0u; column < VARIABLE_BITS; ++column) {
        uint32_t value = columns[column];
        uint64_t combination = UINT64_C(1) << column;
        for (int bit = 31; bit >= 0; --bit) {
            const uint32_t mask = UINT32_C(1) << (unsigned)bit;
            if ((value & mask) == 0u) continue;
            if (basis[bit] != 0u) {
                value ^= basis[bit];
                combination ^= basis_combination[bit];
            } else {
                basis[bit] = value;
                basis_combination[bit] = combination;
                break;
            }
        }
        if (value == 0u) {
            dependency = combination;
            break;
        }
    }
    if (dependency == 0u) return 0;
    for (unsigned bit = 0u; bit < VARIABLE_BITS; ++bit)
        if ((dependency & (UINT64_C(1) << bit)) != 0u)
            second[rom_size - SUFFIX_BYTES + bit / 8u] ^=(uint8_t)(1u << (bit % 8u));
    return state_crc32(first, rom_size) == state_crc32(second, rom_size) &&
           memcmp(first, second, rom_size) != 0;
}

static size_t test_field_offset(const gbb_instance *instance, const char *path) {
    const state_field_descriptor *field = state_field_by_path(path);
    return field == NULL ? SIZE_MAX : state_body_field_offset(instance, field);
}

static int test_state_field_census(const gbb_instance *instance) {
    const size_t descriptor_count = sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]);
    size_t expected_offset = 0u;
    if (descriptor_count != 198u) return 0;
    for (size_t i = 0u; i < descriptor_count; ++i) {
        state_field_record record = {0};
        if (!state_record_field(instance, i, &record) || record.qualified_id == NULL ||
            strcmp(record.qualified_id, STATE_FIELDS[i].path) != 0 ||
            record.offset != expected_offset || record.width != STATE_FIELDS[i].wire_width ||
            record.count != state_field_count_for_instance(instance, &STATE_FIELDS[i]) ||
            record.treatment != STATE_TREAT_SERIALIZE ||
            record.count > (SIZE_MAX - expected_offset) / record.width) return 0;
        expected_offset += record.count * record.width;
    }
    size_t body_size = 0u;
    return state_walk(instance, NULL, NULL, 0u, STATE_WALK_SIZE, &body_size) &&
           expected_offset == body_size;
}

static void test_rechecksum(uint8_t *state, size_t total_size) {
    uint32_t crc = state_crc32_update(UINT32_MAX, state, 60u);
    crc = state_crc32_update(crc, state + TEST_STATE_HEADER_BYTES,
                             total_size - TEST_STATE_HEADER_BYTES) ^ UINT32_MAX;
    state_put_u32(state + 60u, crc);
}

static int test_header_rejection(gbb_instance *target, const uint8_t *state,
                                 size_t size, size_t offset, uint16_t value,
                                 gbb_error expected) {
    uint8_t *mutant = malloc(size);
    if (mutant == NULL) return 0;
    memcpy(mutant, state, size);
    state_put_u16(mutant + offset, value);
    const gbb_error got = gbb_load_state(target, mutant, size);
    free(mutant);
    return got == expected;
}

static size_t test_element_offset(const gbb_instance *instance, const char *path,
                                  size_t index) {
    const state_field_descriptor *field = state_field_by_path(path);
    if (field == NULL || index >= state_field_count_for_instance(instance, field))
        return SIZE_MAX;
    const size_t base = state_body_field_offset(instance, field);
    if (base == SIZE_MAX || index > (SIZE_MAX - base) / field->wire_width) return SIZE_MAX;
    return base + index * field->wire_width;
}

static int test_write_body_field(const gbb_instance *instance, uint8_t *state,
                                 const char *path, size_t index, uint64_t value) {
    const state_field_descriptor *field = state_field_by_path(path);
    const size_t offset = test_element_offset(instance, path, index);
    if (field == NULL || offset == SIZE_MAX || field->wire_width > 8u) return 0;
    state_put_u64(state + TEST_STATE_HEADER_BYTES + offset, value, field->wire_width);
    return 1;
}

typedef struct {
    const char *path;
    size_t index;
    uint64_t value;
} test_state_edit;

/* A refused load must leave the whole receiving instance unchanged. The instance
 * struct alone is not the whole instance: cartridge RAM and the ROM image are
 * separate heap allocations reached through pointers, and cartridge RAM is the
 * one field the load path writes through a pointer. The snapshot therefore keeps
 * the struct bytes (which include the pointer values and sizes) and a copy of
 * every owned RAM and ROM byte (review WR-A03). */
typedef struct {
    uint8_t *instance_bytes;
    uint8_t *ram;
    uint8_t *rom;
} test_target_snapshot;

static void test_snapshot_free(test_target_snapshot *snapshot) {
    free(snapshot->instance_bytes); free(snapshot->ram); free(snapshot->rom);
    snapshot->instance_bytes = NULL; snapshot->ram = NULL; snapshot->rom = NULL;
}

static int test_snapshot_capture(const gbb_instance *target, test_target_snapshot *snapshot) {
    snapshot->instance_bytes = malloc(sizeof(*target));
    snapshot->ram = malloc(target->cartridge_ram_size == 0u ? 1u : target->cartridge_ram_size);
    snapshot->rom = malloc(target->rom_size == 0u ? 1u : target->rom_size);
    if (snapshot->instance_bytes == NULL || snapshot->ram == NULL || snapshot->rom == NULL ||
        (target->cartridge_ram_size != 0u && target->cartridge_ram == NULL) ||
        (target->rom_size != 0u && target->rom == NULL)) {
        test_snapshot_free(snapshot);
        return 0;
    }
    memcpy(snapshot->instance_bytes, target, sizeof(*target));
    if (target->cartridge_ram_size != 0u)
        memcpy(snapshot->ram, target->cartridge_ram, target->cartridge_ram_size);
    if (target->rom_size != 0u) memcpy(snapshot->rom, target->rom, target->rom_size);
    return 1;
}

/* Compare the struct first: equal struct bytes prove the RAM/ROM pointers and
 * sizes are the captured ones, so the owned-byte comparisons read valid extents. */
static int test_snapshot_unchanged(const gbb_instance *target,
                                   const test_target_snapshot *snapshot) {
    if (memcmp(snapshot->instance_bytes, target, sizeof(*target)) != 0) return 0;
    if (target->cartridge_ram_size != 0u &&
        memcmp(snapshot->ram, target->cartridge_ram, target->cartridge_ram_size) != 0) return 0;
    return target->rom_size == 0u || memcmp(snapshot->rom, target->rom, target->rom_size) == 0;
}

typedef gbb_error (*test_state_loader)(gbb_instance *, const uint8_t *, size_t);

static int test_load_rejects_mutations_with(test_state_loader loader, int report,
                                            gbb_instance *target, const uint8_t *saved,
                                            size_t size, const test_state_edit *edits,
                                            size_t edit_count) {
    uint8_t *mutant = malloc(size);
    test_target_snapshot backup = {0};
    if (mutant == NULL || !test_snapshot_capture(target, &backup)) {
        free(mutant); test_snapshot_free(&backup);
        return 0;
    }
    memcpy(mutant, saved, size);
    int wrote = 1;
    for (size_t i = 0u; i < edit_count; ++i)
        if (!test_write_body_field(target, mutant, edits[i].path, edits[i].index,
                                   edits[i].value)) wrote = 0;
    if (wrote) test_rechecksum(mutant, size);
    const gbb_error got = wrote ? loader(target, mutant, size) : GBB_INVALID_ARGUMENT;
    const int unchanged = test_snapshot_unchanged(target, &backup);
    if (report && (got != GBB_STATE_INVALID_CONTENT || !unchanged)) {
        fprintf(stderr, "semantic mutation result=%d unchanged=%d", (int)got, unchanged);
        for (size_t i = 0u; i < edit_count; ++i)
            fprintf(stderr, " %s[%zu]=0x%llx", edits[i].path, edits[i].index,
                    (unsigned long long)edits[i].value);
        fputc('\n', stderr);
    }
    test_snapshot_free(&backup); free(mutant);
    return wrote && got == GBB_STATE_INVALID_CONTENT && unchanged;
}

static int test_load_rejects_mutations(gbb_instance *target, const uint8_t *saved,
                                       size_t size, const test_state_edit *edits,
                                       size_t edit_count) {
    return test_load_rejects_mutations_with(gbb_load_state, 1, target, saved, size,
                                            edits, edit_count);
}

static int test_load_rejects_unchanged(gbb_instance *target, const uint8_t *saved,
                                       size_t size, const char *path, size_t index,
                                       uint64_t value) {
    const test_state_edit edit = {path, index, value};
    return test_load_rejects_mutations(target, saved, size, &edit, 1u);
}

/* Positive control for a relation: a reachable combination of edited fields must
 * load, and the loaded machine must resave the exact mutated bytes. The target is
 * restored from the unedited state afterwards. */
static int test_load_accepts_mutations(gbb_instance *target, const uint8_t *saved,
                                       size_t size, const test_state_edit *edits,
                                       size_t edit_count) {
    uint8_t *mutant = malloc(size);
    uint8_t *resaved = malloc(size);
    if (mutant == NULL || resaved == NULL) {
        free(mutant); free(resaved);
        return 0;
    }
    memcpy(mutant, saved, size);
    int ok = 1;
    for (size_t i = 0u; i < edit_count; ++i)
        if (!test_write_body_field(target, mutant, edits[i].path, edits[i].index,
                                   edits[i].value)) ok = 0;
    if (ok) test_rechecksum(mutant, size);
    const gbb_error loaded = ok ? gbb_load_state(target, mutant, size) : GBB_INVALID_ARGUMENT;
    const gbb_error resave = loaded == GBB_OK ? gbb_save_state(target, resaved, size)
                                              : GBB_INVALID_ARGUMENT;
    ok = ok && loaded == GBB_OK && resave == GBB_OK && memcmp(mutant, resaved, size) == 0;
    if (!ok) {
        fprintf(stderr, "reachable mutation load=%d resave=%d", (int)loaded, (int)resave);
        for (size_t i = 0u; i < edit_count; ++i)
            fprintf(stderr, " %s[%zu]=0x%llx", edits[i].path, edits[i].index,
                    (unsigned long long)edits[i].value);
        fputc('\n', stderr);
    }
    if (gbb_load_state(target, saved, size) != GBB_OK) ok = 0;
    free(resaved); free(mutant);
    return ok;
}

/* A live machine is saveable, and its state reloads into a fresh instance of the
 * same ROM and profile and resaves byte-identically. Returns 1 on success; on
 * failure it prints the first failing step with the caller's label. */
static int test_live_roundtrip(const gbb_instance *source, const char *label) {
    size_t size = 0u;
    const gbb_error sized = gbb_state_size(source, &size);
    if (sized != GBB_OK) {
        fprintf(stderr, "%s: gbb_state_size=%d ly=%u dot=%u mode=%u lcdc=0x%02x\n", label,
                (int)sized, source->ly, source->ppu_dot, source->ppu_mode, source->lcdc);
        return 0;
    }
    uint8_t *saved = malloc(size), *resaved = malloc(size);
    gbb_instance *target = NULL;
    int ok = saved != NULL && resaved != NULL &&
             gbb_create(source->profile, &target) == GBB_OK &&
             gbb_load_rom(target, source->rom, source->rom_size) == GBB_OK;
    const gbb_error save = ok ? gbb_save_state(source, saved, size) : GBB_INVALID_ARGUMENT;
    const gbb_error load = save == GBB_OK ? gbb_load_state(target, saved, size)
                                          : GBB_INVALID_ARGUMENT;
    const gbb_error resave = load == GBB_OK ? gbb_save_state(target, resaved, size)
                                            : GBB_INVALID_ARGUMENT;
    ok = ok && resave == GBB_OK && memcmp(saved, resaved, size) == 0;
    if (!ok)
        fprintf(stderr, "%s: save=%d load=%d resave=%d identical=%d\n", label, (int)save,
                (int)load, (int)resave,
                resave == GBB_OK ? memcmp(saved, resaved, size) == 0 : 0);
    if (target != NULL) gbb_destroy(target);
    free(resaved); free(saved);
    return ok;
}

static int test_load_rejects_header_unchanged_with(test_state_loader loader,
                                                   gbb_instance *target, const uint8_t *saved,
                                                   size_t size, size_t offset, uint8_t value,
                                                   gbb_error expected) {
    uint8_t *mutant = malloc(size);
    test_target_snapshot backup = {0};
    if (mutant == NULL || !test_snapshot_capture(target, &backup)) {
        free(mutant); test_snapshot_free(&backup);
        return 0;
    }
    memcpy(mutant, saved, size);
    mutant[offset] = value;
    test_rechecksum(mutant, size);
    const gbb_error got = loader(target, mutant, size);
    const int unchanged = test_snapshot_unchanged(target, &backup);
    test_snapshot_free(&backup); free(mutant);
    return got == expected && unchanged;
}

static int test_load_rejects_header_unchanged(gbb_instance *target, const uint8_t *saved,
                                              size_t size, size_t offset, uint8_t value,
                                              gbb_error expected) {
    return test_load_rejects_header_unchanged_with(gbb_load_state, target, saved, size,
                                                   offset, value, expected);
}

/* Negative control for the refusal oracle: a loader that writes cartridge RAM
 * before the real load refuses, as a state_apply that ran ahead of validation
 * would. Only heap RAM changes, so a struct-only memcmp cannot see it. */
static gbb_error test_premature_ram_write_load(gbb_instance *target, const uint8_t *bytes,
                                               size_t size) {
    if (target != NULL && target->cartridge_ram_size != 0u && target->cartridge_ram != NULL)
        target->cartridge_ram[target->cartridge_ram_size - 1u] ^= 0x01u;
    return gbb_load_state(target, bytes, size);
}

static int test_refusal_oracle_sees_ram(gbb_instance *target, const uint8_t *saved,
                                        size_t size, const test_state_edit *invalid) {
    if (target->cartridge_ram_size == 0u) return 0;
    uint8_t *struct_before = malloc(sizeof(*target));
    if (struct_before == NULL) return 0;
    memcpy(struct_before, target, sizeof(*target));
    const uint8_t ram_before = target->cartridge_ram[target->cartridge_ram_size - 1u];
    /* The genuine loader refuses without mutation; the premature writer must be caught
     * by both the body and the header refusal helpers. */
    const int genuine = test_load_rejects_mutations(target, saved, size, invalid, 1u);
    const int body_caught = !test_load_rejects_mutations_with(test_premature_ram_write_load, 0,
                                                              target, saved, size, invalid, 1u);
    const int body_ram_changed =
        target->cartridge_ram[target->cartridge_ram_size - 1u] != ram_before;
    /* The struct-only comparison the old helper used is blind to this mutation. */
    const int struct_blind = memcmp(struct_before, target, sizeof(*target)) == 0;
    target->cartridge_ram[target->cartridge_ram_size - 1u] = ram_before;
    const int header_caught = !test_load_rejects_header_unchanged_with(
        test_premature_ram_write_load, target, saved, size, 18u, 1u, GBB_STATE_INVALID_CONTENT);
    target->cartridge_ram[target->cartridge_ram_size - 1u] = ram_before;
    free(struct_before);
    if (!(genuine && body_caught && body_ram_changed && struct_blind && header_caught))
        fprintf(stderr, "refusal oracle control genuine=%d body=%d changed=%d blind=%d header=%d\n",
                genuine, body_caught, body_ram_changed, struct_blind, header_caught);
    return genuine && body_caught && body_ram_changed && struct_blind && header_caught;
}

static int test_make_state(gbb_profile profile, uint8_t cgb_flag, uint8_t cartridge_type,
                           gbb_instance **source, gbb_instance **target, uint8_t **saved,
                           size_t *state_size) {
    uint8_t *rom = calloc(TEST_ROM_BYTES, 1u);
    if (rom == NULL) return 0;
    test_build_rom(rom, cartridge_type, cgb_flag);
    int ok = gbb_create(profile, source) == GBB_OK && gbb_create(profile, target) == GBB_OK &&
             gbb_load_rom(*source, rom, TEST_ROM_BYTES) == GBB_OK &&
             gbb_load_rom(*target, rom, TEST_ROM_BYTES) == GBB_OK &&
             gbb_state_size(*source, state_size) == GBB_OK;
    free(rom);
    if (!ok) {
        if (*source != NULL) gbb_destroy(*source);
        if (*target != NULL) gbb_destroy(*target);
        *source = NULL; *target = NULL;
        return 0;
    }
    *saved = malloc(*state_size);
    if (*saved == NULL) {
        gbb_destroy(*source); gbb_destroy(*target);
        *source = NULL; *target = NULL;
        return 0;
    }
    return 1;
}

static int test_canonical_queue_count(size_t event_count) {
    gbb_instance *source = NULL, *target = NULL;
    uint8_t *saved = NULL, *resaved = NULL;
    size_t size = 0u;
    int ok = test_make_state(GBB_PROFILE_DMG_CPU_B, 0u, 0x06u,
                             &source, &target, &saved, &size);
    if (!ok) fprintf(stderr, "canonical queue setup failed count=%zu\n", event_count);
    if (ok && source->cart.kind != CART_MBC2) {
        fprintf(stderr, "canonical queue mapper mismatch kind=%d\n", (int)source->cart.kind);
        ok = 0;
    }
    if (ok) {
        for (size_t i = 0u; i < source->cartridge_ram_size; ++i)
            source->cartridge_ram[i] = (uint8_t)(0xF0u | (i & 0x0Fu));
        gbb_input_event events[GBB_INPUT_EVENT_CAPACITY];
        for (size_t i = 0u; i < event_count; ++i) {
            const gbb_input_event_kind kinds[] = {
                GBB_INPUT_BUTTON_PRESS, GBB_INPUT_BUTTON_RELEASE,
                GBB_INPUT_SERIAL_EDGE, GBB_INPUT_STOP_WAKE
            };
            const gbb_input_event_kind kind = kinds[i % (sizeof(kinds) / sizeof(kinds[0]))];
            events[i] = (gbb_input_event){
                .at_half_dots = source->time_half_dots,
                .kind = kind,
                .value = kind == GBB_INPUT_STOP_WAKE ? 1u :
                         kind == GBB_INPUT_SERIAL_EDGE ? (uint8_t)((i / 4u) & 1u) :
                         (uint8_t)(i % 8u)
            };
        }
        const gbb_error queued = gbb_queue_events(source, events, event_count);
        if (queued != GBB_OK) fprintf(stderr, "canonical queue admission=%d count=%zu\n",
                                      (int)queued, event_count);
        ok = queued == GBB_OK;
    }
    if (ok) {
        const gbb_error save_error = gbb_save_state(source, saved, size);
        if (save_error != GBB_OK) fprintf(stderr, "canonical save=%d count=%zu\n",
                                          (int)save_error, event_count);
        ok = save_error == GBB_OK;
    }
    resaved = ok ? malloc(size) : NULL;
    if (ok && resaved == NULL) ok = 0;
    if (ok) {
        const gbb_error load_error = gbb_load_state(target, saved, size);
        const gbb_error save_error = load_error == GBB_OK
            ? gbb_save_state(target, resaved, size) : GBB_INVALID_ARGUMENT;
        if (load_error != GBB_OK || save_error != GBB_OK || memcmp(saved, resaved, size) != 0)
            fprintf(stderr, "canonical resave load=%d save=%d equal=%d count=%zu\n",
                    (int)load_error, (int)save_error,
                    memcmp(saved, resaved, size) == 0, event_count);
        ok = load_error == GBB_OK && save_error == GBB_OK && memcmp(saved, resaved, size) == 0;
    }
    if (ok) {
        const gbb_run_result source_run = gbb_run(source, 12000u, NULL, 0u);
        const gbb_run_result target_run = gbb_run(target, 12000u, NULL, 0u);
        ok = same_run_result(source_run, target_run) &&
             gbb_save_state(source, saved, size) == GBB_OK &&
             gbb_save_state(target, resaved, size) == GBB_OK &&
             memcmp(saved, resaved, size) == 0;
    }
    if (!ok) fprintf(stderr, "canonical queue count=%zu failed\n", event_count);
    free(resaved); free(saved);
    if (source != NULL) gbb_destroy(source);
    if (target != NULL) gbb_destroy(target);
    return ok;
}

static int state_canonical(void) {
    gbb_instance *source = NULL, *target = NULL;
    uint8_t *saved = NULL, *resaved = NULL;
    size_t size = 0u;
    REQUIRE_CASE("state_canonical", test_make_state(GBB_PROFILE_CGB_CPU_E, 0u, 0x10u,
                                                      &source, &target, &saved, &size));
    /* This valid accepted-space boundary deliberately uses each multi-byte wire
     * width with recognizable little-endian bytes and raw CGB-compat latches. */
    gbb_audio_frame audio[2048];
    size_t audio_count = 0u;
    REQUIRE_CASE("state_canonical", gbb_run_audio(source, 70000u, audio,
                                    sizeof(audio) / sizeof(audio[0]), &audio_count).reason ==
                                    GBB_STOP_BUDGET);
    REQUIRE_CASE("state_canonical", audio_count != 0u);
    REQUIRE_CASE("state_canonical", state_store_host_value(source,
        state_field_by_path("ppu_dot"), 0u, 0x123u));
    REQUIRE_CASE("state_canonical", state_store_host_value(source,
        state_field_by_path("ppu_object_tiles_fetched"), 0u, 0x01020304u));
    REQUIRE_CASE("state_canonical", state_store_host_value(source,
        state_field_by_path("frame_generation"), 0u, UINT64_C(0x0102030405060708)));
    source->bcps = 0xC8u;
    source->ocps = 0xD0u;
    REQUIRE_CASE("state_canonical", gbb_save_state(source, saved, size) == GBB_OK);
    size_t offset = test_element_offset(source, "ppu_dot", 0u);
    if (offset == SIZE_MAX || saved[64u + offset] != 0x23u ||
        saved[64u + offset + 1u] != 0x01u)
        fprintf(stderr, "wire endian guard: ppu_dot must encode 0x0123 as 23 01\n");
    REQUIRE_CASE("state_canonical", offset != SIZE_MAX && saved[64u + offset] == 0x23u &&
                                    saved[64u + offset + 1u] == 0x01u);
    offset = test_element_offset(source, "ppu_object_tiles_fetched", 0u);
    REQUIRE_CASE("state_canonical", offset != SIZE_MAX && saved[64u + offset] == 0x04u &&
                                    saved[64u + offset + 1u] == 0x03u &&
                                    saved[64u + offset + 2u] == 0x02u &&
                                    saved[64u + offset + 3u] == 0x01u);
    offset = test_element_offset(source, "frame_generation", 0u);
    REQUIRE_CASE("state_canonical", offset != SIZE_MAX && saved[64u + offset] == 0x08u &&
                                    saved[64u + offset + 7u] == 0x01u);
    /* Recompute CRC after changing a valid accepted byte: loading must preserve it. */
    REQUIRE_CASE("state_canonical", test_write_body_field(source, saved,
                                    "apu_pulse[].envelope", 0u, 0xF3u));
    test_rechecksum(saved, size);
    resaved = malloc(size);
    int accepted_bytes_exact = resaved != NULL &&
        gbb_load_state(target, saved, size) == GBB_OK &&
        gbb_save_state(target, resaved, size) == GBB_OK &&
        memcmp(saved, resaved, size) == 0;
    if (!accepted_bytes_exact)
        fprintf(stderr, "normalization guard: accepted apu_pulse[].envelope bytes must resave unchanged\n");
    REQUIRE_CASE("state_canonical", accepted_bytes_exact);
    free(resaved); free(saved); gbb_destroy(source); gbb_destroy(target);
    source = NULL; target = NULL; saved = NULL; resaved = NULL; size = 0u;
    REQUIRE_CASE("state_canonical", test_canonical_queue_count(0u));
    REQUIRE_CASE("state_canonical", test_canonical_queue_count(1u));
    REQUIRE_CASE("state_canonical", test_canonical_queue_count(GBB_INPUT_EVENT_CAPACITY));
    REQUIRE_CASE("state_canonical", test_make_state(GBB_PROFILE_DMG_CPU_B, 0u, 0x10u,
                                                      &source, &target, &saved, &size));
    REQUIRE_CASE("state_canonical", state_store_host_value(source,
        state_field_by_path("cart.ram_bank"), 0u, 0xFFu));
    resaved = malloc(size);
    REQUIRE_CASE("state_canonical", resaved != NULL &&
                                    gbb_save_state(source, saved, size) == GBB_OK &&
                                    gbb_load_state(target, saved, size) == GBB_OK &&
                                    gbb_save_state(target, resaved, size) == GBB_OK &&
                                    memcmp(saved, resaved, size) == 0);
    const gbb_run_result selector_source_run = gbb_run(source, 128u, NULL, 0u);
    const gbb_run_result selector_target_run = gbb_run(target, 128u, NULL, 0u);
    REQUIRE_CASE("state_canonical", same_run_result(selector_source_run, selector_target_run) &&
                                    gbb_save_state(source, saved, size) == GBB_OK &&
                                    gbb_save_state(target, resaved, size) == GBB_OK &&
                                    memcmp(saved, resaved, size) == 0);
    free(resaved); free(saved); gbb_destroy(source); gbb_destroy(target);
    puts("state_canonical pass queues=0,1,64 widths=1,2,4,8 MBC2=512 audio=continued");
    return 0;
}

static int state_override_isolation(void) {
    gbb_instance *source = NULL, *target = NULL;
    uint8_t *source_bytes = NULL, *target_bytes = NULL;
    size_t source_size = 0u, target_size = 0u;
    REQUIRE_CASE("state_override_isolation", test_make_state(GBB_PROFILE_CGB_CPU_E, 0x80u,
        0x00u, &source, &target, &source_bytes, &source_size));
    write8(source, 0xFF76u, 0xA5u);
    write8(source, 0xFF77u, 0x5Au);
#if GBB_TEST_CGB_PCM_WRITABLE
    REQUIRE_CASE("state_override_isolation", source->apu_pcm_test_override_valid == 3u &&
        source->apu_pcm_test_override[0] == 0xA5u &&
        source->apu_pcm_test_override[1] == 0x5Au);
#endif
    REQUIRE_CASE("state_override_isolation", test_state_field_census(source));
    REQUIRE_CASE("state_override_isolation", gbb_state_size(source, &source_size) == GBB_OK &&
        gbb_state_size(target, &target_size) == GBB_OK && source_size == target_size);
    target_bytes = malloc(target_size);
    REQUIRE_CASE("state_override_isolation", target_bytes != NULL &&
        gbb_save_state(source, source_bytes, source_size) == GBB_OK &&
        gbb_save_state(target, target_bytes, target_size) == GBB_OK &&
        memcmp(source_bytes, target_bytes, source_size) == 0);
    free(target_bytes); free(source_bytes);
    gbb_destroy(source); gbb_destroy(target);
    puts("state override isolation pass: test-only PCM values do not enter the wire state");
    return 0;
}

static int test_dma_state_relation(gbb_instance *target, const uint8_t *saved, size_t size) {
    static const uint64_t active_indices[] = {GBB_OAM_BYTES, 0xFFu};
    for (size_t i = 0u; i < sizeof(active_indices) / sizeof(active_indices[0]); ++i) {
        const test_state_edit active_past_end[] = {
            {"dma_active", 0u, 1u}, {"dma_index", 0u, active_indices[i]}
        };
        if (!test_load_rejects_mutations(target, saved, size, active_past_end,
                                         sizeof(active_past_end) / sizeof(active_past_end[0])))
            return 0;
    }
    const test_state_edit finished[] = {{"dma_active", 0u, 0u}, {"dma_index", 0u, GBB_OAM_BYTES}};
    const test_state_edit last_byte[] = {{"dma_active", 0u, 1u}, {"dma_index", 0u, GBB_OAM_BYTES - 1u}};
    if (!test_load_accepts_mutations(target, saved, size, finished, 2u) ||
        !test_load_accepts_mutations(target, saved, size, last_byte, 2u)) return 0;

    /* The tick also refuses to index past OAM if an unvalidated caller (a white-box
     * test or a future decoder bug) ever presents {active, index >= 160}: it ends the
     * transfer without writing. Without the guard this writes oam[160..255], which is
     * the start of frame_working, and UBSan reports the out-of-bounds index. */
    gbb_instance *probe = malloc(sizeof(*probe));
    if (probe == NULL) return 0;
    memcpy(probe, target, sizeof(*probe));
    memset(probe->frame_working, 0, 96u);
    probe->dma_active = 1u;
    probe->dma_index = (uint8_t)GBB_OAM_BYTES;
    probe->dma_phase = 0u;
    probe->dma_page = 0xC0u;
    for (unsigned i = GBB_OAM_BYTES; i < 256u; ++i)
        *wram_byte_mut(probe, (uint16_t)(0xC000u + i)) = 0x5Au; /* a write would be visible */
    for (unsigned tick = 0u; tick < 4u * 96u && probe->dma_active; ++tick)
        dma_advance_half_dot(probe);
    int guarded = probe->dma_active == 0u && probe->dma_index == GBB_OAM_BYTES;
    for (unsigned i = 0u; i < 96u; ++i) if (probe->frame_working[i] != 0u) guarded = 0;
    if (!guarded)
        fprintf(stderr, "dma tick guard active=%u index=%u\n", probe->dma_active, probe->dma_index);
    free(probe);
    return guarded;
}

/* WR-A02. FF53 is the only write that sets the destination cursor's high byte, and it
 * always ORs in 0x8000. Until the guest writes FF53, FF54 changes only the low byte of
 * the reset cursor 0, so 0x0000..0x00F0 (low nibble clear) is reachable while idle or
 * pending. hdma_admit_block refuses any block whose cursor is outside 0x8000..0x9FF0,
 * so an active block never has a low cursor, and such a state is refused. */
static int test_hdma_destination_relation(gbb_instance *source, gbb_instance *target,
                                          const uint8_t *saved, size_t size) {
    static const uint64_t active_low[] = {0x0000u, 0x0010u, 0x00F0u};
    for (size_t i = 0u; i < sizeof(active_low) / sizeof(active_low[0]); ++i) {
        const test_state_edit active_block[] = {
            {"hdma.mode", 0u, 2u}, {"hdma.active", 0u, 1u},
            {"hdma.pending_hblank", 0u, 0u}, {"hdma.blocks_remaining", 0u, 1u},
            {"hdma.source_cursor", 0u, 0xC000u}, {"hdma.destination_cursor", 0u, active_low[i]}
        };
        if (!test_load_rejects_mutations(target, saved, size, active_block,
                                         sizeof(active_block) / sizeof(active_block[0])))
            return 0;
    }
    const test_state_edit unaligned_low[] = {{"hdma.destination_cursor", 0u, 0x0018u}};
    if (!test_load_rejects_mutations(target, saved, size, unaligned_low, 1u)) return 0;
    const test_state_edit valid_block[] = {
        {"hdma.mode", 0u, 2u}, {"hdma.active", 0u, 1u},
        {"hdma.pending_hblank", 0u, 0u}, {"hdma.blocks_remaining", 0u, 1u},
        {"hdma.source_cursor", 0u, 0xC000u}, {"hdma.destination_cursor", 0u, 0x8000u}
    };
    if (!test_load_accepts_mutations(target, saved, size, valid_block,
                                     sizeof(valid_block) / sizeof(valid_block[0]))) return 0;

    /* Guest-driven reachability: FF54 before any FF53 write, idle and then pending. */
    if (source->exec_mode != GBB_MODE_CGB || source->hdma.destination_cursor != 0u) return 0;
    write8(source, 0xFF51u, 0xC0u);
    write8(source, 0xFF52u, 0x00u);
    write8(source, 0xFF54u, 0xF0u);
    if (source->hdma.destination_cursor != 0x00F0u ||
        !test_live_roundtrip(source, "hdma idle low cursor")) return 0;
    write8(source, 0xFF55u, 0x00u); /* general-purpose request, one block */
    return source->hdma.pending_hblank == 1u &&
           test_live_roundtrip(source, "hdma pending low cursor");
}

static int state_semantic_bounds(void) {
    gbb_instance *source = NULL, *target = NULL;
    uint8_t *saved = NULL;
    size_t size = 0u;
    REQUIRE_CASE("state_semantic_bounds", test_make_state(GBB_PROFILE_CGB_CPU_E, 0x80u, 0x00u,
                                                            &source, &target, &saved, &size));
    REQUIRE_CASE("state_semantic_bounds", gbb_save_state(source, saved, size) == GBB_OK);
    REQUIRE_CASE("state_semantic_bounds", gbb_load_state(target, saved, size) == GBB_OK);
    static const struct { const char *path; size_t index; uint64_t value; } cgb_invalid[] = {
        {"hdma.source_low", 0u, 0x01u},
        {"hdma.destination_high", 0u, 0x20u},
        {"hdma.destination_low", 0u, 0x01u},
        {"hdma.mode", 0u, 3u},
        {"hdma.blocks_remaining", 0u, 129u},
        {"hdma.byte_phase", 0u, 4u},
        {"hdma.block_vram_bank", 0u, 2u},
        {"hdma.destination_cursor", 0u, 0x7FFFu},
        {"dma_index", 0u, GBB_OAM_BYTES + 1u},
        {"dma_phase", 0u, GBB_T_PER_M},
        {"ppu_selected_objects", 0u, 40u},
        {"timer_reload_remaining", 0u, 5u},
        {"serial_edge_remaining", 0u, 513u},
        {"joypad_select", 0u, 0x80u},
        {"interrupt_flags", 0u, 0x20u},
        {"stat", 0u, 0x80u},
        {"ppu_window_line", 0u, GBB_FRAME_HEIGHT + 1u},
        {"ppu_fetch_enqueued", 0u, GBB_FRAME_WIDTH + 8u},
        {"ppu_fifo_count", 0u, GBB_PPU_FIFO_CAPACITY + 1u},
        {"apu_noise.length_reg", 0u, 0x40u},
        {"apu_noise.control", 0u, 0x80u},
        {"apu_wave.level", 0u, 0x04u},
        {"apu_pulse[].control", 0u, 0x80u},
        {"input_events[].value", 0u, 1u},
        {"input_event_count", 0u, GBB_INPUT_EVENT_CAPACITY + 1u},
        {"time_half_dots", 0u, (UINT64_C(1) << 62) + 1u}
    };
    for (size_t i = 0u; i < sizeof(cgb_invalid) / sizeof(cgb_invalid[0]); ++i)
        REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
            cgb_invalid[i].path, cgb_invalid[i].index, cgb_invalid[i].value));
    for (size_t i = 0u; i < 12u; ++i)
        REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "compat_rgb555", i, 0x8000u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "rgb_working", GBB_FRAME_PIXELS - 1u, 0x8000u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "frame_completed", 0u, 4u));
    /* Path rules are resolved on a field's first element; later elements must keep them. */
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "frame_completed", GBB_FRAME_PIXELS - 1u, 4u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "frame_working", GBB_FRAME_PIXELS - 1u, 4u));
    /* CR-A02: palette RAM stores all eight bits of every byte the guest writes through
     * BCPD/OCPD; colour lookup masks bit 15 only when rendering. Bit 7 of a high byte is
     * therefore reachable state and must load and resave unchanged. */
    const test_state_edit cram_high_bits[] = {
        {"bg_cram", 1u, 0x80u}, {"bg_cram", 63u, 0xFFu},
        {"obj_cram", 1u, 0x80u}, {"obj_cram", 63u, 0xFFu}
    };
    REQUIRE_CASE("state_semantic_bounds", test_load_accepts_mutations(target, saved, size,
                                    cram_high_bits, sizeof(cram_high_bits) / sizeof(cram_high_bits[0])));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "ime", 0u, 2u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "f", 0u, 0x0Fu));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "ime_delay", 0u, 3u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "div", 0u, 1u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "ppu_objects_stalled", 0u, 1u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "timer_reload_pending", 0u, 2u));
    const test_state_edit invalid_wake[] = {
        {"input_event_count", 0u, 1u},
        {"input_events[].at_half_dots", 0u, 0u},
        {"input_events[].kind", 0u, GBB_INPUT_STOP_WAKE},
        {"input_events[].value", 0u, 2u}
    };
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_mutations(target, saved, size,
                                    invalid_wake, sizeof(invalid_wake) / sizeof(invalid_wake[0])));
    const test_state_edit unordered_events[] = {
        {"input_event_count", 0u, 2u},
        {"input_events[].at_half_dots", 0u, 2u},
        {"input_events[].kind", 0u, GBB_INPUT_BUTTON_PRESS},
        {"input_events[].value", 0u, 0u},
        {"input_events[].at_half_dots", 1u, 1u},
        {"input_events[].kind", 1u, GBB_INPUT_BUTTON_PRESS},
        {"input_events[].value", 1u, 0u}
    };
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_mutations(target, saved, size,
                                    unordered_events, sizeof(unordered_events) / sizeof(unordered_events[0])));
    const test_state_edit invalid_timer_relation[] = {
        {"timer_reload_pending", 0u, 1u}, {"timer_reload_remaining", 0u, 0u}
    };
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_mutations(target, saved, size,
                                    invalid_timer_relation,
                                    sizeof(invalid_timer_relation) / sizeof(invalid_timer_relation[0])));
    const test_state_edit invalid_serial_relation[] = {
        {"serial_active", 0u, 1u}, {"serial_control", 0u, 0u},
        {"serial_edge_remaining", 0u, 512u}
    };
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_mutations(target, saved, size,
                                    invalid_serial_relation,
                                    sizeof(invalid_serial_relation) / sizeof(invalid_serial_relation[0])));
    const test_state_edit invalid_hdma_source[] = {
        {"hdma.mode", 0u, 2u}, {"hdma.active", 0u, 1u},
        {"hdma.pending_hblank", 0u, 0u}, {"hdma.blocks_remaining", 0u, 1u},
        {"hdma.source_cursor", 0u, 0x8000u}, {"hdma.destination_cursor", 0u, 0x8000u}
    };
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_mutations(target, saved, size,
                                    invalid_hdma_source,
                                    sizeof(invalid_hdma_source) / sizeof(invalid_hdma_source[0])));
    const test_state_edit invalid_hdma_destination[] = {
        {"hdma.mode", 0u, 2u}, {"hdma.active", 0u, 1u},
        {"hdma.pending_hblank", 0u, 0u}, {"hdma.blocks_remaining", 0u, 1u},
        {"hdma.source_cursor", 0u, 0x0000u}, {"hdma.destination_cursor", 0u, 0xA000u}
    };
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_mutations(target, saved, size,
                                    invalid_hdma_destination,
                                    sizeof(invalid_hdma_destination) / sizeof(invalid_hdma_destination[0])));
    /* CR-A03: OAM DMA stops when dma_index reaches 160, and dma_start resets it to 0,
     * so an active transfer always has dma_index < 160. Index 160 is reachable only
     * with the transfer finished. Accepting {active, 160} would let the next DMA tick
     * write oam[160], past the 160-byte array. */
    REQUIRE_CASE("state_semantic_bounds", test_dma_state_relation(target, saved, size));
    REQUIRE_CASE("state_semantic_bounds", test_hdma_destination_relation(source, target,
                                    saved, size));
    /* WR-A01: LY counts lines 0..153 and wraps at 154; LCD off holds it at 0. */
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "ly", 0u, GBB_LINES_PER_FRAME));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "ly", 0u, 0xFFu));
    const test_state_edit last_line[] = {{"ly", 0u, GBB_LINES_PER_FRAME - 1u}};
    REQUIRE_CASE("state_semantic_bounds", test_load_accepts_mutations(target, saved, size,
                                    last_line, 1u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_header_unchanged(target, saved,
                                    size, 18u, 1u, GBB_STATE_INVALID_CONTENT));
    gbb_destroy(source); gbb_destroy(target); free(saved);

    source = NULL; target = NULL; saved = NULL; size = 0u;
    REQUIRE_CASE("state_semantic_bounds", test_make_state(GBB_PROFILE_DMG_CPU_B, 0u, 0x00u,
                                                            &source, &target, &saved, &size));
    REQUIRE_CASE("state_semantic_bounds", gbb_save_state(source, saved, size) == GBB_OK);
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "ie", 0u, 0x20u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "ly", 0u, 200u));
    gbb_destroy(source); gbb_destroy(target); free(saved);

    source = NULL; target = NULL; saved = NULL; size = 0u;
    REQUIRE_CASE("state_semantic_bounds", test_make_state(GBB_PROFILE_DMG_CPU_B, 0u, 0x06u,
                                                            &source, &target, &saved, &size));
    REQUIRE_CASE("state_semantic_bounds", gbb_save_state(source, saved, size) == GBB_OK);
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "cartridge_ram", 0u, 0x0Fu));
    const test_state_edit invalid_mbc2_ram = {"cartridge_ram", 0u, 0x0Fu};
    REQUIRE_CASE("state_semantic_bounds", test_refusal_oracle_sees_ram(target, saved, size,
                                    &invalid_mbc2_ram));
    gbb_destroy(source); gbb_destroy(target); free(saved);

    source = NULL; target = NULL; saved = NULL; size = 0u;
    REQUIRE_CASE("state_semantic_bounds", test_make_state(GBB_PROFILE_DMG_CPU_B, 0u, 0x03u,
                                                            &source, &target, &saved, &size));
    REQUIRE_CASE("state_semantic_bounds", gbb_save_state(source, saved, size) == GBB_OK);
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "cart.rom_bank_hi", 0u, 4u));
    const test_state_edit invalid_mbc1_bank = {"cart.rom_bank_hi", 0u, 4u};
    REQUIRE_CASE("state_semantic_bounds", test_refusal_oracle_sees_ram(target, saved, size,
                                    &invalid_mbc1_bank));
    gbb_destroy(source); gbb_destroy(target); free(saved);

    source = NULL; target = NULL; saved = NULL; size = 0u;
    REQUIRE_CASE("state_semantic_bounds", test_make_state(GBB_PROFILE_DMG_CPU_B, 0u, 0x10u,
                                                            &source, &target, &saved, &size));
    REQUIRE_CASE("state_semantic_bounds", gbb_save_state(source, saved, size) == GBB_OK);
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "cart.rtc_dh", 0u, 2u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "cart.rtc_s", 0u, 0x40u));
    REQUIRE_CASE("state_semantic_bounds", test_load_rejects_unchanged(target, saved, size,
                                    "cart.rtc_sub", 0u, RTC_SUB_MASK + 1u));
    gbb_destroy(source); gbb_destroy(target); free(saved);
    puts("state_semantic_bounds pass checksum=valid refusal=non-mutating oracle=struct+ram+rom");
    return 0;
}

static int state_identity(void) {
    REQUIRE_CASE("state_identity", test_sha_vectors());
    uint8_t *rom_a = calloc(TEST_ROM_BYTES, 1u);
    uint8_t *rom_b = calloc(TEST_ROM_BYTES, 1u);
    uint8_t *invalid_rom = calloc(TEST_ROM_BYTES, 1u);
    REQUIRE_CASE("state_identity", rom_a != NULL && rom_b != NULL && invalid_rom != NULL);
    test_build_rom(rom_a, 0x00u, 0u);
    REQUIRE_CASE("state_identity", test_crc_collision_pair(rom_a, rom_b, TEST_ROM_BYTES));
    REQUIRE_CASE("state_identity", memcmp(rom_a, rom_b, 0x150u) == 0);
    REQUIRE_CASE("state_identity", state_crc32(rom_a, TEST_ROM_BYTES) ==
                                    state_crc32(rom_b, TEST_ROM_BYTES));
    uint8_t digest_a[32], digest_b[32];
    state_sha256(rom_a, TEST_ROM_BYTES, digest_a);
    state_sha256(rom_b, TEST_ROM_BYTES, digest_b);
    REQUIRE_CASE("state_identity", memcmp(digest_a, digest_b, sizeof(digest_a)) != 0);

    state_sha256_test_calls = 0u;
    state_sha256_test_bytes = 0u;
    gbb_instance *source = NULL, *target_a = NULL, *target_b = NULL;
    REQUIRE_CASE("state_identity", gbb_create(GBB_PROFILE_DMG_CPU_B, &source) == GBB_OK);
    REQUIRE_CASE("state_identity", gbb_create(GBB_PROFILE_DMG_CPU_B, &target_a) == GBB_OK);
    REQUIRE_CASE("state_identity", gbb_create(GBB_PROFILE_DMG_CPU_B, &target_b) == GBB_OK);
    REQUIRE_CASE("state_identity", gbb_load_rom(source, rom_a, TEST_ROM_BYTES) == GBB_OK);
    REQUIRE_CASE("state_identity", state_sha256_test_calls == 1u &&
                                    state_sha256_test_bytes == TEST_ROM_BYTES);
    REQUIRE_CASE("state_identity", gbb_load_rom(target_a, rom_a, TEST_ROM_BYTES) == GBB_OK);
    REQUIRE_CASE("state_identity", gbb_load_rom(target_b, rom_b, TEST_ROM_BYTES) == GBB_OK);
    REQUIRE_CASE("state_identity", state_sha256_test_calls == 3u &&
                                    state_sha256_test_bytes == 3u * TEST_ROM_BYTES);
    REQUIRE_CASE("state_identity", test_state_field_census(source));

    const gbb_run_result source_prefix = gbb_run(source, 40000u, NULL, 0u);
    const gbb_run_result target_a_prefix = gbb_run(target_a, 40000u, NULL, 0u);
    const gbb_run_result target_b_prefix = gbb_run(target_b, 40000u, NULL, 0u);
    REQUIRE_CASE("state_identity", source_prefix.reason == GBB_STOP_BUDGET &&
                                    target_a_prefix.reason == GBB_STOP_BUDGET &&
                                    target_b_prefix.reason == GBB_STOP_BUDGET);
    size_t state_size = 0u;
    REQUIRE_CASE("state_identity", gbb_state_size(source, &state_size) == GBB_OK);
    uint8_t *saved = malloc(state_size);
    REQUIRE_CASE("state_identity", saved != NULL);
    REQUIRE_CASE("state_identity", gbb_save_state(source, saved, state_size) == GBB_OK);
    uint8_t before[sizeof(gbb_instance)];
    memcpy(before, target_b, sizeof(before));
    REQUIRE_CASE("state_identity", gbb_load_state(target_b, saved, state_size) ==
                                    GBB_STATE_IDENTITY_MISMATCH);
    REQUIRE_CASE("state_identity", memcmp(before, target_b, sizeof(before)) == 0);
    REQUIRE_CASE("state_identity", state_sha256_test_calls == 3u &&
                                    state_sha256_test_bytes == 3u * TEST_ROM_BYTES);

    memcpy(invalid_rom, rom_a, TEST_ROM_BYTES);
    invalid_rom[0x147u] = 0xFEu;
    test_header_checksum(invalid_rom);
    REQUIRE_CASE("state_identity", gbb_load_rom(target_a, invalid_rom, TEST_ROM_BYTES) != GBB_OK);
    REQUIRE_CASE("state_identity", state_sha256_test_calls == 3u);
    REQUIRE_CASE("state_identity", gbb_load_state(target_a, saved, state_size) == GBB_OK);
    REQUIRE_CASE("state_identity", gbb_load_rom(target_a, rom_a, TEST_ROM_BYTES) == GBB_OK);
    REQUIRE_CASE("state_identity", state_sha256_test_calls == 4u &&
                                    state_sha256_test_bytes == 4u * TEST_ROM_BYTES);
    REQUIRE_CASE("state_identity", gbb_load_state(target_a, saved, state_size) == GBB_OK);

    REQUIRE_CASE("state_identity", test_header_rejection(target_a, saved, state_size, 4u,
        (uint16_t)(GBB_STATE_FORMAT_VERSION + 1u), GBB_STATE_UNSUPPORTED_VERSION));
    REQUIRE_CASE("state_identity", test_header_rejection(target_a, saved, state_size, 8u,
        (uint16_t)(GBB_STATE_RELEASE_MAJOR + 1u), GBB_STATE_UNSUPPORTED_VERSION));
    REQUIRE_CASE("state_identity", test_header_rejection(target_a, saved, state_size, 10u,
        (uint16_t)(GBB_STATE_RELEASE_MINOR + 1u), GBB_STATE_UNSUPPORTED_VERSION));
    REQUIRE_CASE("state_identity", test_header_rejection(target_a, saved, state_size, 12u,
        (uint16_t)(GBB_STATE_RELEASE_PATCH + 1u), GBB_STATE_UNSUPPORTED_VERSION));
    REQUIRE_CASE("state_identity", test_header_rejection(target_a, saved, state_size, 14u,
        (uint16_t)(GBB_STATE_BEHAVIOR_VERSION + 1u), GBB_STATE_UNSUPPORTED_VERSION));
    uint8_t *header_mutant = malloc(state_size);
    REQUIRE_CASE("state_identity", header_mutant != NULL);
    memcpy(header_mutant, saved, state_size);
    header_mutant[16] = (uint8_t)GBB_PROFILE_CGB_CPU_E;
    REQUIRE_CASE("state_identity", gbb_load_state(target_a, header_mutant, state_size) ==
                                    GBB_STATE_IDENTITY_MISMATCH);
    memcpy(header_mutant, saved, state_size);
    header_mutant[17] = (uint8_t)GBB_MODE_CGB;
    REQUIRE_CASE("state_identity", gbb_load_state(target_a, header_mutant, state_size) ==
                                    GBB_STATE_IDENTITY_MISMATCH);
    free(header_mutant);

    /* A matching SHA is not sufficient when a state invents mapper capabilities
     * that its immutable ROM header cannot provide. CRC is recomputed so this
     * control reaches semantic validation rather than checksum rejection. */
    const size_t ram_enabled = test_field_offset(target_a, "cart.ram_enabled");
    REQUIRE_CASE("state_identity", ram_enabled != SIZE_MAX);
    saved[TEST_STATE_HEADER_BYTES + ram_enabled] = 1u;
    test_rechecksum(saved, state_size);
    REQUIRE_CASE("state_identity", gbb_load_state(target_a, saved, state_size) ==
                                    GBB_STATE_INVALID_CONTENT);

    free(saved);
    gbb_destroy(source); gbb_destroy(target_a); gbb_destroy(target_b);
    free(invalid_rom); free(rom_b); free(rom_a);
    return 0;
}

static int same_run_result(gbb_run_result a, gbb_run_result b) {
    return a.consumed_half_dots == b.consumed_half_dots && a.reason == b.reason &&
           a.trace_count == b.trace_count && a.diagnostic_count == b.diagnostic_count &&
           a.lockup_pc == b.lockup_pc && a.lockup_opcode == b.lockup_opcode;
}

static int same_frame_info(gbb_frame_info a, gbb_frame_info b) {
    return a.width == b.width && a.height == b.height && a.generation == b.generation &&
           a.completion_half_dots == b.completion_half_dots;
}

static int state_matrix_case(gbb_profile profile, uint8_t cgb_flag, gbb_exec_mode expected_mode,
                             uint8_t cartridge_type) {
    const char *failed_step = "ROM allocation";
    uint8_t *rom = calloc(TEST_ROM_BYTES, 1u);
    if (rom == NULL) return 0;
    test_build_rom(rom, cartridge_type, cgb_flag);
    gbb_instance *source = NULL, *target = NULL;
    int ok = gbb_create(profile, &source) == GBB_OK &&
             gbb_create(profile, &target) == GBB_OK;
    if (ok) failed_step = "create/load ROM";
    if (ok) ok = gbb_load_rom(source, rom, TEST_ROM_BYTES) == GBB_OK &&
                 gbb_load_rom(target, rom, TEST_ROM_BYTES) == GBB_OK;
    if (ok) ok = source->exec_mode == expected_mode && target->exec_mode == expected_mode;
    size_t initial_size = 0u, observed_size = 0u;
    if (ok) failed_step = "initial state size";
    if (ok) {
        const gbb_error size_error = gbb_state_size(source, &initial_size);
        ok = size_error == GBB_OK;
    }
    gbb_audio_frame prefix[4096];
    size_t prefix_count = 0u;
    if (ok) failed_step = "source prefix run";
    if (ok) {
        const gbb_run_result prefix_run = gbb_run_audio(source, 70000u, prefix,
                                                        4096u, &prefix_count);
        ok = prefix_run.reason == GBB_STOP_BUDGET && prefix_run.consumed_half_dots <= 70000u;
        if (!ok) fprintf(stderr, "source run reason=%d consumed=%llu audio=%zu\n",
                         (int)prefix_run.reason,
                         (unsigned long long)prefix_run.consumed_half_dots, prefix_count);
    }
    if (ok) failed_step = "source prefix size";
    if (ok) ok = gbb_state_size(source, &observed_size) == GBB_OK &&
                 observed_size == initial_size;
    if (ok) failed_step = "target prefix run";
    if (ok) {
        const gbb_run_result target_run = gbb_run_audio(target, 23000u, prefix,
                                                        4096u, &prefix_count);
        ok = target_run.reason == GBB_STOP_BUDGET && target_run.consumed_half_dots <= 23000u;
    }

    gbb_compat_palette source_palette = {.struct_size = GBB_COMPAT_PALETTE_SIZE_V1};
    gbb_compat_palette target_palette = {.struct_size = GBB_COMPAT_PALETTE_SIZE_V1};
    for (size_t i = 0u; i < 4u; ++i) {
        source_palette.bg[i] = (uint16_t)(i * 5u);
        source_palette.obj0[i] = (uint16_t)(i * 7u);
        source_palette.obj1[i] = (uint16_t)(i * 9u);
        target_palette.bg[i] = (uint16_t)(0x100u + i * 3u);
        target_palette.obj0[i] = (uint16_t)(0x200u + i * 3u);
        target_palette.obj1[i] = (uint16_t)(0x300u + i * 3u);
    }
    if (ok) failed_step = "set palettes";
    if (ok) ok = gbb_set_compat_palette(source, &source_palette) == GBB_OK &&
                 gbb_set_compat_palette(target, &target_palette) == GBB_OK;
    if (ok) failed_step = "palette state size";
    if (ok) ok = gbb_state_size(source, &observed_size) == GBB_OK &&
                 observed_size == initial_size;
    uint8_t *saved = ok ? malloc(initial_size) : NULL;
    uint8_t *resaved = ok ? malloc(initial_size) : NULL;
    if (ok) failed_step = "allocate state buffers";
    if (ok) ok = saved != NULL && resaved != NULL;
    if (ok) failed_step = "save source";
    if (ok) ok = gbb_save_state(source, saved, initial_size) == GBB_OK;
    if (ok) failed_step = "change target";
    if (ok) {
        const gbb_run_result target_change = gbb_run(target, 19000u, NULL, 0u);
        ok = target_change.reason == GBB_STOP_BUDGET;
    }
    if (ok) failed_step = "load target";
    if (ok) ok = gbb_load_state(target, saved, initial_size) == GBB_OK;
    if (ok) failed_step = "canonical resave";
    if (ok) ok = gbb_save_state(target, resaved, initial_size) == GBB_OK &&
                 memcmp(saved, resaved, initial_size) == 0;

    gbb_audio_frame source_audio[804], target_audio[804];
    size_t source_audio_count = 0u, target_audio_count = 0u;
    gbb_run_result source_future = {0}, target_future = {0};
    if (ok) failed_step = "future audio runs";
    if (ok) {
        source_future = gbb_run_audio(source, 140448u, source_audio, 804u,
                                      &source_audio_count);
        target_future = gbb_run_audio(target, 140448u, target_audio, 804u,
                                      &target_audio_count);
        ok = same_run_result(source_future, target_future) &&
             source_future.reason == GBB_STOP_BUDGET &&
             source_audio_count == target_audio_count;
    }
    if (ok) failed_step = "audio equality";
    if (ok) {
        for (size_t i = 0u; i < source_audio_count; ++i)
            if (source_audio[i].left != target_audio[i].left ||
                source_audio[i].right != target_audio[i].right) ok = 0;
    }
    gbb_frame_info source_info = {0}, target_info = {0};
    if (ok) failed_step = "frame equality";
    if (ok && profile == GBB_PROFILE_DMG_CPU_B) {
        uint8_t source_pixels[GBB_FRAME_PIXELS], target_pixels[GBB_FRAME_PIXELS];
        ok = gbb_copy_frame(source, source_pixels, sizeof(source_pixels), GBB_FRAME_WIDTH,
                            &source_info) == GBB_OK &&
             gbb_copy_frame(target, target_pixels, sizeof(target_pixels), GBB_FRAME_WIDTH,
                            &target_info) == GBB_OK &&
             same_frame_info(source_info, target_info) &&
             memcmp(source_pixels, target_pixels, sizeof(source_pixels)) == 0;
    } else if (ok) {
        uint16_t source_pixels[GBB_FRAME_PIXELS], target_pixels[GBB_FRAME_PIXELS];
        ok = gbb_copy_frame_rgb555(source, source_pixels, sizeof(source_pixels),
                                   GBB_FRAME_WIDTH * sizeof(uint16_t), &source_info) == GBB_OK &&
             gbb_copy_frame_rgb555(target, target_pixels, sizeof(target_pixels),
                                   GBB_FRAME_WIDTH * sizeof(uint16_t), &target_info) == GBB_OK &&
             same_frame_info(source_info, target_info) &&
             memcmp(source_pixels, target_pixels, sizeof(source_pixels)) == 0;
    }
    if (ok) failed_step = "final canonical state";
    if (ok) ok = gbb_save_state(source, saved, initial_size) == GBB_OK &&
                 gbb_save_state(target, resaved, initial_size) == GBB_OK &&
                 memcmp(saved, resaved, initial_size) == 0;
    if (ok) failed_step = "post-continuation run and size";
    if (ok) {
        const gbb_run_result reset = gbb_run(source, 100u, NULL, 0u);
        const gbb_error size_result = gbb_state_size(source, &observed_size);
        ok = reset.reason == GBB_STOP_BUDGET && size_result == GBB_OK &&
             observed_size == initial_size;
        if (!ok) fprintf(stderr, "run_reason=%d size=%d observed=%zu expected=%zu\n",
                         (int)reset.reason, (int)size_result, observed_size, initial_size);
    }
    if (ok) failed_step = "reset size";
    if (ok) {
        const gbb_error reset_result = gbb_reset(source);
        const gbb_error size_result = gbb_state_size(source, &observed_size);
        ok = reset_result == GBB_OK && size_result == GBB_OK &&
             observed_size == initial_size;
        if (!ok) fprintf(stderr, "reset=%d size=%d observed=%zu expected=%zu\n",
                         (int)reset_result, (int)size_result, observed_size, initial_size);
    }
    free(resaved); free(saved);
    gbb_destroy(source); gbb_destroy(target);
    free(rom);
    if (!ok) fprintf(stderr, "state matrix failed step=%s type=%02X mode=%u\n",
                     failed_step, cartridge_type, (unsigned)expected_mode);
    return ok;
}

static int test_state_exact_roundtrip(gbb_instance *instance, size_t state_size) {
    uint8_t *saved = malloc(state_size);
    uint8_t *resaved = malloc(state_size);
    gbb_instance *target = malloc(sizeof(*target));
    if (saved == NULL || resaved == NULL || target == NULL) {
        free(saved); free(resaved); free(target);
        return 0;
    }
    memcpy(target, instance, sizeof(*target));
    int ok = gbb_save_state(instance, saved, state_size) == GBB_OK &&
             gbb_load_state(target, saved, state_size) == GBB_OK &&
             gbb_save_state(target, resaved, state_size) == GBB_OK &&
             memcmp(saved, resaved, state_size) == 0;
    if (ok) {
        const gbb_run_result source_future = gbb_run(instance, 128u, NULL, 0u);
        const gbb_run_result target_future = gbb_run(target, 128u, NULL, 0u);
        ok = same_run_result(source_future, target_future) &&
             gbb_save_state(instance, saved, state_size) == GBB_OK &&
             gbb_save_state(target, resaved, state_size) == GBB_OK &&
             memcmp(saved, resaved, state_size) == 0;
    }
    free(target); free(resaved); free(saved);
    return ok;
}

typedef enum {
    STATE_SIZE_TIMER_RELOAD = 0,
    STATE_SIZE_SERIAL_EDGE,
    STATE_SIZE_OAM_DMA,
    STATE_SIZE_PPU_FETCH,
    STATE_SIZE_INPUT_EVENT,
    STATE_SIZE_HDMA_BLOCK
} state_size_boundary;

static int test_state_size_boundary(gbb_instance *instance, size_t expected_size,
                                    state_size_boundary boundary) {
    gbb_instance *saved = malloc(sizeof(*saved));
    if (saved == NULL) return 0;
    memcpy(saved, instance, sizeof(*saved));
    switch (boundary) {
    case STATE_SIZE_TIMER_RELOAD:
        instance->tac = 0u;
        instance->divider_counter = 0u;
        instance->div = 0u;
        instance->timer_signal = 0;
        instance->timer_reload_pending = 1;
        instance->timer_reload_remaining = 4u;
        break;
    case STATE_SIZE_SERIAL_EDGE:
        instance->serial_control = 0x81u;
        instance->serial_active = 1;
        instance->serial_bits = 3u;
        instance->serial_edge_remaining = 1u;
        break;
    case STATE_SIZE_OAM_DMA:
        instance->dma_register = 0xC0u;
        instance->dma_page = 0xC0u;
        instance->dma_active = 1;
        instance->dma_start_pending = 0;
        instance->dma_cpu_blocked = 1;
        instance->dma_index = GBB_OAM_BYTES - 1u;
        instance->dma_phase = GBB_T_PER_M - 1u;
        break;
    case STATE_SIZE_PPU_FETCH:
        instance->ppu_mode = 3u;
        instance->ppu_transfer_age = 11u;
        instance->ppu_fetch_enqueued = GBB_FRAME_WIDTH;
        instance->ppu_fifo_head = 0u;
        instance->ppu_fifo_count = 1u;
        instance->ppu_fifo[0] = 0u;
        instance->ppu_selected_object_count = 1u;
        instance->ppu_selected_objects[0] = 39u;
        instance->ppu_objects_stalled = 1u;
        break;
    case STATE_SIZE_INPUT_EVENT:
        instance->input_event_count = 1u;
        instance->input_events[0] = (gbb_input_event){
            .at_half_dots = instance->time_half_dots,
            .kind = GBB_INPUT_BUTTON_PRESS,
            .value = GBB_BUTTON_START
        };
        break;
    case STATE_SIZE_HDMA_BLOCK:
        instance->hdma.mode = 2u;
        instance->hdma.active = 1u;
        instance->hdma.pending_hblank = 0u;
        instance->hdma.blocks_remaining = 1u;
        instance->hdma.byte_index = 15u;
        instance->hdma.byte_phase = 3u;
        instance->hdma.source_cursor = 0x0200u;
        instance->hdma.destination_cursor = 0x8000u;
        instance->hdma.block_vram_bank = instance->vram_bank;
        break;
    }
    size_t observed = 0u;
    const int valid = gbb_state_size(instance, &observed) == GBB_OK &&
                      observed == expected_size &&
                      test_state_exact_roundtrip(instance, expected_size);
    memcpy(instance, saved, sizeof(*saved));
    free(saved);
    return valid;
}

static int test_control_flow_size(gbb_stop_reason expected_reason,
                                  const uint8_t *program, size_t program_size) {
    uint8_t *rom = calloc(TEST_ROM_BYTES, 1u);
    gbb_instance *instance = NULL;
    if (rom == NULL) return 0;
    test_build_rom(rom, 0x00u, 0u);
    memcpy(rom + 0x200u, program, program_size);
    test_header_checksum(rom);
    int ok = gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK &&
             gbb_load_rom(instance, rom, TEST_ROM_BYTES) == GBB_OK;
    size_t before = 0u, after = 0u;
    if (ok) ok = gbb_state_size(instance, &before) == GBB_OK;
    if (ok) ok = gbb_run(instance, 4096u, NULL, 0u).reason == expected_reason;
    if (ok) ok = gbb_state_size(instance, &after) == GBB_OK && after == before;
    if (ok) ok = test_state_exact_roundtrip(instance, after);
    if (instance != NULL) gbb_destroy(instance);
    free(rom);
    return ok;
}

static int test_state_boundary_sizes(void) {
    static const uint8_t halt_loop[] = {0x76u, 0x18u, 0xFDu};
    static const uint8_t stop[] = {0x10u, 0x00u};
    static const uint8_t lockup[] = {0xD3u};
    if (!test_control_flow_size(GBB_STOP_HALTED_IDLE, halt_loop, sizeof(halt_loop)) ||
        !test_control_flow_size(GBB_STOP_STOPPED, stop, sizeof(stop)) ||
        !test_control_flow_size(GBB_STOP_LOCKUP, lockup, sizeof(lockup))) return 0;

    uint8_t *rom = calloc(TEST_ROM_BYTES, 1u);
    gbb_instance *dmg = NULL, *cgb = NULL;
    int ok = rom != NULL &&
             gbb_create(GBB_PROFILE_DMG_CPU_B, &dmg) == GBB_OK &&
             gbb_create(GBB_PROFILE_CGB_CPU_E, &cgb) == GBB_OK;
    size_t dmg_size = 0u, cgb_size = 0u;
    if (ok) {
        test_build_rom(rom, 0x00u, 0u);
        ok = gbb_load_rom(dmg, rom, TEST_ROM_BYTES) == GBB_OK &&
             gbb_state_size(dmg, &dmg_size) == GBB_OK;
    }
    if (ok) {
        test_build_rom(rom, 0x00u, 0x80u);
        ok = gbb_load_rom(cgb, rom, TEST_ROM_BYTES) == GBB_OK &&
             gbb_state_size(cgb, &cgb_size) == GBB_OK;
    }
    static const state_size_boundary dmg_boundaries[] = {
        STATE_SIZE_TIMER_RELOAD, STATE_SIZE_SERIAL_EDGE, STATE_SIZE_OAM_DMA,
        STATE_SIZE_PPU_FETCH, STATE_SIZE_INPUT_EVENT
    };
    for (size_t i = 0u; ok && i < sizeof(dmg_boundaries) / sizeof(dmg_boundaries[0]); ++i)
        ok = test_state_size_boundary(dmg, dmg_size, dmg_boundaries[i]);
    if (ok) ok = test_state_size_boundary(cgb, cgb_size, STATE_SIZE_HDMA_BLOCK);
    if (ok) ok = gbb_reset(dmg) == GBB_OK;
    size_t reset_size = 0u;
    if (ok) ok = gbb_state_size(dmg, &reset_size) == GBB_OK && reset_size == dmg_size;
    if (dmg != NULL) gbb_destroy(dmg);
    if (cgb != NULL) gbb_destroy(cgb);
    free(rom);
    return ok;
}

static int state_field_census_instance(gbb_instance **out_instance) {
    uint8_t *rom = calloc(TEST_ROM_BYTES, 1u);
    if (rom == NULL) return 0;
    test_build_rom(rom, 0x1Eu, 0x80u);
    rom[0x149u] = 0x04u; /* MBC5 128 KiB RAM: maximum dynamic leading field. */
    test_header_checksum(rom);
    const gbb_error created = gbb_create(GBB_PROFILE_CGB_CPU_E, out_instance);
    const gbb_error loaded = created == GBB_OK
        ? gbb_load_rom(*out_instance, rom, TEST_ROM_BYTES) : created;
    free(rom);
    return loaded == GBB_OK;
}

static int test_full_field_census(void) {
    gbb_instance *instance = NULL;
    const int ok = state_field_census_instance(&instance) &&
                   instance->cartridge_ram_size == GBB_STATE_MAX_CARTRIDGE_RAM_BYTES &&
                   test_state_field_census(instance);
    if (instance != NULL) gbb_destroy(instance);
    return ok;
}

/* Reachable-state saveability property (review WR-A04). Every state the emulator
 * produces by running a ROM must be saveable, and its saved bytes must reload into a
 * fresh instance and resave identically. Earlier suites saved only at hand-picked
 * instants, so validator rules stricter than the core (CR-A01 stale stalled-object
 * bits, CR-A02 CRAM bit 7) went unnoticed. Two deterministic guest programs pin
 * those cases; a set of in-repository fixtures adds breadth at sampled instants. */
typedef struct {
    unsigned samples;
    unsigned roundtrips;
    unsigned failures;
} reachable_tally;

static int reachable_check(const gbb_instance *m, int full, const char *label,
                           reachable_tally *tally) {
    ++tally->samples;
    int ok;
    if (full) {
        ++tally->roundtrips;
        ok = test_live_roundtrip(m, label);
    } else {
        size_t size = 0u;
        const gbb_error sized = gbb_state_size(m, &size);
        ok = sized == GBB_OK;
        if (!ok && tally->failures < 8u)
            fprintf(stderr, "%s: gbb_state_size=%d ly=%u dot=%u mode=%u lcdc=0x%02x "
                    "stalled=0x%x selected=%u\n", label, (int)sized, m->ly, m->ppu_dot,
                    m->ppu_mode, m->lcdc, m->ppu_objects_stalled, m->ppu_selected_object_count);
    }
    if (!ok) ++tally->failures;
    return ok;
}

static gbb_instance *reachable_boot(gbb_profile profile, const uint8_t *rom, size_t rom_size) {
    gbb_instance *m = NULL;
    if (gbb_create(profile, &m) != GBB_OK) return NULL;
    if (gbb_load_rom(m, rom, rom_size) != GBB_OK) {
        gbb_destroy(m);
        return NULL;
    }
    return m;
}

static int reachable_step(gbb_instance *m, uint64_t budget) {
    const gbb_run_result r = gbb_run(m, budget, NULL, 0u);
    return r.reason == GBB_STOP_BUDGET || r.reason == GBB_STOP_HALTED_IDLE;
}

/* Advance the master clock by at least `half_dots`. A halted guest returns
 * GBB_STOP_HALTED_IDLE before the budget is spent, so one gbb_run call is not
 * enough. A budget below one instruction makes no progress, so each call asks for
 * at least 64 half-dots (longer than any instruction) and may overshoot. The
 * iteration cap bounds a guest that makes no progress at all. */
static int reachable_advance(gbb_instance *m, uint64_t half_dots) {
    const uint64_t target = m->time_half_dots + half_dots;
    for (unsigned i = 0u; i < 1000000u && m->time_half_dots < target; ++i) {
        const uint64_t remaining = target - m->time_half_dots;
        if (!reachable_step(m, remaining < 64u ? 64u : remaining)) return 0;
    }
    return m->time_half_dots >= target;
}

/* One 8x8 object at OAM Y=16, X=8 covers lines 0..7 and stalls mode 3 at x=0. Line 8
 * has no object, so its OAM scan resets the selected count while the stalled bit
 * from line 7 is still set until mode 3 begins (CR-A01). The guest then idles in
 * a 24-half-dot JR loop. Steps use a 48-half-dot budget, enough for any instruction
 * in these programs (JP is 32). */
static void reachable_sprite_rom(uint8_t *rom, uint8_t cgb_flag) {
    test_build_rom(rom, 0x00u, cgb_flag);
    static const uint8_t program[] = {
        0xAFu, 0xE0u, 0x40u,             /* xor a; ldh (LCDC),a: LCD off for OAM writes */
        0x21u, 0x00u, 0xFEu,             /* ld hl,$FE00 */
        0x3Eu, 0x10u, 0x22u,             /* Y=16 */
        0x3Eu, 0x08u, 0x22u,             /* X=8 */
        0xAFu, 0x22u, 0x22u,             /* tile 0, attributes 0 */
        0x3Eu, 0x93u, 0xE0u, 0x40u,      /* LCD, BG and OBJ on, $8000 tile data */
        0x18u, 0xFEu                     /* jr -2 */
    };
    memset(rom + 0x200u, 0, 0x100u);
    memcpy(rom + 0x200u, program, sizeof(program));
}

/* Fill BG and OBJ palette RAM with $FF through auto-incrementing BCPS/OCPS, the
 * common "all white" init: every odd byte has bit 7 set (CR-A02). It also writes
 * FF54 before any FF53, leaving the HDMA destination cursor at $00F0 (WR-A02). */
static void reachable_cram_rom(uint8_t *rom) {
    test_build_rom(rom, 0x00u, 0x80u);
    static const uint8_t program[] = {
        0xAFu, 0xE0u, 0x40u,                    /* LCD off: palette RAM always writable */
        0x3Eu, 0x80u, 0xE0u, 0x68u,             /* BCPS = auto-increment from 0 */
        0x3Eu, 0xFFu, 0x06u, 0x40u,             /* a=$FF, b=64 */
        0xE0u, 0x69u, 0x05u, 0x20u, 0xFBu,      /* ldh (BCPD),a; dec b; jr nz */
        0x3Eu, 0x80u, 0xE0u, 0x6Au,             /* OCPS = auto-increment from 0 */
        0x3Eu, 0xFFu, 0x06u, 0x40u,
        0xE0u, 0x6Bu, 0x05u, 0x20u, 0xFBu,      /* ldh (OCPD),a; dec b; jr nz */
        0x3Eu, 0xF0u, 0xE0u, 0x54u,             /* HDMA4 before HDMA3 */
        0x3Eu, 0x91u, 0xE0u, 0x40u,             /* LCD on */
        0x18u, 0xFEu
    };
    memset(rom + 0x200u, 0, 0x100u);
    memcpy(rom + 0x200u, program, sizeof(program));
}

static int reachable_seek(gbb_instance *m, uint8_t ly, uint16_t dot, uint64_t min_frame) {
    for (unsigned i = 0u; i < 200000u; ++i) {
        if (m->frame_generation >= min_frame && m->ly == ly && m->ppu_dot >= dot) return 1;
        if (!reachable_step(m, 48u)) return 0;
    }
    return 0;
}

static int reachable_sprite_case(gbb_profile profile, uint8_t cgb_flag, const char *label,
                                 reachable_tally *tally) {
    uint8_t *rom = calloc(TEST_ROM_BYTES, 1u);
    if (rom == NULL) return 0;
    reachable_sprite_rom(rom, cgb_flag);
    gbb_instance *m = reachable_boot(profile, rom, TEST_ROM_BYTES);
    free(rom);
    if (m == NULL) return 0;
    int ok = reachable_seek(m, 7u, 300u, 1u);
    /* Precondition: line 7 stalled on the object, so the next OAM scan starts stale. */
    const int stalled = ok && m->ppu_objects_stalled == 1u && m->ppu_selected_object_count == 1u;
    unsigned stale_window = 0u, seen = 0u;
    for (unsigned i = 0u; ok && i < 64u && !(m->ly == 8u && m->ppu_dot >= 100u); ++i) {
        if (m->ly == 8u && m->ppu_dot < 80u) ++stale_window;
        reachable_check(m, (i % 8u) == 0u, label, tally);
        ++seen;
        ok = reachable_step(m, 48u);
    }
    /* LCD off right after the stall line holds the PPU there indefinitely. */
    ok = ok && reachable_seek(m, 7u, 300u, m->frame_generation + 1u);
    if (ok) {
        write8(m, 0xFF40u, 0x13u);
        reachable_check(m, 1, label, tally);
        ok = reachable_advance(m, 6400u);
        reachable_check(m, 1, label, tally);
    }
    gbb_destroy(m);
    if (!ok || !stalled || stale_window == 0u || seen < 8u)
        fprintf(stderr, "%s: setup ok=%d stalled=%d stale_window=%u samples=%u\n", label, ok,
                stalled, stale_window, seen);
    return ok && stalled && stale_window != 0u && seen >= 8u;
}

static int reachable_cram_case(reachable_tally *tally) {
    uint8_t *rom = calloc(TEST_ROM_BYTES, 1u);
    if (rom == NULL) return 0;
    reachable_cram_rom(rom);
    gbb_instance *m = reachable_boot(GBB_PROFILE_CGB_CPU_E, rom, TEST_ROM_BYTES);
    free(rom);
    if (m == NULL) return 0;
    int ok = m->exec_mode == GBB_MODE_CGB;
    for (unsigned i = 0u; ok && i < 40u; ++i) {
        ok = reachable_advance(m, 997u);
        reachable_check(m, (i % 8u) == 7u, "cram-ff", tally);
    }
    /* Precondition: the guest really stored bit 7 in odd palette bytes. */
    int bit7 = 1;
    for (unsigned i = 1u; i < 64u; i += 2u)
        if (m->bg_cram[i] != 0xFFu || m->obj_cram[i] != 0xFFu) bit7 = 0;
    const int low_cursor = m->hdma.destination_cursor == 0x00F0u;
    gbb_destroy(m);
    if (!ok || !bit7 || !low_cursor)
        fprintf(stderr, "cram-ff: setup ok=%d bit7=%d low_cursor=%d\n", ok, bit7, low_cursor);
    return ok && bit7 && low_cursor;
}

static uint8_t *reachable_read_file(const char *path, size_t *size) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) return NULL;
    uint8_t *bytes = NULL;
    long length = -1;
    if (fseek(file, 0L, SEEK_END) == 0) length = ftell(file);
    if (length > 0 && length <= (long)(8u * 1024u * 1024u) && fseek(file, 0L, SEEK_SET) == 0) {
        bytes = malloc((size_t)length);
        if (bytes != NULL && fread(bytes, 1u, (size_t)length, file) != (size_t)length) {
            free(bytes);
            bytes = NULL;
        }
    }
    fclose(file);
    if (bytes != NULL) *size = (size_t)length;
    return bytes;
}

typedef struct {
    const char *path;
    uint64_t warmup;
    unsigned samples;
} reachable_fixture;

/* The stride is prime and not a multiple of the 912-half-dot line, so sampled
 * instants walk through every line phase; each eighth sample is a full roundtrip. */
static int reachable_fixture_case(gbb_profile profile, const char *root,
                                  const reachable_fixture *fixture, reachable_tally *tally) {
    char path[1024];
    const int written = snprintf(path, sizeof(path), "%s/%s", root, fixture->path);
    if (written < 0 || (size_t)written >= sizeof(path)) return 0;
    size_t size = 0u;
    uint8_t *rom = reachable_read_file(path, &size);
    gbb_instance *m = rom == NULL ? NULL : reachable_boot(profile, rom, size);
    free(rom);
    if (m == NULL) {
        fprintf(stderr, "%s: fixture did not load\n", fixture->path);
        return 0;
    }
    int ok = fixture->warmup == 0u || reachable_advance(m, fixture->warmup);
    unsigned objects = 0u;
    for (unsigned i = 0u; ok && i < fixture->samples; ++i) {
        ok = reachable_advance(m, 9973u);
        if (m->ppu_selected_object_count != 0u) ++objects;
        reachable_check(m, (i % 8u) == 7u, fixture->path, tally);
    }
    if (!ok) {
        fprintf(stderr, "%s: run stopped before sampling finished\n", fixture->path);
        reachable_check(m, 1, fixture->path, tally);
    }
    printf("  %s profile=%d mode=%d samples=%u object_samples=%u\n", fixture->path,
           (int)profile, (int)m->exec_mode, fixture->samples, objects);
    gbb_destroy(m);
    return ok;
}

static int state_reachable_saveable(const char *profile_name, const char *fixtures) {
    const int cgb = strcmp(profile_name, "cgb") == 0;
    if (!cgb && strcmp(profile_name, "dmg") != 0) return 2;
    const gbb_profile profile = cgb ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B;
    reachable_tally tally = {0u, 0u, 0u};
    int setup = 1;
    setup &= reachable_sprite_case(profile, 0x00u, cgb ? "sprite-compat" : "sprite-dmg", &tally);
    if (cgb) {
        setup &= reachable_sprite_case(profile, 0x80u, "sprite-cgb", &tally);
        setup &= reachable_cram_case(&tally);
    }
    /* Sample counts keep each case near 3 s at -O0 locally and about 15 s under a
     * macOS ASan/UBSan build, well inside the 60 s base budget (180 s under the
     * sanitizer scale). Each sample runs the full validator. The libbet warm-up
     * skips its title until objects appear (frame ~49 on DMG, ~8 on CGB). */
    static const reachable_fixture dmg_fixtures[] = {
        {"libbet/libbet.gb", 9200000u, 128u},
        {"age/stat-mode-sprites-dmgC-cgbBCE.gb", 0u, 112u},
        {"cgb-colour/colour-attr.gb", 0u, 80u},
        {"visible-demo/demo.gb", 0u, 48u},
        {"tracer/tracer.gb", 0u, 48u}
    };
    static const reachable_fixture cgb_fixtures[] = {
        {"libbet/libbet.gb", 3400000u, 128u},
        {"age/stat-mode-sprites-dmgC-cgbBCE.gb", 0u, 80u},
        {"cgb-colour/colour-attr.gb", 0u, 80u},
        {"cgb-colour/colour-cram.gb", 0u, 40u},
        {"cgb-hdma/hblank.gb", 0u, 40u},
        {"rtc3test/rtc3test.gb", 0u, 40u},
        {"visible-demo/demo.gb", 0u, 32u},
        {"tracer/tracer.gb", 0u, 32u}
    };
    const reachable_fixture *list = cgb ? cgb_fixtures : dmg_fixtures;
    const size_t count = cgb ? sizeof(cgb_fixtures) / sizeof(cgb_fixtures[0])
                             : sizeof(dmg_fixtures) / sizeof(dmg_fixtures[0]);
    for (size_t i = 0u; i < count; ++i)
        setup &= reachable_fixture_case(profile, fixtures, &list[i], &tally);
    printf("state_reachable_saveable profile=%s samples=%u roundtrips=%u failures=%u setup=%s\n",
           profile_name, tally.samples, tally.roundtrips, tally.failures, setup ? "ok" : "FAILED");
    return setup && tally.failures == 0u && tally.roundtrips != 0u ? 0 : 1;
}

static int emit_state_field_census(void) {
    gbb_instance *instance = NULL;
    if (!state_field_census_instance(&instance)) return 1;
    const size_t count = sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]);
    printf("order|qualified_id|offset|max_count|wire_width|treatment\n");
    for (size_t i = 0u; i < count; ++i) {
        state_field_record record = {0};
        if (!state_record_field(instance, i, &record)) {
            gbb_destroy(instance);
            return 1;
        }
        printf("%u|%s|%zu|%zu|%u|serialize\n", STATE_FIELDS[i].order,
               record.qualified_id, record.offset, record.count, record.width);
    }
    gbb_destroy(instance);
    return count == 198u ? 0 : 1;
}

static void test_print_sha256(const uint8_t digest[32]) {
    for (size_t i = 0u; i < 32u; ++i) printf("%02x", digest[i]);
}

static int emit_state_pin_fixture(const char *id, const char *profile_name,
                                  const char *mode_name, const char *cartridge_name,
                                  const char *fixture_name, gbb_profile profile,
                                  uint8_t cgb_flag, uint8_t cartridge_type,
                                  int hdma_in_flight) {
    gbb_instance *source = NULL, *target = NULL;
    uint8_t *saved = NULL;
    size_t size = 0u;
    if (!test_make_state(profile, cgb_flag, cartridge_type, &source, &target,
                         &saved, &size)) return 0;

    gbb_audio_frame audio[4096];
    size_t audio_count = 0u;
    const gbb_run_result run = gbb_run_audio(source, 70000u, audio,
                                              sizeof(audio) / sizeof(audio[0]),
                                              &audio_count);
    int ok = run.reason == GBB_STOP_BUDGET && audio_count != 0u;
    if (ok && hdma_in_flight) {
        source->hdma.mode = 2u;
        source->hdma.active = 1u;
        source->hdma.pending_hblank = 0u;
        source->hdma.blocks_remaining = 1u;
        source->hdma.byte_index = 15u;
        source->hdma.byte_phase = 3u;
        source->hdma.source_cursor = 0x0200u;
        source->hdma.destination_cursor = 0x8000u;
        source->hdma.block_vram_bank = source->vram_bank;
    }

    uint8_t rom_digest[32], state_digest[32];
    if (ok) {
        ok = gbb_save_state(source, saved, size) == GBB_OK;
        if (ok) {
            memcpy(rom_digest, saved + 20u, sizeof(rom_digest));
            state_sha256(saved, size, state_digest);
        }
    }
    if (ok) {
        printf("    {\"id\":\"%s\",\"profile\":\"%s\",\"mode\":\"%s\","
               "\"cartridge\":\"%s\",\"fixture\":\"%s\",\"state_size\":%zu,"
               "\"rom_sha256\":\"", id, profile_name, mode_name,
               cartridge_name, fixture_name, size);
        test_print_sha256(rom_digest);
        printf("\",\"state_sha256\":\"");
        test_print_sha256(state_digest);
        printf("\"}%s\n", strcmp(id, "cgb-native-mbc5-hdma-audio") == 0 ? "" : ",");
    }

    free(saved);
    gbb_destroy(source);
    gbb_destroy(target);
    return ok;
}

static int emit_state_portable_pins(void) {
    gbb_instance *instance = NULL;
    uint8_t *rom = calloc(TEST_ROM_BYTES, 1u);
    if (rom == NULL || gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) != GBB_OK) {
        free(rom);
        if (instance != NULL) gbb_destroy(instance);
        return 1;
    }
    test_build_rom(rom, 0x00u, 0u);
    int ok = gbb_load_rom(instance, rom, TEST_ROM_BYTES) == GBB_OK;
    uint8_t *saved = NULL;
    size_t size = 0u;
    if (ok) ok = gbb_state_size(instance, &size) == GBB_OK;
    if (ok) saved = malloc(size);
    if (ok) ok = saved != NULL && gbb_save_state(instance, saved, size) == GBB_OK;
    if (!ok) {
        free(saved); free(rom); gbb_destroy(instance);
        return 1;
    }
    const unsigned int format_version = (unsigned int)saved[4] |
        ((unsigned int)saved[5] << 8);
    const unsigned int release_major = (unsigned int)saved[8] |
        ((unsigned int)saved[9] << 8);
    const unsigned int release_minor = (unsigned int)saved[10] |
        ((unsigned int)saved[11] << 8);
    const unsigned int release_patch = (unsigned int)saved[12] |
        ((unsigned int)saved[13] << 8);
    const unsigned int behavior_version = (unsigned int)saved[14] |
        ((unsigned int)saved[15] << 8);
    free(saved); free(rom); gbb_destroy(instance);

    printf("{\"schema\":\"state-pin-emission-v1\",\"release\":{"
           "\"major\":%u,\"minor\":%u,\"patch\":%u},"
           "\"format_version\":%u,\"behavior_version\":%u,\"fixtures\":[\n",
           release_major, release_minor, release_patch, format_version,
           behavior_version);
    ok = emit_state_pin_fixture("dmg-rom-only", "DMG-CPU-B", "DMG",
                                "ROM-only", "state-codec-synthetic-v1",
                                GBB_PROFILE_DMG_CPU_B, 0u, 0x00u, 0) &&
         emit_state_pin_fixture("cgb-compat-mbc3-rtc-audio", "CGB-CPU-E",
                                "CGB-DMG-compatibility", "MBC3-RTC-RAM",
                                "state-codec-synthetic-v1", GBB_PROFILE_CGB_CPU_E,
                                0u, 0x10u, 0) &&
         emit_state_pin_fixture("cgb-native-mbc5-hdma-audio", "CGB-CPU-E",
                                "CGB-native", "MBC5-rumble-RAM",
                                "state-codec-synthetic-v1", GBB_PROFILE_CGB_CPU_E,
                                0x80u, 0x1Eu, 1);
    puts("]}");
    return ok ? 0 : 1;
}

static int state_codec_matrix(void) {
    static const struct {
        uint8_t type;
        const char *name;
    } mappers[] = {
        {0x00u, "ROM-only"}, {0x03u, "MBC1"}, {0x06u, "MBC2"},
        {0x10u, "MBC3"}, {0x1Eu, "MBC5"}
    };
    static const struct {
        gbb_profile profile;
        uint8_t cgb_flag;
        gbb_exec_mode mode;
    } modes[] = {
        {GBB_PROFILE_DMG_CPU_B, 0u, GBB_MODE_DMG},
        {GBB_PROFILE_CGB_CPU_E, 0u, GBB_MODE_CGB_DMG_COMPAT},
        {GBB_PROFILE_CGB_CPU_E, 0x80u, GBB_MODE_CGB}
    };
    size_t completed = 0u;
    for (size_t mapper = 0u; mapper < sizeof(mappers) / sizeof(mappers[0]); ++mapper) {
        for (size_t mode = 0u; mode < sizeof(modes) / sizeof(modes[0]); ++mode) {
            if (!state_matrix_case(modes[mode].profile, modes[mode].cgb_flag,
                                   modes[mode].mode, mappers[mapper].type)) {
                fprintf(stderr, "FAIL state_codec_matrix mapper=%s mode=%u\n",
                        mappers[mapper].name, (unsigned)modes[mode].mode);
                return 1;
            }
            ++completed;
        }
    }
    if (!test_state_boundary_sizes()) {
        fprintf(stderr, "FAIL state_codec_matrix stable size at a CPU/device boundary\n");
        return 1;
    }
    if (!test_full_field_census()) {
        fprintf(stderr, "FAIL state_codec_matrix maximum-RAM field census\n");
        return 1;
    }
    printf("state_codec_matrix pass categories=%zu mappers=5 profiles=2 modes=3\n", completed);
    return completed == 15u ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "state_field_census") == 0)
        return emit_state_field_census();
    if (argc == 2 && strcmp(argv[1], "state_portable_pins") == 0)
        return emit_state_portable_pins();
    if (argc == 4 && strcmp(argv[1], "state_reachable_saveable") == 0)
        return state_reachable_saveable(argv[2], argv[3]);
    if (argc != 2) {
        fprintf(stderr, "usage: test_state_codec state_identity|state_codec_matrix|state_canonical|state_semantic_bounds|state_override_isolation|state_field_census|state_reachable_saveable dmg|cgb FIXTURES\n");
        return 2;
    }
    if (strcmp(argv[1], "state_identity") == 0) return state_identity();
    if (strcmp(argv[1], "state_codec_matrix") == 0) return state_codec_matrix();
    if (strcmp(argv[1], "state_canonical") == 0) return state_canonical();
    if (strcmp(argv[1], "state_semantic_bounds") == 0) return state_semantic_bounds();
    if (strcmp(argv[1], "state_override_isolation") == 0) return state_override_isolation();
    fprintf(stderr, "unknown state codec case: %s\n", argv[1]);
    return 2;
}
