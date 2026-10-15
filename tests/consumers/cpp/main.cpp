#include <gabbaboy/gabbaboy.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

static int battery_api_smoke() {
    constexpr size_t rom_bytes = 32768u;
    constexpr size_t ram_bytes = 8192u;
    uint8_t rom[rom_bytes]{};
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = static_cast<uint8_t>(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;

    gbb_instance *machine = nullptr;
    uint8_t input[ram_bytes]{};
    uint8_t output[ram_bytes + 2u]{};
    size_t size = 0u;
    uint64_t generation = 0u;
    bool passed = false;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) goto done;
    if (gbb_battery_size(machine, &size) != GBB_OK || size != ram_bytes) goto done;
    std::memset(output, 0xA7, sizeof(output));
    if (gbb_copy_battery(machine, output + 1u, ram_bytes - 1u) !=
        GBB_BUFFER_TOO_SMALL) goto done;
    for (size_t i = 0u; i < sizeof(output); ++i)
        if (output[i] != 0xA7u) goto done;
    if (gbb_copy_battery(machine, output + 1u, ram_bytes) != GBB_OK) goto done;
    for (size_t i = 0u; i < ram_bytes; ++i)
        if (output[i + 1u] != 0xFFu) goto done;
    if (output[0] != 0xA7u || output[sizeof(output) - 1u] != 0xA7u) goto done;

    for (size_t i = 0u; i < ram_bytes; ++i)
        input[i] = static_cast<uint8_t>(i * 37u + 0x31u);
    if (gbb_import_battery(machine, input, sizeof(input)) != GBB_OK) goto done;
    if (gbb_battery_generation(machine, &generation) != GBB_OK || generation != 1u)
        goto done;
    if (gbb_import_battery(machine, input, sizeof(input) - 1u) !=
        GBB_BATTERY_SIZE_MISMATCH) goto done;
    std::memset(output, 0x5C, sizeof(output));
    if (gbb_copy_battery(machine, output + 1u, ram_bytes) != GBB_OK ||
        std::memcmp(output + 1u, input, sizeof(input)) != 0 ||
        output[0] != 0x5Cu || output[sizeof(output) - 1u] != 0x5Cu ||
        gbb_battery_generation(machine, &generation) != GBB_OK || generation != 1u)
        goto done;
    /* The installed header and library export gbb_rumble_state; a non-rumble
     * cartridge reports GBB_NO_RUMBLE and leaves the outputs alone. */
    {
        uint8_t rumble_on = 0xA5u;
        uint64_t rumble_changes = UINT64_C(0x1122334455667788);
        if (gbb_rumble_state(machine, &rumble_on, &rumble_changes) != GBB_NO_RUMBLE ||
            rumble_on != 0xA5u || rumble_changes != UINT64_C(0x1122334455667788))
            goto done;
    }
    passed = true;

done:
    gbb_destroy(machine);
    return passed ? 0 : 1;
}

// FNV-1a over little-endian left then right words, matching tests/test_audio.c.
static uint64_t fnv1a_frames(const gbb_audio_frame *frames, size_t count) {
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0u; i < count; ++i) {
        const uint16_t values[2] = {static_cast<uint16_t>(frames[i].left),
                                    static_cast<uint16_t>(frames[i].right)};
        for (unsigned channel = 0u; channel < 2u; ++channel) {
            hash ^= static_cast<uint8_t>(values[channel]);
            hash *= UINT64_C(1099511628211);
            hash ^= static_cast<uint8_t>(values[channel] >> 8);
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

/* Installed-package RTC smoke: MBC3+TIMER+RAM+BATTERY ($10) synthetic ROM,
 * explicit host catch-up, block layout and a byte-identical import round trip. */
static void rtc_fill_rom(uint8_t *rom, size_t size, uint8_t cart_type) {
    std::memset(rom, 0, size);
    rom[0x100u] = 0xC3u; /* JP $0150 */
    rom[0x101u] = 0x50u;
    rom[0x102u] = 0x01u;
    rom[0x150u] = 0x76u; /* HALT */
    rom[0x151u] = 0x18u; /* JR -3 */
    rom[0x152u] = 0xFDu;
    rom[0x147u] = cart_type;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    uint8_t checksum = 0u;
    for (std::size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = static_cast<uint8_t>(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static int rtc_api_smoke() {
    enum { ROM_BYTES = 32768, RAM_BYTES = 8192, IMAGE_BYTES = RAM_BYTES + static_cast<int>(GBB_RTC_BLOCK_SIZE) };
    static uint8_t rom[ROM_BYTES];
    uint8_t first[IMAGE_BYTES];
    uint8_t second[IMAGE_BYTES];
    gbb_instance *machine = nullptr;
    gbb_instance *twin = nullptr;
    gbb_instance *plain = nullptr;
    std::size_t size = 0u;
    int passed = 0;

    rtc_fill_rom(rom, sizeof(rom), 0x10u);
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &twin) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK ||
        gbb_load_rom(twin, rom, sizeof(rom)) != GBB_OK) goto done;
    if (gbb_battery_size(machine, &size) != GBB_OK || size != IMAGE_BYTES) goto done;
    if (gbb_rtc_catch_up(machine, 3661) != GBB_OK) goto done;
    if (gbb_copy_battery(machine, first, sizeof(first)) != GBB_OK) goto done;
    if (first[RAM_BYTES] != 0x47u || first[RAM_BYTES + 1u] != 0x42u || /* "GB" */
        first[RAM_BYTES + 2u] != 0x52u || first[RAM_BYTES + 3u] != 0x54u) /* "RT" */
        goto done;
    if (first[RAM_BYTES + 9u] != 1u || first[RAM_BYTES + 10u] != 1u ||
        first[RAM_BYTES + 11u] != 1u) goto done;
    /* Import never catches up: the twin exports exactly the imported bytes. */
    if (gbb_import_battery(twin, first, sizeof(first)) != GBB_OK ||
        gbb_copy_battery(twin, second, sizeof(second)) != GBB_OK ||
        std::memcmp(first, second, sizeof(first)) != 0) goto done;
    if (gbb_rtc_catch_up(machine, -1) != GBB_INVALID_ARGUMENT) goto done;
    if (gbb_rtc_catch_up(nullptr, 1) != GBB_INVALID_ARGUMENT) goto done;

    rtc_fill_rom(rom, sizeof(rom), 0x03u); /* MBC1+RAM+BATTERY: no timer */
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &plain) != GBB_OK ||
        gbb_load_rom(plain, rom, sizeof(rom)) != GBB_OK ||
        gbb_rtc_catch_up(plain, 1) != GBB_NO_RTC) goto done;
    passed = 1;

done:
    gbb_destroy(plain);
    gbb_destroy(twin);
    gbb_destroy(machine);
    return passed ? 0 : 1;
}

// Structural PCM smoke through the installed public header and library only.
// Every assertion is a bound, a formula from header constants, or a comparison
// within this process; no emulator-derived digest or count is pinned.
static int audio_api_smoke() {
    constexpr size_t rom_bytes = 32768u;
    constexpr size_t capacity = 804u;
    // Square-wave tracer: NR12 envelope, NR11 duty, NR13 period low, NR14 trigger, then JR -2.
    static const uint8_t program[] = {
        0x3Eu, 0xF0u, 0xEAu, 0x12u, 0xFFu,
        0x3Eu, 0x80u, 0xEAu, 0x11u, 0xFFu,
        0x3Eu, 0xF0u, 0xEAu, 0x13u, 0xFFu,
        0x3Eu, 0x87u, 0xEAu, 0x14u, 0xFFu,
        0x18u, 0xFEu
    };
    uint8_t rom[rom_bytes]{};
    std::memcpy(rom + 0x100u, program, sizeof(program));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = static_cast<uint8_t>(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;

    // 48000 Hz output over the 8388608 half-dot/s clock: one frame budget of
    // 140448 half-dots yields 803 PCM frames.
    const uint64_t budget = UINT64_C(140448);
    const size_t expected = static_cast<size_t>((budget * UINT64_C(48000)) / UINT64_C(8388608));
    const int16_t poison = static_cast<int16_t>(0x7A5A);
    gbb_audio_frame frames[capacity + 2u]{};
    gbb_audio_frame twin_frames[capacity + 2u]{};
    gbb_instance *machine = nullptr;
    gbb_instance *twin = nullptr;
    gbb_instance *probe = nullptr;
    size_t count = 0u;
    size_t twin_count = 0u;
    unsigned high_samples = 0u;
    unsigned transitions = 0u;
    uint64_t first_hash = 0u;
    gbb_run_result result{};
    gbb_run_result twin_result{};
    bool passed = false;

    for (size_t i = 0u; i < capacity + 2u; ++i) {
        frames[i].left = frames[i].right = poison;
        twin_frames[i].left = twin_frames[i].right = poison;
    }
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &twin) != GBB_OK ||
        gbb_load_rom(twin, rom, sizeof(rom)) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &probe) != GBB_OK ||
        gbb_load_rom(probe, rom, sizeof(rom)) != GBB_OK) goto done;

    // (1) exact budget and formula frame count
    result = gbb_run_audio(machine, budget, frames, capacity, &count);
    if (!(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == budget &&
          count == expected)) goto done;
    // (2) activity bounds
    for (size_t i = 0u; i < count; ++i) {
        if (frames[i].left != frames[i].right) goto done;
        if (frames[i].left != 0) ++high_samples;
        if (i != 0u && frames[i].left != frames[i - 1u].left) ++transitions;
    }
    if (!(high_samples > 100u && high_samples < count && transitions > 20u)) goto done;
    // (3) poison past n, including the two guard frames beyond capacity
    for (size_t i = count; i < capacity + 2u; ++i)
        if (frames[i].left != poison || frames[i].right != poison) goto done;
    // (4) a second fresh instance matches
    twin_result = gbb_run_audio(twin, budget, twin_frames, capacity, &twin_count);
    if (!(twin_result.reason == result.reason &&
          twin_result.consumed_half_dots == result.consumed_half_dots &&
          twin_count == count)) goto done;
    first_hash = fnv1a_frames(frames, count);
    if (fnv1a_frames(twin_frames, twin_count) != first_hash) goto done;
    // (5) reset clears APU state, so a re-run reproduces the fresh-instance hash
    if (gbb_reset(machine) != GBB_OK) goto done;
    for (size_t i = 0u; i < capacity + 2u; ++i)
        twin_frames[i].left = twin_frames[i].right = poison;
    twin_count = 0u;
    twin_result = gbb_run_audio(machine, budget, twin_frames, capacity, &twin_count);
    if (!(twin_result.reason == result.reason &&
          twin_result.consumed_half_dots == result.consumed_half_dots &&
          twin_count == count && fnv1a_frames(twin_frames, twin_count) == first_hash)) goto done;
    // (6) NULL frames with zero capacity stops before consuming the budget
    count = 1u;
    result = gbb_run_audio(probe, budget, nullptr, 0u, &count);
    if (!(result.reason == GBB_STOP_OUTPUT_FULL && count == 0u &&
          result.consumed_half_dots < budget)) goto done;
    // (7) header-defined invalid shapes
    count = 1u;
    result = gbb_run_audio(probe, budget, nullptr, 1u, &count);
    if (!(result.reason == GBB_STOP_INVALID_STATE && count == 0u)) goto done;
    result = gbb_run_audio(probe, budget, frames, capacity, nullptr);
    if (result.reason != GBB_STOP_INVALID_STATE) goto done;
    count = 1u;
    result = gbb_run_audio(nullptr, budget, frames, capacity, &count);
    if (!(result.reason == GBB_STOP_INVALID_STATE && count == 0u)) goto done;
    passed = true;

done:
    gbb_destroy(machine);
    gbb_destroy(twin);
    gbb_destroy(probe);
    return passed ? 0 : 1;
}

/* Installed-package CGB profile smoke: create, probe, info and the PGB/frame refusals. */
static int cgb_api_smoke() {
    constexpr size_t ROM_BYTES = 32768u;
    uint8_t rom[ROM_BYTES]{};
    rom[0x143u] = 0xC0u;
    rom[0x147u] = 0x00u;
    {
        uint8_t checksum = 0u;
        for (size_t i = 0x134u; i <= 0x14Cu; ++i)
            checksum = (uint8_t)(checksum - rom[i] - 1u);
        rom[0x14Du] = checksum;
    }

    gbb_instance *machine = NULL;
    gbb_info info;
    int passed = 0;
    /* $C0 on the DMG profile: informational flag, DMG mode. */
    std::memset(&info, 0xA7, sizeof(info));
    info.struct_size = sizeof(gbb_info);
    if (gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, rom, sizeof(rom), &info) != GBB_OK ||
        info.mode != GBB_MODE_DMG || (info.flags & GBB_INFO_CGB_ONLY_ON_DMG) == 0u ||
        info.struct_size != GBB_INFO_SIZE_V1) goto done;
    /* The CGB profile creates, loads and reports CGB mode. */
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) goto done;
    std::memset(&info, 0xA7, sizeof(info));
    info.struct_size = sizeof(gbb_info);
    if (gbb_get_info(machine, &info) != GBB_OK || info.mode != GBB_MODE_CGB ||
        info.profile != 2u || info.struct_size != GBB_INFO_SIZE_V1 ||
        info.cgb_support != GBB_CGB_SUPPORT_ONLY) goto done;
    /* A zero struct_size is rejected and leaves every other byte alone. */
    {
        gbb_info zero;
        uint8_t raw[sizeof(gbb_info)];
        std::memset(&zero, 0xA7, sizeof(zero));
        zero.struct_size = 0u;
        std::memcpy(raw, &zero, sizeof(raw));
        if (gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, rom, sizeof(rom), &zero) != GBB_INVALID_ARGUMENT ||
            std::memcmp(raw, &zero, sizeof(raw)) != 0)
            goto done;
    }
    /* A PGB-flagged image is refused by the CGB profile on both probe and load. */
    rom[0x143u] = 0x84u;
    {
        uint8_t checksum = 0u;
        for (size_t i = 0x134u; i <= 0x14Cu; ++i)
            checksum = (uint8_t)(checksum - rom[i] - 1u);
        rom[0x14Du] = checksum;
    }
    std::memset(&info, 0xA7, sizeof(info));
    info.struct_size = sizeof(gbb_info);
    if (gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, rom, sizeof(rom), &info) !=
            GBB_UNSUPPORTED_EXECUTION_MODE ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_UNSUPPORTED_EXECUTION_MODE) goto done;
    /* The shade call is refused on the CGB profile; colour is read with the RGB555 call. */
    {
        uint8_t pixels[160u * 144u];
        gbb_frame_info frame;
        if (gbb_copy_frame(machine, pixels, sizeof(pixels), 160u, &frame) !=
            GBB_UNSUPPORTED_PROFILE) goto done;
    }
    {
        static uint16_t rgb[160u * 144u];
        gbb_frame_info frame;
        gbb_instance *dmg = nullptr;
        gbb_compat_palette palette;
        gbb_compat_palette override_palette;
        int colour_ok = 0;
        /* The refused PGB load left the earlier CGB image in place; run two frames of it. */
        for (int i = 0; i < 2; ++i) gbb_run(machine, UINT64_C(140448), NULL, 0);
        if (gbb_copy_frame_rgb555(machine, rgb, sizeof(rgb), 320u, &frame) != GBB_OK ||
            frame.width != 160u || frame.height != 144u || frame.generation == 0u) goto colour_done;
        for (size_t i = 0; i < 160u * 144u; ++i)
            if (rgb[i] > 0x7FFFu) goto colour_done;
        std::memset(rgb, 0xA7, sizeof(rgb));
        if (gbb_copy_frame_rgb555(machine, rgb, sizeof(rgb), 319u, &frame) != GBB_INVALID_ARGUMENT ||
            ((const uint8_t *)rgb)[0] != 0xA7u) goto colour_done;
        if (gbb_create(GBB_PROFILE_DMG_CPU_B, &dmg) != GBB_OK ||
            gbb_copy_frame_rgb555(dmg, rgb, sizeof(rgb), 320u, &frame) != GBB_UNSUPPORTED_PROFILE)
            goto colour_done;
        std::memset(&palette, 0, sizeof(palette));
        palette.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
        if (gbb_get_compat_palette(machine, &palette) != GBB_OK ||
            palette.struct_size != GBB_COMPAT_PALETTE_SIZE_V1) goto colour_done;
        override_palette = palette;
        override_palette.bg[0] = 0x1234u;
        if (gbb_set_compat_palette(machine, &override_palette) != GBB_OK) goto colour_done;
        override_palette.bg[1] = 0x8000u;
        if (gbb_set_compat_palette(machine, &override_palette) != GBB_INVALID_ARGUMENT) goto colour_done;
        if (gbb_get_compat_palette(machine, &palette) != GBB_OK || palette.bg[0] != 0x1234u ||
            palette.bg[1] == 0x8000u) goto colour_done;
        if (gbb_set_compat_palette(machine, NULL) != GBB_OK) goto colour_done;
        colour_ok = 1;
colour_done:
        gbb_destroy(dmg);
        if (!colour_ok) goto done;
    }
    passed = 1;

done:
    gbb_destroy(machine);
    return passed ? 0 : 1;
}

// Build a self-contained, ROM-only CGB guest for the installed public API.
static void cgb_speed_fill_rom(uint8_t *rom, size_t size, uint8_t key1_value) {
    std::memset(rom, 0, size);
    rom[0x100u] = 0xC3u; // JP $0150
    rom[0x101u] = 0x50u;
    rom[0x102u] = 0x01u;
    rom[0x143u] = 0xC0u; // CGB-only
    rom[0x147u] = 0x00u; // ROM-only cartridge
    rom[0x148u] = 0x00u; // 32 KiB ROM
    rom[0x149u] = 0x00u; // no external RAM
    rom[0x150u] = 0x3Eu; // LD A,$55: mark execution before STOP.
    rom[0x151u] = 0x55u;
    rom[0x152u] = 0xEAu; // LD ($C000),A
    rom[0x153u] = 0x00u;
    rom[0x154u] = 0xC0u;
    rom[0x155u] = 0x3Eu; // LD A,key1_value
    rom[0x156u] = key1_value;
    rom[0x157u] = 0xE0u; // LDH ($4D),A: arm only in the positive guest.
    rom[0x158u] = 0x4Du;
    rom[0x159u] = 0x10u; // STOP $00
    rom[0x15Au] = 0x00u;
    rom[0x15Bu] = 0xF0u; // LDH A,($4D): read KEY1 after the switch.
    rom[0x15Cu] = 0x4Du;
    rom[0x15Du] = 0xEAu; // LD ($C000),A
    rom[0x15Eu] = 0x00u;
    rom[0x15Fu] = 0xC0u;
    rom[0x160u] = 0x76u; // HALT
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = static_cast<uint8_t>(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

// Returns true only when an armed switch reaches HALT through partitioned public runs.
static int cgb_speed_partition_smoke(uint8_t key1_value, int *out_unarmed_rejected) {
    constexpr uint64_t slice_half_dots = 4096u;
    constexpr uint64_t frame_half_dots = 140448u;
    constexpr size_t rom_bytes = 32768u;
    const uint64_t cap_half_dots = 2u * frame_half_dots;
    uint8_t rom[rom_bytes]{};
    static uint16_t pixels[160u * 144u];
    gbb_instance *machine = nullptr;
    gbb_run_result result{};
    gbb_frame_info frame{};
    gbb_error frame_error = GBB_FRAME_NOT_READY;
    uint64_t consumed_total = 0u;
    uint64_t full_slice_total = 0u;
    uint64_t halt_partial_half_dots = 0u;
    unsigned calls = 0u;
    int halted = 0;
    int frame_ready = 0;
    int passed = 0;
    if (out_unarmed_rejected != nullptr) *out_unarmed_rejected = 0;
    cgb_speed_fill_rom(rom, sizeof(rom), key1_value);
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) goto done;

    result = gbb_run(machine, slice_half_dots, nullptr, 0u);
    ++calls;
    consumed_total += result.consumed_half_dots;
    if (result.reason == GBB_STOP_STOPPED) {
        if (key1_value == 0u && result.consumed_half_dots > 0u &&
            result.consumed_half_dots <= slice_half_dots &&
            gbb_peek_ram(machine, 0xC000u) == 0x55u &&
            (gbb_peek_ram(machine, 0xC000u) & 0x80u) == 0u &&
            out_unarmed_rejected != nullptr)
            *out_unarmed_rejected = 1;
        goto done;
    }
    if (key1_value == 0u || result.reason != GBB_STOP_BUDGET ||
        result.consumed_half_dots != slice_half_dots ||
        gbb_peek_ram(machine, 0xC000u) != 0x55u) goto done;
    full_slice_total += slice_half_dots;

    for (; calls < 69u; ++calls) {
        result = gbb_run(machine, slice_half_dots, nullptr, 0u);
        consumed_total += result.consumed_half_dots;
        if (result.reason == GBB_STOP_HALTED_IDLE && !halted) halted = 1;
        if (result.reason == GBB_STOP_STOPPED && key1_value == 0u &&
            result.consumed_half_dots > 0u &&
            gbb_peek_ram(machine, 0xC000u) == 0x55u &&
            (gbb_peek_ram(machine, 0xC000u) & 0x80u) == 0u &&
            out_unarmed_rejected != nullptr) {
            *out_unarmed_rejected = 1;
            goto done;
        }
        if ((!halted && result.reason != GBB_STOP_BUDGET) ||
            (halted && result.reason != GBB_STOP_HALTED_IDLE) ||
            result.consumed_half_dots == 0u ||
            result.consumed_half_dots > slice_half_dots) goto done;
        if (result.consumed_half_dots == slice_half_dots)
            full_slice_total += slice_half_dots;
        else if (halted)
            halt_partial_half_dots = result.consumed_half_dots;
        if (consumed_total > cap_half_dots) goto done;
        frame_error = gbb_copy_frame_rgb555(machine, pixels, sizeof(pixels), 320u, &frame);
        if (frame_error == GBB_OK) frame_ready = 1;
        else if (frame_error != GBB_FRAME_NOT_READY) goto done;
        if (halted && frame_ready) break;
    }
    if (!halted || !frame_ready ||
        consumed_total != full_slice_total + halt_partial_half_dots ||
        consumed_total > cap_half_dots ||
        (gbb_peek_ram(machine, 0xC000u) & 0x80u) == 0u ||
        frame.width != 160u || frame.height != 144u || frame.generation == 0u ||
        frame.completion_half_dots > consumed_total)
        goto done;
    passed = 1;

done:
    gbb_destroy(machine);
    return passed;
}

// Execute a small original guest through the installed C API. The ROM is its
// own GDMA source; the guest copies VRAM back to WRAM for public observation.
static int cgb_dma_partition_smoke(int double_speed, int transfer_enabled,
                                   int *out_data_match, int *out_status_match,
                                   int *out_timing_match) {
    constexpr size_t rom_bytes = 32768u;
    constexpr uint64_t slice_half_dots = 257u;
    constexpr size_t dma_bytes = 128u;
    constexpr unsigned max_partitions = 600u;
    uint8_t rom[rom_bytes]{};
    gbb_instance *machine = nullptr;
    uint64_t consumed = 0u;
    unsigned calls = 0u;
    int data_match = 1;
    int status_match = 0;
    int timing_match = 0;
    int passed = 0;
    int first_bad_byte = -1;
    int failure = 0;
    gbb_stop_reason last_reason = GBB_STOP_BUDGET;
    size_t pc = 0x150u;
    static const uint8_t normal_prefix[] = {
        0xAFu, 0xE0u, 0x04u,
        0x3Eu, 0x02u, 0xE0u, 0x51u,
        0xAFu, 0xE0u, 0x52u, 0xAFu, 0xE0u, 0x53u,
        0xAFu, 0xE0u, 0x54u,
        0xF0u, 0x4Du, 0xEAu, 0x04u, 0xC1u
    };
    static const uint8_t double_speed_prefix[] = {
        0x3Eu, 0x01u, 0xE0u, 0x4Du, 0x10u, 0x00u,
        0xAFu, 0xE0u, 0x04u,
        0x3Eu, 0x02u, 0xE0u, 0x51u,
        0xAFu, 0xE0u, 0x52u, 0xAFu, 0xE0u, 0x53u,
        0xAFu, 0xE0u, 0x54u,
        0xF0u, 0x4Du, 0xEAu, 0x04u, 0xC1u
    };
    const uint8_t *prefix = double_speed ? double_speed_prefix : normal_prefix;
    const size_t prefix_size = double_speed ? sizeof(double_speed_prefix)
                                            : sizeof(normal_prefix);
    if (out_data_match != nullptr) *out_data_match = 0;
    if (out_status_match != nullptr) *out_status_match = 0;
    if (out_timing_match != nullptr) *out_timing_match = 0;
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    rom[0x143u] = 0xC0u; rom[0x147u] = 0x00u;
    rom[0x148u] = 0x00u; rom[0x149u] = 0x00u;
    std::memcpy(rom + pc, prefix, prefix_size);
    pc += prefix_size;
    rom[pc++] = 0xF0u; rom[pc++] = 0x41u;
    rom[pc++] = 0xE6u; rom[pc++] = 0x03u;
    rom[pc++] = 0xFEu; rom[pc++] = 0x03u;
    rom[pc++] = 0x20u; rom[pc++] = 0xF8u;
    rom[pc++] = 0xF0u; rom[pc++] = 0x04u;
    rom[pc++] = 0xEAu; rom[pc++] = 0x00u; rom[pc++] = 0xC1u;
    if (transfer_enabled) {
        rom[pc++] = 0x3Eu; rom[pc++] = 0x07u;
        rom[pc++] = 0xE0u; rom[pc++] = 0x55u;
    }
    rom[pc++] = 0xF0u; rom[pc++] = 0x04u;
    rom[pc++] = 0xEAu; rom[pc++] = 0x01u; rom[pc++] = 0xC1u;
    rom[pc++] = 0xF0u; rom[pc++] = 0x55u;
    rom[pc++] = 0xEAu; rom[pc++] = 0x02u; rom[pc++] = 0xC1u;
    rom[pc++] = 0xAFu; rom[pc++] = 0xE0u; rom[pc++] = 0x40u;
    rom[pc++] = 0x21u; rom[pc++] = 0x00u; rom[pc++] = 0x80u;
    rom[pc++] = 0x11u; rom[pc++] = 0x00u; rom[pc++] = 0xC2u;
    rom[pc++] = 0x06u; rom[pc++] = static_cast<uint8_t>(dma_bytes);
    rom[pc++] = 0x2Au; rom[pc++] = 0x12u; rom[pc++] = 0x13u; rom[pc++] = 0x05u;
    rom[pc++] = 0x20u; rom[pc++] = 0xFAu;
    rom[pc++] = 0x3Eu; rom[pc++] = 0xA5u;
    rom[pc++] = 0xEAu; rom[pc++] = 0x03u; rom[pc++] = 0xC1u;
    rom[pc++] = 0x76u;
    for (size_t i = 0u; i < dma_bytes; ++i)
        rom[0x0200u + i] = static_cast<uint8_t>(i ^ 0x5Au);
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = static_cast<uint8_t>(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) { failure = 1; goto done; }
    while (gbb_peek_ram(machine, 0xC103u) != 0xA5u && calls < max_partitions) {
        const gbb_run_result result = gbb_run(machine, slice_half_dots, nullptr, 0u);
        ++calls;
        last_reason = result.reason;
        if (result.consumed_half_dots == 0u ||
            result.consumed_half_dots > slice_half_dots ||
            (result.reason != GBB_STOP_BUDGET && result.reason != GBB_STOP_HALTED_IDLE)) {
            failure = 2; goto done;
        }
        consumed += result.consumed_half_dots;
        if (consumed > static_cast<uint64_t>(max_partitions) * slice_half_dots) { failure = 3; goto done; }
    }
    if (gbb_peek_ram(machine, 0xC103u) != 0xA5u || calls < 2u) { failure = 4; goto done; }
    status_match = gbb_peek_ram(machine, 0xC102u) == 0xFFu;
    timing_match = static_cast<uint8_t>(gbb_peek_ram(machine, 0xC101u) -
                                        gbb_peek_ram(machine, 0xC100u)) > 0u;
    if ((gbb_peek_ram(machine, 0xC104u) & 0x80u) != (double_speed ? 0x80u : 0u))
        { failure = 5; goto done; }
    for (size_t i = 0u; i < dma_bytes; ++i) {
        if (gbb_peek_ram(machine, static_cast<uint16_t>(0xC200u + i)) !=
            static_cast<uint8_t>(i ^ 0x5Au)) {
            data_match = 0;
            first_bad_byte = static_cast<int>(i);
            break;
        }
    }
    if (out_data_match != nullptr) *out_data_match = data_match;
    if (out_status_match != nullptr) *out_status_match = status_match;
    if (out_timing_match != nullptr) *out_timing_match = timing_match;
    if (!transfer_enabled)
        std::fprintf(stderr, "C++ consumer DMA disabled twin diagnosed: data=%d first_bad=%d status=%d timing=%d ff55=%02X calls=%u consumed=%llu\n",
                     data_match, first_bad_byte, status_match, timing_match, gbb_peek_ram(machine, 0xC102u),
                     calls, static_cast<unsigned long long>(consumed));
    passed = transfer_enabled ? data_match && status_match && timing_match
                              : !data_match && !timing_match;
done:
    if (!passed && transfer_enabled)
        std::fprintf(stderr, "C++ consumer DMA guest failed: check=%d stop=%d marker=%02X ff55=%02X key1=%02X calls=%u consumed=%llu\n",
                     failure, static_cast<int>(last_reason),
                     machine != nullptr ? gbb_peek_ram(machine, 0xC103u) : 0u,
                     machine != nullptr ? gbb_peek_ram(machine, 0xC102u) : 0u,
                     machine != nullptr ? gbb_peek_ram(machine, 0xC104u) : 0u,
                     calls, static_cast<unsigned long long>(consumed));
    gbb_destroy(machine);
    return passed;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *file = std::fopen(argv[1], "rb");
    if (file == nullptr || std::fseek(file, 0, SEEK_END) != 0) return 2;
    long length = std::ftell(file);
    if (length <= 0 || std::fseek(file, 0, SEEK_SET) != 0) return 2;
    auto *rom = static_cast<uint8_t *>(std::malloc(static_cast<size_t>(length)));
    if (rom == nullptr || std::fread(rom, 1, static_cast<size_t>(length), file) != static_cast<size_t>(length)) return 2;
    std::fclose(file);

    gbb_instance *machine = nullptr;
    gbb_error error = gbb_create(GBB_PROFILE_DMG_CPU_B, &machine);
    if (error == GBB_OK) error = gbb_load_rom(machine, rom, static_cast<size_t>(length));
    std::free(rom);
    gbb_input_event events[64]{};
    for (size_t i = 0; i < 64; ++i) {
        events[i].at_half_dots = i;
        events[i].kind = GBB_INPUT_STOP_WAKE;
        events[i].value = 1;
    }
    events[62] = {62, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A};
    events[63] = {63, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A};
    gbb_error event_error = error == GBB_OK ? gbb_queue_events(machine, events, 64) : error;
    gbb_input_event excess{64, static_cast<gbb_input_event_kind>(99), 0};
    gbb_error capacity_error = event_error == GBB_OK ? gbb_queue_events(machine, &excess, 1) : event_error;
    auto *trace = static_cast<gbb_trace_record *>(std::calloc(16384, sizeof(gbb_trace_record)));
    auto *diagnostics = static_cast<gbb_diagnostic_record *>(std::calloc(16384, sizeof(gbb_diagnostic_record)));
    gbb_run_result result{};
    if (error == GBB_OK && event_error == GBB_OK && trace != nullptr && diagnostics != nullptr)
        result = gbb_run_ex(machine, UINT64_C(160000), trace, 16384, diagnostics, 16384);
    bool chronological = true;
    for (size_t i = 1; i < result.diagnostic_count; ++i)
        if (diagnostics[i - 1].time_half_dots > diagnostics[i].time_half_dots) chronological = false;
    uint8_t frame[160u * 144u]{};
    gbb_frame_info frame_info{};
    gbb_error frame_error = error == GBB_OK
        ? gbb_copy_frame(machine, frame, sizeof(frame), 160, &frame_info) : error;
    bool shades_valid = true;
    if (frame_error == GBB_OK)
        for (uint8_t shade : frame)
            if (shade > 3u) shades_valid = false;
    bool passed = error == GBB_OK && event_error == GBB_OK && capacity_error == GBB_EVENT_QUEUE_FULL &&
        result.reason == GBB_STOP_BUDGET && result.consumed_half_dots <= UINT64_C(160000) &&
        trace != nullptr && result.trace_count > 0 && result.trace_count <= 16384 &&
        diagnostics != nullptr && result.diagnostic_count > 0 && result.diagnostic_count <= 16384 && chronological &&
        gbb_peek_ram(machine, 0xC001) == 0xA5 && frame_error == GBB_OK &&
        frame_info.width == 160 && frame_info.height == 144 && frame_info.generation > 0 && shades_valid;
    gbb_destroy(machine);
    std::free(trace);
    std::free(diagnostics);
    if (!passed) std::fprintf(stderr, "C++ consumer API smoke failed (error=%d, stop=%d, frame=%d)\n", error, result.reason, frame_error);
    if (!passed || battery_api_smoke() != 0) {
        std::fprintf(stderr, "C++ consumer public battery API smoke failed\n");
        return 1;
    }
    if (cgb_api_smoke() != 0) {
        std::fprintf(stderr, "C++ consumer public CGB API smoke failed\n");
        return 1;
    }
    {
        int unarmed_rejected = 0;
        if (!cgb_speed_partition_smoke(1u, nullptr)) {
            std::fprintf(stderr, "C++ consumer CGB speed partition smoke failed\n");
            return 1;
        }
        if (cgb_speed_partition_smoke(0u, &unarmed_rejected) || !unarmed_rejected) {
            std::fprintf(stderr, "C++ consumer CGB speed smoke accepted unarmed twin\n");
            return 1;
        }
        std::printf("cgb_speed_partition_smoke unarmed twin rejected\n");
    }
    {
        int data_match = 0, status_match = 0, timing_match = 0;
        if (!cgb_dma_partition_smoke(0, 1, &data_match, &status_match, &timing_match)) {
            std::fprintf(stderr, "C++ consumer CGB DMA normal-speed guest predicate failed: data=%d status=%d timing=%d\n",
                         data_match, status_match, timing_match);
            return 1;
        }
        if (!cgb_dma_partition_smoke(1, 1, &data_match, &status_match, &timing_match)) {
            std::fprintf(stderr, "C++ consumer CGB DMA double-speed guest predicate failed: data=%d status=%d timing=%d\n",
                         data_match, status_match, timing_match);
            return 1;
        }
        // FF55 reads FF before a transfer and after GDMA completes, so the
        // disabled twin must fail the data and CPU-steal timing predicates.
        if (!cgb_dma_partition_smoke(0, 0, &data_match, &status_match, &timing_match) ||
            data_match || timing_match) {
            std::fprintf(stderr, "C++ consumer CGB DMA disabled twin lacked diagnosed mismatch\n");
            return 1;
        }
        std::printf("cgb_dma_partition_smoke disabled twin rejected: data=%d status=%d timing=%d\n",
                    data_match, status_match, timing_match);
    }
    if (rtc_api_smoke() != 0) {
        std::fprintf(stderr, "C++ consumer public RTC API smoke failed\n");
        return 1;
    }
    if (audio_api_smoke() != 0) {
        std::fprintf(stderr, "C++ consumer public audio API smoke failed\n");
        return 1;
    }
    return 0;
}
