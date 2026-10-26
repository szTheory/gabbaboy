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
                      observed == expected_size;
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
    if (argc != 2) {
        fprintf(stderr, "usage: test_state_codec state_identity|state_codec_matrix|state_field_census\n");
        return 2;
    }
    if (strcmp(argv[1], "state_identity") == 0) return state_identity();
    if (strcmp(argv[1], "state_codec_matrix") == 0) return state_codec_matrix();
    fprintf(stderr, "unknown state codec case: %s\n", argv[1]);
    return 2;
}
