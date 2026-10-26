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

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_state_api size_bound|audio_bound\n");
        return 2;
    }
    if (strcmp(argv[1], "size_bound") == 0) return state_size_bound(argv[1]);
    if (strcmp(argv[1], "audio_bound") == 0) return state_audio_bound(argv[1]);
    fprintf(stderr, "unknown state proof case: %s\n", argv[1]);
    return 2;
}
