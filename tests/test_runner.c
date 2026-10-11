#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

/* Compile the host protocol helpers into this focused test translation unit. */
#define main gbb_runner_program_main
#include "../src/runner/main.c"
#undef main

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

static void set_protocol_record(gbb_trace_record *record,uint16_t callback_pc,
                                const uint8_t registers[6]) {
    memset(record,0,sizeof(*record));
    record->pc=callback_pc;
    record->opcode[0]=0x00;
    record->b=registers[0];record->c=registers[1];record->d=registers[2];
    record->e=registers[3];record->h=registers[4];record->l=registers[5];
}

/* The mutation and the REQUIREs live here so the caller frees the heap ROM on every path. */
static int induced_guest_failure_on(uint8_t *rom,size_t rom_size) {
    static const uint8_t expected_table_start[]={0x00,0x00,0x00,0x08};
    /* The exact admitted DAA image has its testcases1 table at ROM offset 0x0266. */
    REQUIRE(memcmp(rom+0x0266,expected_table_start,sizeof(expected_table_start))==0);
    rom[0x0268]^=1u;

    protocol_evidence evidence;uint64_t ticks=0;size_t recent_count=0;const char *stop=NULL;
    gbb_diagnostic_record recent[RECENT_CAPACITY];
    const char *status=run_guest(&cases[0],rom,rom_size,&evidence,&ticks,&stop,recent,&recent_count);
    REQUIRE(strcmp(status,"fail")==0);
    REQUIRE(evidence.reached_result);
    REQUIRE(evidence.result_pc==cases[0].result_pc);
    REQUIRE(evidence.callback_pc==cases[0].fail_callback_pc);
    REQUIRE(evidence.callback_result!=NULL && strcmp(evidence.callback_result,"fail")==0);
    REQUIRE(evidence.reason==NULL);
    REQUIRE(ticks>0 && ticks<cases[0].budget);
    REQUIRE(recent_count<=RECENT_CAPACITY);
    printf("control=private-daa-assertion-mutation source_revision=%s source_path=%s report_patch_sha256=%s fixture_sha256=%s status=%s callback_pc=%04x result_pc=%04x ticks=%llu recent=%zu\n",
           MOONEYE_SOURCE_REVISION,cases[0].source_path,MOONEYE_PATCH_SHA256,cases[0].sha256,
           status,evidence.callback_pc,evidence.result_pc,(unsigned long long)ticks,recent_count);
    return 0;
}

static int run_induced_guest_failure(const char *path) {
    size_t rom_size=0;
    uint8_t *rom=malloc(MAX_ROM+1);
    REQUIRE(rom!=NULL);
    int code=1;
    if(read_bounded(path,rom,MAX_ROM,&rom_size)&&rom_size==MAX_ROM&&hash_matches(rom,rom_size,cases[0].sha256)){
        code=induced_guest_failure_on(rom,rom_size);
    }else{
        fprintf(stderr,"%s:%d: admitted DAA fixture did not load\n",__FILE__,__LINE__);
    }
    free(rom);
    return code;
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    if (strcmp(argv[1],"runner_guest_failure")==0)
        return argc==3?run_induced_guest_failure(argv[2]):2;
    if (argc != 2) return 2;
    gbb_trace_record records[2]={{0}};
    protocol_progress progress={0};protocol_evidence evidence={0};
    if (strcmp(argv[1], "runner_pass") == 0) {
        set_protocol_record(&records[0],cases[0].pass_callback_pc,cases[0].pass_registers);
        records[1].pc=cases[0].result_pc;records[1].opcode[0]=0x40;
        records[1].b=cases[0].pass_registers[0];records[1].c=cases[0].pass_registers[1];
        records[1].d=cases[0].pass_registers[2];records[1].e=cases[0].pass_registers[3];
        records[1].h=cases[0].pass_registers[4];records[1].l=cases[0].pass_registers[5];
        REQUIRE(strcmp(protocol_status(&cases[0],records,2,&progress,&evidence),"pass")==0);
        REQUIRE(evidence.reached_result && evidence.result_pc==cases[0].result_pc);
    } else if (strcmp(argv[1], "runner_fail") == 0) {
        set_protocol_record(&records[0],cases[0].fail_callback_pc,cases[0].fail_registers);
        records[1].pc=cases[0].result_pc;records[1].opcode[0]=0x40;
        records[1].b=cases[0].fail_registers[0];records[1].c=cases[0].fail_registers[1];
        records[1].d=cases[0].fail_registers[2];records[1].e=cases[0].fail_registers[3];
        records[1].h=cases[0].fail_registers[4];records[1].l=cases[0].fail_registers[5];
        REQUIRE(strcmp(protocol_status(&cases[0],records,2,&progress,&evidence),"fail")==0);
    } else if (strcmp(argv[1], "runner_wrong_breakpoint") == 0) {
        records[0].pc=0x0200; /* A matching LD B,B signature outside the source symbol is not a result. */
        records[0].opcode[0]=0x40;records[0].b=3;records[0].c=5;records[0].d=8;
        records[0].e=13;records[0].h=21;records[0].l=34;
        REQUIRE(protocol_status(&cases[0],records,1,&progress,&evidence)==NULL);
        records[0].pc=cases[0].result_pc;
        REQUIRE(strcmp(protocol_status(&cases[0],records,1,&progress,&evidence),"unsupported")==0);
        REQUIRE(evidence.reason!=NULL && strcmp(evidence.reason,"callback-not-reached")==0);
    } else if (strcmp(argv[1], "runner_timeout") == 0) {
        REQUIRE(protocol_status(&cases[0],records,1,&progress,&evidence)==NULL);
        REQUIRE(strcmp(budget_status(2000000,2000000),"timeout")==0);
        REQUIRE(cases[0].budget==UINT64_C(2000000));
    } else if (strcmp(argv[1], "runner_unsupported") == 0) {
        REQUIRE(protocol_status(&cases[1],records,1,&progress,&evidence)==NULL);
        REQUIRE(strcmp(unsupported_core_stop(GBB_STOP_UNSUPPORTED_BUS),"unsupported")==0);
        REQUIRE(unsupported_core_stop(GBB_STOP_BUDGET)==NULL);
        REQUIRE(strcmp(cases[1].category,"timer")==0 && strcmp(cases[2].category,"timer")==0);
    } else if (strcmp(argv[1], "runner_zero_eligible") == 0) {
        REQUIRE(!suite_counts_valid(0,0));
        REQUIRE(suite_counts_valid(3,3));
        REQUIRE(!suite_counts_valid(3,2));
    } else { return 2; }
    return 0;
}
