#include "gabbaboy/gabbaboy.h"

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

typedef struct {
    const char *id;
    const char *alias;
    const char *category;
    const char *rom;
    const char *sha256;
    const char *protocol_pass;
    const char *protocol_fail;
    uint64_t budget;
} fixture_case;

static const fixture_case cases[] = {
    {"mooneye-acceptance-instr-daa", "daa", "cpu", "daa.gb", "96cd0e02a85f6f035b1c1947d36a8ad2d8e51963f636b833f05559f021eef57e", "03,05,08,0d,15,22", "42,42,42,42,42,42", UINT64_C(2000000)},
    {"mooneye-acceptance-timer-tim00", "tim00", "timer", "tim00.gb", "6edc430a09522294c96d1eef63a0f1a99078f4401060980048ec5a68640e11bd", "03,05,08,0d,15,22", "42,42,42,42,42,42", UINT64_C(200000)},
    {"mooneye-acceptance-timer-tim00-div-trigger", "tim00-div-trigger", "timer", "tim00_div_trigger.gb", "468d426c4fe6a850a28f4116bd127d471be6adf2ef5dd0f89f2db67ffe212242", "03,05,08,0d,15,22", "42,42,42,42,42,42", UINT64_C(200000)}
};

/* Small standalone SHA-256 implementation keeps fixture verification offline. */
typedef struct { uint32_t h[8]; uint64_t bits; uint8_t block[64]; size_t used; } sha256_ctx;
static const uint32_t sha_k[64] = {
  0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
  0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
  0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
  0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
  0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
  0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
  0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
  0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
};
static uint32_t rotr(uint32_t x, unsigned n) { return (x >> n) | (x << (32u - n)); }
static void sha_transform(sha256_ctx *c, const uint8_t *p) {
    uint32_t w[64];
    for (unsigned i=0;i<16;i++) w[i]=((uint32_t)p[i*4]<<24)|((uint32_t)p[i*4+1]<<16)|((uint32_t)p[i*4+2]<<8)|p[i*4+3];
    for (unsigned i=16;i<64;i++) { uint32_t a=rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3); uint32_t b=rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10); w[i]=w[i-16]+a+w[i-7]+b; }
    uint32_t a=c->h[0],b=c->h[1],d=c->h[3],e=c->h[4],f=c->h[5],g=c->h[6],h=c->h[7],cc=c->h[2];
    for (unsigned i=0;i<64;i++) { uint32_t s1=rotr(e,6)^rotr(e,11)^rotr(e,25), ch=(e&f)^(~e&g); uint32_t t1=h+s1+ch+sha_k[i]+w[i]; uint32_t s0=rotr(a,2)^rotr(a,13)^rotr(a,22), maj=(a&b)^(a&cc)^(b&cc); uint32_t t2=s0+maj; h=g;g=f;f=e;e=d+t1;d=cc;cc=b;b=a;a=t1+t2; }
    c->h[0]+=a;c->h[1]+=b;c->h[2]+=cc;c->h[3]+=d;c->h[4]+=e;c->h[5]+=f;c->h[6]+=g;c->h[7]+=h;
}
static void sha_init(sha256_ctx *c) { static const uint32_t iv[8]={0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u}; memcpy(c->h,iv,sizeof(iv));c->bits=0;c->used=0; }
static void sha_update(sha256_ctx *c,const uint8_t *p,size_t n) { c->bits+=(uint64_t)n*8u; while(n){size_t k=64-c->used;if(k>n)k=n;memcpy(c->block+c->used,p,k);c->used+=k;p+=k;n-=k;if(c->used==64){sha_transform(c,c->block);c->used=0;}} }
static void sha_final(sha256_ctx *c,char out[65]) { c->block[c->used++]=0x80;if(c->used>56){while(c->used<64)c->block[c->used++]=0;sha_transform(c,c->block);c->used=0;}while(c->used<56)c->block[c->used++]=0;for(unsigned i=0;i<8;i++)c->block[63-i]=(uint8_t)(c->bits>>(i*8));sha_transform(c,c->block);for(unsigned i=0;i<8;i++)snprintf(out+i*8,9,"%08x",c->h[i]);out[64]='\0'; }

static int read_bounded(const char *path, uint8_t *buffer, size_t capacity, size_t *length) {
    FILE *f=fopen(path,"rb"); if(!f)return 0;
    size_t n=fread(buffer,1,capacity+1,f); int failed=ferror(f); fclose(f);
    if(failed||n>capacity)return 0; *length=n; return 1;
}
static int hash_matches(const uint8_t *bytes,size_t length,const char *expected) { sha256_ctx c;char hash[65];sha_init(&c);sha_update(&c,bytes,length);sha_final(&c,hash);return strcmp(hash,expected)==0; }
static int manifest_bytes_valid(const uint8_t *bytes,size_t length) {
    static const char expected[]="76204bc792a5a767f3d7430edfe5542698953507fe268de6a0154b7cb02bcc3e";
    return hash_matches(bytes,length,expected);
}
static int manifest_valid(const char *path, uint8_t bytes[MAX_MANIFEST+1], size_t *length) {
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
static const char *load_case_rom(const fixture_case *fc,const char *manifest,uint8_t rom[MAX_ROM+1],size_t *length) {
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
static const char *protocol_status(const gbb_trace_record *trace,size_t count) {
    for(size_t i=0;i<count;i++) if(trace[i].opcode[0]==0x40) {
        if(trace[i].b==3&&trace[i].c==5&&trace[i].d==8&&trace[i].e==13&&trace[i].h==21&&trace[i].l==34)return "pass";
        if(trace[i].b==0x42&&trace[i].c==0x42&&trace[i].d==0x42&&trace[i].e==0x42&&trace[i].h==0x42&&trace[i].l==0x42)return "fail";
    }
    return NULL;
}
static void retain_recent(gbb_diagnostic_record recent[RECENT_CAPACITY],size_t *used,const gbb_diagnostic_record *add,size_t count) {
    for(size_t i=0;i<count;i++){if(*used<RECENT_CAPACITY)recent[(*used)++]=add[i];else{memmove(recent,recent+1,(RECENT_CAPACITY-1)*sizeof(*recent));recent[RECENT_CAPACITY-1]=add[i];}}
}
static int run_one(const fixture_case *fc,const char *manifest,int receipt,size_t eligible,size_t *executed) {
    uint8_t rom[MAX_ROM+1];size_t rom_size=0;
    const char *fixture_error=load_case_rom(fc,manifest,rom,&rom_size);
    if(fixture_error!=NULL){
        if(receipt)printf("case=%s category=%s status=unsupported reason=%s source_revision=31510e12eea6286d36eea060a6adde755e1067aa fixture_sha256=%s profile=DMG-CPU-B boot=skipped protocol=mooneye-ld-b-b eligible=%zu executed=%zu\n",fc->id,fc->category,fixture_error,fc->sha256,eligible,*executed);
        return 3;
    }
    gbb_instance *m=NULL;if(gbb_create(GBB_PROFILE_DMG_CPU_B,&m)!=GBB_OK||gbb_load_rom(m,rom,rom_size)!=GBB_OK){gbb_destroy(m);return 3;}
    gbb_trace_record trace[TRACE_CAPACITY];gbb_diagnostic_record diagnostics[DIAGNOSTIC_CAPACITY],recent[RECENT_CAPACITY];size_t recent_count=0;
    uint64_t ticks=0;const char *status=NULL;const char *stop="budget";
    while(ticks<fc->budget&&!status){
        gbb_run_result r=gbb_run_ex(m,fc->budget-ticks< RUN_CHUNK?fc->budget-ticks:RUN_CHUNK,trace,TRACE_CAPACITY,diagnostics,DIAGNOSTIC_CAPACITY);
        ticks+=r.consumed_half_dots;retain_recent(recent,&recent_count,diagnostics,r.diagnostic_count);
        status=protocol_status(trace,r.trace_count);
        if(status)break;
        if(r.reason==GBB_STOP_TRACE_FULL||r.reason==GBB_STOP_OUTPUT_FULL)continue;
        const char *core_status=unsupported_core_stop(r.reason);
        if(core_status){status=core_status;stop=r.reason==GBB_STOP_HALTED_IDLE?"halted":"core-stop";break;}
        if(r.consumed_half_dots==0)break;
    }
    if(!status)status=budget_status(ticks,fc->budget);
    if(!status)status="unsupported";
    ++*executed;
    int code=strcmp(status,"pass")==0?0:strcmp(status,"fail")==0?1:3;
    if(receipt){
        printf("case=%s category=%s status=%s source_revision=31510e12eea6286d36eea060a6adde755e1067aa core_revision=%s runner_revision=%s build_qualified=%s fixture_sha256=%s profile=DMG-CPU-B boot=skipped protocol=mooneye-ld-b-b ticks=%llu budget=%llu eligible=%zu executed=%zu stop=%s recent=%zu\n",
          fc->id,fc->category,status,GBB_BUILD_REVISION,GBB_BUILD_REVISION,GBB_BUILD_QUALIFIED?"true":"false",fc->sha256,(unsigned long long)ticks,(unsigned long long)fc->budget,eligible,*executed,stop,recent_count);
        size_t start=recent_count>8?recent_count-8:0;
        for(size_t i=start;i<recent_count;i++)printf("diag time=%llu kind=%u pc=%04x opcode=%02x address=%04x value=%02x timer=%02x\n",(unsigned long long)recent[i].time_half_dots,(unsigned)recent[i].kind,recent[i].pc,recent[i].opcode,recent[i].address,recent[i].value,recent[i].timer_state);
    }
    gbb_destroy(m);return code;
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

int main(int argc,char **argv) {
    if(argc==2&&strncmp(argv[1],"--",2)!=0)return run_original_tracer(argv[1]);
    const char *manifest=NULL,*selected=NULL;int receipt=0,suite=0;
    for(int i=1;i<argc;i++){
        if(strcmp(argv[i],"--manifest")==0&&i+1<argc)manifest=argv[++i];
        else if(strcmp(argv[i],"--case")==0&&i+1<argc)selected=argv[++i];
        else if(strcmp(argv[i],"--suite")==0)suite=1;
        else if(strcmp(argv[i],"--receipt")==0)receipt=1;
        else {fprintf(stderr,"invalid-arguments\n");return 2;}
    }
    if(!manifest||(!suite&&!selected)||(suite&&selected)){fprintf(stderr,"invalid-arguments\n");return 2;}
    uint8_t manifest_bytes[MAX_MANIFEST+1];size_t manifest_length=0;
    if(!manifest_valid(manifest,manifest_bytes,&manifest_length)){fprintf(stderr,"invalid-manifest\n");return 2;}
    size_t eligible=suite?sizeof(cases)/sizeof(cases[0]):1,executed=0;int suite_code=0;
    if(suite){
        for(size_t i=0;i<eligible;i++){int code=run_one(&cases[i],manifest,receipt,eligible,&executed);if(code!=0&&suite_code==0)suite_code=code;}
        if(receipt)printf("suite eligible=%zu executed=%zu status=%s\n",eligible,executed,suite_counts_valid(eligible,executed)&&suite_code==0?"pass":"fail");
        return suite_counts_valid(eligible,executed)?suite_code:2;
    }
    const fixture_case *fc=select_case(selected);if(!fc){fprintf(stderr,"unknown-case\n");return 2;}
    return run_one(fc,manifest,receipt,eligible,&executed);
}
