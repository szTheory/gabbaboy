/* Test-only reuse of the explicit private-state partition oracle. */
#define main cgb_partition_existing_main
#include "test_cgb_partition.c"
#undef main

static int cgb_hdma_partition_midbyte(void) {
    partition_scenario scenario = {0};
    partition_machine run;
    REQUIRE(partition_machine_create(&scenario, &run) == 0);

    const uint64_t baseline = partition_digest(run.machine, &run.streams);
    gbb_instance changed = *run.machine;
    changed.hdma.source_cursor ^= 1u;
    const uint64_t altered = partition_digest(&changed, &run.streams);
    if (altered == baseline) {
        fputs("hdma-partition-digest-omitted-field source_cursor\n", stderr);
        partition_machine_destroy(&run);
        return 1;
    }

    partition_machine_destroy(&run);
    puts("cgb_hdma_partition_midbyte pass");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "midbyte") == 0)
        return cgb_hdma_partition_midbyte();
    return 2;
}
