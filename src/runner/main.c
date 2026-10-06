#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TRACE_CAPACITY 16384u
#define RUN_BUDGET_HALF_DOTS UINT64_C(200000)

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: gabbaboy-runner <tracer.gb>\n"); return 2; }
    FILE *file=fopen(argv[1], "rb");
    if (file == NULL) { fprintf(stderr, "invalid-fixture: cannot open ROM\n"); return 2; }
    if (fseek(file,0,SEEK_END)!=0) { fclose(file); return 2; }
    long length=ftell(file);
    if (length < 0 || length > 8*1024*1024 || fseek(file,0,SEEK_SET)!=0) { fclose(file); fprintf(stderr,"invalid-fixture: size out of bounds\n"); return 2; }
    size_t size=(size_t)length;
    uint8_t *rom=malloc(size);
    if (rom == NULL || fread(rom,1,size,file)!=size) { free(rom); fclose(file); return 2; }
    fclose(file);
    gbb_instance *machine=NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B,&machine)!=GBB_OK || gbb_load_rom(machine,rom,size)!=GBB_OK) { free(rom); gbb_destroy(machine); fprintf(stderr,"invalid-fixture: unsupported or malformed ROM\n"); return 2; }
    free(rom);
    gbb_trace_record *trace=calloc(TRACE_CAPACITY,sizeof(*trace));
    if (trace == NULL) { gbb_destroy(machine); fprintf(stderr,"runner-error: trace allocation failed\n"); return 2; }
    gbb_run_result result=gbb_run(machine,RUN_BUDGET_HALF_DOTS,trace,TRACE_CAPACITY);
    uint8_t status=gbb_peek_ram(machine,0xC001);
    const char *outcome=result.reason==GBB_STOP_LOCKUP ? "lockup" :
        result.reason==GBB_STOP_UNSUPPORTED_OPCODE ? "unsupported" :
        result.reason==GBB_STOP_UNSUPPORTED_BUS ? "unsupported-bus" :
        result.reason==GBB_STOP_TRACE_FULL ? "trace-exhausted" :
        result.reason==GBB_STOP_HALTED_IDLE ? "halted-idle" :
        result.reason==GBB_STOP_STOPPED ? "stopped" :
        status==0xEE ? "guest-failure" :
        result.reason==GBB_STOP_BUDGET && status==0xA5 ? "pass" : "timeout";
    printf("fixture=original-wram-tracer profile=DMG-CPU-B outcome=%s stop=%s half_dots=%llu trace_records=%zu\n",
           outcome,result.reason==GBB_STOP_BUDGET?"budget":result.reason==GBB_STOP_TRACE_FULL?"trace-full":result.reason==GBB_STOP_UNSUPPORTED_BUS?"unsupported-bus":result.reason==GBB_STOP_LOCKUP?"lockup":result.reason==GBB_STOP_HALTED_IDLE?"halted-idle":result.reason==GBB_STOP_STOPPED?"stopped":"unsupported-opcode",
           (unsigned long long)result.consumed_half_dots,result.trace_count);
    for (size_t i=0;i<result.trace_count && i<12;i++)
        printf("trace time=%llu pc=%04x opcode=%02x state=A:%02x F:%02x HL:%02x%02x\n",
               (unsigned long long)trace[i].time_half_dots,trace[i].pc,trace[i].opcode[0],trace[i].a,trace[i].f,trace[i].h,trace[i].l);
    gbb_destroy(machine); free(trace);
    return strcmp(outcome,"pass")==0 ? 0 : strcmp(outcome,"guest-failure")==0 ? 1 : 3;
}
