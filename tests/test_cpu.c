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

static void make_rom(uint8_t rom[32768], const uint8_t *program, size_t size) {
    memset(rom, 0, 32768);
    memcpy(rom + 0x100, program, size);
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14c; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14d] = checksum;
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
    REQUIRE(events[2].time_half_dots == 64 && events[2].address == 0xfffc && events[2].access == 1 && events[2].value == 0x03);
    REQUIRE(events[3].time_half_dots == 72 && events[3].address == 0xfffd && events[3].access == 1 && events[3].value == 0x01);
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

static int base_matrix(void) {
    static const uint8_t holes[] = {0xd3,0xdb,0xdd,0xe3,0xe4,0xeb,0xec,0xed,0xf4,0xfc,0xfd};
    uint8_t rom[32768];
    for (unsigned op = 0; op < 256; ++op) {
        uint8_t program[] = {(uint8_t)op,0x00,0x01,0x00};
        make_rom(rom,program,sizeof(program));
        gbb_instance *m=NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK);
        REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
        gbb_trace_record trace[10]={{0}};
        gbb_run_result r=gbb_run(m,96,trace,10);
        int illegal=0; for(size_t i=0;i<sizeof(holes);++i) if(holes[i]==op) illegal=1;
        if(illegal) REQUIRE(r.reason==GBB_STOP_LOCKUP && r.lockup_pc==0x100 && r.lockup_opcode==op);
        else if (op == 0x76) {
            REQUIRE(r.reason == GBB_STOP_HALTED_IDLE && r.consumed_half_dots == 8);
            REQUIRE(r.trace_count == 1 && trace[0].pc == 0x0100);
        } else if (op == 0x10) {
            REQUIRE(r.reason == GBB_STOP_STOPPED && r.consumed_half_dots == 8);
            REQUIRE(r.trace_count == 1 && trace[0].pc == 0x0100);
        } else {
            REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots>0);
            REQUIRE(r.trace_count>=2);
            REQUIRE(trace[1].time_half_dots==expected_first_cost(op));
            if (trace[1].pc != expected_first_pc(op)) fprintf(stderr, "opcode %02x PC got %04x expected %04x\n", op, trace[1].pc, expected_first_pc(op));
            REQUIRE(trace[1].pc==expected_first_pc(op));
            REQUIRE((trace[1].f&0x0f)==0);
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

static int timed_access(void) {
    uint8_t rom[32768]; const uint8_t program[]={0x02,0x00}; make_rom(rom,program,sizeof(program));
    gbb_instance *m=NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)==GBB_OK); REQUIRE(gbb_load_rom(m,rom,sizeof(rom))==GBB_OK);
    gbb_test_bus_event events[4]={{0}}; gbb_test_observer_set(m,events,4);
    gbb_run_result r=gbb_run(m,16,NULL,0);
    REQUIRE(r.consumed_half_dots==16 && gbb_test_observer_count(m)==1);
    REQUIRE(events[0].time_half_dots==8 && events[0].address==0x0013 && events[0].access==2 && events[0].value==1);
    gbb_destroy(m); return 0;
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
    if (strcmp(argv[1], "timed_access") == 0) return timed_access();
    if (strcmp(argv[1], "address_wrap") == 0) return address_wrap();
    if (strcmp(argv[1], "stack_wrap") == 0) return stack_wrap();
    if (strcmp(argv[1], "cb_wram") == 0) return cb_wram();
    if (strcmp(argv[1], "cb_budget") == 0) return cb_budget();
    if (strcmp(argv[1], "cb_matrix") == 0) return cb_matrix();
    if (strcmp(argv[1], "cb_flags_edges") == 0) return cb_flags_edges();
    if (strcmp(argv[1], "cb_timed_access") == 0) return cb_timed_access();
    return 2;
}
