#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FUZZ_INPUT_LIMIT 65536u
#define FUZZ_OPERATION_LIMIT 16u
#define FUZZ_BATTERY_BYTES 8192u
#define FUZZ_IMPORT_LIMIT (FUZZ_BATTERY_BYTES + 1u)
#define FUZZ_RUN_LIMIT UINT64_C(2048)
#define FUZZ_INPUT_HALF_DOT_LIMIT UINT64_C(8192)

static void fix_checksum(uint8_t rom[32768]) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void make_battery_rom(uint8_t rom[32768]) {
    memset(rom, 0, 32768u);
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    fix_checksum(rom);
}

/* Standalone test build: a violated contract is counted and reported so a deliberately mutated core
 * can be shown to trip an invariant through a numeric exit code (cgb_fuzz_palette_mutant_no_mask).
 * The libFuzzer build aborts, which is what the fuzzer needs to record a crash. */
#ifdef GBB_FUZZ_STANDALONE_TEST
static int contract_failures;
int gbb_fuzz_core_contract_failures(void) { return contract_failures; }
#endif

static void contract_failed(const char *what) {
    fprintf(stderr, "fuzz contract failed: %s\n", what);
#ifdef GBB_FUZZ_STANDALONE_TEST
    ++contract_failures;
#else
    abort();
#endif
}

static void require_contract(int condition) {
    if (!condition) contract_failed("contract violated");
}

/* Internal test seam, defined by the core and linked into every fuzz target. */
extern void gbb_test_bank_state(const gbb_instance *, uint8_t *, uint8_t *);

/* D-19(4) and D-27: bank indices are fixed on the DMG profile and bounded on the CGB profile no
 * matter what the untrusted input did. */
static void require_banks(const gbb_instance *machine, int cgb) {
    uint8_t vram_bank = 0xA7u;
    uint8_t wram_bank = 0xA7u;
    gbb_test_bank_state(machine, &vram_bank, &wram_bank);
    if (cgb) {
        require_contract(vram_bank <= 1u);
        require_contract(wram_bank >= 1u && wram_bank <= 7u);
    } else {
        require_contract(vram_bank == 0u && wram_bank == 1u);
    }
}

static void fuzz_loader(gbb_instance *machine, const uint8_t *data, size_t size) {
    if (size <= 1u) {
        require_contract(gbb_load_rom(machine, NULL, size) == GBB_INVALID_ARGUMENT);
        return;
    }
    const gbb_error result = gbb_load_rom(machine, data + 1u, size - 1u);
    if (result != GBB_OK) {
        const gbb_run_result run = gbb_run(machine, FUZZ_RUN_LIMIT, NULL, 0u);
        require_contract(run.consumed_half_dots <= FUZZ_RUN_LIMIT);
        require_contract(run.reason == GBB_STOP_BUDGET ||
                         run.reason == GBB_STOP_UNSUPPORTED_BUS ||
                         run.reason == GBB_STOP_INVALID_STATE);
    }
}

static void fuzz_stateful_api(gbb_instance *machine, const uint8_t *data,
                              size_t size, int cgb) {
    uint8_t input[FUZZ_IMPORT_LIMIT];
    uint8_t before[FUZZ_BATTERY_BYTES];
    uint8_t output[FUZZ_BATTERY_BYTES + 2u];
    size_t cursor = 1u;
    uint64_t input_half_dots = 0u;

    for (size_t operation = 0u;
         operation < FUZZ_OPERATION_LIMIT && cursor < size; ++operation) {
        const uint8_t selector = data[cursor++];
        if (selector % 6u == 0u && cursor < size) {
            size_t length = (size_t)(data[cursor++] % 32u);
            if (length > size - cursor) length = size - cursor;
            (void)gbb_load_rom(machine, data + cursor, length);
            cursor += length;
        } else if (selector % 6u == 1u) {
            size_t battery_size = 0u;
            if (gbb_battery_size(machine, &battery_size) != GBB_OK ||
                battery_size != FUZZ_BATTERY_BYTES) continue;
            size_t length = selector == 1u ? FUZZ_BATTERY_BYTES - 1u :
                            selector == 7u ? FUZZ_IMPORT_LIMIT : FUZZ_BATTERY_BYTES;
            memset(input, (int)selector, sizeof(input));
            require_contract(gbb_copy_battery(machine, before, sizeof(before)) == GBB_OK);
            const gbb_error imported = gbb_import_battery(machine, input, length);
            if (length != FUZZ_BATTERY_BYTES) {
                require_contract(imported == GBB_BATTERY_SIZE_MISMATCH);
                require_contract(gbb_copy_battery(machine, output + 1u,
                                                   sizeof(before)) == GBB_OK);
                require_contract(memcmp(before, output + 1u,
                                        sizeof(before)) == 0);
            } else {
                require_contract(imported == GBB_OK);
            }
        } else if (selector % 6u == 2u) {
            memset(output, 0xA7, sizeof(output));
            (void)gbb_copy_battery(machine, output + 1u,
                                   (selector & 1u) != 0u ?
                                       FUZZ_BATTERY_BYTES - 1u :
                                       sizeof(output) - 2u);
            require_contract(output[0] == 0xA7u);
            require_contract(output[sizeof(output) - 1u] == 0xA7u);
        } else if (selector % 6u == 3u) {
            uint64_t budget = (uint64_t)(selector % 32u) * 64u;
            const uint64_t remaining = FUZZ_INPUT_HALF_DOT_LIMIT - input_half_dots;
            if (budget > remaining) budget = remaining;
            const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
            require_contract(run.consumed_half_dots <= budget);
            input_half_dots += run.consumed_half_dots;
            require_contract(input_half_dots <= FUZZ_INPUT_HALF_DOT_LIMIT);
        } else if (selector % 6u == 4u) {
            (void)gbb_reset(machine);
        } else {
            size_t battery_size = SIZE_MAX;
            const gbb_error result = gbb_battery_size(machine, &battery_size);
            if (result == GBB_NO_BATTERY)
                require_contract(battery_size == SIZE_MAX);
        }
        require_banks(machine, cgb);
    }
}

/* D-28: synthesised-length mode. Only the 0x150-byte header is written; the
 * rest of the one static buffer stays zero, so an 8 MiB + 1 byte load costs no
 * per-input copy. Selector bytes: type, ROM code, RAM code, length class. */
#define FUZZ_MIB (1024u * 1024u)
#define FUZZ_SYNTH_MAX ((size_t)8u * FUZZ_MIB)

static void fuzz_synth_length(gbb_instance *machine, const uint8_t *data,
                              size_t size, int cgb) {
    static uint8_t image[8u * 1024u * 1024u + 1u];
    uint8_t before[FUZZ_BATTERY_BYTES];
    uint8_t after[FUZZ_BATTERY_BYTES];
    size_t before_size = 0u;
    size_t after_size = 0u;

    if (size < 5u) return;
    const uint8_t code = data[2];
    const size_t declared = code <= 8u ? (size_t)32768u << code : (size_t)32768u;
    size_t length = 0u;
    switch (data[4] % 10u) {
    case 0u: length = declared; break;
    case 1u: length = declared - 1u; break;
    case 2u: length = declared + 1u; break;
    case 3u: length = (size_t)2u * FUZZ_MIB; break;
    case 4u: length = (size_t)2u * FUZZ_MIB + 1u; break;
    case 5u: length = (size_t)4u * FUZZ_MIB; break;
    case 6u: length = (size_t)4u * FUZZ_MIB + 1u; break;
    case 7u: length = FUZZ_SYNTH_MAX; break;
    case 8u: length = FUZZ_SYNTH_MAX + 1u; break;
    default: length = SIZE_MAX; break;
    }

    memset(image, 0, 0x150u);
    image[0x147u] = data[1];
    image[0x148u] = code;
    image[0x149u] = data[3];
    /* The CGB profile also sees a fuzzed $143 so PGB-flagged headers are reachable. */
    if (cgb && size > 6u) image[0x143u] = data[6];
    fix_checksum(image);
    if (size > 5u && (data[5] & 1u) != 0u) image[0x14Du] ^= 0xFFu;

    require_contract(gbb_battery_size(machine, &before_size) == GBB_OK &&
                     before_size == FUZZ_BATTERY_BYTES);
    require_contract(gbb_copy_battery(machine, before, sizeof(before)) == GBB_OK);

    const gbb_error result = gbb_load_rom(machine, image, length);
    require_contract(result == GBB_OK || result == GBB_ROM_TOO_LARGE ||
                     result == GBB_UNSUPPORTED_CARTRIDGE ||
                     result == GBB_UNSUPPORTED_ROM_SIZE ||
                     result == GBB_UNSUPPORTED_RAM_SIZE ||
                     result == GBB_ROM_TRUNCATED ||
                     result == GBB_ROM_SIZE_MISMATCH ||
                     result == GBB_INVALID_ROM ||
                     result == GBB_UNSUPPORTED_CARTRIDGE_VARIANT ||
                     (cgb && result == GBB_UNSUPPORTED_EXECUTION_MODE));
    if (length > FUZZ_SYNTH_MAX) require_contract(result == GBB_ROM_TOO_LARGE);
    if (result != GBB_OK) {
        require_contract(gbb_battery_size(machine, &after_size) == GBB_OK &&
                         after_size == before_size);
        require_contract(gbb_copy_battery(machine, after, sizeof(after)) == GBB_OK);
        require_contract(memcmp(before, after, sizeof(before)) == 0);
    } else {
        const gbb_run_result run = gbb_run(machine, FUZZ_RUN_LIMIT, NULL, 0u);
        require_contract(run.consumed_half_dots <= FUZZ_RUN_LIMIT);
    }
    require_banks(machine, cgb);
}

/* D-27: CGB I/O decode under untrusted guest code. The input becomes up to FUZZ_CGB_OPERATION_LIMIT
 * guest operations, three bytes each: a selector, a value and an address byte. Selector bit 0 makes
 * a read (LDH A,(n)), otherwise a write (LD A,value; LDH (n),A). Selector bit 1 redirects the
 * access to VBK ($FF4F, selector bit 2 set) or SVBK ($FF70) so bank switching is hit often; any
 * other access lands on a fuzzed address in FF00-FF7F. $143 is $80 or $00 from data[1]. */
#define FUZZ_CGB_OPERATION_LIMIT 64u
#define FUZZ_CGB_PROGRAM 0x150u

static void fuzz_cgb_io(gbb_instance *machine, const uint8_t *data, size_t size) {
    static uint8_t rom[32768];
    size_t at = FUZZ_CGB_PROGRAM;
    size_t cursor = 2u;

    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;   /* JP $0150 over the header */
    rom[0x143u] = size > 1u && (data[1] & 1u) != 0u ? 0x80u : 0x00u;
    for (size_t operation = 0u;
         operation < FUZZ_CGB_OPERATION_LIMIT && cursor + 2u < size; ++operation) {
        const uint8_t selector = data[cursor];
        const uint8_t value = data[cursor + 1u];
        uint8_t offset = (uint8_t)(data[cursor + 2u] & 0x7Fu);
        cursor += 3u;
        if ((selector & 2u) != 0u) offset = (selector & 4u) != 0u ? 0x4Fu : 0x70u;
        if ((selector & 1u) != 0u) {
            rom[at++] = 0xF0u; rom[at++] = offset;                 /* LDH A,(n) */
        } else {
            rom[at++] = 0x3Eu; rom[at++] = value;                  /* LD A,value */
            rom[at++] = 0xE0u; rom[at++] = offset;                 /* LDH (n),A */
        }
    }
    rom[at] = 0x76u;                                               /* HALT */
    fix_checksum(rom);
    require_contract(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, FUZZ_RUN_LIMIT, NULL, 0u);
    require_contract(run.consumed_half_dots <= FUZZ_RUN_LIMIT);
    require_contract(run.reason == GBB_STOP_BUDGET ||
                     run.reason == GBB_STOP_HALTED_IDLE ||
                     run.reason == GBB_STOP_UNSUPPORTED_BUS);
    require_banks(machine, 1);
}

/* D-34: palette RAM and the compatibility palette API under untrusted input. data[0] = 0xA0 | ... on
 * the CGB profile selects this path (bit 6 clear). data[1] bit 0 picks CGB mode ($143 = $80) or
 * compatibility mode ($143 = $00), so the same sequence is read in both. The remaining bytes are up
 * to FUZZ_PALETTE_OPERATION_LIMIT operations of three bytes (selector, a, b):
 *   selector % 8 in 0..4  guest write of `a` to FF68 + selector (BCPS, BCPD, OCPS, OCPD, OPRI)
 *   5                     guest read of FF68 + b % 5
 *   6                     guest write of `a` to LCDC, which toggles the LCD on and off
 *   7                     host action, in order, interleaved with gbb_run slices of the guest:
 *                         a & 3 = 0 run (b + 1) * 256 half-dots; 1 gbb_set_compat_palette with
 *                         struct_size {0, 27, 28, 29, 64}[b % 5] and, when a & 4, bit 15 set on one
 *                         entry; 2 set with a NULL palette; 3 gbb_get_compat_palette.
 * Invariants: every gbb_copy_frame_rgb555 pixel has bit 15 clear, a rejected set leaves the palette
 * unchanged and an accepted one stores exactly what was given. */
#define FUZZ_PALETTE_OPERATION_LIMIT 512u
#define FUZZ_PALETTE_HALF_DOT_LIMIT UINT64_C(400000)
#define FUZZ_PIXELS (160u * 144u)

static uint16_t frame_pixels[FUZZ_PIXELS];

static const uint32_t palette_sizes[5] = {0u, 27u, 28u, 29u, 64u};

typedef union {
    gbb_compat_palette palette;
    uint8_t raw[64];
} palette_buffer;

static int palette_equal(const gbb_compat_palette *a, const gbb_compat_palette *b) {
    return memcmp(a->bg, b->bg, sizeof(a->bg)) == 0 &&
           memcmp(a->obj0, b->obj0, sizeof(a->obj0)) == 0 &&
           memcmp(a->obj1, b->obj1, sizeof(a->obj1)) == 0;
}

static void require_frame_bit15_clear(const gbb_instance *machine) {
    gbb_frame_info info;
    memset(frame_pixels, 0xFF, sizeof(frame_pixels));
    const gbb_error result = gbb_copy_frame_rgb555(machine, frame_pixels, sizeof(frame_pixels),
                                                   160u * 2u, &info);
    if (result != GBB_OK) {
        require_contract(result == GBB_FRAME_NOT_READY);
        return;
    }
    for (size_t i = 0u; i < FUZZ_PIXELS; ++i)
        if (frame_pixels[i] > 0x7FFFu) {
            contract_failed("pixel above 0x7FFF");
            return;
        }
}

static void fuzz_palette_set(gbb_instance *machine, uint8_t a, uint8_t b) {
    palette_buffer given;
    palette_buffer before;
    palette_buffer after;
    memset(&given, 0, sizeof(given));
    uint16_t words[12];
    for (unsigned i = 0u; i < 12u; ++i)
        words[i] = (uint16_t)((b * 0x0101u + i * 0x1357u) & 0x7FFFu);
    if ((a & 4u) != 0u) words[(b >> 3) % 12u] |= 0x8000u;
    memcpy(given.palette.bg, words, 8u);
    memcpy(given.palette.obj0, words + 4, 8u);
    memcpy(given.palette.obj1, words + 8, 8u);
    given.palette.struct_size = palette_sizes[b % 5u];

    memset(&before, 0, sizeof(before));
    before.palette.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    require_contract(gbb_get_compat_palette(machine, &before.palette) == GBB_OK);

    const int null_palette = (a & 3u) == 2u;
    const gbb_error result = gbb_set_compat_palette(machine, null_palette ? NULL : &given.palette);
    const int bit15 = (a & 4u) != 0u;
    const int should_reject = !null_palette &&
        (given.palette.struct_size < GBB_COMPAT_PALETTE_SIZE_V1 || bit15);
    require_contract(result == (should_reject ? GBB_INVALID_ARGUMENT : GBB_OK));

    memset(&after, 0, sizeof(after));
    after.palette.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    require_contract(gbb_get_compat_palette(machine, &after.palette) == GBB_OK);
    if (result == GBB_INVALID_ARGUMENT) {
        if (!palette_equal(&before.palette, &after.palette))
            contract_failed("a rejected gbb_set_compat_palette changed the palette");
    } else if (!null_palette) {
        require_contract(palette_equal(&given.palette, &after.palette));
    }
}

static void fuzz_palette(gbb_instance *machine, const uint8_t *data, size_t size) {
    static uint8_t rom[32768];
    uint8_t host[FUZZ_PALETTE_OPERATION_LIMIT][3];
    size_t host_count = 0u;
    size_t at = FUZZ_CGB_PROGRAM;
    size_t cursor = 2u;

    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;   /* JP $0150 over the header */
    rom[0x143u] = size > 1u && (data[1] & 1u) != 0u ? 0x80u : 0x00u;
    for (size_t operation = 0u;
         operation < FUZZ_PALETTE_OPERATION_LIMIT && cursor + 2u < size; ++operation) {
        const uint8_t selector = (uint8_t)(data[cursor] % 8u);
        const uint8_t a = data[cursor + 1u];
        const uint8_t b = data[cursor + 2u];
        cursor += 3u;
        if (selector <= 4u) {
            rom[at++] = 0x3Eu; rom[at++] = a;                          /* LD A,a */
            rom[at++] = 0xE0u; rom[at++] = (uint8_t)(0x68u + selector); /* LDH (n),A */
        } else if (selector == 5u) {
            rom[at++] = 0xF0u; rom[at++] = (uint8_t)(0x68u + b % 5u);  /* LDH A,(n) */
        } else if (selector == 6u) {
            rom[at++] = 0x3Eu; rom[at++] = a;
            rom[at++] = 0xE0u; rom[at++] = 0x40u;                      /* LDH (LCDC),A */
        } else {
            host[host_count][0] = 7u; host[host_count][1] = a; host[host_count][2] = b;
            ++host_count;
        }
    }
    rom[at++] = 0x18u; rom[at] = 0xFEu;                                /* JR -2: time keeps passing */
    fix_checksum(rom);
    require_contract(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);

    uint64_t spent = 0u;
    for (size_t i = 0u; i < host_count; ++i) {
        const uint8_t kind = (uint8_t)(host[i][1] & 3u);
        if (kind == 0u) {
            uint64_t budget = ((uint64_t)host[i][2] + 1u) * 256u;
            if (budget > FUZZ_PALETTE_HALF_DOT_LIMIT - spent)
                budget = FUZZ_PALETTE_HALF_DOT_LIMIT - spent;
            const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
            require_contract(run.consumed_half_dots <= budget);
            spent += run.consumed_half_dots;
        } else if (kind == 3u) {
            palette_buffer out;
            memset(&out, 0, sizeof(out));
            for (size_t k = 0u; k < 3u; ++k) {
                out.palette.struct_size = palette_sizes[(host[i][2] + k) % 5u];
                const gbb_error got = gbb_get_compat_palette(machine, &out.palette);
                const uint32_t asked = palette_sizes[(host[i][2] + k) % 5u];
                if (asked < GBB_COMPAT_PALETTE_SIZE_V1) {
                    require_contract(got == GBB_INVALID_ARGUMENT);
                    require_contract(out.palette.struct_size == asked);
                } else {
                    require_contract(got == GBB_OK);
                    require_contract(out.palette.struct_size == GBB_COMPAT_PALETTE_SIZE_V1);
                }
            }
        } else {
            fuzz_palette_set(machine, host[i][1], host[i][2]);
        }
        require_frame_bit15_clear(machine);
    }
    while (spent < FUZZ_PALETTE_HALF_DOT_LIMIT) {
        uint64_t budget = FUZZ_PALETTE_HALF_DOT_LIMIT - spent;
        if (budget > 65536u) budget = 65536u;
        const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
        require_contract(run.consumed_half_dots <= budget);
        if (run.consumed_half_dots == 0u) break;
        spent += run.consumed_half_dots;
    }
    require_frame_bit15_clear(machine);
    require_banks(machine, 1);
}

/* The DMG profile has no RGB store: the colour copy is refused and writes nothing. */
static void require_dmg_rgb_store_empty(const gbb_instance *machine) {
    gbb_frame_info info;
    memset(frame_pixels, 0xA5, sizeof(frame_pixels));
    require_contract(gbb_copy_frame_rgb555(machine, frame_pixels, sizeof(frame_pixels), 160u * 2u,
                                           &info) == GBB_UNSUPPORTED_PROFILE);
    for (size_t i = 0u; i < FUZZ_PIXELS; ++i)
        if (frame_pixels[i] != 0xA5A5u) {
            contract_failed("DMG profile wrote to the RGB frame buffer");
            return;
        }
}

/* Test-only observer (standalone test build): the profile the most recent input selected, -1 before
 * any input. Lets cgb_fuzz_profile_select prove that bit 7 really reaches gbb_create. */
static int last_profile_cgb = -1;
#ifdef GBB_FUZZ_STANDALONE_TEST
int gbb_fuzz_core_last_profile_cgb(void) { return last_profile_cgb; }
#endif

int gbb_fuzz_core_one_input(const uint8_t *data, size_t size) {
    if (data == NULL || size == 0u || size > FUZZ_INPUT_LIMIT) return 0;

    /* data[0] bit 7 selects the profile (clear = DMG-CPU-B, set = CGB-CPU-E); with bit 6 also set
     * on the CGB profile the input drives the guest I/O path. Bits 0-1 keep the mode selector. */
    const int cgb = (data[0] & 0x80u) != 0u;
    last_profile_cgb = cgb;
    gbb_instance *machine = NULL;
    require_contract(gbb_create(cgb ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B,
                                &machine) == GBB_OK);
    uint8_t base_rom[32768];
    make_battery_rom(base_rom);
    require_contract(gbb_load_rom(machine, base_rom, sizeof(base_rom)) == GBB_OK);

    if (cgb && (data[0] & 0x40u) != 0u)
        fuzz_cgb_io(machine, data, size);
    else if (cgb && (data[0] & 0x20u) != 0u)
        fuzz_palette(machine, data, size);
    else if ((data[0] & 3u) == 2u)
        fuzz_synth_length(machine, data, size, cgb);
    else if ((data[0] & 3u) == 0u)
        fuzz_loader(machine, data, size);
    else
        fuzz_stateful_api(machine, data, size, cgb);
    require_banks(machine, cgb);
    if (!cgb) require_dmg_rgb_store_empty(machine);

    gbb_destroy(machine);
    return 0;
}

#ifndef GBB_FUZZ_STANDALONE_TEST
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    return gbb_fuzz_core_one_input(data, size);
}
#endif
