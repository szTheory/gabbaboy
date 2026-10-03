#include "gabbaboy/gabbaboy.h"

#include <stdlib.h>
#include <string.h>

struct gbb_instance {
    uint8_t *rom;
    size_t rom_size;
    uint8_t ram[8192];
    uint8_t a, f, b, c, d, e, h, l;
    uint8_t div, stat;
    uint16_t pc, sp;
    uint64_t time_half_dots;
    int loaded;
};

#define GBB_MAX_ROM_SIZE ((size_t)8u * 1024u * 1024u)

static void reset_state(gbb_instance *m) {
    m->a = 0x01; m->f = 0x80; m->b = 0x00; m->c = 0x13;
    m->d = 0x00; m->e = 0xD8; m->h = 0x01; m->l = 0x4D;
    m->pc = 0x0100; m->sp = 0xFFFE;
    m->div = 0xAB; m->stat = 0x85;
    memset(m->ram, 0, sizeof(m->ram));
    m->time_half_dots = 0;
}

static uint8_t read8(const gbb_instance *m, uint16_t address) {
    if (address < m->rom_size) return m->rom[address];
    if (address >= 0xA000 && address <= 0xBFFF) return m->ram[address - 0xA000];
    return 0xFF;
}

static void write8(gbb_instance *m, uint16_t address, uint8_t value) {
    if (address >= 0xA000 && address <= 0xBFFF) m->ram[address - 0xA000] = value;
}

static uint16_t hl(const gbb_instance *m) { return (uint16_t)(((uint16_t)m->h << 8) | m->l); }
static void set_hl(gbb_instance *m, uint16_t value) { m->h = (uint8_t)(value >> 8); m->l = (uint8_t)value; }

static gbb_error validate_header(const uint8_t *rom, size_t size) {
    if (rom == NULL || size == 0) return GBB_INVALID_ARGUMENT;
    if (size < 0x150) return GBB_ROM_TRUNCATED;
    if (size > GBB_MAX_ROM_SIZE) return GBB_ROM_TOO_LARGE;
    if (rom[0x147] != 0) return GBB_UNSUPPORTED_CARTRIDGE;
    if (rom[0x148] > 8) return GBB_UNSUPPORTED_ROM_SIZE;
    if (rom[0x149] != 0) return GBB_UNSUPPORTED_RAM_SIZE;
    size_t declared = 32768u << rom[0x148];
    if (size < declared) return GBB_ROM_TRUNCATED;
    if (size != declared) return GBB_INVALID_ROM;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    return checksum == rom[0x14D] ? GBB_OK : GBB_INVALID_ROM;
}

gbb_error gbb_create(gbb_profile profile, gbb_instance **out_instance) {
    if (out_instance == NULL) return GBB_INVALID_ARGUMENT;
    *out_instance = NULL;
    if (profile != GBB_PROFILE_DMG_CPU_B) return GBB_UNSUPPORTED_PROFILE;
    gbb_instance *m = calloc(1, sizeof(*m));
    if (m == NULL) return GBB_OUT_OF_MEMORY;
    reset_state(m); /* RAM fill is emulator policy; hardware power-on RAM is unspecified. */
    *out_instance = m;
    return GBB_OK;
}

void gbb_destroy(gbb_instance *instance) {
    if (instance != NULL) { free(instance->rom); free(instance); }
}

gbb_error gbb_reset(gbb_instance *instance) {
    if (instance == NULL) return GBB_INVALID_ARGUMENT;
    reset_state(instance);
    return GBB_OK;
}

gbb_error gbb_load_rom(gbb_instance *instance, const uint8_t *rom, size_t rom_size) {
    if (instance == NULL) return GBB_INVALID_ARGUMENT;
    gbb_error validation = validate_header(rom, rom_size);
    if (validation != GBB_OK) return validation;
    uint8_t *copy = malloc(rom_size);
    if (copy == NULL) return GBB_OUT_OF_MEMORY;
    memcpy(copy, rom, rom_size);
    free(instance->rom);
    instance->rom = copy;
    instance->rom_size = rom_size;
    reset_state(instance);
    instance->loaded = 1;
    return GBB_OK;
}

typedef struct { uint8_t size; uint8_t ticks; int supported; } decoded;

static decoded decode(const gbb_instance *m) {
    uint8_t op = read8(m, m->pc);
    switch (op) {
        case 0xC3: return (decoded){3, 32, 1}; /* JP a16 */
        case 0x21: return (decoded){3, 24, 1}; /* LD HL,d16 */
        case 0x3E: return (decoded){2, 16, 1}; /* LD A,d8 */
        case 0x77: case 0x7E: case 0x23: return (decoded){1, 8, 1};
        case 0xFE: return (decoded){2, 16, 1}; /* CP d8 */
        case 0x20: return (decoded){2, 0, 1}; /* JR NZ,r8; branch cost depends on flags */
        case 0x18: return (decoded){2, 0, 1}; /* JR r8 */
        default: return (decoded){1, 0, 0};
    }
}

static uint8_t instruction_cost(const gbb_instance *m, decoded d) {
    uint8_t op = read8(m, m->pc);
    if (op == 0x18) return 24;
    if (op == 0x20) return (m->f & 0x80) == 0 ? 24 : 16;
    return d.ticks;
}

static void save_trace(const gbb_instance *m, decoded d, gbb_trace_record *r) {
    memset(r, 0, sizeof(*r));
    r->time_half_dots = m->time_half_dots; r->pc = m->pc; r->opcode_size = d.size;
    for (uint8_t i = 0; i < d.size && i < 3; ++i) r->opcode[i] = read8(m, (uint16_t)(m->pc + i));
    r->a=m->a; r->f=m->f; r->b=m->b; r->c=m->c; r->d=m->d; r->e=m->e; r->h=m->h; r->l=m->l; r->sp=m->sp;
}

static void execute(gbb_instance *m, uint8_t cost) {
    uint16_t pc = m->pc;
    uint8_t op = read8(m, pc);
    switch (op) {
        case 0xC3: m->pc=(uint16_t)(read8(m, pc+1) | ((uint16_t)read8(m, pc+2)<<8)); break;
        case 0x21: set_hl(m, (uint16_t)(read8(m, pc+1) | ((uint16_t)read8(m, pc+2)<<8))); m->pc+=3; break;
        case 0x3E: m->a=read8(m, pc+1); m->pc+=2; break;
        case 0x77: write8(m, hl(m), m->a); m->pc++; break;
        case 0x7E: m->a=read8(m, hl(m)); m->pc++; break;
        case 0x23: set_hl(m, (uint16_t)(hl(m)+1)); m->pc++; break;
        case 0xFE: {
            uint8_t result=(uint8_t)(m->a-read8(m,pc+1));
            m->f=(uint8_t)(0x40 | (result==0 ? 0x80 : 0) | ((m->a & 15) < (read8(m,pc+1) & 15) ? 0x20 : 0) | (m->a < read8(m,pc+1) ? 0x10 : 0));
            m->pc+=2; break;
        }
        case 0x20: { int8_t rel=(int8_t)read8(m,pc+1); m->pc+=2; if ((m->f&0x80)==0) m->pc=(uint16_t)(m->pc+rel); break; }
        case 0x18: m->pc=(uint16_t)(pc+2+(int8_t)read8(m,pc+1)); break;
        default: break;
    }
    m->time_half_dots += cost;
}

gbb_run_result gbb_run(gbb_instance *instance, uint64_t budget_half_dots,
                       gbb_trace_record *trace, size_t trace_capacity) {
    gbb_run_result result={0, GBB_STOP_BUDGET, 0};
    if (instance == NULL || !instance->loaded || (trace == NULL && trace_capacity != 0)) { result.reason=GBB_STOP_INVALID_STATE; return result; }
    while (result.consumed_half_dots < budget_half_dots) {
        decoded d=decode(instance);
        if (!d.supported) { result.reason=GBB_STOP_UNSUPPORTED_OPCODE; return result; }
        uint8_t cost=instruction_cost(instance,d);
        if (cost > budget_half_dots-result.consumed_half_dots) return result;
        if (trace != NULL && result.trace_count == trace_capacity) { result.reason=GBB_STOP_TRACE_FULL; return result; }
        if (trace != NULL) save_trace(instance,d,&trace[result.trace_count++]);
        execute(instance,cost);
        result.consumed_half_dots += cost;
    }
    return result;
}

uint8_t gbb_peek_ram(const gbb_instance *instance, uint16_t address) {
    if (instance == NULL || address < 0xA000 || address > 0xBFFF) return 0xFF;
    return instance->ram[address - 0xA000];
}
