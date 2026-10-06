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
    if (op == 0xc9 || op == 0xd9) return 0xff00;
    if ((op & 0xe7u) == 0xc0u) return expected_condition((op >> 3) & 3u) ? 0xff00 : 0x0101;
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
        else {
            REQUIRE(r.reason==GBB_STOP_BUDGET && r.consumed_half_dots>0);
            REQUIRE(r.trace_count>=2);
            REQUIRE(trace[1].time_half_dots==expected_first_cost(op));
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

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    active_case=argv[1];
    if (strcmp(argv[1], "call_stack") == 0) return call_stack();
    if (strcmp(argv[1], "conditional_budget") == 0) return conditional_budget();
    if (strcmp(argv[1], "base_matrix") == 0) return base_matrix();
    if (strcmp(argv[1], "illegal_lockup") == 0) return illegal_lockup();
    if (strcmp(argv[1], "flags_edges") == 0) return flags_edges();
    if (strcmp(argv[1], "timed_access") == 0) return timed_access();
    if (strcmp(argv[1], "cb_wram") == 0) return cb_wram();
    if (strcmp(argv[1], "cb_budget") == 0) return cb_budget();
    return 2;
}
