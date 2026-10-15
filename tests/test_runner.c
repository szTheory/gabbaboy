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
    const char *status=run_guest(GBB_RUNNER_PROFILE_DMG,&cases[0],rom,rom_size,&evidence,&ticks,&stop,recent,&recent_count);
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


/* D-29 first control: the admitted MBC5 image run with a wrong mapper type must not pass.
 * Only header byte $147 (MBC5 -> MBC1) changes, and the header checksum is recomputed so a header
 * validity check cannot be the reason the status differs. The unmutated image must pass first. */
static const fixture_case *mbc_case_by_alias(const char *alias) {
    for(size_t i=0;i<sizeof(mbc_cases)/sizeof(mbc_cases[0]);i++)
        if(strcmp(mbc_cases[i].alias,alias)==0)return &mbc_cases[i];
    return NULL;
}

static int type_mutation_on(const fixture_case *fc,uint8_t *rom,size_t rom_size) {
    protocol_evidence evidence;uint64_t ticks=0;size_t recent_count=0;const char *stop=NULL;
    gbb_diagnostic_record recent[RECENT_CAPACITY];
    const char *baseline=run_guest(GBB_RUNNER_PROFILE_DMG,fc,rom,rom_size,&evidence,&ticks,&stop,recent,&recent_count);
    REQUIRE(baseline!=NULL && strcmp(baseline,"pass")==0);

    REQUIRE(rom_size>0x14d && rom[0x147]>=0x19 && rom[0x147]<=0x1e); /* an MBC5 cartridge type */
    rom[0x147]=0x01;
    uint8_t checksum=0;
    for(size_t i=0x134;i<=0x14c;i++)checksum=(uint8_t)(checksum-rom[i]-1u);
    rom[0x14d]=checksum;

    const char *status=run_guest(GBB_RUNNER_PROFILE_DMG,fc,rom,rom_size,&evidence,&ticks,&stop,recent,&recent_count);
    REQUIRE(status!=NULL && strcmp(status,"pass")!=0);
    printf("control=mbc5-type-byte-mutation alias=%s header147=01 header_checksum=%02x status=%s stop=%s ticks=%llu\n",
           fc->alias,checksum,status,stop!=NULL?stop:"none",(unsigned long long)ticks);
    return 0;
}

static int run_type_mutation(const char *path) {
    const fixture_case *fc=mbc_case_by_alias("mbc5_rom_512kb");
    REQUIRE(fc!=NULL);
    size_t rom_size=0;
    uint8_t *rom=malloc(fc->size_bytes+1);
    REQUIRE(rom!=NULL);
    int code=1;
    if(read_bounded(path,rom,fc->size_bytes,&rom_size)&&rom_size==fc->size_bytes&&hash_matches(rom,rom_size,fc->sha256)){
        code=type_mutation_on(fc,rom,rom_size);
    }else{
        fprintf(stderr,"%s:%d: admitted MBC5 fixture did not load\n",__FILE__,__LINE__);
    }
    free(rom);
    return code;
}

/* The runner's compiled rows are gated by the manifest SHA, so a tampered manifest never reaches them
 * through the command line; this control reads the disposition from the tampered copy and applies it to
 * the compiled row to prove that a failing guest cannot be relabelled as passing. */
static const fixture_case *cgb_case_by_alias(const char *alias) {
    for(size_t i=0;i<sizeof(cgb_cases)/sizeof(cgb_cases[0]);i++)
        if(strcmp(cgb_cases[i].alias,alias)==0)return &cgb_cases[i];
    return NULL;
}
/* The string value of `"key"` inside [from,to), tolerant of the whitespace around the colon (CMake rewrites
 * JSON as `"key" : "value"`). A key like "expect_stop" never matches "expect" because the closing quote is part
 * of the needle. */
static int json_string_in(const char *from,const char *to,const char *key,char out[32]) {
    char needle[64];
    if(snprintf(needle,sizeof(needle),"\"%s\"",key)>=(int)sizeof(needle))return 0;
    for(const char *at=from;at<to;at++){
        const char *hit=strstr(at,needle);if(hit==NULL||hit>=to)return 0;
        const char *p=hit+strlen(needle);
        while(p<to&&(*p==' '||*p=='\t'||*p=='\n'||*p=='\r'))p++;
        if(p>=to||*p!=':'){at=hit;continue;}
        p++;while(p<to&&(*p==' '||*p=='\t'||*p=='\n'||*p=='\r'))p++;
        if(p>=to||*p!='"'){at=hit;continue;}
        p++;const char *quote=memchr(p,'"',(size_t)(to-p));
        if(quote==NULL||quote-p>=31)return 0;
        memcpy(out,p,(size_t)(quote-p));out[quote-p]=0;return 1;
    }
    return 0;
}
/* A string field of the fixture object whose alias is given, read from raw manifest JSON text. The object
 * is bounded by the braces around the alias (fixture objects hold no nested objects), so the key cannot come
 * from another row. */
static int manifest_fixture_string(const char *json,const char *alias,const char *key,char out[32]) {
    const char *fixtures=strstr(json,"\"fixtures\"");if(fixtures==NULL)return 0;
    for(const char *open=strchr(fixtures,'{');open!=NULL;open=strchr(open+1,'{')){
        const char *close=strchr(open,'}');if(close==NULL)return 0;
        char found[32];
        if(json_string_in(open,close,"alias",found)&&strcmp(found,alias)==0)return json_string_in(open,close,key,out);
    }
    return 0;
}
/* Apply the manifest's observed disposition while leaving its author expectation untouched. */
static int apply_manifest_disposition(fixture_case *row,const char *disposition) {
    if(strcmp(disposition,"pass")==0){row->observed_disposition=GBB_OBSERVED_PASS;return 1;}
    if(strcmp(disposition,"expected-unsupported")==0){row->observed_disposition=GBB_OBSERVED_UNSUPPORTED;return 1;}
    if(strcmp(disposition,"expected-failure")==0){row->observed_disposition=GBB_OBSERVED_FAILURE;return 1;}
    return 0;
}
static int run_cgb_row(const fixture_case *row,const char *dir,const char **status_out,const char **reason_out,int *code_out,protocol_evidence *evidence_out) {
    char path[4096];
    if(snprintf(path,sizeof(path),"%s/%s",dir,row->rom)>=(int)sizeof(path))return 0;
    uint8_t *rom=malloc(row->size_bytes+1);if(rom==NULL)return 0;
    size_t length=0;
    int loaded=read_bounded(path,rom,row->size_bytes,&length)&&length==row->size_bytes&&hash_matches(rom,length,row->sha256);
    if(loaded){
        protocol_evidence evidence;uint64_t ticks=0;size_t recent_count=0;const char *stop=NULL;stop_evidence stopped;
        gbb_diagnostic_record recent[RECENT_CAPACITY];
        const char *run=run_guest_stop(row_profile(row),row,rom,length,&evidence,&ticks,&stop,recent,&recent_count,&stopped);
        if(evidence_out!=NULL)*evidence_out=evidence;
        *code_out=row_outcome(row,run,&evidence,&stopped,status_out,reason_out);
    }
    free(rom);
    return loaded;
}
static int run_expected_disposition_controls(const char *tampered_manifest,const char *untampered_manifest,const char *dir) {
    uint8_t *tampered=malloc(MAX_MANIFEST+1),*untampered=malloc(MAX_MANIFEST+1);
    REQUIRE(tampered!=NULL&&untampered!=NULL);
    size_t n=0,m=0;
    REQUIRE(read_bounded(tampered_manifest,tampered,MAX_MANIFEST,&n)&&read_bounded(untampered_manifest,untampered,MAX_MANIFEST,&m));
    tampered[n]=0;untampered[m]=0;
    char tampered_expect[32],untampered_expect[32],tampered_disposition[32],untampered_disposition[32];
    REQUIRE(manifest_fixture_string((const char *)tampered,"boot_hwio-C","expect",tampered_expect));
    REQUIRE(manifest_fixture_string((const char *)untampered,"boot_hwio-C","expect",untampered_expect));
    REQUIRE(manifest_fixture_string((const char *)tampered,"boot_hwio-C","observed_disposition",tampered_disposition));
    REQUIRE(manifest_fixture_string((const char *)untampered,"boot_hwio-C","observed_disposition",untampered_disposition));
    REQUIRE(strcmp(tampered_expect,"pass")==0&&strcmp(untampered_expect,"pass")==0); /* source assertion stays pass */
    REQUIRE(strcmp(tampered_disposition,"pass")==0);                                  /* tamper is in the observation */
    REQUIRE(strcmp(untampered_disposition,"expected-failure")==0);
    free(tampered);free(untampered);
    const fixture_case *compiled=cgb_case_by_alias("boot_hwio-C");REQUIRE(compiled!=NULL);
    const char *status=NULL,*reason=NULL;int code=-1;
    protocol_evidence evidence;

    /* The raw guest verdict is fail at the source's exact fail callback and result assertion. */
    fixture_case row=*compiled;
    row.observed_disposition=GBB_OBSERVED_PASS;
    REQUIRE(run_cgb_row(&row,dir,&status,&reason,&code,&evidence));
    REQUIRE(strcmp(status,"fail")==0&&code==1);
    REQUIRE(evidence.reached_result&&evidence.result_pc==row.result_pc);
    REQUIRE(evidence.callback_result!=NULL&&strcmp(evidence.callback_result,"fail")==0);
    REQUIRE(evidence.callback_pc==row.fail_callback_pcs[0]);
    printf("observed=fail alias=boot_hwio-C callback_result=%s callback_pc=%04x result_pc=%04x\n",evidence.callback_result,evidence.callback_pc,evidence.result_pc);

    const fixture_case *unused=cgb_case_by_alias("unused_hwio-C");REQUIRE(unused!=NULL);
    row=*unused;row.observed_disposition=GBB_OBSERVED_PASS;
    REQUIRE(run_cgb_row(&row,dir,&status,&reason,&code,&evidence));
    REQUIRE(strcmp(status,"fail")==0&&code==1&&evidence.reached_result&&evidence.result_pc==row.result_pc);
    REQUIRE(evidence.callback_result!=NULL&&strcmp(evidence.callback_result,"fail")==0);
    REQUIRE(evidence.callback_pc==row.fail_callback_pcs[0]);
    printf("observed=fail alias=unused_hwio-C callback_result=%s callback_pc=%04x result_pc=%04x\n",evidence.callback_result,evidence.callback_pc,evidence.result_pc);

    /* The pinned exact signature may be reported as xfail, never as a guest pass. */
    row=*compiled;
    REQUIRE(apply_manifest_disposition(&row,untampered_disposition));
    REQUIRE(run_cgb_row(&row,dir,&status,&reason,&code,&evidence));
    REQUIRE(strcmp(status,"xfail")==0&&strcmp(reason,"declared-failure-signature")==0&&code==0);
    printf("control=exact-failure-disposition alias=boot_hwio-C status=%s observed=fail callback_pc=%04x result_pc=%04x\n",status,evidence.callback_pc,evidence.result_pc);
    row=*unused;row.observed_disposition=GBB_OBSERVED_FAILURE;
    REQUIRE(run_cgb_row(&row,dir,&status,&reason,&code,&evidence));
    REQUIRE(strcmp(status,"xfail")==0&&strcmp(reason,"declared-failure-signature")==0&&code==0);
    printf("control=exact-failure-disposition alias=unused_hwio-C status=%s observed=fail callback_pc=%04x result_pc=%04x\n",status,evidence.callback_pc,evidence.result_pc);

    /* A changed observed disposition that claims pass still fails on the real failing guest. */
    row=*compiled;
    REQUIRE(apply_manifest_disposition(&row,tampered_disposition));
    REQUIRE(run_cgb_row(&row,dir,&status,&reason,&code,&evidence));
    REQUIRE(strcmp(status,"fail")==0&&code==1&&strcmp(evidence.callback_result,"fail")==0);
    printf("control=xfail-tampered-to-pass alias=boot_hwio-C author_expect=pass status=%s observed=fail code=%d\n",status,code);

    /* Reclassifying the same terminal protocol result as an old FF76 stop remains a failure. */
    row=*compiled;row.observed_disposition=GBB_OBSERVED_UNSUPPORTED;row.expect_stop_address=0xFF76u;
    REQUIRE(run_cgb_row(&row,dir,&status,&reason,&code,&evidence));
    REQUIRE(strcmp(status,"fail")==0&&strcmp(reason,"no-unsupported-bus-stop")==0&&code==1);
    printf("control=stale-unsupported-disposition alias=boot_hwio-C status=%s reason=%s code=%d\n",status,reason,code);

    /* A changed failure callback invalidates the exact xfail signature. */
    row=*compiled;row.fail_callback_pcs[0]++;
    REQUIRE(run_cgb_row(&row,dir,&status,&reason,&code,&evidence));
    REQUIRE(strcmp(status,"unexpected-failure")==0&&code==1);
    printf("control=expected-failure-wrong-callback alias=boot_hwio-C status=%s reason=%s code=%d\n",status,reason,code);

    /* A passing ROM cannot be called an expected failure. */
    const fixture_case *passing=cgb_case_by_alias("boot_regs-cgb");REQUIRE(passing!=NULL);
    row=*passing;row.observed_disposition=GBB_OBSERVED_FAILURE;
    REQUIRE(run_cgb_row(&row,dir,&status,&reason,&code,&evidence));
    REQUIRE(strcmp(status,"unexpected-pass")==0&&code==1);
    printf("control=expected-failure-pass-is-failure alias=boot_regs-cgb status=%s code=%d\n",status,code);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    if (strcmp(argv[1],"cgb_mooneye_expected_disposition_controls")==0)
        return argc==5?run_expected_disposition_controls(argv[2],argv[3],argv[4]):2;
    if (strcmp(argv[1],"runner_guest_failure")==0)
        return argc==3?run_induced_guest_failure(argv[2]):2;
    if (strcmp(argv[1],"mooneye_mbc_type_mutation")==0)
        return argc==3?run_type_mutation(argv[2]):2;
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
