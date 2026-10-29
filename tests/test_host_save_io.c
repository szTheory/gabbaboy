/* D-08, D-09, D-10: the directory-relative writer, sweep and reader, driven below the runner.
 *
 *   test_host_save_io fault_temp|fault_write|fault_sync|fault_close|fault_target|fault_rename|
 *                     fault_dirsync|eio_no_retry|eexist|target_not_regular|sweep_exact_prefix|
 *                     import_device
 *
 * Linked against gabbaboy_host_testing, the only library built with GBB_HOST_TESTING. Each fault case
 * injects one failure at one writer stage and requires that stage's own code, the previous .sav byte-
 * and inode-identical (the dir-sync stage excepted: the rename already happened), and no temp entry.
 * Each case prints `PASS <case>` or `FAIL <case>`; the repo copies small file helpers rather than
 * sharing them. POSIX only: it uses mkdtemp, openat-style descriptors and symlinks. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gbb_host.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define IMAGE_BYTES 64u

typedef struct {
    char root[512];
    int dirfd;
} fixture;

static bool path_join(char *out, size_t capacity, const char *left, const char *right) {
    const int count = snprintf(out, capacity, "%s/%s", left, right);
    return count >= 0 && (size_t)count < capacity;
}

static void remove_tree(const char *path) {
    struct stat info;
    if (lstat(path, &info) != 0) return;
    if (!S_ISDIR(info.st_mode)) {
        (void)unlink(path);
        return;
    }
    DIR *directory = opendir(path);
    if (directory != NULL) {
        struct dirent *entry;
        while ((entry = readdir(directory)) != NULL) {
            if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) continue;
            char child[1024];
            if (path_join(child, sizeof(child), path, entry->d_name)) remove_tree(child);
        }
        (void)closedir(directory);
    }
    (void)rmdir(path);
}

static int fixture_open(fixture *f) {
    const char *base = getenv("TMPDIR");
    if (base == NULL || base[0] == '\0') base = "/tmp";
    if (snprintf(f->root, sizeof(f->root), "%s/gbb-host-save-io-XXXXXX", base) >= (int)sizeof(f->root))
        return 1;
    if (mkdtemp(f->root) == NULL) return 1;
    return host_save_io_open_dir(f->root, &f->dirfd) == HOST_IO_OK ? 0 : 1;
}

static void fixture_close(fixture *f) {
    if (f->dirfd >= 0) (void)close(f->dirfd);
    remove_tree(f->root);
}

static int write_file(const fixture *f, const char *name, const void *bytes, size_t size) {
    char path[1024];
    if (!path_join(path, sizeof(path), f->root, name)) return 1;
    FILE *file = fopen(path, "wb");
    if (file == NULL) return 1;
    const size_t count = size == 0u ? 0u : fwrite(bytes, 1u, size, file);
    return (fclose(file) == 0 && count == size) ? 0 : 1;
}

/* Reads the whole file (at most `capacity` bytes) following no links; returns its size or -1. */
static long read_file(const fixture *f, const char *name, uint8_t *out, size_t capacity) {
    const int fd = openat(f->dirfd, name, O_RDONLY | O_NOFOLLOW);
    if (fd < 0) return -1;
    const ssize_t count = read(fd, out, capacity);
    (void)close(fd);
    return (long)count;
}

static void fill(uint8_t *bytes, size_t size, uint8_t seed) {
    for (size_t i = 0u; i < size; ++i) bytes[i] = (uint8_t)(seed + i);
}

/* The directory holds exactly `expected` entries of any kind, not counting . and .. . */
static int entry_count(const fixture *f) {
    const int duplicate = dup(f->dirfd);
    if (duplicate < 0) return -1;
    DIR *directory = fdopendir(duplicate);
    if (directory == NULL) { (void)close(duplicate); return -1; }
    rewinddir(directory);
    int count = 0;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL)
        if (strcmp(entry->d_name, ".") != 0 && strcmp(entry->d_name, "..") != 0) ++count;
    (void)closedir(directory);
    return count;
}

static bool entry_exists(const fixture *f, const char *name) {
    struct stat info;
    return fstatat(f->dirfd, name, &info, AT_SYMLINK_NOFOLLOW) == 0;
}

/* One writer stage fails once: the stage's code comes back, the previous target is untouched. */
static int fault_case(int stage, int expect_code, bool rename_happened) {
    fixture f;
    REQUIRE(fixture_open(&f) == 0);
    uint8_t old_image[IMAGE_BYTES], new_image[IMAGE_BYTES], got[IMAGE_BYTES + 1u];
    fill(old_image, sizeof(old_image), 0x10u);
    fill(new_image, sizeof(new_image), 0x90u);
    REQUIRE(write_file(&f, "game.sav", old_image, sizeof(old_image)) == 0);
    struct stat before;
    REQUIRE(fstatat(f.dirfd, "game.sav", &before, AT_SYMLINK_NOFOLLOW) == 0);

    host_save_io_test_fail_next(stage, EIO);
    errno = 0;
    const int code = host_save_io_replace(f.dirfd, "game.sav", new_image, sizeof(new_image));
    REQUIRE(code == expect_code);
    REQUIRE(errno == EIO); /* the writer preserves the failing errno for the caller */

    struct stat after;
    REQUIRE(fstatat(f.dirfd, "game.sav", &after, AT_SYMLINK_NOFOLLOW) == 0);
    const long size = read_file(&f, "game.sav", got, sizeof(got));
    REQUIRE(size == (long)IMAGE_BYTES);
    if (rename_happened) {
        /* Dir-sync failed after the rename: the new image is in place and the caller must treat it as
         * still dirty, so the temp name is gone and the target holds the new bytes. */
        REQUIRE(memcmp(got, new_image, IMAGE_BYTES) == 0);
    } else {
        REQUIRE(memcmp(got, old_image, IMAGE_BYTES) == 0);
        REQUIRE(after.st_ino == before.st_ino && after.st_dev == before.st_dev);
    }
    REQUIRE(entry_count(&f) == 1); /* no .game.sav.tmp- entry survives any stage */

    /* The fault is one-shot: the very next write succeeds. */
    REQUIRE(host_save_io_replace(f.dirfd, "game.sav", new_image, sizeof(new_image)) == HOST_IO_OK);
    REQUIRE(read_file(&f, "game.sav", got, sizeof(got)) == (long)IMAGE_BYTES);
    REQUIRE(memcmp(got, new_image, IMAGE_BYTES) == 0);
    fixture_close(&f);
    return 0;
}

static int fault_temp(void) { return fault_case(HOST_IO_ETEMP, HOST_IO_ETEMP, false); }
static int fault_write(void) { return fault_case(HOST_IO_EWRITE, HOST_IO_EWRITE, false); }
static int fault_sync(void) { return fault_case(HOST_IO_ESYNC, HOST_IO_ESYNC, false); }
static int fault_close(void) { return fault_case(HOST_IO_ECLOSE, HOST_IO_ECLOSE, false); }
static int fault_target(void) { return fault_case(HOST_IO_ETARGET, HOST_IO_ETARGET, false); }
static int fault_rename(void) { return fault_case(HOST_IO_ERENAME, HOST_IO_ERENAME, false); }
static int fault_dirsync(void) { return fault_case(HOST_IO_EDIRSYNC, HOST_IO_EDIRSYNC, true); }

/* D-09 step 3: after EIO from sync the kernel may have dropped the pages, so the same descriptor is
 * never synced a second time. The attempt is abandoned; the caller rewrites from memory later. */
static int eio_no_retry(void) {
    fixture f;
    REQUIRE(fixture_open(&f) == 0);
    uint8_t image[IMAGE_BYTES];
    fill(image, sizeof(image), 0x33u);
    const unsigned calls_before = host_save_io_test_sync_calls();
    host_save_io_test_fail_next(HOST_IO_ESYNC, EIO);
    REQUIRE(host_save_io_replace(f.dirfd, "game.sav", image, sizeof(image)) == HOST_IO_ESYNC);
    REQUIRE(host_save_io_test_sync_calls() - calls_before == 1u);
    REQUIRE(!entry_exists(&f, "game.sav")); /* nothing was published */
    REQUIRE(entry_count(&f) == 0);
    fixture_close(&f);
    return 0;
}

/* D-09 step 1: 16 O_EXCL collisions fail with the temp stage and touch nothing; one collision moves on
 * to the next sequence number. */
static int eexist(void) {
    fixture f;
    REQUIRE(fixture_open(&f) == 0);
    uint8_t old_image[IMAGE_BYTES], new_image[IMAGE_BYTES], got[IMAGE_BYTES + 1u];
    fill(old_image, sizeof(old_image), 0x10u);
    fill(new_image, sizeof(new_image), 0x77u);
    REQUIRE(write_file(&f, "game.sav", old_image, sizeof(old_image)) == 0);
    const long pid = (long)getpid();
    char name[128];
    for (unsigned seq = 0u; seq < GBB_HOST_TEMP_RETRIES; ++seq) {
        (void)snprintf(name, sizeof(name), ".game.sav.tmp-%ld-%u", pid, seq);
        REQUIRE(write_file(&f, name, "squat", 5u) == 0);
    }
    REQUIRE(host_save_io_replace(f.dirfd, "game.sav", new_image, sizeof(new_image)) == HOST_IO_ETEMP);
    REQUIRE(errno == EEXIST);
    REQUIRE(read_file(&f, "game.sav", got, sizeof(got)) == (long)IMAGE_BYTES);
    REQUIRE(memcmp(got, old_image, IMAGE_BYTES) == 0);
    REQUIRE(entry_count(&f) == 1 + (int)GBB_HOST_TEMP_RETRIES);
    for (unsigned seq = 0u; seq < GBB_HOST_TEMP_RETRIES; ++seq) {
        (void)snprintf(name, sizeof(name), ".game.sav.tmp-%ld-%u", pid, seq);
        REQUIRE(read_file(&f, name, got, sizeof(got)) == 5 && memcmp(got, "squat", 5u) == 0);
    }
    fixture_close(&f);

    REQUIRE(fixture_open(&f) == 0);
    (void)snprintf(name, sizeof(name), ".game.sav.tmp-%ld-0", pid);
    REQUIRE(write_file(&f, name, "squat", 5u) == 0);
    REQUIRE(host_save_io_replace(f.dirfd, "game.sav", new_image, sizeof(new_image)) == HOST_IO_OK);
    REQUIRE(read_file(&f, "game.sav", got, sizeof(got)) == (long)IMAGE_BYTES);
    REQUIRE(memcmp(got, new_image, IMAGE_BYTES) == 0);
    REQUIRE(read_file(&f, name, got, sizeof(got)) == 5 && memcmp(got, "squat", 5u) == 0);
    REQUIRE(entry_count(&f) == 2);
    fixture_close(&f);
    return 0;
}

/* D-09 step 5: a directory or a symlink at the target is refused, the temp is unlinked, and a symlink's
 * destination is never written through. */
static int target_not_regular(void) {
    fixture f;
    REQUIRE(fixture_open(&f) == 0);
    uint8_t new_image[IMAGE_BYTES], got[IMAGE_BYTES + 1u];
    fill(new_image, sizeof(new_image), 0x55u);
    char path[1024];
    REQUIRE(path_join(path, sizeof(path), f.root, "game.sav"));
    REQUIRE(mkdir(path, 0700) == 0);
    REQUIRE(host_save_io_replace(f.dirfd, "game.sav", new_image, sizeof(new_image)) == HOST_IO_ETARGET);
    struct stat info;
    REQUIRE(fstatat(f.dirfd, "game.sav", &info, AT_SYMLINK_NOFOLLOW) == 0 && S_ISDIR(info.st_mode));
    REQUIRE(entry_count(&f) == 1);
    REQUIRE(rmdir(path) == 0);

    REQUIRE(write_file(&f, "outside.bin", "outside", 7u) == 0);
    REQUIRE(symlinkat("outside.bin", f.dirfd, "game.sav") == 0);
    REQUIRE(host_save_io_replace(f.dirfd, "game.sav", new_image, sizeof(new_image)) == HOST_IO_ETARGET);
    REQUIRE(fstatat(f.dirfd, "game.sav", &info, AT_SYMLINK_NOFOLLOW) == 0 && S_ISLNK(info.st_mode));
    REQUIRE(read_file(&f, "outside.bin", got, sizeof(got)) == 7 && memcmp(got, "outside", 7u) == 0);
    REQUIRE(entry_count(&f) == 2); /* the link and its destination, no temp */
    fixture_close(&f);
    return 0;
}

/* D-10: exactly `.<stem>.sav.tmp-` is swept; a symlink entry is removed itself and never followed. */
static int sweep_exact_prefix(void) {
    fixture f;
    REQUIRE(fixture_open(&f) == 0);
    REQUIRE(write_file(&f, "outside.bin", "outside", 7u) == 0);
    REQUIRE(write_file(&f, ".game.sav.tmp-1-0", "x", 1u) == 0);
    REQUIRE(write_file(&f, ".game.sav.tmp-", "x", 1u) == 0); /* the bare prefix still matches */
    REQUIRE(symlinkat("outside.bin", f.dirfd, ".game.sav.tmp-99-3") == 0);
    static const char *const kept[] = {
        ".game.sav.tmp", "game.sav.tmp-1", ".other.sav.tmp-1", ".game.sav", "game.sav",
        ".game.sav.tm-1", ".Game.sav.tmp-1", ".game.sav.tmp1"
    };
    for (size_t i = 0u; i < sizeof(kept) / sizeof(kept[0]); ++i)
        REQUIRE(write_file(&f, kept[i], "keep", 4u) == 0);

    REQUIRE(host_save_io_sweep(f.dirfd, "game") == 3);
    REQUIRE(!entry_exists(&f, ".game.sav.tmp-1-0"));
    REQUIRE(!entry_exists(&f, ".game.sav.tmp-"));
    REQUIRE(!entry_exists(&f, ".game.sav.tmp-99-3"));
    for (size_t i = 0u; i < sizeof(kept) / sizeof(kept[0]); ++i) REQUIRE(entry_exists(&f, kept[i]));
    uint8_t got[16];
    REQUIRE(read_file(&f, "outside.bin", got, sizeof(got)) == 7 && memcmp(got, "outside", 7u) == 0);
    REQUIRE(host_save_io_sweep(f.dirfd, "game") == 0); /* idempotent */
    REQUIRE(entry_count(&f) == (int)(sizeof(kept) / sizeof(kept[0])) + 1);
    fixture_close(&f);
    return 0;
}

/* D-08/D-30: a character device at the .sav path is refused as not-regular and never read. */
static int import_device(void) {
    int dirfd = -1;
    REQUIRE(host_save_io_open_dir("/dev", &dirfd) == HOST_IO_OK);
    uint8_t buf[IMAGE_BYTES + 1u];
    memset(buf, 0xA5, sizeof(buf));
    REQUIRE(host_save_io_read_exact(dirfd, "null", buf, IMAGE_BYTES) == HOST_IO_ENOTREG);
    for (size_t i = 0u; i < sizeof(buf); ++i) REQUIRE(buf[i] == 0xA5); /* nothing was read */
    (void)close(dirfd);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_host_save_io <case>\n");
        return 2;
    }
    static const struct { const char *name; int (*run)(void); } cases[] = {
        {"fault_temp", fault_temp}, {"fault_write", fault_write}, {"fault_sync", fault_sync},
        {"fault_close", fault_close}, {"fault_target", fault_target}, {"fault_rename", fault_rename},
        {"fault_dirsync", fault_dirsync}, {"eio_no_retry", eio_no_retry}, {"eexist", eexist},
        {"target_not_regular", target_not_regular}, {"sweep_exact_prefix", sweep_exact_prefix},
        {"import_device", import_device}
    };
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (strcmp(argv[1], cases[i].name) != 0) continue;
        if (cases[i].run() != 0) {
            printf("FAIL %s\n", cases[i].name);
            return 1;
        }
        printf("PASS %s\n", cases[i].name);
        return 0;
    }
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
