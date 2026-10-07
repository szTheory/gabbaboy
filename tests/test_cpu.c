#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

static const char *active_case = "unknown";
#define REQUIRE(x) do { if (!(x)) { \
    printf("TAP version 13\n1..1\nnot ok 1 - cpu_%s\n  ---\n  message: \"assertion failed at %s:%d\"\n  ...\n", active_case, __FILE__, __LINE__); \
    return 1; \
} } while (0)

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;
extern void gbb_test_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_observer_count(const gbb_instance *);
extern void gbb_test_cpu_snapshot(const gbb_instance *, gbb_trace_record *);

static void make_rom(uint8_t rom[32768], const uint8_t *program, size_t size) {
    memset(rom, 0, 32768);
    memcpy(rom + 0x100, program, size);
    /* Generic CPU cases use checksum zero so their independent F=80 setup stays stable. */
    rom[0x134] = 0xe7;
    rom[0x14d] = 0;
}

static int call_stack(void) {
    uint8_t rom[32768];
    const uint8_t start[] = {0xcc, 0x50, 0x01, 0x00}; /* CALL Z,$0150; NOP */
    make_rom(rom, start, sizeof(start));
    rom[0x150] = 0xc9; /* RET */
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_trace_record trace[4] = {{0}};
    gbb_test_bus_event events[8] = {{0}};
    gbb_test_observer_set(m, events, 8);
    gbb_run_result r = gbb_run(m, 80, trace, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET);
    REQUIRE(r.consumed_half_dots == 80);
    REQUIRE(r.trace_count == 2);
    REQUIRE(trace[0].pc == 0x100 && trace[1].pc == 0x150);
    REQUIRE(gbb_peek_ram(m, 0xfffd) == 0x01);
    REQUIRE(gbb_peek_ram(m, 0xfffc) == 0x03);
    REQUIRE(gbb_test_observer_count(m) >= 4);
    REQUIRE(events[0].time_half_dots == 32 && events[0].address == 0xfffd && events[0].access == 2 && events[0].value == 0x01);
    REQUIRE(events[1].time_half_dots == 40 && events[1].address == 0xfffc && events[1].access == 2 && events[1].value == 0x03);
    REQUIRE(events[2].time_half_dots == 56 && events[2].address == 0xfffc && events[2].access == 1 && events[2].value == 0x03);
    REQUIRE(events[3].time_half_dots == 64 && events[3].address == 0xfffd && events[3].access == 1 && events[3].value == 0x01);
    gbb_destroy(m);
    return 0;
}

static int conditional_budget(void) {
    uint8_t rom[32768];
    const uint8_t start[] = {0xc4, 0x50, 0x01}; /* CALL NZ,$0150; Z is set in post-boot state */
    make_rom(rom, start, sizeof(start));
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_trace_record trace[2] = {{0}};
    gbb_run_result r = gbb_run(m, 23, trace, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0);
    REQUIRE(r.trace_count == 0);
    REQUIRE(gbb_peek_ram(m, 0xfffc) == 0 && gbb_peek_ram(m, 0xfffd) == 0);
    gbb_destroy(m);
    return 0;
}

static int expected_condition(unsigned condition) {
    /* The generated ROM starts from F=80: NZ=false, Z=true, NC=true, C=false. */
    return condition == 1 || condition == 2;
}

static unsigned expected_first_cost(unsigned op) {
    if ((op & 0xc7u) == 0x06u) return ((op >> 3) & 7u) == 6u ? 24u : 16u;
    if ((op & 0xcfu) == 0x01u) return 24;
    if ((op & 0xcfu) == 0x03u || (op & 0xcfu) == 0x0bu || (op & 0xcfu) == 0x09u) return 16;
    if ((op & 0xc7u) == 0x04u || (op & 0xc7u) == 0x05u) return ((op >> 3) & 7u) == 6u ? 24u : 8u;
    if (op >= 0x40 && op <= 0x7f) return op == 0x76 || ((op & 7u) != 6u && ((op >> 3) & 7u) != 6u) ? 8u : 16u;
    if (op >= 0x80 && op <= 0xbf) return (op & 7u) == 6u ? 16u : 8u;
    if ((op & 0xe7u) == 0x20u) return expected_condition((op >> 3) & 3u) ? 24u : 16u;
    if ((op & 0xe7u) == 0xc0u) return expected_condition((op >> 3) & 3u) ? 40u : 16u;
    if ((op & 0xe7u) == 0xc2u) return expected_condition((op >> 3) & 3u) ? 32u : 24u;
    if ((op & 0xe7u) == 0xc4u) return expected_condition((op >> 3) & 3u) ? 48u : 24u;
    if ((op & 0xcfu) == 0xc1u) return 24;
    if ((op & 0xcfu) == 0xc5u) return 32;
    if ((op & 0xc7u) == 0xc6u) return 16;
    if ((op & 0xc7u) == 0xc7u) return 32;
    switch (op) {
        case 0x08: return 40;
        case 0x10: case 0x18: case 0xe0: case 0xf0: return op == 0x18 ? 24u : op == 0x10 ? 8u : 24u;
        case 0x02: case 0x0a: case 0x12: case 0x1a: case 0x22: case 0x2a: case 0x32: case 0x3a: return 16;
        case 0xc3: return 32;
        case 0xc9: case 0xd9: return 32;
        case 0xcd: return 48;
        case 0xe2: case 0xf2: case 0xf9: return 16;
        case 0xe8: return 48;
        case 0xe9: case 0xf3: case 0xfb: return 8;
        case 0xea: case 0xfa: return 32;
        case 0xf8: return 24;
        case 0xcb: return 16;
        default: return 8;
    }
}

static uint16_t expected_first_pc(unsigned op) {
    if ((op & 0xe7u) == 0x20u || op == 0x18) return 0x0102;
    if (op == 0xc3) return 0x0100;
    if ((op & 0xe7u) == 0xc2u) return expected_condition((op >> 3) & 3u) ? 0x0100 : 0x0103;
    if (op == 0xcd) return 0x0100;
    if ((op & 0xe7u) == 0xc4u) return expected_condition((op >> 3) & 3u) ? 0x0100 : 0x0103;
    if (op == 0xc9 || op == 0xd9) return 0xe000; /* FFFF is IE and reads back with unused bits high. */
    if ((op & 0xe7u) == 0xc0u) return expected_condition((op >> 3) & 3u) ? 0xe000 : 0x0101;
    if ((op & 0xc7u) == 0xc7u) return (uint16_t)(op & 0x38u);
    if (op == 0xe9) return 0x014d;
    if (op == 0x10 || op == 0x18 || (op & 0xe7u) == 0x20u ||
        (op & 0xc7u) == 0x06u || (op & 0xc7u) == 0xc6u ||
        op == 0xe0 || op == 0xe8 || op == 0xf0 || op == 0xf8)
        return 0x0102;
    if ((op & 0xcfu) == 0x01u || op == 0x08 || op == 0xea || op == 0xfa ||
        (op & 0xe7u) == 0xc2u || (op & 0xe7u) == 0xc4u) return 0x0103;
    if (op == 0xcb) return 0x0102;
    return 0x0101;
}

typedef struct {
    uint8_t a, f, b, c, d, e, h, l;
    uint16_t sp, pc;
} base_expected_state;

static uint16_t expected_pair(const base_expected_state *s, unsigned pair) {
    switch (pair) {
        case 0: return (uint16_t)(((uint16_t)s->b << 8) | s->c);
        case 1: return (uint16_t)(((uint16_t)s->d << 8) | s->e);
        case 2: return (uint16_t)(((uint16_t)s->h << 8) | s->l);
        default: return s->sp;
    }
}

static void expected_set_pair(base_expected_state *s, unsigned pair, uint16_t value) {
    switch (pair) {
        case 0: s->b=(uint8_t)(value>>8); s->c=(uint8_t)value; break;
        case 1: s->d=(uint8_t)(value>>8); s->e=(uint8_t)value; break;
        case 2: s->h=(uint8_t)(value>>8); s->l=(uint8_t)value; break;
        default: s->sp=value; break;
    }
}

static uint8_t expected_register(const base_expected_state *s, unsigned reg) {
    switch (reg) {
        case 0: return s->b;
        case 1: return s->c;
        case 2: return s->d;
        case 3: return s->e;
        case 4: return s->h;
        case 5: return s->l;
        case 7: return s->a;
        default: return 0; /* (HL) points at the test ROM checksum byte, fixed to zero. */
    }
}

static void expected_set_register(base_expected_state *s, unsigned reg, uint8_t value) {
    switch (reg) {
        case 0: s->b=value; break;
        case 1: s->c=value; break;
        case 2: s->d=value; break;
        case 3: s->e=value; break;
        case 4: s->h=value; break;
        case 5: s->l=value; break;
        case 7: s->a=value; break;
        default: break; /* (HL) is in ROM in the one-encoding matrix. */
    }
}

static void expected_inc8(base_expected_state *s, unsigned reg, int decrement) {
    uint8_t before=expected_register(s,reg);
    uint8_t after=(uint8_t)(before+(decrement?-1:1));
    uint8_t flags=(uint8_t)(s->f&0x10u);
    if (after==0) flags|=0x80u;
    if (decrement) {
        flags|=0x40u;
        if ((before&0x0fu)==0) flags|=0x20u;
    } else if ((before&0x0fu)==0x0fu) flags|=0x20u;
    s->f=flags;
    expected_set_register(s,reg,after);
}

static void expected_alu(base_expected_state *s, unsigned group, uint8_t operand) {
    unsigned carry=(s->f&0x10u)!=0;
    unsigned result=0;
    uint8_t flags=0;
    switch (group) {
        case 0: case 1: { /* ADD / ADC */
            unsigned add_carry=group==1?carry:0;
            result=(unsigned)s->a+operand+add_carry;
            if ((result&0xffu)==0) flags|=0x80u;
            if (((s->a&0x0fu)+(operand&0x0fu)+add_carry)>0x0fu) flags|=0x20u;
            if (result>0xffu) flags|=0x10u;
            s->a=(uint8_t)result;
            break;
        }
        case 2: case 3: case 7: { /* SUB / SBC / CP */
            unsigned sub_carry=group==3?carry:0;
            unsigned rhs=(unsigned)operand+sub_carry;
            uint8_t difference=(uint8_t)((unsigned)s->a-rhs);
            flags=0x40u;
            if (difference==0) flags|=0x80u;
            if ((s->a&0x0fu)<((operand&0x0fu)+sub_carry)) flags|=0x20u;
            if ((unsigned)s->a<rhs) flags|=0x10u;
            if (group!=7) s->a=difference;
            break;
        }
        case 4: s->a=(uint8_t)(s->a&operand); flags=0x20u; if(s->a==0)flags|=0x80u; break;
        case 5: s->a=(uint8_t)(s->a^operand); if(s->a==0)flags=0x80u; break;
        default: s->a=(uint8_t)(s->a|operand); if(s->a==0)flags=0x80u; break;
    }
    s->f=flags;
}

static base_expected_state expected_base_state(unsigned op, int f2_prefetched) {
    base_expected_state s={1,0x80,0,0x13,0,0xd8,1,0x4d,0xfffe,0};
    s.pc=(uint16_t)(expected_first_pc(op)+(f2_prefetched?2u:0u));
    if (f2_prefetched) s.c=0x80;

    if ((op&0xcfu)==0x01u) { expected_set_pair(&s,(op>>4)&3u,0x0100); return s; }
    if ((op&0xcfu)==0x03u) { unsigned p=(op>>4)&3u; expected_set_pair(&s,p,(uint16_t)(expected_pair(&s,p)+1u)); return s; }
    if ((op&0xcfu)==0x0bu) { unsigned p=(op>>4)&3u; expected_set_pair(&s,p,(uint16_t)(expected_pair(&s,p)-1u)); return s; }
    if ((op&0xcfu)==0x09u) {
        uint16_t hl=expected_pair(&s,2), rhs=expected_pair(&s,(op>>4)&3u);
        uint32_t sum=(uint32_t)hl+rhs;
        s.f=(uint8_t)((s.f&0x80u)|(((hl&0x0fffu)+(rhs&0x0fffu)>0x0fffu)?0x20u:0u)|(sum>0xffffu?0x10u:0u));
        expected_set_pair(&s,2,(uint16_t)sum);
        return s;
    }
    if ((op&0xc7u)==0x04u) { expected_inc8(&s,(op>>3)&7u,0); return s; }
    if ((op&0xc7u)==0x05u) { expected_inc8(&s,(op>>3)&7u,1); return s; }
    if ((op&0xc7u)==0x06u) { expected_set_register(&s,(op>>3)&7u,0); return s; }

    if (op>=0x40u && op<=0x7fu) {
        if (op!=0x76u) expected_set_register(&s,(op>>3)&7u,expected_register(&s,op&7u));
        return s;
    }
    if (op>=0x80u && op<=0xbfu) { expected_alu(&s,(op>>3)&7u,expected_register(&s,op&7u)); return s; }
    if ((op&0xc7u)==0xc6u) { expected_alu(&s,(op>>3)&7u,0); return s; }

    if ((op&0xe7u)==0xc0u) {
        if (expected_condition((op>>3)&3u)) s.sp=0;
        return s;
    }
    if ((op&0xcfu)==0xc1u) {
        unsigned p=(op>>4)&3u;
        if (p==3u) { s.a=0xe0; s.f=0; }
        else expected_set_pair(&s,p,0xe000);
        s.sp=0;
        return s;
    }
    if ((op&0xe7u)==0xc2u) return s;
    if (op==0xc3u) return s;
    if ((op&0xe7u)==0xc4u) { if(expected_condition((op>>3)&3u))s.sp=0xfffc; return s; }
    if (op==0xcdu) { s.sp=0xfffc; return s; }
    if ((op&0xcfu)==0xc5u) { s.sp=0xfffc; return s; }
    if ((op&0xc7u)==0xc7u) { s.sp=0xfffc; return s; }
    if (op==0xc9u || op==0xd9u) { s.sp=0; return s; }
    if (op==0xcbu) { /* The one-byte matrix uses CB 00: RLC B, with B=0. */ s.f=0x80; return s; }

    switch (op) {
        case 0x07: s.a=2; s.f=0; break;                         /* RLCA */
        case 0x08: break;                                       /* LD (a16),SP to ROM */
        case 0x0a: s.a=0; break;                                /* LD A,(BC), ROM byte 0013 */
        case 0x0f: s.a=0x80; s.f=0x10; break;                   /* RRCA */
        case 0x10: break;                                       /* STOP: checked as a stop outcome */
        case 0x12: break;                                       /* LD (DE),A to ROM */
        case 0x17: s.a=2; s.f=0; break;                         /* RLA */
        case 0x27: s.f=0; break;                                /* DAA: A=01 has no correction; Z/N/H/C clear. */
        case 0x18: break;                                       /* JR 0 */
        case 0x1a: s.a=0; break;                                /* LD A,(DE), ROM byte 00D8 */
        case 0x1f: s.a=0; s.f=0x10; break;                     /* RRA */
        case 0x22: s.l=0x4e; break;                             /* LDI (HL),A */
        case 0x2a: s.a=0; s.l=0x4e; break;                      /* LDI A,(HL) */
        case 0x2f: s.a=0xfe; s.f=0xe0; break;                   /* CPL */
        case 0x32: s.l=0x4c; break;                             /* LDD (HL),A */
        case 0x34: s.f=0; break;                                /* INC (HL), ROM value 00 */
        case 0x35: s.f=0x60; break;                             /* DEC (HL), ROM value 00 */
        case 0x36: break;                                       /* LD (HL),00 to ROM */
        case 0x37: s.f=0x90; break;                             /* SCF */
        case 0x3a: s.a=0; s.l=0x4c; break;                      /* LDD A,(HL) */
        case 0x3f: s.f=0x90; break;                             /* CCF */
        case 0xe0: case 0xe2: case 0xea: break;                 /* stores */
        case 0xe6: expected_alu(&s,4,0); break;
        case 0xe8: s.f=0; break;                                /* ADD SP,00 */
        case 0xe9: s.pc=0x014d; break;                           /* JP HL */
        case 0xee: expected_alu(&s,5,0); break;
        case 0xf0: s.a=0; break;                                /* LDH A,($FF80), initialized HRAM */
        case 0xf2: s.a=0; break;                                /* LDH A,(C): C preloaded to $80 */
        case 0xf6: expected_alu(&s,6,0); break;
        case 0xf8: s.h=0xff; s.l=0xfe; s.f=0; break;             /* LD HL,SP+00 */
        case 0xf9: s.sp=0x014d; break;                           /* LD SP,HL */
        case 0xfa: s.a=0xfa; break;                              /* LD A,(0100), opcode byte */
        case 0xfe: expected_alu(&s,7,0); break;
        default: break;
    }
    return s;
}

static int trace_matches_expected(const gbb_trace_record *actual, const base_expected_state *expected) {
    return actual->a==expected->a && actual->f==expected->f &&
        actual->b==expected->b && actual->c==expected->c &&
        actual->d==expected->d && actual->e==expected->e &&
        actual->h==expected->h && actual->l==expected->l &&
        actual->sp==expected->sp && actual->pc==expected->pc;
}

static int base_matrix(void) {
    static const uint8_t holes[] = {0xd3,0xdb,0xdd,0xe3,0xe4,0xeb,0xec,0xed,0xf4,0xfc,0xfd};
    uint8_t rom[32768];
    for (unsigned op = 0; op < 256; ++op) {
        uint8_t program[] = {(uint8_t)op,0x00,0x01,0x00};
        /* This legal decode/timing matrix uses initialized HRAM for high-memory
         * reads; timer/device register semantics have dedicated tests. */
        if (op == 0xf0) program[1] = 0x80;
        make_rom(rom,program,sizeof(program));
        if (op == 0xf2) {
            const uint8_t indexed[] = {0x0e,0x80,0xf2,0x00};
            make_rom(rom, indexed, sizeof(indexed));
        }
        gbb_instance *m=NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK);
        REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
        if (op == 0xf2) REQUIRE(gbb_run(m,16,NULL,0).consumed_half_dots==16);
        gbb_trace_record trace[16]={{0}};
        gbb_run_result r=gbb_run(m,96,trace,16);
        int illegal=0; for(size_t i=0;i<sizeof(holes);++i) if(holes[i]==op) illegal=1;
        if(illegal) REQUIRE(r.reason==GBB_STOP_LOCKUP && r.lockup_pc==0x100 && r.lockup_opcode==op);
        else if (op == 0x76) {
            REQUIRE(r.reason == GBB_STOP_HALTED_IDLE && r.consumed_half_dots == 8);
            REQUIRE(r.trace_count == 1 && trace[0].pc == 0x0100);
        } else if (op == 0x10) {
            REQUIRE(r.reason == GBB_STOP_STOPPED && r.consumed_half_dots == 8);
            REQUIRE(r.trace_count == 1 && trace[0].pc == 0x0100);
        } else {
            if (r.reason != GBB_STOP_BUDGET) fprintf(stderr, "opcode %02x stopped with reason %u after %llu half-dots\n", op, (unsigned)r.reason, (unsigned long long)r.consumed_half_dots);
            REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots>0);
            REQUIRE(r.trace_count>=2);
            REQUIRE(trace[1].time_half_dots==expected_first_cost(op)+(op==0xf2?16u:0u));
            uint16_t expected_pc=(uint16_t)(expected_first_pc(op)+(op==0xf2?2u:0u));
            if (trace[1].pc != expected_pc) fprintf(stderr, "opcode %02x PC got %04x expected %04x\n", op, trace[1].pc, expected_pc);
            REQUIRE(trace[1].pc==expected_pc);
            REQUIRE((trace[1].f&0x0f)==0);
            base_expected_state expected=expected_base_state(op,op==0xf2);
            if (!trace_matches_expected(&trace[1],&expected)) {
                fprintf(stderr,"opcode %02x state got A=%02x F=%02x BC=%02x%02x DE=%02x%02x HL=%02x%02x SP=%04x PC=%04x; expected A=%02x F=%02x BC=%02x%02x DE=%02x%02x HL=%02x%02x SP=%04x PC=%04x\n",
                    op,trace[1].a,trace[1].f,trace[1].b,trace[1].c,trace[1].d,trace[1].e,trace[1].h,trace[1].l,trace[1].sp,trace[1].pc,
                    expected.a,expected.f,expected.b,expected.c,expected.d,expected.e,expected.h,expected.l,expected.sp,expected.pc);
            }
            REQUIRE(trace_matches_expected(&trace[1],&expected));
        }
        gbb_destroy(m);
    }
    return 0;
}

static int illegal_lockup(void) {
    uint8_t rom[32768]; const uint8_t program[]={0xd3,0x00}; make_rom(rom,program,sizeof(program));
    gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
    gbb_run_result first=gbb_run(m,100,NULL,0);
    REQUIRE(first.reason==GBB_STOP_LOCKUP && first.consumed_half_dots==0 && first.lockup_pc==0x100 && first.lockup_opcode==0xd3);
    gbb_run_result again=gbb_run(m,100,NULL,0);
    REQUIRE(again.reason==GBB_STOP_LOCKUP && again.consumed_half_dots==0 && again.lockup_pc==first.lockup_pc && again.lockup_opcode==first.lockup_opcode);
    REQUIRE(gbb_reset(m)==GBB_OK);
    gbb_run_result reset=gbb_run(m,8,NULL,0);
    REQUIRE(reset.reason==GBB_STOP_LOCKUP && reset.lockup_pc==0x100);
    gbb_destroy(m); return 0;
}

static int flags_edges(void) {
    uint8_t rom[32768]; const uint8_t program[]={0x3e,0x0f,0xc6,0x01,0x00}; make_rom(rom,program,sizeof(program));
    gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
    gbb_trace_record trace[3]={{0}}; gbb_run_result r=gbb_run(m,40,trace,3);
    REQUIRE(r.consumed_half_dots==40 && r.trace_count==3);
    REQUIRE(trace[2].a==0x10 && trace[2].f==0x20 && (trace[2].f&0x0f)==0);
    gbb_destroy(m); return 0;
}

static int base_semantic_tracer(void) {
    uint8_t rom[32768];
    const uint8_t program[]={
        0x3e,0xff, 0xc6,0x01, /* A=FF; ADD A,1 -> A=00, Z/H/C */
        0x3e,0x00, 0xd6,0x01, /* A=00; SUB 1 -> A=FF, N/H/C */
        0x3e,0x00, 0xfe,0x00, /* A=00; CP 0 -> A stays 00, Z/N */
        0x00
    };
    make_rom(rom,program,sizeof(program));
    gbb_instance *m=NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK);
    REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
    gbb_trace_record trace[8]={{0}};
    gbb_run_result r=gbb_run(m,104,trace,8);
    REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==104 && r.trace_count==7);
    REQUIRE(trace[2].pc==0x0104 && trace[2].time_half_dots==32);
    REQUIRE(trace[2].a==0x00 && trace[2].f==0xb0 && (trace[2].f&0x0f)==0);
    REQUIRE(trace[4].pc==0x0108 && trace[4].time_half_dots==64);
    REQUIRE(trace[4].a==0xff && trace[4].f==0x70 && (trace[4].f&0x0f)==0);
    REQUIRE(trace[6].pc==0x010c && trace[6].time_half_dots==96);
    REQUIRE(trace[6].a==0x00 && trace[6].f==0xc0 && (trace[6].f&0x0f)==0);
    gbb_destroy(m);
    return 0;
}

enum { BRANCH_JR, BRANCH_JP, BRANCH_CALL, BRANCH_RET };

static unsigned conditional_branch_cost(unsigned family, int taken) {
    switch (family) {
        case BRANCH_JR: return taken ? 24u : 16u;
        case BRANCH_JP: return taken ? 32u : 24u;
        case BRANCH_CALL: return taken ? 48u : 24u;
        default: return taken ? 40u : 16u;
    }
}

static int check_conditional_branch(unsigned family, unsigned condition, int taken) {
    uint8_t rom[32768], program[16] = {0};
    size_t length = 0;
    uint64_t setup_time = 0;
    uint8_t expected_flags;
    if (condition < 2u) {
        int want_zero = condition == 1u ? taken : !taken;
        program[length++] = 0x3e; program[length++] = want_zero ? 0x00 : 0x01;
        program[length++] = 0xfe; program[length++] = 0x00;
        setup_time = 32;
        expected_flags = want_zero ? 0xc0 : 0x40; /* CP sets N; C/H remain clear. */
    } else if ((condition == 3u) == (unsigned)taken) {
        program[length++] = 0x37; /* SCF preserves post-boot Z and sets C. */
        setup_time = 8;
        expected_flags = 0x90;
    } else {
        expected_flags = 0x80; /* post-boot Z=1, C=0 */
    }

    uint16_t branch_pc = (uint16_t)(0x0100u + length);
    uint8_t opcode;
    switch (family) {
        case BRANCH_JR: opcode = (uint8_t)(0x20u + condition * 8u); break;
        case BRANCH_JP: opcode = (uint8_t)(0xc2u + condition * 8u); break;
        case BRANCH_CALL: opcode = (uint8_t)(0xc4u + condition * 8u); break;
        default: opcode = (uint8_t)(0xc0u + condition * 8u); break;
    }
    program[length++] = opcode;
    if (family == BRANCH_JR) program[length++] = 0x02;
    if (family == BRANCH_JP || family == BRANCH_CALL) {
        program[length++] = 0x50;
        program[length++] = 0x01;
    }
    program[length++] = 0x00; /* fall-through instruction */
    make_rom(rom, program, length);

    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    if (setup_time != 0) {
        gbb_run_result setup = gbb_run(m, setup_time, NULL, 0);
        REQUIRE(setup.reason == GBB_STOP_BUDGET && setup.consumed_half_dots == setup_time);
    }

    gbb_test_bus_event events[4] = {{0}};
    gbb_test_observer_set(m, events, 4);
    gbb_trace_record trace[2] = {{0}};
    unsigned cost = conditional_branch_cost(family, taken);
    gbb_run_result r = gbb_run(m, cost + 8u, trace, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == cost + 8u && r.trace_count == 2);
    if (trace[0].pc != branch_pc || trace[0].time_half_dots != setup_time || trace[0].f != expected_flags)
        fprintf(stderr,"branch setup family=%u condition=%u taken=%d got PC=%04x time=%llu F=%02x expected PC=%04x time=%llu F=%02x\n",
            family,condition,taken,trace[0].pc,(unsigned long long)trace[0].time_half_dots,trace[0].f,
            branch_pc,(unsigned long long)setup_time,expected_flags);
    REQUIRE(trace[0].pc == branch_pc && trace[0].time_half_dots == setup_time && trace[0].f == expected_flags);
    REQUIRE(trace[1].time_half_dots == setup_time + cost && trace[1].f == expected_flags);

    uint16_t expected_pc;
    if (!taken) expected_pc = (uint16_t)(branch_pc + (family == BRANCH_JR ? 2u : family == BRANCH_JP || family == BRANCH_CALL ? 3u : 1u));
    else if (family == BRANCH_JR) expected_pc = (uint16_t)(branch_pc + 4u);
    else if (family == BRANCH_JP || family == BRANCH_CALL) expected_pc = 0x0150;
    else expected_pc = 0xe000;
    REQUIRE(trace[1].pc == expected_pc);
    REQUIRE(trace[1].sp == (family == BRANCH_CALL && taken ? 0xfffcu : family == BRANCH_RET && taken ? 0u : 0xfffeu));

    if (family == BRANCH_CALL && taken) {
        uint16_t return_pc = (uint16_t)(branch_pc + 3u);
        REQUIRE(gbb_test_observer_count(m) == 2);
        REQUIRE(events[0].time_half_dots == setup_time + 32u && events[0].address == 0xfffd && events[0].access == 2 && events[0].value == (uint8_t)(return_pc >> 8));
        REQUIRE(events[1].time_half_dots == setup_time + 40u && events[1].address == 0xfffc && events[1].access == 2 && events[1].value == (uint8_t)return_pc);
    } else if (family == BRANCH_RET && taken) {
        REQUIRE(gbb_test_observer_count(m) == 2);
        REQUIRE(events[0].time_half_dots == setup_time + 16u && events[0].address == 0xfffe && events[0].access == 1 && events[0].value == 0x00);
        REQUIRE(events[1].time_half_dots == setup_time + 24u && events[1].address == 0xffff && events[1].access == 1 && events[1].value == 0xe0);
    } else {
        REQUIRE(gbb_test_observer_count(m) == 0);
    }
    if (family == BRANCH_CALL && taken) {
        REQUIRE(gbb_peek_ram(m, 0xfffc) == (uint8_t)(branch_pc + 3u));
        REQUIRE(gbb_peek_ram(m, 0xfffd) == (uint8_t)((branch_pc + 3u) >> 8));
    }
    gbb_destroy(m);
    return 0;
}

static int base_conditional_paths(void) {
    for (unsigned family = BRANCH_JR; family <= BRANCH_RET; ++family)
        for (unsigned condition = 0; condition < 4u; ++condition)
            for (unsigned taken = 0; taken < 2u; ++taken)
                REQUIRE(check_conditional_branch(family, condition, (int)taken) == 0);
    return 0;
}

static int check_base_vector(const uint8_t *program, size_t program_size, uint64_t budget,
                             const base_expected_state *expected) {
    uint8_t rom[32768];
    make_rom(rom, program, program_size);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_trace_record trace[16] = {{0}};
    gbb_run_result r = gbb_run(m, budget, trace, 16);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == budget && r.trace_count >= 2);
    REQUIRE(trace[r.trace_count - 1u].time_half_dots == budget - 8u);
    if (!trace_matches_expected(&trace[r.trace_count - 1u], expected))
        fprintf(stderr,"semantic vector got A=%02x F=%02x BC=%02x%02x DE=%02x%02x HL=%02x%02x SP=%04x PC=%04x; expected A=%02x F=%02x BC=%02x%02x DE=%02x%02x HL=%02x%02x SP=%04x PC=%04x\n",
            trace[r.trace_count - 1u].a,trace[r.trace_count - 1u].f,trace[r.trace_count - 1u].b,trace[r.trace_count - 1u].c,
            trace[r.trace_count - 1u].d,trace[r.trace_count - 1u].e,trace[r.trace_count - 1u].h,trace[r.trace_count - 1u].l,
            trace[r.trace_count - 1u].sp,trace[r.trace_count - 1u].pc,
            expected->a,expected->f,expected->b,expected->c,expected->d,expected->e,expected->h,expected->l,expected->sp,expected->pc);
    REQUIRE(trace_matches_expected(&trace[r.trace_count - 1u], expected));
    REQUIRE((trace[r.trace_count - 1u].f & 0x0fu) == 0);
    gbb_destroy(m);
    return 0;
}

static int base_arithmetic_edges(void) {
    static const uint8_t adc_half[] = {0x3e,0x0f,0x37,0xce,0x00,0x00};
    static const uint8_t adc_carry[] = {0x3e,0xff,0x37,0xce,0x00,0x00};
    static const uint8_t sbc_borrow[] = {0x3e,0x00,0x37,0xde,0x00,0x00};
    static const uint8_t cp_borrow[] = {0x3e,0x00,0xfe,0x01,0x00};
    static const uint8_t daa_add[] = {0x3e,0x99,0xc6,0x01,0x27,0x00};
    static const uint8_t daa_sub[] = {0x3e,0x00,0xd6,0x01,0x27,0x00};
    static const uint8_t inc_dec_carry[] = {0x06,0x0f,0x37,0x04,0x05,0x00};
    static const uint8_t add_hl_half[] = {0x21,0xff,0x0f,0x11,0x01,0x00,0x19,0x00};
    static const uint8_t add_sp_positive[] = {0x31,0xfe,0xff,0xe8,0x01,0x00};
    static const uint8_t add_sp_negative[] = {0x31,0xfe,0xff,0xe8,0xff,0x00};
    static const uint8_t ld_hl_sp_positive[] = {0x31,0xff,0xff,0xf8,0x01,0x00};
    static const uint8_t ld_hl_sp_negative[] = {0x31,0xff,0xff,0xf8,0xff,0x00};
    static const uint8_t rlca_edge[] = {0x3e,0x80,0x07,0x00};
    static const uint8_t rrca_edge[] = {0x3e,0x01,0x0f,0x00};
    static const uint8_t rla_edge[] = {0x3e,0x80,0x37,0x17,0x00};
    static const uint8_t rra_edge[] = {0x3e,0x01,0x37,0x1f,0x00};
    const base_expected_state adc_half_expected = {0x10,0x20,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0105};
    const base_expected_state adc_carry_expected = {0x00,0xb0,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0105};
    const base_expected_state sbc_borrow_expected = {0xff,0x70,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0105};
    const base_expected_state cp_borrow_expected = {0x00,0x70,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0104};
    const base_expected_state daa_add_expected = {0x00,0x90,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0105};
    const base_expected_state daa_sub_expected = {0x99,0x50,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0105};
    const base_expected_state inc_dec_expected = {0x01,0x70,0x0f,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0105};
    const base_expected_state add_hl_expected = {0x01,0xa0,0x00,0x13,0x00,0x01,0x10,0x00,0xfffe,0x0107};
    const base_expected_state add_sp_pos_expected = {0x01,0x00,0x00,0x13,0x00,0xd8,0x01,0x4d,0xffff,0x0105};
    const base_expected_state add_sp_neg_expected = {0x01,0x30,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffd,0x0105};
    const base_expected_state ld_hl_pos_expected = {0x01,0x30,0x00,0x13,0x00,0xd8,0x00,0x00,0xffff,0x0105};
    const base_expected_state ld_hl_neg_expected = {0x01,0x30,0x00,0x13,0x00,0xd8,0xff,0xfe,0xffff,0x0105};
    const base_expected_state rlca_expected = {0x01,0x10,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0103};
    const base_expected_state rrca_expected = {0x80,0x10,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0103};
    const base_expected_state rla_expected = {0x01,0x10,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0104};
    const base_expected_state rra_expected = {0x80,0x10,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x0104};
    REQUIRE(check_base_vector(adc_half,sizeof(adc_half),48,&adc_half_expected)==0);
    REQUIRE(check_base_vector(adc_carry,sizeof(adc_carry),48,&adc_carry_expected)==0);
    REQUIRE(check_base_vector(sbc_borrow,sizeof(sbc_borrow),48,&sbc_borrow_expected)==0);
    REQUIRE(check_base_vector(cp_borrow,sizeof(cp_borrow),40,&cp_borrow_expected)==0);
    REQUIRE(check_base_vector(daa_add,sizeof(daa_add),48,&daa_add_expected)==0);
    REQUIRE(check_base_vector(daa_sub,sizeof(daa_sub),48,&daa_sub_expected)==0);
    REQUIRE(check_base_vector(inc_dec_carry,sizeof(inc_dec_carry),48,&inc_dec_expected)==0);
    REQUIRE(check_base_vector(add_hl_half,sizeof(add_hl_half),72,&add_hl_expected)==0);
    REQUIRE(check_base_vector(add_sp_positive,sizeof(add_sp_positive),80,&add_sp_pos_expected)==0);
    REQUIRE(check_base_vector(add_sp_negative,sizeof(add_sp_negative),80,&add_sp_neg_expected)==0);
    REQUIRE(check_base_vector(ld_hl_sp_positive,sizeof(ld_hl_sp_positive),56,&ld_hl_pos_expected)==0);
    REQUIRE(check_base_vector(ld_hl_sp_negative,sizeof(ld_hl_sp_negative),56,&ld_hl_neg_expected)==0);
    REQUIRE(check_base_vector(rlca_edge,sizeof(rlca_edge),32,&rlca_expected)==0);
    REQUIRE(check_base_vector(rrca_edge,sizeof(rrca_edge),32,&rrca_expected)==0);
    REQUIRE(check_base_vector(rla_edge,sizeof(rla_edge),40,&rla_expected)==0);
    REQUIRE(check_base_vector(rra_edge,sizeof(rra_edge),40,&rra_expected)==0);
    return 0;
}

static int base_address_effects(void) {
    {
        uint8_t rom[32768];
        const uint8_t program[]={0x01,0x00,0xc0,0x11,0x01,0xc0,0x3e,0xa5,0x02,0x1a,0x12,0x0a,0x00};
        make_rom(rom,program,sizeof(program));
        gbb_instance *m=NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK);
        REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
        gbb_test_bus_event events[8]={{0}}; gbb_test_observer_set(m,events,8);
        gbb_trace_record trace[8]={{0}};
        gbb_run_result r=gbb_run(m,136,trace,8);
        REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==136 && r.trace_count==8);
        const base_expected_state expected={0xa5,0x80,0xc0,0x00,0xc0,0x01,0x01,0x4d,0xfffe,0x010c};
        REQUIRE(trace_matches_expected(&trace[7],&expected));
        REQUIRE(gbb_test_observer_count(m)==4);
        REQUIRE(events[0].time_half_dots==72 && events[0].address==0xc000 && events[0].access==2 && events[0].value==0xa5);
        REQUIRE(events[1].time_half_dots==88 && events[1].address==0xc001 && events[1].access==1 && events[1].value==0x00);
        REQUIRE(events[2].time_half_dots==104 && events[2].address==0xc001 && events[2].access==2 && events[2].value==0x00);
        REQUIRE(events[3].time_half_dots==120 && events[3].address==0xc000 && events[3].access==1 && events[3].value==0xa5);
        REQUIRE(gbb_peek_ram(m,0xc000)==0xa5 && gbb_peek_ram(m,0xc001)==0x00);
        gbb_destroy(m);
    }
    {
        uint8_t rom[32768];
        const uint8_t program[]={0x21,0x01,0xc0,0x3e,0xa5,0x22,0x3a,0x32,0x2a,0x00};
        make_rom(rom,program,sizeof(program));
        gbb_instance *m=NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK);
        REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
        gbb_test_bus_event events[8]={{0}}; gbb_test_observer_set(m,events,8);
        gbb_trace_record trace[8]={{0}};
        gbb_run_result r=gbb_run(m,112,trace,8);
        REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==112 && r.trace_count==7);
        const base_expected_state expected={0x00,0x80,0x00,0x13,0x00,0xd8,0xc0,0x01,0xfffe,0x0109};
        REQUIRE(trace_matches_expected(&trace[6],&expected));
        REQUIRE(gbb_test_observer_count(m)==4);
        REQUIRE(events[0].time_half_dots==48 && events[0].address==0xc001 && events[0].access==2 && events[0].value==0xa5);
        REQUIRE(events[1].time_half_dots==64 && events[1].address==0xc002 && events[1].access==1 && events[1].value==0x00);
        REQUIRE(events[2].time_half_dots==80 && events[2].address==0xc001 && events[2].access==2 && events[2].value==0x00);
        REQUIRE(events[3].time_half_dots==96 && events[3].address==0xc000 && events[3].access==1 && events[3].value==0x00);
        REQUIRE(gbb_peek_ram(m,0xc001)==0x00);
        gbb_destroy(m);
    }
    {
        uint8_t rom[32768];
        const uint8_t program[]={0x21,0x00,0xc0,0x36,0x0f,0x34,0x35,0x7e,0x00};
        make_rom(rom,program,sizeof(program));
        gbb_instance *m=NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK);
        REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
        gbb_test_bus_event events[8]={{0}}; gbb_test_observer_set(m,events,8);
        gbb_trace_record trace[8]={{0}};
        gbb_run_result r=gbb_run(m,120,trace,8);
        REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==120 && r.trace_count==6);
        const base_expected_state expected={0x0f,0x60,0x00,0x13,0x00,0xd8,0xc0,0x00,0xfffe,0x0108};
        REQUIRE(trace_matches_expected(&trace[5],&expected));
        REQUIRE(gbb_test_observer_count(m)==6);
        REQUIRE(events[0].time_half_dots==40 && events[0].address==0xc000 && events[0].access==2 && events[0].value==0x0f);
        REQUIRE(events[1].time_half_dots==56 && events[1].address==0xc000 && events[1].access==1 && events[1].value==0x0f);
        REQUIRE(events[2].time_half_dots==64 && events[2].address==0xc000 && events[2].access==2 && events[2].value==0x10);
        REQUIRE(events[3].time_half_dots==80 && events[3].address==0xc000 && events[3].access==1 && events[3].value==0x10);
        REQUIRE(events[4].time_half_dots==88 && events[4].address==0xc000 && events[4].access==2 && events[4].value==0x0f);
        REQUIRE(events[5].time_half_dots==104 && events[5].address==0xc000 && events[5].access==1 && events[5].value==0x0f);
        REQUIRE(gbb_peek_ram(m,0xc000)==0x0f);
        gbb_destroy(m);
    }
    {
        uint8_t rom[32768];
        const uint8_t program[]={0x3e,0x5a,0xe0,0x80,0x3e,0x00,0xf0,0x80,0xea,0x00,0xc0,0xfa,0x00,0xc0,0x00};
        make_rom(rom,program,sizeof(program));
        gbb_instance *m=NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK);
        REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
        gbb_test_bus_event events[8]={{0}}; gbb_test_observer_set(m,events,8);
        gbb_trace_record trace[8]={{0}};
        gbb_run_result r=gbb_run(m,152,trace,8);
        REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==152 && r.trace_count==7);
        const base_expected_state expected={0x5a,0x80,0x00,0x13,0x00,0xd8,0x01,0x4d,0xfffe,0x010e};
        REQUIRE(trace_matches_expected(&trace[6],&expected));
        REQUIRE(gbb_test_observer_count(m)==4);
        REQUIRE(events[0].time_half_dots==32 && events[0].address==0xff80 && events[0].access==2 && events[0].value==0x5a);
        REQUIRE(events[1].time_half_dots==72 && events[1].address==0xff80 && events[1].access==1 && events[1].value==0x5a);
        REQUIRE(events[2].time_half_dots==104 && events[2].address==0xc000 && events[2].access==2 && events[2].value==0x5a);
        REQUIRE(events[3].time_half_dots==136 && events[3].address==0xc000 && events[3].access==1 && events[3].value==0x5a);
        REQUIRE(gbb_peek_ram(m,0xc000)==0x5a);
        gbb_destroy(m);
    }
    return 0;
}

static int timed_access(void) {
    uint8_t rom[32768]; const uint8_t program[]={0x02,0x00}; make_rom(rom,program,sizeof(program));
    gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
    gbb_test_bus_event events[4]={{0}}; gbb_test_observer_set(m,events,4);
    gbb_run_result r=gbb_run(m,16,NULL,0);
    REQUIRE(r.consumed_half_dots==16 && gbb_test_observer_count(m)==1);
    REQUIRE(events[0].time_half_dots==8 && events[0].address==0x0013 && events[0].access==2 && events[0].value==1);
    gbb_destroy(m); return 0;
}

static int check_return_case(uint8_t opcode, int taken, int pending, uint8_t cost,
                             uint8_t low_phase, uint8_t high_phase) {
    uint8_t rom[32768];
    static const uint8_t ordinary_setup[] = {0x31, 0x02, 0xc0, 0xcd, 0x50, 0x01};
    static const uint8_t pending_setup[] = {
        0x3e, 0x01, 0xea, 0xff, 0xff, 0xea, 0x0f, 0xff,
        0x31, 0x02, 0xc0, 0xcd, 0x50, 0x01
    };
    const uint8_t *setup = pending ? pending_setup : ordinary_setup;
    size_t setup_size = pending ? sizeof(pending_setup) : sizeof(ordinary_setup);
    uint64_t setup_time = pending ? 152u : 72u;
    uint16_t return_pc = pending ? 0x010e : 0x0106;
    make_rom(rom, setup, setup_size);
    rom[0x150] = opcode;

    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_run_result r = gbb_run(m, setup_time, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == setup_time);

    gbb_test_bus_event events[8] = {{0}};
    gbb_test_observer_set(m, events, 8);
    gbb_trace_record before = {0}, after = {0}, trace[2] = {{0}};
    gbb_test_cpu_snapshot(m, &before);
    r = gbb_run(m, (uint64_t)cost - 1u, trace, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0 && r.trace_count == 0);
    gbb_test_cpu_snapshot(m, &after);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);
    REQUIRE(gbb_test_observer_count(m) == 0);

    r = gbb_run(m, cost, trace, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == cost && r.trace_count == 1);
    REQUIRE(trace[0].time_half_dots == setup_time && trace[0].pc == 0x0150);
    REQUIRE(trace[0].sp == 0xc000 && trace[0].f == 0x80);
    gbb_test_cpu_snapshot(m, &after);
    REQUIRE(after.time_half_dots == setup_time + cost && after.f == 0x80);

    if (taken) {
        REQUIRE(gbb_test_observer_count(m) == 2);
        REQUIRE(events[0].time_half_dots == setup_time + low_phase);
        REQUIRE(events[0].address == 0xc000 && events[0].access == 1 && events[0].value == (uint8_t)return_pc);
        REQUIRE(events[1].time_half_dots == setup_time + high_phase);
        REQUIRE(events[1].address == 0xc001 && events[1].access == 1 && events[1].value == (uint8_t)(return_pc >> 8));
        REQUIRE(after.pc == return_pc && after.sp == 0xc002);
    } else {
        REQUIRE(gbb_test_observer_count(m) == 0);
        REQUIRE(after.pc == 0x0151 && after.sp == 0xc000);
    }

    if (pending) {
        before = after;
        r = gbb_run(m, 39, trace, 2);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0 && r.trace_count == 0);
        gbb_test_cpu_snapshot(m, &after);
        REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);
        REQUIRE(gbb_test_observer_count(m) == 2);

        r = gbb_run(m, 40, trace, 2);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 40);
        gbb_test_cpu_snapshot(m, &after);
        REQUIRE(after.pc == 0x0040 && after.sp == 0xc000 && after.time_half_dots == setup_time + cost + 40u);
        REQUIRE(gbb_test_observer_count(m) == 5);
        REQUIRE(events[2].time_half_dots == setup_time + cost + 8u && events[2].address == 0xff0f);
        REQUIRE(events[3].time_half_dots == setup_time + cost + 16u && events[3].address == 0xc001);
        REQUIRE(events[4].time_half_dots == setup_time + cost + 24u && events[4].address == 0xc000);
    }

    gbb_destroy(m);
    return 0;
}

static int return_phases(void) {
    /* Opcode timing contract: RET/RETI read at M2/M3; taken RET cc adds its condition cycle first. */
    REQUIRE(check_return_case(0xc9, 1, 0, 32, 8, 16) == 0);
    REQUIRE(check_return_case(0xd9, 1, 1, 32, 8, 16) == 0);
    REQUIRE(check_return_case(0xc8, 1, 0, 40, 16, 24) == 0);
    REQUIRE(check_return_case(0xc0, 0, 0, 16, 0, 0) == 0);
    return 0;
}

static int address_wrap(void) {
    uint8_t rom[32768];
    const uint8_t p[] = {0x31,0x34,0x12,0x08,0xff,0xff,0xfa,0x00,0x00,0x00};
    make_rom(rom, p, sizeof(p)); rom[0] = 0x9a;
    gbb_instance *m = NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_test_bus_event e[4] = {{0}}; gbb_test_observer_set(m, e, 4);
    gbb_trace_record t[4] = {{0}}; gbb_run_result r = gbb_run(m, 104, t, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 104 && r.trace_count == 4);
    REQUIRE(e[0].address == 0xffff && e[0].value == 0x34 && e[0].access == 2 && e[0].time_half_dots == 48);
    REQUIRE(e[1].address == 0x0000 && e[1].value == 0x12 && e[1].access == 2 && e[1].time_half_dots == 56);
    REQUIRE(e[2].address == 0x0000 && e[2].value == 0x9a && e[2].access == 1);
    REQUIRE(t[3].a == 0x9a && t[3].sp == 0x1234); /* ROM write at zero was ignored. */
    gbb_destroy(m);
    /* Opcode F6 comes from IE=16 with its unused high bits; its immediate wraps to ROM zero. */
    const uint8_t fetch[] = {0x3e,0x16,0xea,0xff,0xff,0xc3,0xff,0xff};
    make_rom(rom, fetch, sizeof(fetch)); rom[0] = 0x01;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    r = gbb_run(m, 80, NULL, 0); REQUIRE(r.consumed_half_dots == 80);
    r = gbb_run(m, 24, t, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 24 && r.trace_count == 2);
    REQUIRE(t[0].pc == 0xffff && t[0].opcode[0] == 0xf6 && t[0].opcode[1] == 0x01);
    REQUIRE(t[1].pc == 0x0001 && t[1].a == 0x17);
    gbb_destroy(m); return 0;
}

static int stack_wrap(void) {
    uint8_t rom[32768];
    const uint8_t pop[] = {0x31,0xff,0xff,0x3e,4,0xea,0xff,0xff,0xc1,0x00};
    make_rom(rom, pop, sizeof(pop)); rom[0] = 0x12;
    gbb_instance *m = NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(gbb_run(m, 72, NULL, 0).consumed_half_dots == 72);
    gbb_test_bus_event e[4] = {{0}}; gbb_test_observer_set(m, e, 4);
    gbb_trace_record t[2] = {{0}}; gbb_run_result r = gbb_run(m, 32, t, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 32 && r.trace_count == 2);
    REQUIRE(e[0].address == 0xffff && e[0].value == 0xe4 && e[0].access == 1 && e[0].time_half_dots == 80);
    REQUIRE(e[1].address == 0x0000 && e[1].value == 0x12 && e[1].access == 1 && e[1].time_half_dots == 88);
    REQUIRE(t[1].sp == 0x0001 && t[1].b == 0x12 && t[1].c == 0xe4);
    gbb_destroy(m);
    const uint8_t push[] = {0x01,0x56,0x12,0x31,0x01,0x00,0xc5,0xfa,0x00,0x00,0x00};
    make_rom(rom, push, sizeof(push)); rom[0] = 0x34;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(gbb_run(m, 48, NULL, 0).consumed_half_dots == 48);
    gbb_test_observer_set(m, e, 4);
    r = gbb_run(m, 72, t, 2);
    REQUIRE(r.reason == GBB_STOP_TRACE_FULL && r.consumed_half_dots == 64 && r.trace_count == 2);
    REQUIRE(e[0].address == 0x0000 && e[0].value == 0x12 && e[0].access == 2 && e[0].time_half_dots == 64);
    REQUIRE(e[1].address == 0xffff && e[1].value == 0x56 && e[1].access == 2 && e[1].time_half_dots == 72);
    r = gbb_run(m, 8, t, 2);
    REQUIRE(r.trace_count == 1 && t[0].sp == 0xffff && t[0].a == 0x34);
    gbb_destroy(m); return 0;
}

static int cb_wram(void) {
    uint8_t rom[32768];
    const uint8_t program[]={0x21,0x00,0xC0,0x3E,0x01,0x77,0x37,0xCB,0x46,0xCB,0x86,0x00};
    make_rom(rom,program,sizeof(program));
    gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
    gbb_trace_record trace[20]={{0}}; gbb_test_bus_event events[8]={{0}}; gbb_test_observer_set(m,events,8);
    gbb_run_result r=gbb_run(m,128,trace,20);
    REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==128);
    REQUIRE(gbb_peek_ram(m,0xC000)==0);
    REQUIRE(r.trace_count>=7);
    REQUIRE(trace[4].pc==0x107 && trace[5].pc==0x109 && trace[6].pc==0x10B);
    REQUIRE(trace[4].f==0x90); /* SCF establishes carry before BIT. */
    REQUIRE(trace[5].f==0x30); /* BIT sets H and preserves carry; bit zero is set. */
    REQUIRE(trace[6].f==0x30); /* RES preserves every flag. */
    REQUIRE(gbb_test_observer_count(m)==4);
    REQUIRE(events[0].time_half_dots==56 && events[0].address==0xC000 && events[0].access==2 && events[0].value==1);
    REQUIRE(events[1].time_half_dots==80 && events[1].address==0xC000 && events[1].access==1 && events[1].value==1);
    REQUIRE(events[2].time_half_dots==104 && events[2].address==0xC000 && events[2].access==1 && events[2].value==1);
    REQUIRE(events[3].time_half_dots==112 && events[3].address==0xC000 && events[3].access==2 && events[3].value==0);
    gbb_destroy(m); return 0;
}

static int cb_budget(void) {
    uint8_t rom[32768]; const uint8_t program[]={0x21,0x00,0xC0,0x3E,0x01,0x77,0x37,0xCB,0x46}; make_rom(rom,program,sizeof(program));
    gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
    gbb_trace_record trace[5]={{0}}; gbb_test_bus_event events[4]={{0}}; gbb_test_observer_set(m,events,4);
    gbb_run_result r=gbb_run(m,95,trace,5);
    REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==88 && r.trace_count==5);
    REQUIRE(trace[4].pc==0x107 && gbb_peek_ram(m,0xC000)==1);
    REQUIRE(gbb_test_observer_count(m)==2);
    REQUIRE(events[0].time_half_dots==56);
    REQUIRE(events[0].value==1);
    REQUIRE(events[1].time_half_dots==80);
    REQUIRE(events[1].access==1 && events[1].value==1);
    gbb_destroy(m); return 0;
}

static uint8_t cb_expected(uint8_t value, uint8_t flags, unsigned op, uint8_t *next_flags) {
    unsigned group=op>>6, function=(op>>3)&7u, bit=function;
    uint8_t result=value, carry=(uint8_t)(flags&0x10u);
    if(group==0u) {
        switch(function) {
            case 0: carry=(uint8_t)(value>>7); result=(uint8_t)((value<<1)|carry); break;
            case 1: carry=(uint8_t)(value&1u); result=(uint8_t)((value>>1)|(carry<<7)); break;
            case 2: { uint8_t out=(uint8_t)(value>>7); result=(uint8_t)((value<<1)|(carry!=0)); carry=out; break; }
            case 3: { uint8_t out=(uint8_t)(value&1u); result=(uint8_t)((value>>1)|(carry!=0?0x80u:0)); carry=out; break; }
            case 4: carry=(uint8_t)(value>>7); result=(uint8_t)(value<<1); break;
            case 5: carry=(uint8_t)(value&1u); result=(uint8_t)((value>>1)|(value&0x80u)); break;
            case 6: carry=0; result=(uint8_t)((value<<4)|(value>>4)); break;
            default: carry=(uint8_t)(value&1u); result=(uint8_t)(value>>1); break;
        }
        *next_flags=(uint8_t)((result==0?0x80u:0)|(carry?0x10u:0));
    } else if(group==1u) {
        *next_flags=(uint8_t)((flags&0x10u)|0x20u|((value&(1u<<bit))==0?0x80u:0));
    } else {
        result=group==2u?(uint8_t)(value&~(1u<<bit)):(uint8_t)(value|(1u<<bit));
        *next_flags=flags;
    }
    return result;
}

static int cb_matrix(void) {
    uint8_t rom[32768]; gbb_trace_record trace[6];
    for(unsigned op=0;op<256;++op) {
        const uint8_t program[]={0x21,0x00,0xC0,0x3E,0xA5,0x77,0x37,0xCB,(uint8_t)op,0x00};
        make_rom(rom,program,sizeof(program));
        gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
        memset(trace,0,sizeof(trace));
        unsigned target=op&7u, cost=target==6u?((op>>6)==1u?24u:32u):16u;
        gbb_run_result r=gbb_run(m,72u+cost,trace,6);
        REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==72u+cost && r.trace_count==6);
        REQUIRE(trace[4].pc==0x107 && trace[5].pc==0x109);
        uint8_t before[8]={0x00,0x13,0x00,0xD8,0xC0,0x00,0xA5,0xA5};
        uint8_t flags=0x90, expected_flags=0;
        uint8_t expected=cb_expected(before[target],flags,op,&expected_flags);
        uint8_t after[8]={trace[5].b,trace[5].c,trace[5].d,trace[5].e,trace[5].h,trace[5].l,gbb_peek_ram(m,0xC000),trace[5].a};
        REQUIRE(trace[5].f==expected_flags);
        for(unsigned reg=0;reg<8;++reg) REQUIRE(after[reg]==(reg==target?expected:before[reg]));
        gbb_destroy(m);
    }
    return 0;
}

static int cb_flags_edges(void) {
    static const uint8_t values[]={0x00,0x01,0x7F,0x80,0xFF};
    static const uint8_t operations[]={0x00,0x08,0x10,0x18,0x20,0x28,0x30,0x38};
    for(size_t i=0;i<sizeof(values);++i) for(size_t j=0;j<sizeof(operations);++j) {
        uint8_t rom[32768]; const uint8_t program[]={0x06,values[i],0x37,0xCB,operations[j],0x00}; make_rom(rom,program,sizeof(program));
        gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
        gbb_trace_record trace[4]={{0}}; unsigned cost=16;
        gbb_run_result r=gbb_run(m,48,trace,4);
        REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==48 && r.trace_count==4);
        uint8_t expected_flags=0, expected=cb_expected(values[i],0x90,operations[j],&expected_flags);
        REQUIRE(trace[3].b==expected && trace[3].f==expected_flags);
        gbb_destroy(m); (void)cost;
    }
    return 0;
}

static int cb_timed_access(void) {
    uint8_t rom[32768]; const uint8_t program[]={0x21,0x00,0xC0,0x3E,0xA5,0x77,0x37,0xCB,0x46,0xCB,0x86,0x00}; make_rom(rom,program,sizeof(program));
    gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
    gbb_test_bus_event events[8]={{0}}; gbb_test_observer_set(m,events,8); gbb_trace_record trace[7]={{0}};
    gbb_run_result r=gbb_run(m,128,trace,7);
    REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots==128 && r.trace_count==7);
    REQUIRE(gbb_test_observer_count(m)==4);
    REQUIRE(events[0].address==0xC000 && events[0].access==2 && events[0].time_half_dots==56);
    REQUIRE(events[1].address==0xC000 && events[1].access==1 && events[1].time_half_dots==80);
    REQUIRE(events[2].address==0xC000 && events[2].access==1 && events[2].time_half_dots==104);
    REQUIRE(events[3].address==0xC000 && events[3].access==2 && events[3].time_half_dots==112);
    REQUIRE(gbb_peek_ram(m,0xC000)==0xA4);
    gbb_destroy(m); return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    active_case=argv[1];
    if (strcmp(argv[1], "call_stack") == 0) return call_stack();
    if (strcmp(argv[1], "conditional_budget") == 0) return conditional_budget();
    if (strcmp(argv[1], "base_matrix") == 0) return base_matrix();
    if (strcmp(argv[1], "illegal_lockup") == 0) return illegal_lockup();
    if (strcmp(argv[1], "flags_edges") == 0) return flags_edges();
    if (strcmp(argv[1], "base_semantic_tracer") == 0) return base_semantic_tracer();
    if (strcmp(argv[1], "base_conditional_paths") == 0) return base_conditional_paths();
    if (strcmp(argv[1], "base_arithmetic_edges") == 0) return base_arithmetic_edges();
    if (strcmp(argv[1], "base_address_effects") == 0) return base_address_effects();
    if (strcmp(argv[1], "timed_access") == 0) return timed_access();
    if (strcmp(argv[1], "return_phases") == 0) return return_phases();
    if (strcmp(argv[1], "address_wrap") == 0) return address_wrap();
    if (strcmp(argv[1], "stack_wrap") == 0) return stack_wrap();
    if (strcmp(argv[1], "cb_wram") == 0) return cb_wram();
    if (strcmp(argv[1], "cb_budget") == 0) return cb_budget();
    if (strcmp(argv[1], "cb_matrix") == 0) return cb_matrix();
    if (strcmp(argv[1], "cb_flags_edges") == 0) return cb_flags_edges();
    if (strcmp(argv[1], "cb_timed_access") == 0) return cb_timed_access();
    return 2;
}
