#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"
#include "acceptance.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef GBB_BUILD_REVISION
#define GBB_BUILD_REVISION "unknown"
#endif
#ifndef GBB_BUILD_QUALIFIED
#define GBB_BUILD_QUALIFIED 0
#endif

#define MAX_MANIFEST 65536u
#define MAX_ROM 32768u
#define RECENT_CAPACITY 128u
#define RUN_CHUNK UINT64_C(2048)
#define TRACE_CAPACITY 128u
#define DIAGNOSTIC_CAPACITY 4096u
#define MOONEYE_SOURCE_REVISION "31510e12eea6286d36eea060a6adde755e1067aa"
#define MOONEYE_SOURCE_TREE "2b8c52424a49a2a7466cf631fd8992c53d0de2fa"
#define MOONEYE_PATCH_SHA256 "c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d"
#define MOONEYE_BUILDER_REVISION "91c52b1f4ef3cc8ba3c0638f7536539579af6a9f"
#define MOONEYE_BUILDER_ARCHIVE_SHA256 "24a95d77a79feeb70d1de87d66749c006e37337308ce9c00e44efac4c46ab976"
#define MOONEYE_MANIFEST_SHA256 "98a1799b8be9c022ac13467a552890fb12bdd706017e42e12c944ec618d60527"

typedef struct {
    const char *id;
    const char *alias;
    const char *category;
    const char *rom;
    const char *sha256;
    const char *original_sha256;
    const char *source_path;
    uint16_t pass_callback_pc;
    uint16_t fail_callback_pc;
    uint16_t result_pc;
    uint8_t pass_registers[6];
    uint8_t fail_registers[6];
    uint64_t budget;
} fixture_case;

static const fixture_case cases[] = {
    {"mooneye-acceptance-instr-daa", "daa", "cpu", "daa.gb",
     "3a39eda77a09b817e4e38004a3d117990565fb797e8a4f470920f1b7608f0a08",
     "96cd0e02a85f6f035b1c1947d36a8ad2d8e51963f636b833f05559f021eef57e",
     "acceptance/instr/daa.s", 0x0166, 0x01b3, 0x409a,
     {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(2000000)},
    {"mooneye-acceptance-timer-tim00", "tim00", "timer", "tim00.gb",
     "476b2332de3f2d6604f8e1478daa8cbc7c59c89c50837fd47cc95e96e784d4f7",
     "6edc430a09522294c96d1eef63a0f1a99078f4401060980048ec5a68640e11bd",
     "acceptance/timer/tim00.s", 0x4000, 0x4000, 0x4327,
     {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(200000)},
    {"mooneye-acceptance-timer-tim00-div-trigger", "tim00-div-trigger", "timer", "tim00_div_trigger.gb",
     "566da853858061c69866c47cc31b85b1fef003d4c088c8e8dbb26973da9944da",
     "468d426c4fe6a850a28f4116bd127d471be6adf2ef5dd0f89f2db67ffe212242",
     "acceptance/timer/tim00_div_trigger.s", 0x4000, 0x4000, 0x4327,
     {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(200000)}
};

static int read_bounded(const char *path, uint8_t *buffer, size_t capacity, size_t *length) {
    FILE *f=fopen(path,"rb"); if(!f)return 0;
    size_t n=fread(buffer,1,capacity+1,f); int failed=ferror(f); fclose(f);
    if(failed||n>capacity)return 0; *length=n; return 1;
}
static int hash_matches(const uint8_t *bytes,size_t length,const char *expected) { char hash[65];gbb_accept_sha256_hex(bytes,length,hash);return strcmp(hash,expected)==0; }
static int manifest_bytes_valid(const uint8_t *bytes,size_t length) {
    static const char expected[]=MOONEYE_MANIFEST_SHA256;
    return hash_matches(bytes,length,expected);
}
/* bytes must hold MAX_MANIFEST+1 so an oversize file is detected, not truncated. */
static int manifest_valid(const char *path, uint8_t *bytes, size_t *length) {
    return read_bounded(path,bytes,MAX_MANIFEST,length)&&manifest_bytes_valid(bytes,*length);
}
static const fixture_case *select_case(const char *name) {
    for(size_t i=0;i<sizeof(cases)/sizeof(cases[0]);i++)if(strcmp(name,cases[i].id)==0||strcmp(name,cases[i].alias)==0)return &cases[i];
    return NULL;
}
static int locate_rom(const char *manifest,const char *rom,char path[4096]) {
    size_t n=strlen(manifest); if(n==0||n>=4000)return 0; const char *slash=strrchr(manifest,'/');
    const char *backslash=strrchr(manifest,'\\');
    if(backslash!=NULL&&(slash==NULL||backslash>slash))slash=backslash;
    size_t dir=slash?(size_t)(slash-manifest+1):0; if(dir+strlen(rom)>=4095)return 0;
    memcpy(path,manifest,dir);strcpy(path+dir,rom);return 1;
}
/* rom must hold MAX_ROM+1 bytes; the caller owns the heap buffer (D-27). */
static const char *load_case_rom(const fixture_case *fc,const char *manifest,uint8_t *rom,size_t *length) {
    char path[4096];
    if(!locate_rom(manifest,fc->rom,path))return "invalid-fixture-path";
    FILE *file=fopen(path,"rb");
    if(file==NULL)return errno==ENOENT?"missing-fixture":"fixture-read-error";
    size_t n=fread(rom,1,MAX_ROM+1,file);
    int failed=ferror(file);
    if(fclose(file)!=0)failed=1;
    if(failed)return "fixture-read-error";
    if(n!=MAX_ROM)return "bad-size";
    if(!hash_matches(rom,n,fc->sha256))return "bad-digest";
    *length=n;
    return NULL;
}
static const char *unsupported_core_stop(gbb_stop_reason reason) {
    if(reason==GBB_STOP_UNSUPPORTED_BUS||reason==GBB_STOP_UNSUPPORTED_OPCODE||
       reason==GBB_STOP_LOCKUP||reason==GBB_STOP_INVALID_STATE||reason==GBB_STOP_STOPPED||
       reason==GBB_STOP_HALTED_IDLE||reason==GBB_STOP_NO_PROGRESS)return "unsupported";
    return NULL;
}
static const char *budget_status(uint64_t ticks,uint64_t budget) {
    return ticks>=budget?"timeout":NULL;
}
static int suite_counts_valid(size_t eligible,size_t executed) { return eligible!=0&&eligible==executed; }
typedef struct {
    int pass_callback_seen;
    int fail_callback_seen;
} protocol_progress;
typedef struct {
    int reached_result;
    uint16_t result_pc;
    uint16_t callback_pc;
    const char *callback_result;
    const char *reason;
} protocol_evidence;
static int registers_match(const gbb_trace_record *record,const uint8_t expected[6]) {
    return record->b==expected[0]&&record->c==expected[1]&&record->d==expected[2]&&
           record->e==expected[3]&&record->h==expected[4]&&record->l==expected[5];
}
static const char *protocol_status(const fixture_case *fc,const gbb_trace_record *trace,size_t count,
                                   protocol_progress *progress,protocol_evidence *evidence) {
    for(size_t i=0;i<count;i++) {
        const gbb_trace_record *record=&trace[i];
        if(record->pc==fc->pass_callback_pc)progress->pass_callback_seen=1;
        if(record->pc==fc->fail_callback_pc)progress->fail_callback_seen=1;
        if(record->pc!=fc->result_pc||record->opcode[0]!=0x40)continue;
        evidence->reached_result=1;
        evidence->result_pc=record->pc;
        if(registers_match(record,fc->pass_registers)&&progress->pass_callback_seen) {
            evidence->callback_pc=fc->pass_callback_pc;
            evidence->callback_result="pass";
            evidence->reason=NULL;
            return "pass";
        }
        if(registers_match(record,fc->fail_registers)&&progress->fail_callback_seen) {
            evidence->callback_pc=fc->fail_callback_pc;
            evidence->callback_result="fail";
            evidence->reason=NULL;
            return "fail";
        }
        evidence->reason=!progress->pass_callback_seen&&!progress->fail_callback_seen?
            "callback-not-reached":"unexpected-register-result";
        return "unsupported";
    }
    return NULL;
}
static void retain_recent(gbb_diagnostic_record recent[RECENT_CAPACITY],size_t *used,const gbb_diagnostic_record *add,size_t count) {
    for(size_t i=0;i<count;i++){if(*used<RECENT_CAPACITY)recent[(*used)++]=add[i];else{memmove(recent,recent+1,(RECENT_CAPACITY-1)*sizeof(*recent));recent[RECENT_CAPACITY-1]=add[i];}}
}
static const char *run_guest(const fixture_case *fc,const uint8_t *rom,size_t rom_size,
                             protocol_evidence *evidence,uint64_t *ticks_out,
                             const char **stop_out,
                             gbb_diagnostic_record recent[RECENT_CAPACITY],
                             size_t *recent_count_out) {
    memset(evidence,0,sizeof(*evidence));
    *ticks_out=0;*stop_out="core-load";*recent_count_out=0;
    gbb_instance *m=NULL;if(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)!=GBB_OK||gbb_load_rom(m,rom,rom_size)!=GBB_OK){gbb_destroy(m);return "unsupported";}
    gbb_trace_record trace[TRACE_CAPACITY];gbb_diagnostic_record diagnostics[DIAGNOSTIC_CAPACITY];size_t recent_count=0;
    protocol_progress progress={0};
    uint64_t ticks=0;const char *status=NULL;const char *stop="budget";
    while(ticks<fc->budget&&!status){
        gbb_run_result r=gbb_run_ex(m,fc->budget-ticks< RUN_CHUNK?fc->budget-ticks:RUN_CHUNK,trace,TRACE_CAPACITY,diagnostics,DIAGNOSTIC_CAPACITY);
        ticks+=r.consumed_half_dots;retain_recent(recent,&recent_count,diagnostics,r.diagnostic_count);
        status=protocol_status(fc,trace,r.trace_count,&progress,evidence);
        if(status)break;
        if(r.reason==GBB_STOP_TRACE_FULL||r.reason==GBB_STOP_OUTPUT_FULL)continue;
        const char *core_status=unsupported_core_stop(r.reason);
        if(core_status){status=core_status;stop=r.reason==GBB_STOP_HALTED_IDLE?"halted":"core-stop";break;}
        if(r.consumed_half_dots==0)break;
    }
    if(!status)status=budget_status(ticks,fc->budget);
    if(!status)status="unsupported";
    if(evidence->reached_result)stop="protocol-result";
    else if(strcmp(status,"pass")==0||strcmp(status,"fail")==0)stop="protocol-result";
    *ticks_out=ticks;*stop_out=stop;*recent_count_out=recent_count;
    gbb_destroy(m);
    return status;
}
static int run_one(const fixture_case *fc,const char *manifest,int receipt,size_t eligible,size_t *executed) {
    size_t rom_size=0;
    uint8_t *rom=malloc(MAX_ROM+1);
    if(rom==NULL){fprintf(stderr,"runner-error: ROM buffer allocation failed\n");return 2;}
    const char *fixture_error=load_case_rom(fc,manifest,rom,&rom_size);
    if(fixture_error!=NULL){
        if(receipt)printf("case=%s category=%s status=unsupported reason=%s manifest_sha256=%s source_revision=%s source_tree=%s source_path=%s report_patch_sha256=%s original_rom_sha256=%s fixture_sha256=%s fixture_origin=derived-headless-report-closure profile=DMG-CPU-B boot=skipped protocol=mooneye-ld-b-b protocol_stage=not-reached eligible=%zu executed=%zu\n",fc->id,fc->category,fixture_error,MOONEYE_MANIFEST_SHA256,MOONEYE_SOURCE_REVISION,MOONEYE_SOURCE_TREE,fc->source_path,MOONEYE_PATCH_SHA256,fc->original_sha256,fc->sha256,eligible,*executed);
        free(rom);
        return 3;
    }
    protocol_evidence evidence;uint64_t ticks=0;size_t recent_count=0;const char *stop=NULL;
    gbb_diagnostic_record recent[RECENT_CAPACITY];
    const char *status=run_guest(fc,rom,rom_size,&evidence,&ticks,&stop,recent,&recent_count);
    free(rom);
    ++*executed;
    int code=strcmp(status,"pass")==0?0:strcmp(status,"fail")==0?1:3;
    if(receipt){
        const char *stage=evidence.callback_result?"callback-then-ld-b-b":
            evidence.reached_result?"ld-b-b-without-expected-callback":"not-reached";
        printf("case=%s category=%s status=%s manifest_sha256=%s source_revision=%s source_tree=%s source_path=%s report_patch_sha256=%s builder_revision=%s builder_archive_sha256=%s original_rom_sha256=%s fixture_sha256=%s fixture_origin=derived-headless-report-closure upstream_assertions=unchanged core_revision=%s runner_revision=%s build_qualified=%s profile=DMG-CPU-B boot=skipped protocol=mooneye-ld-b-b protocol_stage=%s callback_result=%s callback_pc=%04x result_pc=%04x protocol_reason=%s ticks=%llu budget=%llu eligible=%zu executed=%zu stop=%s recent=%zu\n",
          fc->id,fc->category,status,MOONEYE_MANIFEST_SHA256,MOONEYE_SOURCE_REVISION,MOONEYE_SOURCE_TREE,fc->source_path,MOONEYE_PATCH_SHA256,MOONEYE_BUILDER_REVISION,MOONEYE_BUILDER_ARCHIVE_SHA256,fc->original_sha256,fc->sha256,GBB_BUILD_REVISION,GBB_BUILD_REVISION,GBB_BUILD_QUALIFIED?"true":"false",stage,evidence.callback_result?evidence.callback_result:"none",evidence.callback_pc,evidence.result_pc,evidence.reason?evidence.reason:"none",(unsigned long long)ticks,(unsigned long long)fc->budget,eligible,*executed,stop,recent_count);
        size_t start=recent_count>8?recent_count-8:0;
        for(size_t i=start;i<recent_count;i++)printf("diag time=%llu kind=%u pc=%04x opcode=%02x address=%04x value=%02x timer=%02x\n",(unsigned long long)recent[i].time_half_dots,(unsigned)recent[i].kind,recent[i].pc,recent[i].opcode,recent[i].address,recent[i].value,recent[i].timer_state);
    }
    return code;
}

static int run_original_tracer(const char *path) {
    FILE *file=fopen(path,"rb");if(!file){fprintf(stderr,"invalid-fixture: cannot open ROM\n");return 2;}
    if(fseek(file,0,SEEK_END)!=0){fclose(file);return 2;}long length=ftell(file);
    if(length<0||length>8*1024*1024||fseek(file,0,SEEK_SET)!=0){fclose(file);fprintf(stderr,"invalid-fixture: size out of bounds\n");return 2;}
    size_t size=(size_t)length;uint8_t *rom=malloc(size);
    if(!rom||fread(rom,1,size,file)!=size){free(rom);fclose(file);return 2;}fclose(file);
    gbb_instance *machine=NULL;
    if(gbb_create(GBB_PROFILE_DMG_CPU_B,&machine)!=GBB_OK||gbb_load_rom(machine,rom,size)!=GBB_OK){free(rom);gbb_destroy(machine);fprintf(stderr,"invalid-fixture: unsupported or malformed ROM\n");return 2;}
    free(rom);gbb_trace_record *trace=calloc(16384,sizeof(*trace));
    if(!trace){gbb_destroy(machine);fprintf(stderr,"runner-error: trace allocation failed\n");return 2;}
    gbb_run_result result=gbb_run(machine,UINT64_C(200000),trace,16384);uint8_t value=gbb_peek_ram(machine,0xC001);
    const char *outcome=result.reason==GBB_STOP_LOCKUP?"lockup":result.reason==GBB_STOP_UNSUPPORTED_OPCODE?"unsupported":
      result.reason==GBB_STOP_UNSUPPORTED_BUS?"unsupported-bus":result.reason==GBB_STOP_TRACE_FULL?"trace-exhausted":
      result.reason==GBB_STOP_HALTED_IDLE?"halted-idle":result.reason==GBB_STOP_STOPPED?"stopped":
      value==0xEE?"guest-failure":result.reason==GBB_STOP_BUDGET&&value==0xA5?"pass":"timeout";
    printf("fixture=original-wram-tracer profile=DMG-CPU-B outcome=%s stop=%s half_dots=%llu trace_records=%zu\n",outcome,
      result.reason==GBB_STOP_BUDGET?"budget":result.reason==GBB_STOP_TRACE_FULL?"trace-full":result.reason==GBB_STOP_UNSUPPORTED_BUS?"unsupported-bus":
      result.reason==GBB_STOP_LOCKUP?"lockup":result.reason==GBB_STOP_HALTED_IDLE?"halted-idle":result.reason==GBB_STOP_STOPPED?"stopped":"unsupported-opcode",
      (unsigned long long)result.consumed_half_dots,result.trace_count);
    for(size_t i=0;i<result.trace_count&&i<12;i++)printf("trace time=%llu pc=%04x opcode=%02x state=A:%02x F:%02x HL:%02x%02x\n",
      (unsigned long long)trace[i].time_half_dots,trace[i].pc,trace[i].opcode[0],trace[i].a,trace[i].f,trace[i].h,trace[i].l);
    gbb_destroy(machine);free(trace);
    return strcmp(outcome,"pass")==0?0:strcmp(outcome,"guest-failure")==0?1:3;
}

static void print_usage(FILE *stream, const char *program) {
    fprintf(stream,
      "Usage:\n"
      "  %s <rom.gb>\n"
      "  %s --manifest <manifest.json> --case <id> [--receipt]\n"
      "  %s --manifest <manifest.json> --suite [--receipt]\n"
      "  %s --acceptance <cases.txt> --case <id> [--receipt] [--failure-dir <dir>]\n"
      "  %s --acceptance <cases.txt> --case <id> --observe [--input-script <file>]\n"
      "      [--frame-digest-at <half-dots>] [--pcm-digest] [--dump-checkpoints <dir>]\n",
      program, program, program, program, program);
}

/* Strict decimal parse for --frame-digest-at: digits only, at most the 600 s script bound. */
static int parse_half_dots(const char *text,uint64_t *out) {
    size_t n=strlen(text);if(n==0||n>10)return 0;
    uint64_t value=0;for(size_t i=0;i<n;i++){if(text[i]<'0'||text[i]>'9')return 0;value=value*10u+(uint64_t)(text[i]-'0');}
    if(value>GBB_ACCEPT_MAX_SCRIPT_HALF_DOTS)return 0;
    *out=value;return 1;
}

int main(int argc,char **argv) {
    if(argc==2&&strncmp(argv[1],"--",2)!=0)return run_original_tracer(argv[1]);
    const char *manifest=NULL,*selected=NULL,*acceptance=NULL;int receipt=0,suite=0;
    gbb_acceptance_options options;memset(&options,0,sizeof(options));
    int observe_only_flag=0;
    for(int i=1;i<argc;i++){
        if(strcmp(argv[i],"--help")==0){print_usage(stdout,argv[0]);return 0;}
        else if(strcmp(argv[i],"--manifest")==0&&i+1<argc)manifest=argv[++i];
        else if(strcmp(argv[i],"--acceptance")==0&&i+1<argc)acceptance=argv[++i];
        else if(strcmp(argv[i],"--case")==0&&i+1<argc)selected=argv[++i];
        else if(strcmp(argv[i],"--suite")==0)suite=1;
        else if(strcmp(argv[i],"--receipt")==0)receipt=1;
        else if(strcmp(argv[i],"--failure-dir")==0&&i+1<argc)options.failure_dir=argv[++i];
        else if(strcmp(argv[i],"--observe")==0)options.observe=1;
        else if(strcmp(argv[i],"--input-script")==0&&i+1<argc){options.observe_input_script=argv[++i];observe_only_flag=1;}
        else if(strcmp(argv[i],"--frame-digest-at")==0&&i+1<argc){
            if(!parse_half_dots(argv[++i],&options.frame_digest_at)){fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
            options.has_frame_digest_at=1;observe_only_flag=1;}
        else if(strcmp(argv[i],"--pcm-digest")==0){options.pcm_only=1;observe_only_flag=1;}
        else if(strcmp(argv[i],"--dump-checkpoints")==0&&i+1<argc){options.dump_dir=argv[++i];observe_only_flag=1;}
        else {fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
    }
    if(acceptance){
        if(manifest||suite||!selected||(observe_only_flag&&!options.observe)){fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
        options.receipt=receipt;options.core_revision=GBB_BUILD_REVISION;options.build_qualified=GBB_BUILD_QUALIFIED;
        return gbb_acceptance_run_file(acceptance,selected,&options);
    }
    if(options.failure_dir||options.observe||observe_only_flag){fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
    if(!manifest||(!suite&&!selected)||(suite&&selected)){fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
    size_t manifest_length=0;
    uint8_t *manifest_bytes=malloc(MAX_MANIFEST+1);
    if(manifest_bytes==NULL){fprintf(stderr,"runner-error: manifest buffer allocation failed\n");return 2;}
    int manifest_ok=manifest_valid(manifest,manifest_bytes,&manifest_length);
    free(manifest_bytes); /* only the digest check needed the bytes */
    if(!manifest_ok){fprintf(stderr,"invalid-manifest\n");return 2;}
    size_t eligible=suite?sizeof(cases)/sizeof(cases[0]):1,executed=0;int suite_code=0;
    if(suite){
        for(size_t i=0;i<eligible;i++){int code=run_one(&cases[i],manifest,receipt,eligible,&executed);if(code!=0&&suite_code==0)suite_code=code;}
        if(receipt)printf("suite eligible=%zu executed=%zu status=%s\n",eligible,executed,suite_counts_valid(eligible,executed)&&suite_code==0?"pass":"fail");
        return suite_counts_valid(eligible,executed)?suite_code:2;
    }
    const fixture_case *fc=select_case(selected);if(!fc){fprintf(stderr,"unknown-case: use --help for invocation forms\n");return 2;}
    return run_one(fc,manifest,receipt,eligible,&executed);
}
