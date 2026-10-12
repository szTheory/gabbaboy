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
/* Sibling mbc2/mbc5 suite (Phase 8): admitted by the SHA-256 of its raw manifest bytes, like the parent. */
#define MOONEYE_MBC_MANIFEST_SHA256 "9800c795fcf033abd6bda2e171af6c22d27e745f2b5946fc49bd0f9ce2fb5801"
/* Phase 10 CGB-profile suite (D-26): admitted by the SHA-256 of its raw manifest bytes, like the others. */
#define MOONEYE_CGB_MANIFEST_SHA256 "e17346ad051482b767ad637bdd66d2e5916209c46b8cf7372a6d5bf1d2e6e844"

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
    size_t size_bytes;              /* exact ROM length; replaces the fixed 32 KiB check (D-28) */
    uint16_t fail_callback_pcs[6];  /* fail_callback_pc stays the scalar the parent tests read */
    uint8_t fail_callback_count;
    /* Trailing so every pre-Phase-10 positional initialiser keeps its meaning (D-26). */
    gbb_profile profile;            /* 0 means DMG-CPU-B; the run profile of this row (D-25) */
    uint8_t expect_stop;            /* 0: the row must pass; 1: it must stop on unsupported-bus */
    uint16_t expect_stop_address;   /* the one address that stop must name when expect_stop is 1 */
} fixture_case;
/* The parent and mbc rows predate the column: 0 selects the DMG profile. */
static gbb_profile row_profile(const fixture_case *fc) { return fc->profile==0?GBB_RUNNER_PROFILE_DMG:fc->profile; }

static const fixture_case cases[] = {
    {"mooneye-acceptance-instr-daa", "daa", "cpu", "daa.gb",
     "3a39eda77a09b817e4e38004a3d117990565fb797e8a4f470920f1b7608f0a08",
     "96cd0e02a85f6f035b1c1947d36a8ad2d8e51963f636b833f05559f021eef57e",
     "acceptance/instr/daa.s", 0x0166, 0x01b3, 0x409a,
     {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(2000000),
     MAX_ROM, {0x01b3}, 1},
    {"mooneye-acceptance-timer-tim00", "tim00", "timer", "tim00.gb",
     "476b2332de3f2d6604f8e1478daa8cbc7c59c89c50837fd47cc95e96e784d4f7",
     "6edc430a09522294c96d1eef63a0f1a99078f4401060980048ec5a68640e11bd",
     "acceptance/timer/tim00.s", 0x4000, 0x4000, 0x4327,
     {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(200000),
     MAX_ROM, {0x4000}, 1},
    {"mooneye-acceptance-timer-tim00-div-trigger", "tim00-div-trigger", "timer", "tim00_div_trigger.gb",
     "566da853858061c69866c47cc31b85b1fef003d4c088c8e8dbb26973da9944da",
     "468d426c4fe6a850a28f4116bd127d471be6adf2ef5dd0f89f2db67ffe212242",
     "acceptance/timer/tim00_div_trigger.s", 0x4000, 0x4000, 0x4327,
     {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(200000),
     MAX_ROM, {0x4000}, 1}
};

/* One row per line, each starting with the id literal: cmake/VerifyMooneyeMbc.cmake parses these against
 * fixtures/mooneye-mbc/manifest.json. Fail PCs come from the linker .sym (tests/scripts/reproduce-mooneye-mbc.sh --facts). */
static const fixture_case mbc_cases[] = {
/* gbb:mbc-rows-begin */
    {"mooneye-emulator-only-mbc2-bits-ramg", "mbc2_bits_ramg", "mbc2", "mbc2_bits_ramg.gb", "7eb87a09e2214693d978b754957f6dc09f79095fb1bbca7089c9ca7e563115ae", "none", "emulator-only/mbc2/bits_ramg.s", 0x01d7, 0x0218, 0x407e, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(97200000), 32768u, {0x0218, 0x0255, 0x029c, 0x02c1}, 4},
    {"mooneye-emulator-only-mbc2-bits-romb", "mbc2_bits_romb", "mbc2", "mbc2_bits_romb.gb", "f382f82c0025093b52575bcd35715131b681392f28a81d88180db973b5ff8090", "none", "emulator-only/mbc2/bits_romb.s", 0x01c0, 0x0174, 0x407e, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(49600000), 65536u, {0x0174, 0x01f8}, 2},
    {"mooneye-emulator-only-mbc2-bits-unused", "mbc2_bits_unused", "mbc2", "mbc2_bits_unused.gb", "d33bed573c162b3384048dddc10c3b0d0d89dbb9023d1608cd70286988c0fa77", "none", "emulator-only/mbc2/bits_unused.s", 0x018d, 0x01cc, 0x407e, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(46200000), 262144u, {0x01cc}, 1},
    {"mooneye-emulator-only-mbc2-ram", "mbc2_ram", "mbc2", "mbc2_ram.gb", "5b82d04e284a0c396271e4df0d345c7383d1c86467675a272d9a4e286f790f13", "none", "emulator-only/mbc2/ram.s", 0x029c, 0x06f8, 0x4071, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(5300000), 32768u, {0x06f8, 0x0719, 0x073a, 0x075b, 0x077c, 0x079d}, 6},
    {"mooneye-emulator-only-mbc2-rom-512kb", "mbc2_rom_512kb", "mbc2", "mbc2_rom_512kb.gb", "4c7a8a58e3bf5a45afb71b079aead912f336a13972ff93b59f964bedbc87fda5", "none", "emulator-only/mbc2/rom_512kb.s", 0x0207, 0x0175, 0x4071, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(100000), 65536u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc2-rom-1Mb", "mbc2_rom_1Mb", "mbc2", "mbc2_rom_1Mb.gb", "7eba692d8f426d1b6187095a9c14a99ef5ea80534d996949bca8bf0bd9e77cc3", "none", "emulator-only/mbc2/rom_1Mb.s", 0x0207, 0x0175, 0x4071, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(100000), 131072u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc2-rom-2Mb", "mbc2_rom_2Mb", "mbc2", "mbc2_rom_2Mb.gb", "32530509d8182718b005e183259cb6eaeeb7db15c6b634ebdc362016591dadec", "none", "emulator-only/mbc2/rom_2Mb.s", 0x0207, 0x0175, 0x4071, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(100000), 262144u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc5-rom-512kb", "mbc5_rom_512kb", "mbc5", "mbc5_rom_512kb.gb", "701cce7a923f2291756c364ad587b0f3a1ca3c12ed904e61323614ce6ddddc0b", "none", "emulator-only/mbc5/rom_512kb.s", 0x0216, 0x0175, 0x4072, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(900000), 65536u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc5-rom-1Mb", "mbc5_rom_1Mb", "mbc5", "mbc5_rom_1Mb.gb", "9d9d21129bfc91b5c22d9d6a30a08bdee309786ad21532cb8817e19295fffe69", "none", "emulator-only/mbc5/rom_1Mb.s", 0x0216, 0x0175, 0x4072, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(900000), 131072u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc5-rom-2Mb", "mbc5_rom_2Mb", "mbc5", "mbc5_rom_2Mb.gb", "5a152aa873f104f6acf865f642b1cf86abc5f2cceea81118f238794aaf9f70ab", "none", "emulator-only/mbc5/rom_2Mb.s", 0x0216, 0x0175, 0x4072, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(900000), 262144u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc5-rom-4Mb", "mbc5_rom_4Mb", "mbc5", "mbc5_rom_4Mb.gb", "4173c92d61533ed5f3cdd8f2ca83d3701ca042b28bceeed1021a79065368fa86", "none", "emulator-only/mbc5/rom_4Mb.s", 0x0216, 0x0175, 0x4072, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(900000), 524288u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc5-rom-8Mb", "mbc5_rom_8Mb", "mbc5", "mbc5_rom_8Mb.gb", "176cd6f9a16519ba30f7d0cec3d46226ef304f3ad54e41d6d23974a03e6157a1", "none", "emulator-only/mbc5/rom_8Mb.s", 0x0216, 0x0175, 0x4072, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(900000), 1048576u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc5-rom-16Mb", "mbc5_rom_16Mb", "mbc5", "mbc5_rom_16Mb.gb", "65602bf590e9c2f5d22e3db3597c95d763a8fe562556bac9c8a82baf3ed3a59e", "none", "emulator-only/mbc5/rom_16Mb.s", 0x0216, 0x0175, 0x4072, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(900000), 2097152u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc5-rom-32Mb", "mbc5_rom_32Mb", "mbc5", "mbc5_rom_32Mb.gb", "f37b1e7af46d69e5c42df0e7e421e306b48b6c6e789cb35e091e41c0fe67e668", "none", "emulator-only/mbc5/rom_32Mb.s", 0x0216, 0x0175, 0x4072, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(900000), 4194304u, {0x0175}, 1},
    {"mooneye-emulator-only-mbc5-rom-64Mb", "mbc5_rom_64Mb", "mbc5", "mbc5_rom_64Mb.gb", "f1148d3cc631e330b991b3f34d728de5b3789b00b80b9778fb08a9bbb59efef7", "none", "emulator-only/mbc5/rom_64Mb.s", 0x0216, 0x0175, 0x4072, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(900000), 8388608u, {0x0175}, 1},
/* gbb:mbc-rows-end */
};

/* Phase 10 CGB-profile derivatives (D-26): the profile, and the stop an expected-unsupported row must
 * make, are columns of the row. One row per line, each starting with the id literal:
 * cmake/VerifyMooneyeCgb.cmake pc-table mode parses these against fixtures/mooneye-cgb/manifest.json.
 * Assert-style ROMs (boot_regs-cgb, boot_div-cgbABCDE) end in one shared check_asserts_cb callback, so
 * their pass and fail callback PCs are the same, as for tim00; the ld b,b registers decide. PCs come from
 * the linker .sym (tests/scripts/reproduce-mooneye-cgb.sh --facts). */
static const fixture_case cgb_cases[] = {
/* gbb:cgb-rows-begin */
    {"mooneye-misc-boot-regs-cgb", "boot_regs-cgb", "post-boot-registers", "boot_regs-cgb.gb", "77eb76b5448ff9e6bb885e789b0ce0a9113146bc3f0949f3655587968dae5c77", "86c4ab93428b849864409cd10bcfdb231d2dd066c200c2791af1faa6eeb23dd1", "misc/boot_regs-cgb.s", 0x4000, 0x4000, 0x4327, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(500000), 32768u, {0x4000, 0x01da}, 2, GBB_PROFILE_CGB_CPU_E, 0, 0x0000},
    {"mooneye-misc-boot-div-cgbabcde", "boot_div-cgbABCDE", "post-boot-div", "boot_div-cgbABCDE.gb", "7887a53a1b308c4f35c4e1e94a0ffb67397c6d213c034a706a7f92258ba93f90", "24b1be8fe190fe5c585b245203e95ab756fe7ff68e342d446395392ca8f9b822", "misc/boot_div-cgbABCDE.s", 0x4000, 0x4000, 0x4327, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(500000), 32768u, {0x4000}, 1, GBB_PROFILE_CGB_CPU_E, 0, 0x0000},
    {"mooneye-misc-boot-hwio-c", "boot_hwio-C", "post-boot-hwio", "boot_hwio-C.gb", "267eb659c4995ad7fa38b7d442a6076a630cf88824fe2d16e5de5927c7a8b7a9", "d69232d9b71b4cfccc710f6693363a7b5b627f0bf0bb7333997cdee19cfa8b86", "misc/boot_hwio-C.s", 0x01ce, 0x01f5, 0x4067, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(2000000), 32768u, {0x01f5}, 1, GBB_PROFILE_CGB_CPU_E, 1, 0xFF76},
    {"mooneye-misc-unused-hwio-c", "unused_hwio-C", "unused-hwio", "unused_hwio-C.gb", "a44d65497bbec81ec1ba51a06ad1177b2193f6ca1e829a9cb2307dea8ab4cc27", "7ab9e7ccbefe0740f55b7f6172a8780e8c67632f979365bc8381f5bf65e7929b", "misc/bits/unused_hwio-C.s", 0x1a02, 0x1a31, 0x4070, {3, 5, 8, 13, 21, 34}, {0x42, 0x42, 0x42, 0x42, 0x42, 0x42}, UINT64_C(2000000), 32768u, {0x1a31}, 1, GBB_PROFILE_CGB_CPU_E, 1, 0xFF76}
/* gbb:cgb-rows-end */
};

#define MAX_SUITE_CATEGORIES 8u
typedef struct {
    const char *manifest_sha256;
    const char *patch_sha256;
    const fixture_case *cases;
    size_t count;
    const char *const *categories; /* printed in the "suite categories" line; NULL prints none */
    size_t category_count;
} suite_def;
static const char *const mbc_categories[] = {"mbc2", "mbc5"};
static const char *const cgb_categories[] = {"post-boot-registers", "post-boot-div", "post-boot-hwio", "unused-hwio"};

/* The runner admits a suite only by the exact SHA-256 of its manifest bytes (D-28). */
static const suite_def suites[] = {
    {MOONEYE_MANIFEST_SHA256, MOONEYE_PATCH_SHA256, cases, sizeof(cases)/sizeof(cases[0]), NULL, 0},
    {MOONEYE_MBC_MANIFEST_SHA256, MOONEYE_PATCH_SHA256, mbc_cases, sizeof(mbc_cases)/sizeof(mbc_cases[0]), mbc_categories, 2},
    {MOONEYE_CGB_MANIFEST_SHA256, MOONEYE_PATCH_SHA256, cgb_cases, sizeof(cgb_cases)/sizeof(cgb_cases[0]), cgb_categories, 4}
};

static int read_bounded(const char *path, uint8_t *buffer, size_t capacity, size_t *length) {
    FILE *f=fopen(path,"rb"); if(!f)return 0;
    size_t n=fread(buffer,1,capacity+1,f); int failed=ferror(f); fclose(f);
    if(failed||n>capacity)return 0; *length=n; return 1;
}
static int hash_matches(const uint8_t *bytes,size_t length,const char *expected) { char hash[65];gbb_accept_sha256_hex(bytes,length,hash);return strcmp(hash,expected)==0; }
static const suite_def *manifest_suite(const uint8_t *bytes,size_t length) {
    char hash[65];gbb_accept_sha256_hex(bytes,length,hash);
    for(size_t i=0;i<sizeof(suites)/sizeof(suites[0]);i++)if(strcmp(hash,suites[i].manifest_sha256)==0)return &suites[i];
    return NULL;
}
/* bytes must hold MAX_MANIFEST+1 so an oversize file is detected, not truncated. NULL means invalid-manifest. */
static const suite_def *manifest_valid(const char *path, uint8_t *bytes, size_t *length) {
    return read_bounded(path,bytes,MAX_MANIFEST,length)?manifest_suite(bytes,*length):NULL;
}
static const fixture_case *select_case(const suite_def *suite,const char *name) {
    for(size_t i=0;i<suite->count;i++)if(strcmp(name,suite->cases[i].id)==0||strcmp(name,suite->cases[i].alias)==0)return &suite->cases[i];
    return NULL;
}
static int locate_rom(const char *manifest,const char *rom,char path[4096]) {
    size_t n=strlen(manifest); if(n==0||n>=4000)return 0; const char *slash=strrchr(manifest,'/');
    const char *backslash=strrchr(manifest,'\\');
    if(backslash!=NULL&&(slash==NULL||backslash>slash))slash=backslash;
    size_t dir=slash?(size_t)(slash-manifest+1):0; if(dir+strlen(rom)>=4095)return 0;
    memcpy(path,manifest,dir);strcpy(path+dir,rom);return 1;
}
/* rom must hold fc->size_bytes+1 bytes (never above GBB_CASES_MAX_ROM_BYTES); the caller owns the heap buffer. */
static const char *load_case_rom(const fixture_case *fc,const char *manifest,uint8_t *rom,size_t *length) {
    char path[4096];
    if(fc->size_bytes==0||fc->size_bytes>GBB_CASES_MAX_ROM_BYTES)return "bad-size";
    if(!locate_rom(manifest,fc->rom,path))return "invalid-fixture-path";
    FILE *file=fopen(path,"rb");
    if(file==NULL)return errno==ENOENT?"missing-fixture":"fixture-read-error";
    size_t n=fread(rom,1,fc->size_bytes+1,file);
    int failed=ferror(file);
    if(fclose(file)!=0)failed=1;
    if(failed)return "fixture-read-error";
    if(n!=fc->size_bytes)return "bad-size";
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
    uint16_t fail_callback_pc; /* the listed fail callback that was reached */
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
        for(uint8_t k=0;k<fc->fail_callback_count;k++)
            if(record->pc==fc->fail_callback_pcs[k]){progress->fail_callback_seen=1;progress->fail_callback_pc=record->pc;}
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
            evidence->callback_pc=progress->fail_callback_pc;
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
/* The address the core refused. The public run result carries only the stop reason, and a refused
 * pre-flight read stops before its instruction is traced, so the address comes from the core's private
 * test seam (read-only; declared in gabbaboy.c, not public ABI). The runner is an in-tree test host. */
uint16_t gbb_test_last_unsupported_address(const gbb_instance *m);
/* What a run that ended on GBB_STOP_UNSUPPORTED_BUS refused (D-26 expected-unsupported rows). */
typedef struct {
    int unsupported_bus;
    uint16_t address;
} stop_evidence;
static const char *run_guest_stop(gbb_profile profile,const fixture_case *fc,const uint8_t *rom,size_t rom_size,
                                  protocol_evidence *evidence,uint64_t *ticks_out,
                                  const char **stop_out,
                                  gbb_diagnostic_record recent[RECENT_CAPACITY],
                                  size_t *recent_count_out,stop_evidence *stop_evidence_out) {
    memset(evidence,0,sizeof(*evidence));memset(stop_evidence_out,0,sizeof(*stop_evidence_out));
    *ticks_out=0;*stop_out="core-load";*recent_count_out=0;
    gbb_instance *m=NULL;if(gbb_create(profile,&m)!=GBB_OK||gbb_load_rom(m,rom,rom_size)!=GBB_OK){gbb_destroy(m);return "unsupported";}
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
        if(core_status){
            status=core_status;stop=r.reason==GBB_STOP_HALTED_IDLE?"halted":"core-stop";
            if(r.reason==GBB_STOP_UNSUPPORTED_BUS){stop_evidence_out->unsupported_bus=1;stop_evidence_out->address=gbb_test_last_unsupported_address(m);}
            break;
        }
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
static const char *run_guest(gbb_profile profile,const fixture_case *fc,const uint8_t *rom,size_t rom_size,
                             protocol_evidence *evidence,uint64_t *ticks_out,
                             const char **stop_out,
                             gbb_diagnostic_record recent[RECENT_CAPACITY],
                             size_t *recent_count_out) {
    stop_evidence ignored;
    return run_guest_stop(profile,fc,rom,rom_size,evidence,ticks_out,stop_out,recent,recent_count_out,&ignored);
}
/* D-26: an expected-unsupported row is satisfied only by a stop on GBB_STOP_UNSUPPORTED_BUS at exactly the
 * declared address. A pass is never a satisfied expectation (the unbuilt register must not have been
 * invented), and a stop elsewhere says nothing about the declared address. Only "expected-unsupported"
 * is a success; unexpected-pass and fail both fail the row. */
static const char *expect_stop_status(const fixture_case *fc,const char *run_status,const stop_evidence *stop,const char **reason) {
    *reason="none";
    if(strcmp(run_status,"pass")==0){*reason="guest-passed";return "unexpected-pass";}
    if(!stop->unsupported_bus){*reason="no-unsupported-bus-stop";return "fail";}
    if(stop->address!=fc->expect_stop_address){*reason="wrong-stop-address";return "fail";}
    return "expected-unsupported";
}
/* One row's final status and exit code. A row without expect_stop keeps the original mapping (pass 0,
 * fail 1, anything else 3); a row with expect_stop is judged by expect_stop_status (met 0, else 1). */
static int row_outcome(const fixture_case *fc,const char *run_status,const stop_evidence *stop,const char **status_out,const char **reason_out) {
    if(fc->expect_stop){
        *status_out=expect_stop_status(fc,run_status,stop,reason_out);
        return strcmp(*status_out,"expected-unsupported")==0?0:1;
    }
    *status_out=run_status;*reason_out="none";
    return strcmp(run_status,"pass")==0?0:strcmp(run_status,"fail")==0?1:3;
}
typedef struct { size_t expected_total, expected_met; } suite_tally;
/* --observe lines for one Mooneye case. They come from the same gbb_runner_capture_ldbb helper as the
 * frame-digest@ldbb case-file oracle, so both paths yield the same canonical digest. A breakpoint
 * reached before the first completed frame is the token not-ready, an observation and not an error. */
static void observe_case(gbb_profile profile,const fixture_case *fc,const uint8_t *rom,size_t rom_size) {
    /* D-05: the CGB profile has no colour output yet, so a CGB row has no frame to digest. The token is
     * emitted instead of a digest so a reader cannot take an absent frame for a DMG observation. */
    if(profile!=GBB_RUNNER_PROFILE_DMG){printf("mooneye.%s.frame\tnot-applicable\n",fc->alias);return;}
    gbb_instance *m=NULL;gbb_ldbb_capture *capture=malloc(sizeof(*capture));
    if(capture==NULL||gbb_create(profile,&m)!=GBB_OK||gbb_load_rom(m,rom,rom_size)!=GBB_OK){
        fprintf(stderr,"runner-error: observation setup failed\n");gbb_destroy(m);free(capture);return;}
    int rc=gbb_runner_capture_ldbb(m,fc->budget,capture);
    gbb_destroy(m);
    const char *alias=fc->alias;
    if(rc!=0){fprintf(stderr,"runner-error: frame capture failed for %s\n",alias);free(capture);return;}
    printf("mooneye.%s.frame\t%s\n",alias,capture->frame_ready?capture->digest:"not-ready");
    if(capture->frame_ready)printf("mooneye.%s.frame_generation\t%llu\n",alias,(unsigned long long)capture->generation);
    else printf("mooneye.%s.frame_generation\tnone\n",alias);
    if(capture->reached){
        printf("mooneye.%s.ldbb_half_dots\t%llu\n",alias,(unsigned long long)capture->ldbb_half_dots);
        printf("mooneye.%s.registers\t%02x%02x%02x%02x%02x%02x\n",alias,capture->b,capture->c,capture->d,capture->e,capture->h,capture->l);
        printf("mooneye.%s.result_pc\t%04x\n",alias,capture->pc);
    } else {
        printf("mooneye.%s.ldbb_half_dots\tnone\nmooneye.%s.registers\tnone\nmooneye.%s.result_pc\tnone\n",alias,alias,alias);
    }
    free(capture);
}
static int run_one(const suite_def *suite,const fixture_case *fc,const char *manifest,int receipt,int observe,size_t eligible,size_t *executed,suite_tally *tally) {
    const gbb_profile profile=row_profile(fc); /* the row, never the command line, picks the run profile (D-25) */
    size_t rom_size=0;
    if(fc->size_bytes==0||fc->size_bytes>GBB_CASES_MAX_ROM_BYTES){fprintf(stderr,"runner-error: ROM size out of bounds\n");return 2;}
    uint8_t *rom=malloc(fc->size_bytes+1);
    if(rom==NULL){fprintf(stderr,"runner-error: ROM buffer allocation failed\n");return 2;}
    const char *fixture_error=load_case_rom(fc,manifest,rom,&rom_size);
    if(fixture_error!=NULL){
        if(receipt)printf("case=%s category=%s status=unsupported reason=%s manifest_sha256=%s source_revision=%s source_tree=%s source_path=%s report_patch_sha256=%s original_rom_sha256=%s fixture_sha256=%s fixture_origin=derived-headless-report-closure profile=%s boot=skipped protocol=mooneye-ld-b-b protocol_stage=not-reached eligible=%zu executed=%zu\n",fc->id,fc->category,fixture_error,suite->manifest_sha256,MOONEYE_SOURCE_REVISION,MOONEYE_SOURCE_TREE,fc->source_path,suite->patch_sha256,fc->original_sha256,fc->sha256,gbb_runner_profile_label(profile),eligible,*executed);
        free(rom);
        return 3;
    }
    protocol_evidence evidence;uint64_t ticks=0;size_t recent_count=0;const char *stop=NULL;
    gbb_diagnostic_record recent[RECENT_CAPACITY];
    stop_evidence stopped;
    const char *status=run_guest_stop(profile,fc,rom,rom_size,&evidence,&ticks,&stop,recent,&recent_count,&stopped);
    if(observe)observe_case(profile,fc,rom,rom_size);
    free(rom);
    ++*executed;
    const char *final_status=status,*reason="none";
    int code=row_outcome(fc,status,&stopped,&final_status,&reason);
    if(fc->expect_stop) {
        const char *expectation=final_status;
        tally->expected_total++;if(code==0)tally->expected_met++;
        if(receipt)printf("case=%s category=%s status=%s stop=%s address=%04x reason=%s expect_stop=unsupported-bus expect_address=%04x manifest_sha256=%s source_revision=%s source_tree=%s source_path=%s report_patch_sha256=%s original_rom_sha256=%s fixture_sha256=%s fixture_origin=derived-headless-report-closure upstream_assertions=unchanged core_revision=%s runner_revision=%s build_qualified=%s profile=%s boot=skipped protocol=mooneye-ld-b-b ticks=%llu budget=%llu eligible=%zu executed=%zu\n",
          fc->id,fc->category,expectation,stopped.unsupported_bus?"unsupported-bus":stop,stopped.unsupported_bus?stopped.address:0u,reason,fc->expect_stop_address,
          suite->manifest_sha256,MOONEYE_SOURCE_REVISION,MOONEYE_SOURCE_TREE,fc->source_path,suite->patch_sha256,fc->original_sha256,fc->sha256,GBB_BUILD_REVISION,GBB_BUILD_REVISION,GBB_BUILD_QUALIFIED?"true":"false",gbb_runner_profile_label(profile),(unsigned long long)ticks,(unsigned long long)fc->budget,eligible,*executed);
        return code;
    }
    if(receipt){
        const char *stage=evidence.callback_result?"callback-then-ld-b-b":
            evidence.reached_result?"ld-b-b-without-expected-callback":"not-reached";
        printf("case=%s category=%s status=%s manifest_sha256=%s source_revision=%s source_tree=%s source_path=%s report_patch_sha256=%s builder_revision=%s builder_archive_sha256=%s original_rom_sha256=%s fixture_sha256=%s fixture_origin=derived-headless-report-closure upstream_assertions=unchanged core_revision=%s runner_revision=%s build_qualified=%s profile=%s boot=skipped protocol=mooneye-ld-b-b protocol_stage=%s callback_result=%s callback_pc=%04x result_pc=%04x protocol_reason=%s ticks=%llu budget=%llu eligible=%zu executed=%zu stop=%s recent=%zu\n",
          fc->id,fc->category,status,suite->manifest_sha256,MOONEYE_SOURCE_REVISION,MOONEYE_SOURCE_TREE,fc->source_path,suite->patch_sha256,MOONEYE_BUILDER_REVISION,MOONEYE_BUILDER_ARCHIVE_SHA256,fc->original_sha256,fc->sha256,GBB_BUILD_REVISION,GBB_BUILD_REVISION,GBB_BUILD_QUALIFIED?"true":"false",gbb_runner_profile_label(profile),stage,evidence.callback_result?evidence.callback_result:"none",evidence.callback_pc,evidence.result_pc,evidence.reason?evidence.reason:"none",(unsigned long long)ticks,(unsigned long long)fc->budget,eligible,*executed,stop,recent_count);
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
    gbb_instance *machine=NULL;gbb_profile profile=GBB_RUNNER_PROFILE_DMG;
    if(gbb_create(profile,&machine)!=GBB_OK||gbb_load_rom(machine,rom,size)!=GBB_OK){free(rom);gbb_destroy(machine);fprintf(stderr,"invalid-fixture: unsupported or malformed ROM\n");return 2;}
    free(rom);gbb_trace_record *trace=calloc(16384,sizeof(*trace));
    if(!trace){gbb_destroy(machine);fprintf(stderr,"runner-error: trace allocation failed\n");return 2;}
    gbb_run_result result=gbb_run(machine,UINT64_C(200000),trace,16384);uint8_t value=gbb_peek_ram(machine,0xC001);
    const char *outcome=result.reason==GBB_STOP_LOCKUP?"lockup":result.reason==GBB_STOP_UNSUPPORTED_OPCODE?"unsupported":
      result.reason==GBB_STOP_UNSUPPORTED_BUS?"unsupported-bus":result.reason==GBB_STOP_TRACE_FULL?"trace-exhausted":
      result.reason==GBB_STOP_HALTED_IDLE?"halted-idle":result.reason==GBB_STOP_STOPPED?"stopped":
      value==0xEE?"guest-failure":result.reason==GBB_STOP_BUDGET&&value==0xA5?"pass":"timeout";
    printf("fixture=original-wram-tracer profile=%s outcome=%s stop=%s half_dots=%llu trace_records=%zu\n",gbb_runner_profile_label(profile),outcome,
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
      "  %s --manifest <manifest.json> --case <id> [--profile dmg|cgb] [--receipt] [--observe]\n"
      "  %s --manifest <manifest.json> --suite [--profile dmg|cgb] [--receipt] [--observe]\n"
      "  %s --acceptance <cases.txt> (--case <id> | --suite --expect-excluded <n>) [--model <id> | --profile dmg|cgb] [--revision <r>] [--failure-dir <dir>] [--receipt]\n"
      "  %s --acceptance <cases.txt> --case <id> --observe [--input-script <file>] [--frame-digest-at <half-dots>] [--pcm-digest] [--dump-checkpoints <dir>]\n"
      "  %s --acceptance <cases.txt> --case <id> --raw-verdict [--receipt]\n"
      "  %s --acceptance <cases.txt> (--case <id> | --suite --expect-excluded <n>) --mutate drop:<BUTTON> [--receipt]\n",
      program, program, program, program, program, program, program);
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
    int observe_only_flag=0;const char *profile_option=NULL;
    for(int i=1;i<argc;i++){
        if(strcmp(argv[i],"--help")==0){print_usage(stdout,argv[0]);return 0;}
        else if(strcmp(argv[i],"--manifest")==0&&i+1<argc)manifest=argv[++i];
        else if(strcmp(argv[i],"--acceptance")==0&&i+1<argc)acceptance=argv[++i];
        else if(strcmp(argv[i],"--case")==0&&i+1<argc)selected=argv[++i];
        else if(strcmp(argv[i],"--suite")==0)suite=1;
        else if(strcmp(argv[i],"--receipt")==0)receipt=1;
        else if(strcmp(argv[i],"--failure-dir")==0&&i+1<argc)options.failure_dir=argv[++i];
        else if(strcmp(argv[i],"--observe")==0)options.observe=1;
        else if(strcmp(argv[i],"--raw-verdict")==0)options.raw_verdict=1;
        else if(strcmp(argv[i],"--mutate")==0&&i+1<argc){
            const char *spec=argv[++i];static const char *const names[8]={"RIGHT","LEFT","UP","DOWN","A","B","SELECT","START"};
            int found=0;
            if(strncmp(spec,"drop:",5)==0)for(unsigned b=0;b<8;b++)if(strcmp(spec+5,names[b])==0){options.drop_button=(uint8_t)b;found=1;}
            if(!found||options.has_drop_button){fprintf(stderr,"invalid-arguments: reason=invalid-mutate\n");return 2;}
            options.has_drop_button=1;options.mutate_label=spec;}
        else if(strcmp(argv[i],"--model")==0&&i+1<argc)options.model=argv[++i];
        else if(strcmp(argv[i],"--profile")==0&&i+1<argc)profile_option=argv[++i];
        else if(strcmp(argv[i],"--revision")==0&&i+1<argc)options.revision=argv[++i];
        else if(strcmp(argv[i],"--expect-excluded")==0&&i+1<argc){
            const char *text=argv[++i];size_t n=strlen(text);unsigned value=0;int valid=n>0&&n<=3;
            for(size_t k=0;valid&&k<n;k++){if(text[k]<'0'||text[k]>'9')valid=0;else value=value*10u+(unsigned)(text[k]-'0');}
            if(valid&&value>GBB_CASES_MAX_CASES)valid=0;
            if(!valid){fprintf(stderr,"invalid-arguments: reason=invalid-expect-excluded\n");return 2;}
            options.expect_excluded=value;options.has_expect_excluded=1;}
        else if(strcmp(argv[i],"--input-script")==0&&i+1<argc){options.observe_input_script=argv[++i];observe_only_flag=1;}
        else if(strcmp(argv[i],"--frame-digest-at")==0&&i+1<argc){
            if(!parse_half_dots(argv[++i],&options.frame_digest_at)){fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
            options.has_frame_digest_at=1;observe_only_flag=1;}
        else if(strcmp(argv[i],"--pcm-digest")==0){options.pcm_only=1;observe_only_flag=1;}
        else if(strcmp(argv[i],"--dump-checkpoints")==0&&i+1<argc){options.dump_dir=argv[++i];observe_only_flag=1;}
        else {fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
    }
    /* D-25: one model<->profile mapping. --profile selects the model token; --model must agree. */
    gbb_profile profile=GBB_RUNNER_PROFILE_DMG;
    if(profile_option!=NULL){
        const char *mapped=gbb_runner_model_for_option(profile_option);
        if(mapped==NULL){fprintf(stderr,"invalid-arguments: reason=unknown-profile\n");return 2;}
        if(options.model!=NULL&&strcmp(options.model,mapped)!=0){fprintf(stderr,"invalid-arguments: reason=profile-model-conflict\n");return 2;}
        options.model=mapped;
    }
    if(options.model!=NULL&&gbb_case_model_known(options.model))gbb_runner_profile_for_model(options.model,&profile);
    if(acceptance){
        if(observe_only_flag&&!options.observe){fprintf(stderr,"invalid-arguments: reason=observe-only-flag\n");return 2;}
        if(options.model!=NULL&&!gbb_case_model_known(options.model)){fprintf(stderr,"invalid-arguments: reason=unknown-model\n");return 2;}
        if(options.has_drop_button&&options.observe){fprintf(stderr,"invalid-arguments: reason=invalid-mutate\n");return 2;}
        if(options.raw_verdict&&(suite||options.observe||!selected)){fprintf(stderr,"invalid-arguments: reason=raw-verdict-requires-case\n");return 2;}
        if(suite&&!options.has_expect_excluded){fprintf(stderr,"invalid-arguments: reason=expect-excluded-required\n");return 2;}
        if(manifest||(suite&&(selected||options.observe))||(!suite&&(!selected||options.has_expect_excluded))){fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
        options.suite=suite;
        options.receipt=receipt;options.core_revision=GBB_BUILD_REVISION;options.build_qualified=GBB_BUILD_QUALIFIED;
        return gbb_acceptance_run_file(acceptance,selected,&options);
    }
    if(options.failure_dir||observe_only_flag||(options.model&&!profile_option)||options.revision||options.has_expect_excluded||options.raw_verdict||options.has_drop_button){fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
    if(!manifest||(!suite&&!selected)||(suite&&selected)){fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
    size_t manifest_length=0;
    uint8_t *manifest_bytes=malloc(MAX_MANIFEST+1);
    if(manifest_bytes==NULL){fprintf(stderr,"runner-error: manifest buffer allocation failed\n");return 2;}
    const suite_def *selected_suite=manifest_valid(manifest,manifest_bytes,&manifest_length);
    free(manifest_bytes); /* only the digest check needed the bytes */
    if(selected_suite==NULL){fprintf(stderr,"invalid-manifest\n");return 2;}
    size_t eligible=suite?selected_suite->count:1,executed=0;int suite_code=0;
    if(profile_option!=NULL&&profile!=row_profile(&selected_suite->cases[0])){
        /* An explicit --profile that differs from the suite's profile excludes every row: report it under
         * the requested label and never run it on another profile (D-25). A suite is homogeneous. */
        if(suite){for(size_t i=0;i<eligible;i++)printf("mooneye.%s status=excluded reason=unsupported-model profile=%s\n",selected_suite->cases[i].alias,gbb_runner_profile_label(profile));}
        else{const fixture_case *xc=select_case(selected_suite,selected);if(!xc){fprintf(stderr,"unknown-case: use --help for invocation forms\n");return 2;}
            printf("mooneye.%s status=excluded reason=unsupported-model profile=%s\n",xc->alias,gbb_runner_profile_label(profile));}
        return 4;
    }
    if(suite){
        size_t category_pass[MAX_SUITE_CATEGORIES]={0},category_total[MAX_SUITE_CATEGORIES]={0},category_xu[MAX_SUITE_CATEGORIES]={0};
        suite_tally tally={0,0};
        if(selected_suite->category_count>MAX_SUITE_CATEGORIES){fprintf(stderr,"runner-error: too many suite categories\n");return 2;}
        for(size_t i=0;i<eligible;i++){
            const fixture_case *fc=&selected_suite->cases[i];
            int code=run_one(selected_suite,fc,manifest,receipt,options.observe,eligible,&executed,&tally);
            if(code!=0&&suite_code==0)suite_code=code;
            for(size_t k=0;k<selected_suite->category_count;k++)if(strcmp(fc->category,selected_suite->categories[k])==0){category_total[k]++;if(code==0){if(fc->expect_stop)category_xu[k]++;else category_pass[k]++;}}
        }
        /* A suite that passes only because rows met a declared unsupported-bus stop says so in the headline. */
        if(receipt){const int ok=suite_counts_valid(eligible,executed)&&suite_code==0;
            printf("suite eligible=%zu executed=%zu status=%s\n",eligible,executed,!ok?"fail":tally.expected_met!=0?"pass-with-expected-unsupported":"pass");}
        if(receipt&&selected_suite->category_count!=0){
            printf("suite categories");
            /* name=P/T counts plain passes only. A row that met its declared unsupported-bus stop never reached its
             * verdict, so it is reported as name.expected-unsupported=N and not as a pass (D-26). */
            for(size_t k=0;k<selected_suite->category_count;k++){
                printf(" %s=%zu/%zu",selected_suite->categories[k],category_pass[k],category_total[k]);
                if(category_xu[k]!=0)printf(" %s.expected-unsupported=%zu",selected_suite->categories[k],category_xu[k]);
            }
            printf("\n");
        }
        /* Rows that met their declared unsupported-bus stop count as passing for the suite status; this line
         * states how many rows were staged that way so a reader cannot take them for plain passes. */
        if(receipt&&tally.expected_total!=0)printf("suite expected-unsupported=%zu/%zu\n",tally.expected_met,tally.expected_total);
        return suite_counts_valid(eligible,executed)?suite_code:2;
    }
    const fixture_case *fc=select_case(selected_suite,selected);if(!fc){fprintf(stderr,"unknown-case: use --help for invocation forms\n");return 2;}
    suite_tally single={0,0};
    return run_one(selected_suite,fc,manifest,receipt,options.observe,eligible,&executed,&single);
}
