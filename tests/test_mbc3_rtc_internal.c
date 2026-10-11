/* Single-TU white-box RTC tests. The test includes the core source itself to reach
 * the static write8/read8, rtc_add_seconds and the instance layout, so it must not
 * link GabbaBoy::core. Plan 09-15 compiles this same file against mutant copies of
 * the core by defining GBB_CORE_SOURCE_PATH. */
#ifndef GBB_CORE_SOURCE_PATH
#define GBB_CORE_SOURCE_PATH "../src/core/gabbaboy.c"
#endif
#include GBB_CORE_SOURCE_PATH

#include <stdio.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define SECOND ((uint64_t)1u << 23) /* half-dots per emulated second */

/* ---- helpers ------------------------------------------------------------- */

static uint64_t rng_state = 0x9E3779B97F4A7C15ull;
static uint64_t rng(void) {
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return rng_state;
}

/* A 32 KiB image of the given MBC3 type. $200 holds a busy loop (JR -2), reached
 * from the entry point, so gbb_run advances time without touching the clock. */
static gbb_instance *make(uint8_t type) {
    static uint8_t rom[0x8000];
    memset(rom, 0, sizeof(rom));
    rom[0x147u] = type;
    rom[0x149u] = (type == 0x0Fu || type == 0x11u) ? 0x00u : 0x02u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x00u; rom[0x102u] = 0x02u;
    rom[0x200u] = 0x18u; rom[0x201u] = 0xFEu;
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK) return NULL;
    if (gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) { gbb_destroy(m); return NULL; }
    return m;
}

/* Direct bus access stamps the time itself: bus_write normally advances the devices
 * first, so time_half_dots is the write timestamp. */
static void enable(gbb_instance *m) { write8(m, 0x0000u, 0x0Au); }
static void wreg(gbb_instance *m, uint64_t now, unsigned reg, uint8_t v) {
    m->time_half_dots = now;
    write8(m, 0x4000u, (uint8_t)(0x08u + reg));
    write8(m, 0xA000u, v);
}
static void latch(gbb_instance *m, uint64_t now) {
    m->time_half_dots = now;
    write8(m, 0x6000u, 0x00u);
    write8(m, 0x6000u, 0x01u);
}
static uint8_t rreg(gbb_instance *m, unsigned reg) {
    write8(m, 0x4000u, (uint8_t)(0x08u + reg));
    return read8(m, 0xA000u);
}
static void read_all(gbb_instance *m, uint8_t out[5]) {
    for (unsigned r = 0u; r < 5u; ++r) out[r] = rreg(m, r);
}

/* Fresh machine, registers written at t = 0 (DH last), latch at `when`, read back. */
static int scenario(uint8_t type, const uint8_t init[5], uint64_t when, uint8_t out[5]) {
    gbb_instance *m = make(type);
    if (m == NULL) return 0;
    enable(m);
    for (unsigned r = 0u; r < 5u; ++r) wreg(m, 0u, r, init[r]);
    latch(m, when);
    read_all(m, out);
    gbb_destroy(m);
    return 1;
}

#define EXPECT5(out, a, b, c, d, e) \
    REQUIRE((out)[0] == (a) && (out)[1] == (b) && (out)[2] == (c) && \
            (out)[3] == (d) && (out)[4] == (e))

/* ---- naive per-second model: the D-08 rules, one second at a time -------- */

static void naive_second(cart_state *c) {
    int carry = 0;
    if (c->rtc_s == 59u) { c->rtc_s = 0u; carry = 1; }
    else c->rtc_s = (uint8_t)((c->rtc_s + 1u) & 0x3Fu);
    if (carry) {
        carry = 0;
        if (c->rtc_m == 59u) { c->rtc_m = 0u; carry = 1; }
        else c->rtc_m = (uint8_t)((c->rtc_m + 1u) & 0x3Fu);
    }
    if (carry) {
        carry = 0;
        if (c->rtc_h == 23u) { c->rtc_h = 0u; carry = 1; }
        else c->rtc_h = (uint8_t)((c->rtc_h + 1u) & 0x1Fu);
    }
    if (carry) {
        const unsigned day = c->rtc_dl | ((c->rtc_dh & 1u) << 8);
        if (day == 511u) { c->rtc_dl = 0u; c->rtc_dh = (uint8_t)((c->rtc_dh & 0xC0u) | 0x80u); }
        else {
            const unsigned next = day + 1u;
            c->rtc_dl = (uint8_t)(next & 0xFFu);
            c->rtc_dh = (uint8_t)((c->rtc_dh & 0xC0u) | ((next >> 8) & 1u));
        }
    }
}

static void random_state(cart_state *c) {
    memset(c, 0, sizeof(*c));
    c->rtc_s = (uint8_t)(rng() & 0x3Fu);
    c->rtc_m = (uint8_t)(rng() & 0x3Fu);
    c->rtc_h = (uint8_t)(rng() & 0x1Fu);
    c->rtc_dl = (uint8_t)rng();
    c->rtc_dh = (uint8_t)(rng() & 0xC1u);
}

static int same_clock(const cart_state *a, const cart_state *b) {
    return a->rtc_s == b->rtc_s && a->rtc_m == b->rtc_m && a->rtc_h == b->rtc_h &&
           a->rtc_dl == b->rtc_dl && a->rtc_dh == b->rtc_dh;
}

/* ---- D-12 differential and metamorphic ----------------------------------- */

static int rtc_closed_form_differential(void) {
    /* The naive stepper cannot run 2^40 seconds, so the long counts use the period:
     * for an in-range state a whole number of 512-day cycles returns every field to
     * where it started and leaves the sticky carry set. */
    const uint64_t period = 512ull * 86400ull;
    for (int i = 0; i < 100000; ++i) {
        cart_state a, b;
        random_state(&a);
        b = a;
        const uint64_t n = (i % 1000 == 0) ? rng() % 200000u : rng() % 1000u;
        for (uint64_t k = 0u; k < n; ++k) naive_second(&a);
        rtc_add_seconds(&b, n);
        REQUIRE(same_clock(&a, &b));
    }
    for (int i = 0; i < 2000; ++i) {
        cart_state a, b;
        random_state(&a);
        a.rtc_s %= 60u; a.rtc_m %= 60u; a.rtc_h %= 24u;
        a.rtc_dh = (uint8_t)(a.rtc_dh & 0x01u);
        b = a;
        const uint64_t cycles = 1u + rng() % ((1ull << 40) / period);
        const uint64_t rest = rng() % 5000u;
        for (uint64_t k = 0u; k < rest; ++k) naive_second(&a);
        a.rtc_dh |= 0x80u; /* a full cycle crosses 511 -> 0 at least once */
        rtc_add_seconds(&b, cycles * period + rest);
        REQUIRE(same_clock(&a, &b));
    }
    return 0;
}

static int rtc_add_composes(void) {
    for (int i = 0; i < 20000; ++i) {
        cart_state a, b;
        random_state(&a);
        b = a;
        const uint64_t x = rng() >> (rng() % 40u + 24u);
        const uint64_t y = rng() >> (rng() % 40u + 24u);
        rtc_add_seconds(&a, x);
        rtc_add_seconds(&a, y);
        rtc_add_seconds(&b, x + y);
        REQUIRE(same_clock(&a, &b));
    }
    /* Both halves fit int64_t, their sum does not; the model must never sum in int64_t. */
    cart_state a, b;
    random_state(&a);
    b = a;
    rtc_add_seconds(&a, 0x7FFFFFFFFFFFFFFFull);
    rtc_add_seconds(&a, 0x7FFFFFFFFFFFFFFFull);
    rtc_add_seconds(&b, 0xFFFFFFFFFFFFFFFEull);
    REQUIRE(same_clock(&a, &b));
    return 0;
}

/* ---- D-08 behaviour table ------------------------------------------------ */

static int rtc_rate_exact(void) {
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 1000u, 0u, 5u);
    latch(m, 1000u + SECOND - 1u);
    REQUIRE(rreg(m, 0u) == 5u);
    latch(m, 1000u + SECOND);
    REQUIRE(rreg(m, 0u) == 6u);
    gbb_destroy(m);
    return 0;
}

static int rtc_prescaler_rules(void) {
    const uint64_t t0 = 4000000u;
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);

    /* A seconds write restarts the prescaler, even when the value is unchanged. */
    wreg(m, 0u, 0u, 0u);
    wreg(m, t0, 0u, 0u);
    latch(m, SECOND);
    REQUIRE(rreg(m, 0u) == 0u);
    REQUIRE(m->cart.rtc_sub == (uint32_t)(SECOND - t0));

    /* M, H and DL writes keep it: the second still ends at 2^23 after the first write. */
    gbb_destroy(m);
    m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 0u);
    wreg(m, t0, 1u, 1u);
    wreg(m, t0, 2u, 1u);
    wreg(m, t0, 3u, 1u);
    latch(m, SECOND);
    REQUIRE(rreg(m, 0u) == 1u);

    /* Halting and un-halting keep it, and the halted period is not credited. */
    gbb_destroy(m);
    m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 0u);
    wreg(m, t0, 4u, 0x40u);
    wreg(m, t0 + 3u * SECOND, 4u, 0x00u);
    latch(m, t0 + 3u * SECOND + (SECOND - t0));
    REQUIRE(rreg(m, 0u) == 1u);
    gbb_destroy(m);
    return 0;
}

static int rtc_write_masks(void) {
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    for (unsigned r = 0u; r < 5u; ++r) wreg(m, 0u, r, 0xFFu);
    latch(m, 0u);
    uint8_t out[5];
    read_all(m, out);
    EXPECT5(out, 0x3Fu, 0x3Fu, 0x1Fu, 0xFFu, 0xC1u);
    gbb_destroy(m);
    return 0;
}

static int rtc_out_of_range_rollover(void) {
    uint8_t out[5];
    /* Seconds 63 steps to 0 with no minute carry. */
    const uint8_t s63[5] = {63u, 5u, 5u, 0u, 0u};
    REQUIRE(scenario(0x10u, s63, SECOND, out));
    EXPECT5(out, 0u, 5u, 5u, 0u, 0u);
    /* Seconds 60 is out of range, so it also steps to 61 without carrying. */
    const uint8_t s60[5] = {60u, 5u, 5u, 0u, 0u};
    REQUIRE(scenario(0x10u, s60, SECOND, out));
    EXPECT5(out, 61u, 5u, 5u, 0u, 0u);
    /* Seconds 59 carries into minutes 60, which then steps to 61 on the next carry. */
    const uint8_t s59[5] = {59u, 60u, 5u, 0u, 0u};
    REQUIRE(scenario(0x10u, s59, SECOND, out));
    EXPECT5(out, 0u, 61u, 5u, 0u, 0u);
    /* Minutes 63 with a carry steps to 0 and does not carry into hours. */
    const uint8_t m63[5] = {59u, 63u, 23u, 7u, 0u};
    REQUIRE(scenario(0x10u, m63, SECOND, out));
    EXPECT5(out, 0u, 0u, 23u, 7u, 0u);
    /* Hours 31 steps to 0 with no day carry. */
    const uint8_t h31[5] = {59u, 59u, 31u, 7u, 0u};
    REQUIRE(scenario(0x10u, h31, SECOND, out));
    EXPECT5(out, 0u, 0u, 0u, 7u, 0u);
    /* Hours 24 is out of range too: 25 after the carry. */
    const uint8_t h24[5] = {59u, 59u, 24u, 7u, 0u};
    REQUIRE(scenario(0x10u, h24, SECOND, out));
    EXPECT5(out, 0u, 0u, 25u, 7u, 0u);
    /* Exactly 59:59:23 carries into the day. */
    const uint8_t full[5] = {59u, 59u, 23u, 7u, 0u};
    REQUIRE(scenario(0x10u, full, SECOND, out));
    EXPECT5(out, 0u, 0u, 0u, 8u, 0u);
    return 0;
}

static int rtc_day_carry_sticky(void) {
    uint8_t out[5];
    const uint8_t end511[5] = {59u, 59u, 23u, 0xFFu, 0x01u};
    REQUIRE(scenario(0x10u, end511, SECOND, out));
    EXPECT5(out, 0u, 0u, 0u, 0u, 0x80u); /* 511 -> 0 with the carry set */
    REQUIRE(scenario(0x10u, end511, SECOND + 86400u * SECOND, out));
    EXPECT5(out, 0u, 0u, 0u, 1u, 0x80u); /* the carry stays while time continues */

    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 4u, 0x80u);              /* a DH write with bit 7 set keeps the carry */
    latch(m, 0u);
    REQUIRE(rreg(m, 4u) == 0x80u);
    wreg(m, 0u, 4u, 0x00u);              /* a DH write with bit 7 clear clears it */
    latch(m, 0u);
    REQUIRE(rreg(m, 4u) == 0x00u);
    gbb_destroy(m);
    return 0;
}

static int rtc_halt_freezes(void) {
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 4u, 0x40u);
    latch(m, 10u * SECOND);
    uint8_t out[5];
    read_all(m, out);
    EXPECT5(out, 0u, 0u, 0u, 0u, 0x40u);
    REQUIRE(m->cart.rtc_synced_at == 10u * SECOND); /* the anchor still moved */
    wreg(m, 10u * SECOND, 4u, 0x00u);
    latch(m, 11u * SECOND);
    REQUIRE(rreg(m, 0u) == 1u); /* one second after un-halting, not eleven */
    gbb_destroy(m);
    return 0;
}

static int rtc_latch_edges(void) {
    static const struct { uint8_t seq[4]; unsigned n; uint8_t expect; } cases[] = {
        {{0x01u}, 1u, 0u},                    /* 01 alone: previous write is the load value */
        {{0x00u, 0x01u}, 2u, 13u},            /* 00 then 01 latches */
        {{0x00u, 0x00u, 0x01u}, 3u, 13u},     /* latches at the 01 */
        {{0x01u, 0x01u}, 2u, 0u},             /* 01 01 does not */
        {{0x00u, 0x02u, 0x01u}, 3u, 0u},      /* 02 in between breaks the pair */
        {{0x00u, 0x81u}, 2u, 0u},             /* only exactly 01 latches */
    };
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        gbb_instance *m = make(0x10u);
        REQUIRE(m != NULL);
        enable(m);
        wreg(m, 0u, 0u, 10u);
        m->time_half_dots = 3u * SECOND;
        for (unsigned k = 0u; k < cases[i].n; ++k) write8(m, 0x6000u, cases[i].seq[k]);
        REQUIRE(rreg(m, 0u) == cases[i].expect);
        gbb_destroy(m);
    }

    /* Writes while latched leave the latched bytes alone; a lone 01 afterwards does not latch. */
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 10u);
    latch(m, 3u * SECOND);
    REQUIRE(rreg(m, 0u) == 13u);
    wreg(m, 5u * SECOND, 0u, 40u);
    REQUIRE(rreg(m, 0u) == 13u);
    m->time_half_dots = 6u * SECOND;
    write8(m, 0x6000u, 0x01u);
    REQUIRE(rreg(m, 0u) == 13u);

    /* Reset preserves the latched bytes and sets latch_prev to $FF. */
    REQUIRE(gbb_reset(m) == GBB_OK);
    REQUIRE(m->cart.rtc_latch_prev == 0xFFu);
    enable(m); /* reset closes the RAM and RTC gate with the other mapper registers */
    m->time_half_dots = 2u * SECOND;
    write8(m, 0x6000u, 0x01u);
    REQUIRE(rreg(m, 0u) == 13u);
    gbb_destroy(m);
    return 0;
}

static int rtc_generation_rules(void) {
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    REQUIRE(m->battery_generation == 0u);
    wreg(m, 0u, 0u, 5u);
    REQUIRE(m->battery_generation == 1u);
    wreg(m, 0u, 0u, 5u);                       /* identical, no elapsed time */
    REQUIRE(m->battery_generation == 1u);
    wreg(m, 1000u, 0u, 5u);                    /* same value, but sub 1000 is dropped */
    REQUIRE(m->battery_generation == 2u);
    latch(m, 1000u + 3u * SECOND);             /* latch and elapsed ticks never bump */
    REQUIRE(m->battery_generation == 2u);
    wreg(m, 1000u + 3u * SECOND, 1u, 7u);
    REQUIRE(m->battery_generation == 3u);
    wreg(m, 1000u + 3u * SECOND, 1u, 7u);      /* same M value keeps the sub */
    REQUIRE(m->battery_generation == 3u);
    gbb_destroy(m);

    /* A tick that sets the carry flag is elapsed time, not a guest write. */
    m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 59u); wreg(m, 0u, 1u, 59u); wreg(m, 0u, 2u, 23u);
    wreg(m, 0u, 3u, 0xFFu); wreg(m, 0u, 4u, 0x01u);
    const uint64_t before = m->battery_generation;
    latch(m, SECOND);
    REQUIRE(rreg(m, 4u) == 0x80u);
    REQUIRE(m->battery_generation == before);
    gbb_destroy(m);

    /* $13 has a battery but no timer: selection $08 maps nothing and never bumps. */
    m = make(0x13u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 5u);
    REQUIRE(m->battery_generation == 0u);
    write8(m, 0x4000u, 0x00u);
    write8(m, 0xA000u, 0x42u);                 /* ordinary RAM still bumps */
    REQUIRE(m->battery_generation == 1u);
    gbb_destroy(m);

    /* $12 has RAM but no battery and no timer. */
    m = make(0x12u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 5u);
    write8(m, 0x4000u, 0x00u);
    write8(m, 0xA000u, 0x42u);
    REQUIRE(m->battery_generation == 0u);
    gbb_destroy(m);
    return 0;
}

static int rtc_time_near_max(void) {
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    const uint64_t t0 = UINT64_MAX - 3u * SECOND - 5u;
    wreg(m, t0, 0u, 0u);
    latch(m, UINT64_MAX);
    REQUIRE(rreg(m, 0u) == 3u);

    /* A clock anchored at 0 and read at UINT64_MAX credits floor(2^64 / 2^23) - 1 seconds. */
    gbb_destroy(m);
    m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    m->time_half_dots = UINT64_MAX;
    rtc_sync(&m->cart, m->time_half_dots);
    cart_state expect;
    memset(&expect, 0, sizeof(expect));
    rtc_add_seconds(&expect, (UINT64_MAX >> 23));
    REQUIRE(same_clock(&expect, &m->cart));
    REQUIRE(m->cart.rtc_sub == (uint32_t)(SECOND - 1u));

    /* A timestamp behind the anchor credits nothing and does not wrap. */
    const cart_state frozen = m->cart;
    rtc_sync(&m->cart, 5u);
    REQUIRE(same_clock(&frozen, &m->cart));
    REQUIRE(m->cart.rtc_synced_at == 5u);
    gbb_destroy(m);
    return 0;
}

static int rtc_reset_rebase(void) {
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 0u);
    const uint64_t n = 3u * SECOND + (SECOND >> 1);
    gbb_run_result run = gbb_run(m, n, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    const uint64_t tn = m->time_half_dots;
    REQUIRE(tn > 3u * SECOND && tn <= n);
    latch(m, tn);
    REQUIRE(rreg(m, 0u) == 3u);

    REQUIRE(gbb_reset(m) == GBB_OK);
    REQUIRE(m->time_half_dots == 0u);
    REQUIRE(m->cart.rtc_synced_at == 0u);
    REQUIRE(m->cart.rtc_latch_prev == 0xFFu);
    enable(m); /* reset closes the RAM and RTC gate with the other mapper registers */
    REQUIRE(rreg(m, 0u) == 3u);                 /* the latched byte survives */
    REQUIRE(m->cart.rtc_sub == (uint32_t)(tn & (SECOND - 1u)));

    run = gbb_run(m, 2u * SECOND, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    const uint64_t tm = m->time_half_dots;
    latch(m, tm);
    const uint64_t total = tn + tm;             /* time before and after the reset adds up */
    REQUIRE(rreg(m, 0u) == (uint8_t)(total >> 23));
    REQUIRE(m->cart.rtc_sub == (uint32_t)(total & (SECOND - 1u)));
    gbb_destroy(m);
    return 0;
}

/* ---- metamorphic: time is the only input ---------------------------------- */

/* Run until the machine's time is within a few half-dots of `target`; whole
 * instructions never straddle the budget, so the machine stops just short. */
static int drive(gbb_instance *m, uint64_t target, uint64_t slice_cap, int random_slices) {
    while (m->time_half_dots + 64u <= target) {
        uint64_t slice = random_slices ? 64u + rng() % slice_cap : slice_cap;
        const uint64_t left = target - m->time_half_dots;
        if (slice > left) slice = left;
        const gbb_run_result r = gbb_run(m, slice, NULL, 0u);
        if (r.reason != GBB_STOP_BUDGET && r.reason != GBB_STOP_STOPPED &&
            r.reason != GBB_STOP_HALTED_IDLE && r.reason != GBB_STOP_NO_PROGRESS)
            return 0;
        if (r.consumed_half_dots == 0u && r.reason != GBB_STOP_BUDGET) return 0;
    }
    return 1;
}

static void final_sync(gbb_instance *m, uint64_t target, cart_state *out) {
    rtc_sync(&m->cart, target);
    *out = m->cart;
}

static int rtc_slice_invariance(void) {
    const uint64_t target = 2u * SECOND + 12345u;
    cart_state whole, sliced, tiny;
    gbb_instance *m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 58u);
    REQUIRE(drive(m, target, target, 0));
    final_sync(m, target, &whole);
    gbb_destroy(m);

    const uint64_t caps[] = {64u, 4096u, 100000u, 3u * SECOND};
    for (size_t i = 0u; i < sizeof(caps) / sizeof(caps[0]); ++i) {
        m = make(0x10u);
        REQUIRE(m != NULL);
        enable(m);
        wreg(m, 0u, 0u, 58u);
        REQUIRE(drive(m, target, caps[i], i % 2u));
        final_sync(m, target, &sliced);
        REQUIRE(same_clock(&whole, &sliced));
        REQUIRE(whole.rtc_sub == sliced.rtc_sub);
        gbb_destroy(m);
    }
    /* Fixed small slices of 64 half-dots, the finest a whole instruction fits in. */
    m = make(0x10u);
    REQUIRE(m != NULL);
    enable(m);
    wreg(m, 0u, 0u, 58u);
    REQUIRE(drive(m, SECOND, 64u, 0));
    final_sync(m, target, &tiny);
    REQUIRE(same_clock(&whole, &tiny));
    gbb_destroy(m);
    return 0;
}

static gbb_instance *make_variant(int variant) {
    gbb_instance *m = make(0x10u);
    if (m == NULL) return NULL;
    /* Replace the busy loop at $200: 0 = JR -2, 1 = HALT, 2 = STOP then JR -2. */
    static uint8_t rom[0x8000];
    memset(rom, 0, sizeof(rom));
    rom[0x147u] = 0x10u; rom[0x149u] = 0x02u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x00u; rom[0x102u] = 0x02u;
    if (variant == 0) { rom[0x200u] = 0x18u; rom[0x201u] = 0xFEu; }
    if (variant == 1) { rom[0x200u] = 0x76u; }
    if (variant == 2) { rom[0x200u] = 0x10u; rom[0x201u] = 0x00u; rom[0x202u] = 0x18u; rom[0x203u] = 0xFEu; }
    if (gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) { gbb_destroy(m); return NULL; }
    return m;
}

static int rtc_cpu_independence(void) {
    const uint64_t target = 2u * SECOND + 777u;
    cart_state result[3];
    for (int variant = 0; variant < 3; ++variant) {
        gbb_instance *m = make_variant(variant);
        REQUIRE(m != NULL);
        enable(m);
        wreg(m, 0u, 0u, 58u);
        wreg(m, 0u, 1u, 59u);
        wreg(m, 0u, 2u, 23u);
        wreg(m, 0u, 3u, 0xFFu);
        wreg(m, 0u, 4u, 0x01u);
        if (variant == 2) {
            const gbb_input_event wake = {SECOND, GBB_INPUT_STOP_WAKE, 1u};
            REQUIRE(gbb_queue_events(m, &wake, 1u) == GBB_OK);
        }
        REQUIRE(drive(m, target, 1u << 20, 0));
        REQUIRE(m->time_half_dots + 64u > target || variant == 1);
        final_sync(m, target, &result[variant]);
        gbb_destroy(m);
    }
    REQUIRE(same_clock(&result[0], &result[1]) && result[0].rtc_sub == result[1].rtc_sub);
    REQUIRE(same_clock(&result[0], &result[2]) && result[0].rtc_sub == result[2].rtc_sub);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    static const struct { const char *name; int (*run)(void); } table[] = {
        {"rtc_closed_form_differential", rtc_closed_form_differential},
        {"rtc_add_composes", rtc_add_composes},
        {"rtc_rate_exact", rtc_rate_exact},
        {"rtc_prescaler_rules", rtc_prescaler_rules},
        {"rtc_write_masks", rtc_write_masks},
        {"rtc_out_of_range_rollover", rtc_out_of_range_rollover},
        {"rtc_day_carry_sticky", rtc_day_carry_sticky},
        {"rtc_halt_freezes", rtc_halt_freezes},
        {"rtc_latch_edges", rtc_latch_edges},
        {"rtc_generation_rules", rtc_generation_rules},
        {"rtc_time_near_max", rtc_time_near_max},
        {"rtc_reset_rebase", rtc_reset_rebase},
        {"rtc_slice_invariance", rtc_slice_invariance},
        {"rtc_cpu_independence", rtc_cpu_independence},
    };
    for (size_t i = 0u; i < sizeof(table) / sizeof(table[0]); ++i)
        if (strcmp(argv[1], table[i].name) == 0) return table[i].run();
    return 2;
}
