/* Single-TU proof tests access the private field inventory and arithmetic bounds.
 * Save/load behavior is added only after this gate is committed and recorded.
 */
#include "../src/core/gabbaboy.c"

#include <stdio.h>

#define REQUIRE(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #condition); \
        return 1; \
    } \
} while (0)

static int state_size_bound(const char *case_name) {
    const size_t field_count = sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]);
    size_t body_size = SIZE_MAX;
    size_t total_size = SIZE_MAX;
    REQUIRE(field_count != 0u);
    REQUIRE(state_descriptor_max_body_size(STATE_FIELDS, field_count, &body_size));
    REQUIRE(state_descriptor_max_total_size(STATE_FIELDS, field_count, &total_size));
    REQUIRE(body_size > GBB_STATE_MAX_CARTRIDGE_RAM_BYTES);
    REQUIRE(body_size <= GBB_STATE_MAX_BODY_BYTES);
    REQUIRE(total_size == body_size + GBB_STATE_HEADER_BYTES);
    REQUIRE(total_size <= GBB_STATE_HEADER_BYTES + GBB_STATE_MAX_BODY_BYTES);

    size_t untouched = 123u;
    REQUIRE(!state_descriptor_max_body_size(STATE_FIELDS, 0u, &untouched));
    REQUIRE(untouched == 123u);

    state_field_descriptor mutated[sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0])];
    memcpy(mutated, STATE_FIELDS, sizeof(mutated));
    mutated[0].wire_width = 8u;
    mutated[0].max_count = SIZE_MAX;
    untouched = 123u;
    REQUIRE(!state_descriptor_max_body_size(mutated, field_count, &untouched));
    REQUIRE(untouched == 123u);

    memcpy(mutated, STATE_FIELDS, sizeof(mutated));
    mutated[0].wire_width = 1u;
    mutated[0].max_count = (size_t)GBB_STATE_MAX_BODY_BYTES + 1u;
    REQUIRE(!state_descriptor_max_body_size(mutated, field_count, &untouched));

    memcpy(mutated, STATE_FIELDS, sizeof(mutated));
    mutated[1].order = 0u;
    REQUIRE(!state_descriptor_max_body_size(mutated, field_count, &untouched));

    printf("state_size_bound pass fields=%zu body_max=%zu total_max=%zu dynamic_ram_max=%u\n",
           field_count, body_size, total_size, GBB_STATE_MAX_CARTRIDGE_RAM_BYTES);
    (void)case_name;
    return 0;
}

static uint64_t ceil_div_u64(uint64_t numerator, uint64_t denominator) {
    return numerator / denominator + (numerator % denominator != 0u ? 1u : 0u);
}

static int state_audio_bound(const char *case_name) {
    const int32_t dac_min = -16384;
    const int32_t dac_max = 14336;
    const int32_t volume_max = 8;
    const int32_t one_channel_min =
        (dac_min * volume_max) / GBB_AUDIO_MIX_HEADROOM_DIV;
    const int32_t one_channel_max =
        (dac_max * volume_max) / GBB_AUDIO_MIX_HEADROOM_DIV;
    const int32_t mix_min = one_channel_min * 4;
    const int32_t mix_max = one_channel_max * 4;
    REQUIRE(mix_min == GBB_STATE_AUDIO_MIX_MIN);
    REQUIRE(mix_max == GBB_STATE_AUDIO_MIX_MAX);
    REQUIRE(state_audio_mix_level_valid(mix_min));
    REQUIRE(state_audio_mix_level_valid(mix_max));
    REQUIRE(!state_audio_mix_level_valid(mix_min - 1));
    REQUIRE(!state_audio_mix_level_valid(mix_max + 1));
    const uint64_t max_delta = (uint64_t)((int64_t)mix_max - (int64_t)mix_min);
    REQUIRE(max_delta == GBB_STATE_AUDIO_MAX_DELTA);

    uint64_t max_coefficient_delta = 0u;
    for (unsigned phase = 0u; phase < GBB_AUDIO_EVENT_PHASES; ++phase) {
        for (unsigned tap = 0u; tap < GBB_AUDIO_EVENT_TAPS; ++tap) {
            const int32_t difference = (int32_t)audio_step_q15[phase][tap] - 32767;
            const uint64_t magnitude = difference < 0
                ? (uint64_t)(-(int64_t)difference) : (uint64_t)difference;
            if (magnitude > max_coefficient_delta) max_coefficient_delta = magnitude;
        }
    }
    REQUIRE(max_coefficient_delta == GBB_STATE_AUDIO_MAX_COEFFICIENT_DELTA);
    REQUIRE(max_delta <= UINT64_MAX / max_coefficient_delta);
    const uint64_t max_edge_contribution = max_delta * max_coefficient_delta;
    REQUIRE(max_edge_contribution == GBB_STATE_AUDIO_MAX_EDGE_CONTRIBUTION);
    REQUIRE(GBB_AUDIO_EVENT_TAPS == 16u);
    REQUIRE(GBB_AUDIO_SAMPLE_RATE < GBB_AUDIO_CLOCK_HALF_DOTS);

    const uint64_t lifetime_numerator = UINT64_C(16) * GBB_AUDIO_CLOCK_HALF_DOTS;
    const uint64_t expected_lifetime_ticks =
        ceil_div_u64(lifetime_numerator, GBB_AUDIO_SAMPLE_RATE);
    REQUIRE(expected_lifetime_ticks == GBB_STATE_AUDIO_MAX_EDGE_TICKS);
    REQUIRE(expected_lifetime_ticks == 2797u);

    /* Every phase value maps to some residual modulo sample rate. For total
     * lifetime S=16*clock and edge period R=sample_rate, the rounded prefix plus
     * suffix is floor(S/R) or ceil(S/R), regardless of the slot's current age.
     * Enumerating all R residues checks both rounding branches without assuming
     * a convenient APU phase or guest register-write cadence.
     */
    const uint64_t base_lifetime = lifetime_numerator / GBB_AUDIO_SAMPLE_RATE;
    const uint64_t lifetime_remainder = lifetime_numerator % GBB_AUDIO_SAMPLE_RATE;
    for (uint64_t phase_remainder = 0u; phase_remainder < GBB_AUDIO_SAMPLE_RATE; ++phase_remainder) {
        const uint64_t opportunities = base_lifetime +
            (lifetime_remainder > phase_remainder ? 1u : 0u);
        REQUIRE(opportunities <= expected_lifetime_ticks);
    }

    REQUIRE(max_edge_contribution <= UINT64_MAX / expected_lifetime_ticks);
    const uint64_t max_ring_lifetime = max_edge_contribution * expected_lifetime_ticks;
    REQUIRE(max_ring_lifetime == UINT64_C(5630932930560));
    REQUIRE(max_ring_lifetime < (uint64_t)INT64_MAX);
    const uint64_t mix_scaled = UINT64_C(32768) * UINT64_C(32768);
    REQUIRE(max_ring_lifetime <= (uint64_t)INT64_MAX - mix_scaled - UINT64_C(16384));
    const uint64_t mix_and_ring = max_ring_lifetime + mix_scaled;
    REQUIRE(mix_and_ring <= (uint64_t)INT64_MAX - UINT64_C(16384));
    REQUIRE(mix_and_ring + UINT64_C(16384) < (uint64_t)INT64_MAX);
    const uint64_t max_hpf_product = UINT64_C(32768) * GBB_AUDIO_HPF_Q15;
    REQUIRE(max_hpf_product <= UINT64_MAX - UINT64_C(65536) - UINT64_C(16384));
    REQUIRE(max_hpf_product + UINT64_C(65536) + UINT64_C(16384) < (uint64_t)INT64_MAX);
    REQUIRE(state_audio_hpf_history_valid(INT16_MIN, INT16_MAX));
    REQUIRE(!state_audio_hpf_history_valid((int32_t)INT16_MIN - 1, 0));
    REQUIRE(!state_audio_hpf_history_valid(0, (int32_t)INT16_MAX + 1));

    static const uint64_t phase_probes[] = {
        0u, 1u, GBB_AUDIO_SAMPLE_RATE - 1u, GBB_AUDIO_SAMPLE_RATE,
        GBB_AUDIO_CLOCK_HALF_DOTS / 2u, GBB_AUDIO_CLOCK_HALF_DOTS - 1u
    };
    for (uint8_t head = 0u; head < GBB_AUDIO_EVENT_TAPS; ++head) {
        for (size_t offset = 0u; offset < GBB_AUDIO_EVENT_TAPS; ++offset) {
            const size_t slot = (offset + head) % GBB_AUDIO_EVENT_TAPS;
            const uint64_t completed = (uint64_t)(GBB_AUDIO_EVENT_TAPS - 1u - offset);
            for (size_t p = 0u; p < sizeof(phase_probes) / sizeof(phase_probes[0]); ++p) {
                const uint64_t phase = phase_probes[p];
                if (phase >= GBB_AUDIO_CLOCK_HALF_DOTS) continue;
                const uint64_t past_ticks =
                    (completed * GBB_AUDIO_CLOCK_HALF_DOTS + phase) / GBB_AUDIO_SAMPLE_RATE;
                const uint64_t future_ticks = ceil_div_u64(
                    ((uint64_t)offset + 1u) * GBB_AUDIO_CLOCK_HALF_DOTS - phase,
                    GBB_AUDIO_SAMPLE_RATE);
                REQUIRE(past_ticks + future_ticks <= expected_lifetime_ticks);
                REQUIRE(past_ticks <= UINT64_MAX / max_edge_contribution);
                const uint64_t accepted_limit = past_ticks * max_edge_contribution;
                REQUIRE(accepted_limit <= (uint64_t)INT64_MAX);
                REQUIRE(state_audio_ring_slot_valid(head, slot, phase, (int64_t)accepted_limit));
                REQUIRE(state_audio_ring_slot_valid(head, slot, phase, -(int64_t)accepted_limit));
                REQUIRE(!state_audio_ring_slot_valid(head, slot, phase,
                                                     (int64_t)(accepted_limit + 1u)));
                REQUIRE(!state_audio_ring_slot_valid(head, slot, phase,
                                                     -(int64_t)(accepted_limit + 1u)));
                REQUIRE(!state_audio_ring_slot_valid(head, slot, phase, INT64_MAX));
            }
        }
    }
    REQUIRE(!state_audio_ring_slot_valid(GBB_AUDIO_EVENT_TAPS, 0u, 0u, 0));
    REQUIRE(!state_audio_ring_slot_valid(0u, GBB_AUDIO_EVENT_TAPS, 0u, 0));
    REQUIRE(!state_audio_ring_slot_valid(0u, 0u, GBB_AUDIO_CLOCK_HALF_DOTS, 0));

    printf("state_audio_bound pass mix=[%d,%d] delta=%llu coefficient=%llu edge=%llu halfdot_lifetime=%llu ring=%llu\n",
           mix_min, mix_max, (unsigned long long)max_delta,
           (unsigned long long)max_coefficient_delta,
           (unsigned long long)max_edge_contribution,
           (unsigned long long)expected_lifetime_ticks,
           (unsigned long long)max_ring_lifetime);
    (void)case_name;
    return 0;
}

static uint8_t *state_read_file(const char *path, size_t *size_out) {
    FILE *file = fopen(path, "rb");
    if (file == NULL || fseek(file, 0, SEEK_END) != 0) {
        if (file != NULL) fclose(file);
        return NULL;
    }
    const long length = ftell(file);
    if (length < 0 || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return NULL;
    }
    uint8_t *bytes = malloc((size_t)length);
    if (bytes == NULL || fread(bytes, 1u, (size_t)length, file) != (size_t)length) {
        free(bytes);
        fclose(file);
        return NULL;
    }
    fclose(file);
    *size_out = (size_t)length;
    return bytes;
}

static uint32_t state_test_crc32_update(uint32_t crc, const uint8_t *bytes, size_t length) {
    for (size_t i = 0u; i < length; ++i) {
        crc ^= bytes[i];
        for (unsigned bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) != 0u ? UINT32_C(0xEDB88320) : 0u);
    }
    return crc;
}

static void state_test_rechecksum(uint8_t *bytes, size_t total_size) {
    uint32_t crc = state_test_crc32_update(UINT32_MAX, bytes, 60u);
    crc = state_test_crc32_update(crc, bytes + GBB_STATE_HEADER_BYTES,
                                  total_size - GBB_STATE_HEADER_BYTES) ^ UINT32_MAX;
    for (unsigned i = 0u; i < 4u; ++i) bytes[60u + i] = (uint8_t)(crc >> (i * 8u));
}

static uint32_t state_test_u32(const uint8_t *bytes) {
    return (uint32_t)bytes[0] | ((uint32_t)bytes[1] << 8) |
           ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

static void state_test_put_u16(uint8_t *bytes, uint16_t value) {
    bytes[0] = (uint8_t)value;
    bytes[1] = (uint8_t)(value >> 8);
}

static void state_test_put_u32(uint8_t *bytes, uint32_t value) {
    for (unsigned i = 0u; i < 4u; ++i) bytes[i] = (uint8_t)(value >> (i * 8u));
}

static size_t state_test_body_offset(const char *path, size_t cartridge_ram_size) {
    size_t offset = 0u;
    const size_t count = sizeof(STATE_FIELDS) / sizeof(STATE_FIELDS[0]);
    for (size_t i = 0u; i < count; ++i) {
        const size_t elements = strcmp(STATE_FIELDS[i].path, "cartridge_ram") == 0
            ? cartridge_ram_size : STATE_FIELDS[i].max_count;
        if (strcmp(STATE_FIELDS[i].path, path) == 0) return offset;
        offset += elements * STATE_FIELDS[i].wire_width;
    }
    return SIZE_MAX;
}

static int state_expect_unchanged(gbb_instance *instance, const uint8_t *bytes,
                                  size_t length, gbb_error expected) {
    gbb_instance before = *instance;
    const gbb_error result = gbb_load_state(instance, bytes, length);
    if (result != expected || memcmp(&before, instance, sizeof(before)) != 0) {
        fprintf(stderr, "state refusal expected=%d actual=%d mutation=%d\n",
                (int)expected, (int)result,
                memcmp(&before, instance, sizeof(before)) != 0);
        return 1;
    }
    return 0;
}

static int state_format_contract(const char *rom_path) {
    REQUIRE(state_crc32((const uint8_t *)"123456789", 9u) == UINT32_C(0xCBF43926));
    const int64_t signed_values[] = { INT64_MIN + 1, INT64_MIN / 2, -1, 0, 1, INT64_MAX };
    for (size_t i = 0u; i < sizeof(signed_values) / sizeof(signed_values[0]); ++i) {
        uint8_t encoded[8];
        state_encode_i64(signed_values[i], encoded);
        int64_t decoded = 0;
        REQUIRE(state_decode_i64(encoded, &decoded));
        REQUIRE(decoded == signed_values[i]);
    }
    uint8_t forbidden_min[8] = { 0u };
    forbidden_min[7] = 0x80u;
    int64_t forbidden_decoded = 0;
    REQUIRE(state_decode_i64(forbidden_min, &forbidden_decoded));
    REQUIRE(forbidden_decoded == INT64_MIN);
    REQUIRE(!state_audio_ring_slot_valid(0u, 0u, 0u, forbidden_decoded));

    size_t rom_size = 0u;
    uint8_t *rom = state_read_file(rom_path, &rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *source = NULL;
    gbb_instance *target = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &source) == GBB_OK);
    size_t untouched_size = 731u;
    REQUIRE(gbb_state_size(NULL, &untouched_size) == GBB_INVALID_ARGUMENT);
    REQUIRE(untouched_size == 731u);
    REQUIRE(gbb_state_size(source, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_state_size(source, &untouched_size) == GBB_STATE_NO_ROM);
    REQUIRE(untouched_size == 731u);
    uint8_t no_rom_buffer[GBB_STATE_HEADER_BYTES + 4u];
    memset(no_rom_buffer, 0xA5, sizeof(no_rom_buffer));
    uint8_t no_rom_snapshot[sizeof(no_rom_buffer)];
    memcpy(no_rom_snapshot, no_rom_buffer, sizeof(no_rom_buffer));
    REQUIRE(gbb_save_state(source, no_rom_buffer, sizeof(no_rom_buffer)) == GBB_STATE_NO_ROM);
    REQUIRE(memcmp(no_rom_buffer, no_rom_snapshot, sizeof(no_rom_buffer)) == 0);
    REQUIRE(gbb_load_state(source, no_rom_buffer, GBB_STATE_HEADER_BYTES - 1u) == GBB_STATE_BAD_FORMAT);
    REQUIRE(gbb_load_state(source, no_rom_buffer, GBB_STATE_HEADER_BYTES) == GBB_STATE_BAD_FORMAT);
    no_rom_buffer[0] = 'G'; no_rom_buffer[1] = 'B'; no_rom_buffer[2] = 'B'; no_rom_buffer[3] = 'S';
    REQUIRE(gbb_load_state(source, no_rom_buffer, GBB_STATE_HEADER_BYTES) == GBB_STATE_UNSUPPORTED_VERSION);

    REQUIRE(gbb_load_rom(source, rom, rom_size) == GBB_OK);
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &target) == GBB_OK);
    REQUIRE(gbb_load_rom(target, rom, rom_size) == GBB_OK);
    gbb_audio_frame audio[1024];
    size_t audio_count = 0u;
    const gbb_run_result progressed = gbb_run_audio(source, UINT64_C(100000), audio,
                                                     sizeof(audio) / sizeof(audio[0]), &audio_count);
    REQUIRE(progressed.reason == GBB_STOP_BUDGET);
    REQUIRE(progressed.consumed_half_dots == UINT64_C(100000));
    REQUIRE(audio_count != 0u);

    size_t state_size = 0u;
    REQUIRE(gbb_state_size(source, &state_size) == GBB_OK);
    REQUIRE(state_size >= GBB_STATE_HEADER_BYTES);
    REQUIRE(state_size <= GBB_STATE_HEADER_BYTES + GBB_STATE_MAX_BODY_BYTES);
    REQUIRE(gbb_state_size(source, &untouched_size) == GBB_OK);
    REQUIRE(untouched_size == state_size);
    uint8_t *state = malloc(state_size + 8u);
    uint8_t *copy = malloc(state_size);
    REQUIRE(state != NULL && copy != NULL);
    memset(state, 0xA5, state_size + 8u);
    REQUIRE(gbb_save_state(source, NULL, state_size) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_save_state(source, state, state_size - 1u) == GBB_BUFFER_TOO_SMALL);
    for (size_t i = 0u; i < state_size + 8u; ++i) REQUIRE(state[i] == 0xA5u);
    gbb_instance source_before_save = *source;
    REQUIRE(gbb_save_state(source, state, state_size + 8u) == GBB_OK);
    REQUIRE(memcmp(&source_before_save, source, sizeof(*source)) == 0);
    for (size_t i = state_size; i < state_size + 8u; ++i) REQUIRE(state[i] == 0xA5u);
    REQUIRE(memcmp(state, "GBBS", 4u) == 0);
    REQUIRE(state_test_u32(state + 52u) <= GBB_STATE_MAX_BODY_BYTES);
    REQUIRE(state_test_u32(state + 56u) == state_size);
    memcpy(copy, state, state_size);

    REQUIRE(gbb_load_state(target, state, state_size) == GBB_OK);
    size_t target_size = 0u;
    REQUIRE(gbb_state_size(target, &target_size) == GBB_OK && target_size == state_size);
    uint8_t *target_state = malloc(target_size);
    REQUIRE(target_state != NULL);
    REQUIRE(gbb_save_state(target, target_state, target_size) == GBB_OK);
    REQUIRE(memcmp(target_state, state, state_size) == 0);

    REQUIRE(state_expect_unchanged(target, state, state_size - 1u, GBB_STATE_SIZE_MISMATCH) == 0);
    memcpy(copy, state, state_size);
    copy[0] = 'X';
    REQUIRE(state_expect_unchanged(target, copy, state_size, GBB_STATE_BAD_FORMAT) == 0);
    memcpy(copy, state, state_size);
    state_test_put_u16(copy + 4u, (uint16_t)(GBB_STATE_FORMAT_VERSION + 1u));
    REQUIRE(state_expect_unchanged(target, copy, state_size, GBB_STATE_UNSUPPORTED_VERSION) == 0);
    memcpy(copy, state, state_size);
    copy[20] ^= 1u;
    state_test_put_u32(copy + 52u, 0u);
    state_test_put_u32(copy + 56u, GBB_STATE_HEADER_BYTES);
    REQUIRE(state_expect_unchanged(target, copy, GBB_STATE_HEADER_BYTES,
                                   GBB_STATE_IDENTITY_MISMATCH) == 0);
    memcpy(copy, state, state_size);
    copy[GBB_STATE_HEADER_BYTES] ^= 1u;
    REQUIRE(state_expect_unchanged(target, copy, state_size, GBB_STATE_CORRUPT) == 0);
    memcpy(copy, state, state_size);
    state_test_put_u16(copy + 18u, 1u);
    state_test_rechecksum(copy, state_size);
    REQUIRE(state_expect_unchanged(target, copy, state_size, GBB_STATE_INVALID_CONTENT) == 0);
    memcpy(copy, state, state_size);
    const size_t phase_offset = state_test_body_offset("apu_sample_phase", 0u);
    REQUIRE(phase_offset != SIZE_MAX);
    for (unsigned i = 0u; i < 8u; ++i) copy[GBB_STATE_HEADER_BYTES + phase_offset + i] = 0xFFu;
    state_test_rechecksum(copy, state_size);
    REQUIRE(state_expect_unchanged(target, copy, state_size, GBB_STATE_INVALID_CONTENT) == 0);
    memcpy(copy, state, state_size);
    const size_t ring_offset = state_test_body_offset("audio_event_ring", 0u);
    REQUIRE(ring_offset != SIZE_MAX);
    memset(copy + GBB_STATE_HEADER_BYTES + ring_offset, 0, 8u);
    copy[GBB_STATE_HEADER_BYTES + ring_offset + 7u] = 0x80u;
    state_test_rechecksum(copy, state_size);
    REQUIRE(state_expect_unchanged(target, copy, state_size, GBB_STATE_INVALID_CONTENT) == 0);

    REQUIRE(gbb_reset(target) == GBB_OK);
    REQUIRE(gbb_load_state(target, state, state_size) == GBB_OK);
    REQUIRE(gbb_save_state(target, target_state, target_size) == GBB_OK);
    REQUIRE(memcmp(target_state, state, state_size) == 0);
    printf("state_format_contract pass bytes=%zu audio_frames=%zu crc=CBF43926\n",
           state_size, audio_count);
    free(target_state);
    free(copy);
    free(state);
    gbb_destroy(target);
    gbb_destroy(source);
    free(rom);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2 && argc != 3) {
        fprintf(stderr, "usage: test_state_api size_bound|audio_bound|format_contract [rom]\n");
        return 2;
    }
    if (strcmp(argv[1], "size_bound") == 0) return state_size_bound(argv[1]);
    if (strcmp(argv[1], "audio_bound") == 0) return state_audio_bound(argv[1]);
    if (strcmp(argv[1], "format_contract") == 0 && argc == 3)
        return state_format_contract(argv[2]);
    fprintf(stderr, "unknown state proof case: %s\n", argv[1]);
    return 2;
}
