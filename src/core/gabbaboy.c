#include "gabbaboy/gabbaboy.h"

#include <stdlib.h>
#include <string.h>

struct gbb_instance {
    uint8_t *rom;
    size_t rom_size;
    uint8_t wram[8192];
    uint8_t hram[127];
    uint8_t a, f, b, c, d, e, h, l;
    uint8_t div, stat;
    uint16_t pc, sp;
    uint64_t time_half_dots;
    uint16_t lockup_pc;
    uint8_t lockup_opcode;
    int locked;
    struct gbb_test_bus_event *test_events;
    size_t test_event_capacity;
    size_t test_event_count;
    int loaded;
};

typedef struct gbb_test_bus_event {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;

void gbb_test_observer_set(gbb_instance *m, gbb_test_bus_event *events, size_t capacity) {
    if (m == NULL) return;
    m->test_events = events;
    m->test_event_capacity = capacity;
    m->test_event_count = 0;
}

size_t gbb_test_observer_count(const gbb_instance *m) {
    return m == NULL ? 0 : m->test_event_count;
}

static void observe_bus(gbb_instance *m, uint64_t offset, uint16_t address, uint8_t access, uint8_t value) {
    if (m->test_events != NULL && m->test_event_count < m->test_event_capacity) {
        gbb_test_bus_event *event = &m->test_events[m->test_event_count++];
        event->time_half_dots = m->time_half_dots + offset;
        event->address = address;
        event->access = access;
        event->value = value;
    }
}

#define GBB_MAX_ROM_SIZE ((size_t)8u * 1024u * 1024u)

static void reset_state(gbb_instance *m) {
    m->a = 0x01; m->f = 0x80; m->b = 0x00; m->c = 0x13;
    m->d = 0x00; m->e = 0xD8; m->h = 0x01; m->l = 0x4D;
    m->pc = 0x0100; m->sp = 0xFFFE;
    m->div = 0xAB; m->stat = 0x85;
    memset(m->wram, 0, sizeof(m->wram));
    memset(m->hram, 0, sizeof(m->hram));
    m->time_half_dots = 0;
    m->lockup_pc = 0;
    m->lockup_opcode = 0;
    m->locked = 0;
}

static uint8_t read8(const gbb_instance *m, uint16_t address) {
    if (address < m->rom_size) return m->rom[address];
    if (address >= 0xC000 && address <= 0xDFFF) return m->wram[address - 0xC000];
    if (address >= 0xE000 && address <= 0xFDFF) return m->wram[address - 0xE000];
    if (address >= 0xFF80 && address <= 0xFFFE) return m->hram[address - 0xFF80];
    return 0xFF;
}

static uint8_t bus_read(gbb_instance *m, uint16_t address, uint64_t offset) {
    uint8_t value = read8(m, address);
    observe_bus(m, offset, address, 1, value);
    return value;
}

static void write8(gbb_instance *m, uint16_t address, uint8_t value) {
    if (address >= 0xC000 && address <= 0xDFFF) m->wram[address - 0xC000] = value;
    else if (address >= 0xE000 && address <= 0xFDFF) m->wram[address - 0xE000] = value;
    else if (address >= 0xFF80 && address <= 0xFFFE) m->hram[address - 0xFF80] = value;
}

static void bus_write(gbb_instance *m, uint16_t address, uint8_t value, uint64_t offset) {
    observe_bus(m, offset, address, 2, value);
    write8(m, address, value);
}

static int read_supported(uint16_t address) {
    return address < 0x8000 ||
           (address >= 0xC000 && address <= 0xDFFF) ||
           (address >= 0xE000 && address <= 0xFDFF) ||
           (address >= 0xFF80 && address <= 0xFFFE);
}

static uint16_t hl(const gbb_instance *m) { return (uint16_t)(((uint16_t)m->h << 8) | m->l); }
static void set_hl(gbb_instance *m, uint16_t value) { m->h = (uint8_t)(value >> 8); m->l = (uint8_t)value; }

static gbb_error validate_header(const uint8_t *rom, size_t size) {
    if (rom == NULL || size == 0) return GBB_INVALID_ARGUMENT;
    if (size < 0x150) return GBB_ROM_TRUNCATED;
    if (size > GBB_MAX_ROM_SIZE) return GBB_ROM_TOO_LARGE;
    if (rom[0x147] != 0) return GBB_UNSUPPORTED_CARTRIDGE;
    if (rom[0x148] > 0) return GBB_UNSUPPORTED_ROM_SIZE;
    if (rom[0x149] != 0) return GBB_UNSUPPORTED_RAM_SIZE;
    size_t declared = 32768u << rom[0x148];
    if (size < declared) return GBB_ROM_TRUNCATED;
    if (size != declared) return GBB_ROM_SIZE_MISMATCH;
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

static int is_unused_opcode(uint8_t op) {
    return op == 0xD3 || op == 0xDB || op == 0xDD || op == 0xE3 || op == 0xE4 ||
           op == 0xEB || op == 0xEC || op == 0xED || op == 0xF4 || op == 0xFC || op == 0xFD;
}

static int condition_true(const gbb_instance *m, unsigned condition) {
    switch (condition & 3u) {
        case 0: return (m->f & 0x80) == 0;
        case 1: return (m->f & 0x80) != 0;
        case 2: return (m->f & 0x10) == 0;
        default: return (m->f & 0x10) != 0;
    }
}

static decoded decode(const gbb_instance *m) {
    uint8_t op = read8(m, m->pc);
    if (is_unused_opcode(op)) return (decoded){1, 0, 0};
    if (op == 0xCB) {
        uint8_t extension = read8(m, (uint16_t)(m->pc + 1u));
        unsigned group = extension >> 6;
        unsigned target = extension & 7u;
        uint8_t ticks = target == 6u ? (uint8_t)(group == 1u ? 24u : 32u) : 16u;
        return (decoded){2, ticks, 1};
    }
    if ((op & 0xC7u) == 0x06u) return (decoded){2, (uint8_t)(((op >> 3) & 7u) == 6u ? 24 : 16), 1};
    if ((op & 0xCFu) == 0x01u) return (decoded){3, 24, 1};
    if ((op & 0xCFu) == 0x03u || (op & 0xCFu) == 0x0Bu || (op & 0xCFu) == 0x09u) return (decoded){1, 16, 1};
    if ((op & 0xC7u) == 0x04u || (op & 0xC7u) == 0x05u) return (decoded){1, (uint8_t)(((op >> 3) & 7u) == 6u ? 24 : 8), 1};
    if (op >= 0x40 && op <= 0x7F) return (decoded){1, (uint8_t)((op == 0x76 || ((op & 7u) != 6u && ((op >> 3) & 7u) != 6u)) ? 8 : 16), 1};
    if (op >= 0x80 && op <= 0xBF) return (decoded){1, (uint8_t)((op & 7u) == 6u ? 16 : 8), 1};
    if ((op & 0xE7u) == 0x20u) return (decoded){2, (uint8_t)(condition_true(m, (op >> 3) & 3u) ? 24 : 16), 1};
    if ((op & 0xE7u) == 0xC0u) return (decoded){1, (uint8_t)(condition_true(m, (op >> 3) & 3u) ? 40 : 16), 1};
    if ((op & 0xE7u) == 0xC2u) return (decoded){3, (uint8_t)(condition_true(m, (op >> 3) & 3u) ? 32 : 24), 1};
    if ((op & 0xE7u) == 0xC4u) return (decoded){3, (uint8_t)(condition_true(m, (op >> 3) & 3u) ? 48 : 24), 1};
    if ((op & 0xCFu) == 0xC1u) return (decoded){1, (uint8_t)(op == 0xF1 ? 24 : 24), 1};
    if ((op & 0xCFu) == 0xC5u) return (decoded){1, 32, 1};
    if ((op & 0xC7u) == 0xC6u) return (decoded){2, 16, 1};
    if ((op & 0xC7u) == 0xC7u) return (decoded){1, 32, 1};
    switch (op) {
        case 0x00: case 0x07: case 0x0F: case 0x10: case 0x17: case 0x1F:
        case 0x27: case 0x2F: case 0x37: case 0x3F: case 0x76: case 0xC9:
        case 0xD9: case 0xE9: case 0xF3: case 0xFB:
            return (decoded){(uint8_t)(op == 0x10 ? 2 : 1), (uint8_t)((op == 0xC9 || op == 0xD9) ? 32 : 8), 1};
        case 0x08: return (decoded){3, 40, 1};
        case 0x18: return (decoded){2, 24, 1};
        case 0x02: case 0x0A: case 0x12: case 0x1A:
        case 0x22: case 0x2A: case 0x32: case 0x3A: return (decoded){1, 16, 1};
        case 0xC3: return (decoded){3, 32, 1};
        case 0xCD: return (decoded){3, 48, 1};
        case 0xE0: case 0xF0: return (decoded){2, 24, 1};
        case 0xE2: case 0xF2: return (decoded){1, 16, 1};
        case 0xE8: return (decoded){2, 48, 1};
        case 0xEA: case 0xFA: return (decoded){3, 32, 1};
        case 0xF8: return (decoded){2, 24, 1};
        case 0xF9: return (decoded){1, 16, 1};
        default: return (decoded){1, 8, 1};
    }
}

static uint8_t instruction_cost(const gbb_instance *m, decoded d) { (void)m; return d.ticks; }

static uint16_t pair_value(const gbb_instance *m, unsigned pair) {
    switch (pair & 3u) {
        case 0: return (uint16_t)(((uint16_t)m->b << 8) | m->c);
        case 1: return (uint16_t)(((uint16_t)m->d << 8) | m->e);
        case 2: return hl(m);
        default: return m->sp;
    }
}

static void set_pair(gbb_instance *m, unsigned pair, uint16_t value) {
    switch (pair & 3u) {
        case 0: m->b=(uint8_t)(value>>8); m->c=(uint8_t)value; break;
        case 1: m->d=(uint8_t)(value>>8); m->e=(uint8_t)value; break;
        case 2: set_hl(m,value); break;
        default: m->sp=value; break;
    }
}

static uint16_t stack_pair(const gbb_instance *m, unsigned pair) {
    return pair == 3 ? (uint16_t)(((uint16_t)m->a << 8) | m->f) : pair_value(m,pair);
}

static void set_stack_pair(gbb_instance *m, unsigned pair, uint16_t value) {
    if (pair == 3) { m->a=(uint8_t)(value>>8); m->f=(uint8_t)(value&0xF0u); }
    else set_pair(m,pair,value);
}

static uint8_t get_reg(gbb_instance *m, unsigned reg, uint64_t offset) {
    switch (reg & 7u) {
        case 0: return m->b; case 1: return m->c; case 2: return m->d; case 3: return m->e;
        case 4: return m->h; case 5: return m->l; case 6: return bus_read(m,hl(m),offset); default: return m->a;
    }
}

static void set_reg(gbb_instance *m, unsigned reg, uint8_t value, uint64_t offset) {
    switch (reg & 7u) {
        case 0: m->b=value; break; case 1: m->c=value; break; case 2: m->d=value; break; case 3: m->e=value; break;
        case 4: m->h=value; break; case 5: m->l=value; break; case 6: bus_write(m,hl(m),value,offset); break; default: m->a=value; break;
    }
}

static void execute_cb(gbb_instance *m, uint16_t pc, uint8_t extension) {
    unsigned group = extension >> 6;
    unsigned operation = (extension >> 3) & 7u;
    unsigned target = extension & 7u;
    uint8_t value = get_reg(m, target, 16);
    if (group == 0u) {
        uint8_t carry_in = (uint8_t)((m->f & 0x10u) != 0);
        uint8_t carry_out = 0;
        switch (operation) {
            case 0: carry_out = (uint8_t)(value >> 7); value = (uint8_t)((value << 1) | carry_out); break;
            case 1: carry_out = (uint8_t)(value & 1u); value = (uint8_t)((value >> 1) | (carry_out << 7)); break;
            case 2: { uint8_t out = (uint8_t)(value >> 7); value = (uint8_t)((value << 1) | carry_in); carry_out = out; break; }
            case 3: { uint8_t out = (uint8_t)(value & 1u); value = (uint8_t)((value >> 1) | (carry_in << 7)); carry_out = out; break; }
            case 4: carry_out = (uint8_t)(value >> 7); value = (uint8_t)(value << 1); break;
            case 5: carry_out = (uint8_t)(value & 1u); value = (uint8_t)((value >> 1) | (value & 0x80u)); break;
            case 6: value = (uint8_t)((value << 4) | (value >> 4)); break;
            default: carry_out = (uint8_t)(value & 1u); value = (uint8_t)(value >> 1); break;
        }
        m->f = (uint8_t)((value == 0 ? 0x80u : 0u) | (carry_out ? 0x10u : 0u));
        set_reg(m, target, value, 24);
    } else if (group == 1u) {
        unsigned bit = operation;
        uint8_t carry = (uint8_t)(m->f & 0x10u);
        m->f = (uint8_t)(carry | 0x20u | ((value & (uint8_t)(1u << bit)) == 0 ? 0x80u : 0));
    } else if (group == 2u) {
        value = (uint8_t)(value & (uint8_t)~(1u << operation));
        set_reg(m, target, value, 24);
    } else {
        value = (uint8_t)(value | (uint8_t)(1u << operation));
        set_reg(m, target, value, 24);
    }
    m->pc = (uint16_t)(pc + 2u);
}

static uint8_t add8(gbb_instance *m, uint8_t lhs, uint8_t rhs, unsigned carry) {
    unsigned sum=(unsigned)lhs+(unsigned)rhs+carry; uint8_t result=(uint8_t)sum;
    m->f=(uint8_t)((result==0?0x80:0)|(((lhs&15u)+(rhs&15u)+carry>15u)?0x20:0)|(sum>255u?0x10:0)); return result;
}

static uint8_t sub8(gbb_instance *m, uint8_t lhs, uint8_t rhs, unsigned carry) {
    unsigned sub=(unsigned)rhs+carry; uint8_t result=(uint8_t)((unsigned)lhs-sub);
    m->f=(uint8_t)(0x40|(result==0?0x80:0)|((lhs&15u)<((rhs&15u)+carry)?0x20:0)|((unsigned)lhs<sub?0x10:0)); return result;
}

static void alu(gbb_instance *m, unsigned operation, uint8_t value) {
    switch (operation & 7u) {
        case 0: m->a=add8(m,m->a,value,0); break;
        case 1: m->a=add8(m,m->a,value,(m->f&0x10u)!=0); break;
        case 2: m->a=sub8(m,m->a,value,0); break;
        case 3: m->a=sub8(m,m->a,value,(m->f&0x10u)!=0); break;
        case 4: m->a&=value; m->f=(uint8_t)((m->a==0?0x80:0)|0x20); break;
        case 5: m->a^=value; m->f=(uint8_t)(m->a==0?0x80:0); break;
        case 6: m->a|=value; m->f=(uint8_t)(m->a==0?0x80:0); break;
        default: (void)sub8(m,m->a,value,0); break;
    }
}

static void push16(gbb_instance *m, uint16_t value, uint64_t high_time, uint64_t low_time) {
    --m->sp; bus_write(m,m->sp,(uint8_t)(value>>8),high_time);
    --m->sp; bus_write(m,m->sp,(uint8_t)value,low_time);
}

static uint16_t pop16(gbb_instance *m, uint64_t low_time, uint64_t high_time) {
    uint8_t lo=bus_read(m,m->sp,low_time); ++m->sp;
    uint8_t hi=bus_read(m,m->sp,high_time); ++m->sp;
    return (uint16_t)(lo | ((uint16_t)hi<<8));
}

static void execute(gbb_instance *m, uint8_t cost) {
    uint16_t pc=m->pc; uint8_t op=read8(m,pc); uint64_t base=0;
    if (op>=0x40 && op<=0x7F) {
        if (op==0x76) { m->pc=(uint16_t)(pc+1); }
        else { uint8_t value=get_reg(m,op&7u,8); set_reg(m,(op>>3)&7u,value,16); m->pc=(uint16_t)(pc+1); }
    } else if (op>=0x80 && op<=0xBF) {
        uint8_t value=get_reg(m,op&7u,8); alu(m,(op>>3)&7u,value); m->pc=(uint16_t)(pc+1);
    } else if ((op&0xC7u)==0x04u || (op&0xC7u)==0x05u) {
        unsigned reg=(op>>3)&7u; uint8_t old=get_reg(m,reg,8); uint8_t carry=(uint8_t)(m->f&0x10u);
        uint8_t value=(op&1u)?(uint8_t)(old-1u):(uint8_t)(old+1u);
        if (op&1u) m->f=(uint8_t)(carry|0x40u|(value==0?0x80:0)|((old&15u)==0?0x20:0));
        else m->f=(uint8_t)(carry|(value==0?0x80:0)|((old&15u)==15u?0x20:0));
        set_reg(m,reg,value,16); m->pc=(uint16_t)(pc+1);
    } else if ((op&0xC7u)==0x06u) {
        uint8_t value=read8(m,(uint16_t)(pc+1)); set_reg(m,(op>>3)&7u,value,16); m->pc=(uint16_t)(pc+2);
    } else if ((op&0xCFu)==0x01u) {
        uint16_t value=(uint16_t)(read8(m,pc+1)|((uint16_t)read8(m,pc+2)<<8)); set_pair(m,(op>>4)&3u,value); m->pc=(uint16_t)(pc+3);
    } else if ((op&0xCFu)==0x03u || (op&0xCFu)==0x0Bu) {
        unsigned pair=(op>>4)&3u; uint16_t value=pair_value(m,pair); set_pair(m,pair,(uint16_t)(value+((op&8u)?-1:1))); m->pc=(uint16_t)(pc+1);
    } else if ((op&0xCFu)==0x09u) {
        uint16_t lhs=hl(m), rhs=pair_value(m,(op>>4)&3u); uint32_t sum=(uint32_t)lhs+rhs;
        m->f=(uint8_t)((m->f&0x80u)|(((lhs&0xFFFu)+(rhs&0xFFFu)>0xFFFu)?0x20u:0)|(sum>0xFFFFu?0x10u:0)); set_hl(m,(uint16_t)sum); m->pc=(uint16_t)(pc+1);
    } else if ((op&0xE7u)==0x20u) {
        int8_t offset=(int8_t)read8(m,pc+1); m->pc=(uint16_t)(pc+2); if(condition_true(m,(op>>3)&3u)) m->pc=(uint16_t)(m->pc+offset);
    } else if (op==0x18) { m->pc=(uint16_t)(pc+2+(int8_t)read8(m,pc+1)); }
    else if ((op&0xE7u)==0xC2u) { uint16_t dst=(uint16_t)(read8(m,pc+1)|((uint16_t)read8(m,pc+2)<<8)); m->pc=condition_true(m,(op>>3)&3u)?dst:(uint16_t)(pc+3); }
    else if (op==0xC3) m->pc=(uint16_t)(read8(m,pc+1)|((uint16_t)read8(m,pc+2)<<8));
    else if ((op&0xE7u)==0xC4u || op==0xCD) {
        uint16_t dst=(uint16_t)(read8(m,pc+1)|((uint16_t)read8(m,pc+2)<<8)); int take=op==0xCD||condition_true(m,(op>>3)&3u);
        if(take){ push16(m,(uint16_t)(pc+3),32,40); m->pc=dst; } else m->pc=(uint16_t)(pc+3);
    } else if ((op&0xE7u)==0xC0u || op==0xC9 || op==0xD9) {
        int take=op==0xC9||op==0xD9||condition_true(m,(op>>3)&3u);
        if(take){ m->pc=pop16(m,16,24); } else m->pc=(uint16_t)(pc+1);
    } else if ((op&0xCFu)==0xC1u) { set_stack_pair(m,(op>>4)&3u,pop16(m,8,16)); m->pc=(uint16_t)(pc+1); }
    else if ((op&0xCFu)==0xC5u) { push16(m,stack_pair(m,(op>>4)&3u),16,24); m->pc=(uint16_t)(pc+1); }
    else if ((op&0xC7u)==0xC6u) { uint8_t value=read8(m,pc+1); alu(m,(op>>3)&7u,value); m->pc=(uint16_t)(pc+2); }
    else if ((op&0xC7u)==0xC7u) { push16(m,(uint16_t)(pc+1),16,24); m->pc=(uint16_t)(op&0x38u); }
    else {
        switch(op) {
            case 0x00: m->pc++; break;
            case 0x02: bus_write(m,pair_value(m,0),m->a,8); m->pc++; break;
            case 0x0A: m->a=bus_read(m,pair_value(m,0),8); m->pc++; break;
            case 0x12: bus_write(m,pair_value(m,1),m->a,8); m->pc++; break;
            case 0x1A: m->a=bus_read(m,pair_value(m,1),8); m->pc++; break;
            case 0x22: bus_write(m,hl(m),m->a,8); set_hl(m,(uint16_t)(hl(m)+1)); m->pc++; break;
            case 0x2A: m->a=bus_read(m,hl(m),8); set_hl(m,(uint16_t)(hl(m)+1)); m->pc++; break;
            case 0x32: bus_write(m,hl(m),m->a,8); set_hl(m,(uint16_t)(hl(m)-1)); m->pc++; break;
            case 0x3A: m->a=bus_read(m,hl(m),8); set_hl(m,(uint16_t)(hl(m)-1)); m->pc++; break;
            case 0x08: { uint16_t addr=(uint16_t)(read8(m,pc+1)|((uint16_t)read8(m,pc+2)<<8)); bus_write(m,addr,(uint8_t)m->sp,24); bus_write(m,(uint16_t)(addr+1),(uint8_t)(m->sp>>8),32); m->pc+=3; break; }
            case 0x10: m->pc=(uint16_t)(pc+2); break;
            case 0x07: { uint8_t c=(uint8_t)(m->a>>7); m->a=(uint8_t)((m->a<<1)|c); m->f=c?0x10:0; m->pc++; break; }
            case 0x0F: { uint8_t c=(uint8_t)(m->a&1); m->a=(uint8_t)((m->a>>1)|(c<<7)); m->f=c?0x10:0; m->pc++; break; }
            case 0x17: { uint8_t c=(uint8_t)(m->a>>7), old=(uint8_t)((m->f>>4)&1); m->a=(uint8_t)((m->a<<1)|old); m->f=c?0x10:0; m->pc++; break; }
            case 0x1F: { uint8_t c=(uint8_t)(m->a&1), old=(uint8_t)((m->f>>4)&1); m->a=(uint8_t)((m->a>>1)|(old<<7)); m->f=c?0x10:0; m->pc++; break; }
            case 0x27: { uint8_t correction=0; int carry=(m->f&0x10u)!=0; if((m->f&0x40u)==0){if((m->f&0x20u)||(m->a&15u)>9) correction|=6; if(carry||m->a>0x99){correction|=0x60;carry=1;} m->a=(uint8_t)(m->a+correction);}else{if(m->f&0x20u)correction|=6;if(carry)correction|=0x60;m->a=(uint8_t)(m->a-correction);} m->f=(uint8_t)((m->f&0x40u)|(m->a==0?0x80u:0)|(carry?0x10u:0));m->pc++;break; }
            case 0x2F: m->a=(uint8_t)~m->a; m->f=(uint8_t)((m->f&0x90u)|0x60u); m->pc++; break;
            case 0x37: m->f=(uint8_t)((m->f&0x80u)|0x10u); m->pc++; break;
            case 0x3F: m->f=(uint8_t)((m->f&0x80u)|((m->f&0x10u)?0:0x10u)); m->pc++; break;
            case 0xE0: bus_write(m,(uint16_t)(0xFF00u+read8(m,pc+1)),m->a,16); m->pc+=2; break;
            case 0xE2: bus_write(m,(uint16_t)(0xFF00u+m->c),m->a,8); m->pc++; break;
            case 0xF0: m->a=bus_read(m,(uint16_t)(0xFF00u+read8(m,pc+1)),16); m->pc+=2; break;
            case 0xF2: m->a=bus_read(m,(uint16_t)(0xFF00u+m->c),8); m->pc++; break;
            case 0xEA: { uint16_t addr=(uint16_t)(read8(m,pc+1)|((uint16_t)read8(m,pc+2)<<8)); bus_write(m,addr,m->a,24); m->pc+=3; break; }
            case 0xFA: { uint16_t addr=(uint16_t)(read8(m,pc+1)|((uint16_t)read8(m,pc+2)<<8)); m->a=bus_read(m,addr,24); m->pc+=3; break; }
            case 0xE8: case 0xF8: { uint8_t e=read8(m,pc+1); uint16_t old=m->sp; uint16_t value=(uint16_t)(old+(int8_t)e); uint8_t flags=(uint8_t)(((old&15u)+(e&15u)>15u?0x20u:0)|((old&255u)+e>255u?0x10u:0)); if(op==0xE8)m->sp=value;else set_hl(m,value);m->f=flags;m->pc+=2;break; }
            case 0xF9: m->sp=hl(m); m->pc++; break;
            case 0xE9: m->pc=hl(m); break;
            case 0xF3: case 0xFB: m->pc++; break; /* Interrupt-enable sequencing is owned by the control-state plan. */
            case 0xCB: {
                uint8_t extension = read8(m, (uint16_t)(pc + 1u));
                execute_cb(m, pc, extension);
                break;
            }
            default: m->pc=(uint16_t)(pc+1); break;
        }
    }
    m->f &= 0xF0u;
    m->time_half_dots += cost;
}

static void save_trace(const gbb_instance *m, decoded d, gbb_trace_record *r) {
    memset(r, 0, sizeof(*r));
    r->time_half_dots = m->time_half_dots; r->pc = m->pc; r->opcode_size = d.size;
    for (uint8_t i = 0; i < d.size && i < 3; ++i) r->opcode[i] = read8(m, (uint16_t)(m->pc + i));
    r->a=m->a; r->f=m->f; r->b=m->b; r->c=m->c; r->d=m->d; r->e=m->e; r->h=m->h; r->l=m->l; r->sp=m->sp;
}

gbb_run_result gbb_run(gbb_instance *instance, uint64_t budget_half_dots,
                       gbb_trace_record *trace, size_t trace_capacity) {
    gbb_run_result result={0, GBB_STOP_BUDGET, 0, 0, 0};
    if (instance == NULL || !instance->loaded || (trace == NULL && trace_capacity != 0)) { result.reason=GBB_STOP_INVALID_STATE; return result; }
    while (result.consumed_half_dots < budget_half_dots) {
        if (instance->locked) { result.reason=GBB_STOP_LOCKUP; result.lockup_pc=instance->lockup_pc; result.lockup_opcode=instance->lockup_opcode; return result; }
        decoded d=decode(instance);
        if (!d.supported) {
            instance->locked=1; instance->lockup_pc=instance->pc; instance->lockup_opcode=read8(instance,instance->pc);
            result.reason=GBB_STOP_LOCKUP; result.lockup_pc=instance->lockup_pc; result.lockup_opcode=instance->lockup_opcode; return result;
        }
        uint8_t opcode = read8(instance, instance->pc);
        if (opcode == 0x7E && !read_supported(hl(instance))) {
            result.reason = GBB_STOP_UNSUPPORTED_BUS;
            return result;
        }
        uint8_t cost=instruction_cost(instance,d);
        if (cost > budget_half_dots-result.consumed_half_dots) return result;
        if (UINT64_MAX - instance->time_half_dots < cost) {
            result.reason = GBB_STOP_INVALID_STATE;
            return result;
        }
        if (trace != NULL && result.trace_count == trace_capacity) { result.reason=GBB_STOP_TRACE_FULL; return result; }
        if (trace != NULL) save_trace(instance,d,&trace[result.trace_count++]);
        execute(instance,cost);
        result.consumed_half_dots += cost;
    }
    return result;
}

uint8_t gbb_peek_ram(const gbb_instance *instance, uint16_t address) {
    if (instance == NULL) return 0xFF;
    if (address >= 0xC000 && address <= 0xDFFF) return instance->wram[address - 0xC000];
    if (address >= 0xE000 && address <= 0xFDFF) return instance->wram[address - 0xE000];
    if (address >= 0xFF80 && address <= 0xFFFE) return instance->hram[address - 0xFF80];
    return 0xFF;
}
