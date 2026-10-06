#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

/* Compile the host protocol helpers into this focused test translation unit. */
#define main gbb_runner_program_main
#include "../src/runner/main.c"
#undef main

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    gbb_trace_record record = {0};
    record.opcode[0] = 0x40; /* LD B,B remains an ordinary CPU instruction. */
    if (strcmp(argv[1], "runner_pass") == 0) {
        record.b=3;record.c=5;record.d=8;record.e=13;record.h=21;record.l=34;
        REQUIRE(strcmp(protocol_status(&record,1),"pass")==0);
    } else if (strcmp(argv[1], "runner_fail") == 0) {
        record.b=record.c=record.d=record.e=record.h=record.l=0x42;
        REQUIRE(strcmp(protocol_status(&record,1),"fail")==0);
    } else if (strcmp(argv[1], "runner_timeout") == 0) {
        REQUIRE(protocol_status(&record,1)==NULL);
        REQUIRE(strcmp(cases[0].id,"mooneye-acceptance-instr-daa")==0 && cases[0].budget==UINT64_C(200000));
    } else if (strcmp(argv[1], "runner_unsupported") == 0) {
        REQUIRE(protocol_status(&record,1)==NULL);
        REQUIRE(strcmp(cases[1].category,"timer")==0 && strcmp(cases[2].category,"timer")==0);
    } else if (strcmp(argv[1], "runner_missing_fixture") == 0) {
        char path[4096];
        REQUIRE(locate_rom("/definitely-absent/manifest.json",cases[0].rom,path));
        FILE *f=fopen(path,"rb");
        REQUIRE(f==NULL);
    } else if (strcmp(argv[1], "runner_bad_manifest") == 0) {
        uint8_t bytes[MAX_MANIFEST+1]={0};size_t n=1;
        REQUIRE(!hash_matches(bytes,n,"7c3367fc5882fab5bffca422d60b69847a80ac7b7407b2742b3fb0f03f4790ba"));
    } else if (strcmp(argv[1], "runner_zero_eligible") == 0) {
        REQUIRE(sizeof(cases)/sizeof(cases[0])==3);
    } else { return 2; }
    return 0;
}
