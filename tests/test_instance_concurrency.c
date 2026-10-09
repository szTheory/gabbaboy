#include "gabbaboy/gabbaboy.h"

#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
typedef HANDLE test_thread;
#else
#include <pthread.h>
typedef pthread_t test_thread;
#endif

typedef struct {
    gbb_instance *instance;
    atomic_int *ready;
    atomic_int *start;
    uint8_t expected_ram_value;
    int passed;
} worker_args;

static void *run_repeatedly(void *opaque) {
    worker_args *args = (worker_args *)opaque;
    atomic_fetch_add_explicit(args->ready, 1, memory_order_release);
    while (atomic_load_explicit(args->start, memory_order_acquire) == 0) { }

    args->passed = 1;
    for (int i = 0; i < 100; ++i) {
        gbb_run_result result;
        if (gbb_reset(args->instance) != GBB_OK) { args->passed = 0; break; }
        result = gbb_run(args->instance, 88, NULL, 0);
        if (result.reason != GBB_STOP_BUDGET || result.consumed_half_dots != 88 ||
            gbb_peek_ram(args->instance, 0xC000) != args->expected_ram_value) {
            args->passed = 0;
            break;
        }
    }
    return NULL;
}

#ifdef _WIN32
static DWORD WINAPI windows_worker(LPVOID opaque) {
    (void)run_repeatedly(opaque);
    return 0;
}
#endif

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (!file || fseek(file, 0, SEEK_END) != 0) return 2;
    long length = ftell(file);
    if (length <= 0 || fseek(file, 0, SEEK_SET) != 0) return 2;
    uint8_t *rom[2] = {
        (uint8_t *)malloc((size_t)length),
        (uint8_t *)malloc((size_t)length)
    };
    if (!rom[0] || !rom[1] || fread(rom[0], 1, (size_t)length, file) != (size_t)length) return 2;
    fclose(file);
    memcpy(rom[1], rom[0], (size_t)length);

    /* Change the second fixture's write and compare immediates outside the header. */
    if ((size_t)length <= 0x158u) return 2;
    rom[1][0x154] = 0xA5;
    rom[1][0x158] = 0xA5;

    gbb_instance *instances[2] = {NULL, NULL};
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &instances[0]) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &instances[1]) != GBB_OK ||
        gbb_load_rom(instances[0], rom[0], (size_t)length) != GBB_OK ||
        gbb_load_rom(instances[1], rom[1], (size_t)length) != GBB_OK) return 1;
    free(rom[0]);
    free(rom[1]);

    atomic_int ready = 0;
    atomic_int start = 0;
    worker_args args[2] = {
        {instances[0], &ready, &start, 0x5A, 0},
        {instances[1], &ready, &start, 0xA5, 0}
    };
    test_thread threads[2];
#ifdef _WIN32
    threads[0] = CreateThread(NULL, 0, windows_worker, &args[0], 0, NULL);
    if (!threads[0]) {
        gbb_destroy(instances[0]);
        gbb_destroy(instances[1]);
        return 2;
    }
    threads[1] = CreateThread(NULL, 0, windows_worker, &args[1], 0, NULL);
    if (!threads[1]) {
        atomic_store_explicit(&start, 1, memory_order_release);
        WaitForSingleObject(threads[0], INFINITE);
        CloseHandle(threads[0]);
        gbb_destroy(instances[0]);
        gbb_destroy(instances[1]);
        return 2;
    }
#else
    if (pthread_create(&threads[0], NULL, run_repeatedly, &args[0]) != 0) {
        gbb_destroy(instances[0]);
        gbb_destroy(instances[1]);
        return 2;
    }
    if (pthread_create(&threads[1], NULL, run_repeatedly, &args[1]) != 0) {
        atomic_store_explicit(&start, 1, memory_order_release);
        pthread_join(threads[0], NULL);
        gbb_destroy(instances[0]);
        gbb_destroy(instances[1]);
        return 2;
    }
#endif
    while (atomic_load_explicit(&ready, memory_order_acquire) != 2) { }
    atomic_store_explicit(&start, 1, memory_order_release);
#ifdef _WIN32
    WaitForMultipleObjects(2, threads, TRUE, INFINITE);
    CloseHandle(threads[0]);
    CloseHandle(threads[1]);
#else
    pthread_join(threads[0], NULL);
    pthread_join(threads[1], NULL);
#endif
    gbb_destroy(instances[0]);
    gbb_destroy(instances[1]);
    if (!args[0].passed || !args[1].passed) {
        fprintf(stderr, "concurrent independent instance run diverged\n");
        return 1;
    }
    return 0;
}
