/* WR-05: host_save_io_replace keeps the permission bits of the save it replaces.
 *
 *   test_host_save_mode preserve_mode
 *
 * A separate program from test_host_save_io so a mutant host library can be linked without the fault seams.
 * The temp is created 0600, and a rename would publish that, dropping the access of a save that was shared
 * (0644, 0664) or read by a supervisor under another uid. A first write has no mode to keep and stays 0600.
 * Prints `PASS preserve_mode` or `FAIL preserve_mode: file:line expr`. POSIX only. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gbb_host.h"

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define REQUIRE(x) do { if (!(x)) { \
    printf("FAIL preserve_mode: %s:%d %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define IMAGE_BYTES 64u

static bool put(int dirfd, const char *name, mode_t mode) {
    const int fd = openat(dirfd, name, O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) return false;
    const bool ok = write(fd, "old", 3u) == 3 && fchmod(fd, mode) == 0;
    return close(fd) == 0 && ok;
}

static void remove_entries(int dirfd, const char *const *names, size_t count) {
    for (size_t i = 0u; i < count; ++i) (void)unlinkat(dirfd, names[i], 0);
}

static int preserve_mode(void) {
    char root[512];
    const char *base = getenv("TMPDIR");
    if (base == NULL || base[0] == '\0') base = "/tmp";
    REQUIRE(snprintf(root, sizeof(root), "%s/gbb-host-save-mode-XXXXXX", base) < (int)sizeof(root));
    REQUIRE(mkdtemp(root) != NULL);
    int dirfd = -1;
    REQUIRE(host_save_io_open_dir(root, &dirfd) == HOST_IO_OK);

    uint8_t image[IMAGE_BYTES];
    for (size_t i = 0u; i < sizeof(image); ++i) image[i] = (uint8_t)(0x66u + i);
    struct stat info;
    int result = 0;

    /* No target yet: owner-only. */
    if (host_save_io_replace(dirfd, "fresh.sav", image, sizeof(image)) != HOST_IO_OK ||
        fstatat(dirfd, "fresh.sav", &info, AT_SYMLINK_NOFOLLOW) != 0 || (info.st_mode & 0777) != 0600)
        result = 1;

    /* An existing target keeps its bits, whether wider or narrower than 0600. */
    static const mode_t modes[] = {0640, 0664, 0644, 0400};
    for (size_t i = 0u; result == 0 && i < sizeof(modes) / sizeof(modes[0]); ++i) {
        if (!put(dirfd, "game.sav", modes[i]) ||
            host_save_io_replace(dirfd, "game.sav", image, sizeof(image)) != HOST_IO_OK ||
            fstatat(dirfd, "game.sav", &info, AT_SYMLINK_NOFOLLOW) != 0 || !S_ISREG(info.st_mode) ||
            (info.st_mode & 0777) != modes[i] || info.st_size != (off_t)sizeof(image))
            result = 1;
        (void)fchmodat(dirfd, "game.sav", 0600, 0); /* so the cleanup below can unlink under any umask */
    }

    static const char *const names[] = {"fresh.sav", "game.sav"};
    remove_entries(dirfd, names, sizeof(names) / sizeof(names[0]));
    (void)close(dirfd);
    (void)rmdir(root);
    REQUIRE(result == 0);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2 || strcmp(argv[1], "preserve_mode") != 0) {
        fprintf(stderr, "usage: test_host_save_mode preserve_mode\n");
        return 2;
    }
    if (preserve_mode() != 0) return 1;
    printf("PASS preserve_mode\n");
    return 0;
}
