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
        REQUIRE(strcmp(budget_status(2000000,2000000),"timeout")==0);
        REQUIRE(cases[0].budget==UINT64_C(2000000));
    } else if (strcmp(argv[1], "runner_unsupported") == 0) {
        REQUIRE(protocol_status(&record,1)==NULL);
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
