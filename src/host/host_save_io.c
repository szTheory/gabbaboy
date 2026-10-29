/* Directory-relative raw `.sav` I/O for host mode (D-06, D-08, D-09).
 *
 * Every operation goes through one directory descriptor opened once, so a symlink swapped into the
 * save-dir path later cannot redirect a write. The POSIX body sits inside #ifndef _WIN32 with ISO C
 * stubs: host mode is POSIX-only in v0.3 (D-05) but this file must still compile on MSVC. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gbb_host.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>

#ifndef _WIN32
#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#endif

const char *host_io_stage_name(int code) {
    switch (code) {
    case HOST_IO_OK: return "ok";
    case HOST_IO_EMISSING: return "save-missing";
    case HOST_IO_ESYMLINK: return "save-symlink";
    case HOST_IO_ENOTREG: return "save-not-regular";
    case HOST_IO_ESIZE: return "save-size";
    case HOST_IO_EUNSTABLE: return "save-unstable";
    case HOST_IO_EREAD: return "save-read";
    case HOST_IO_ETEMP: return "temp";
    case HOST_IO_EWRITE: return "write";
    case HOST_IO_ESYNC: return "sync";
    case HOST_IO_ECLOSE: return "close";
    case HOST_IO_ETARGET: return "target";
    case HOST_IO_ERENAME: return "rename";
    case HOST_IO_EDIRSYNC: return "dir-sync";
    case HOST_IO_ENOTDIR: return "save-dir-not-directory";
    default: return "unknown";
    }
}

#ifndef _WIN32

int host_save_io_open_dir(const char *path, int *out_dirfd) {
    if (path == NULL || out_dirfd == NULL) return HOST_IO_EMISSING;
    const int fd = open(path, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (fd < 0) return errno == ENOTDIR ? HOST_IO_ENOTDIR : HOST_IO_EMISSING;
    *out_dirfd = fd;
    return HOST_IO_OK;
}

/* The one place a regular file is opened for reading: no symlink is followed and nothing blocks, so a
 * FIFO or device cannot stall the caller. On HOST_IO_OK the descriptor is open and `*before` is its fstat. */
static int open_regular_nofollow(int dirfd, const char *name, int *out_fd, struct stat *before) {
    const int fd = openat(dirfd, name,
                          O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_NOCTTY | O_CLOEXEC);
    if (fd < 0) {
        if (errno == ENOENT) return HOST_IO_EMISSING;
        if (errno == ELOOP || errno == EMLINK) return HOST_IO_ESYMLINK;
        return HOST_IO_EREAD;
    }
    if (fstat(fd, before) != 0) { (void)close(fd); return HOST_IO_EREAD; }
    if (!S_ISREG(before->st_mode)) { (void)close(fd); return HOST_IO_ENOTREG; }
    *out_fd = fd;
    return HOST_IO_OK;
}

int host_save_io_read_exact(int dirfd, const char *name, uint8_t *buf, size_t want) {
    if (name == NULL || buf == NULL) return HOST_IO_EREAD;
    int fd = -1;
    struct stat before;
    const int opened = open_regular_nofollow(dirfd, name, &fd, &before);
    if (opened != HOST_IO_OK) return opened;
    /* The size is compared, never used to size an allocation: the caller owns `want + 1` bytes. */
    if (before.st_size < 0 || (uintmax_t)before.st_size != (uintmax_t)want) {
        (void)close(fd);
        return HOST_IO_ESIZE;
    }
    size_t total = 0u;
    while (total < want + 1u) {
        const ssize_t count = read(fd, buf + total, want + 1u - total);
        if (count > 0) { total += (size_t)count; continue; }
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) { (void)close(fd); return HOST_IO_EREAD; }
        break;
    }
    struct stat after;
    const bool stable = fstat(fd, &after) == 0 && after.st_dev == before.st_dev &&
                        after.st_ino == before.st_ino && after.st_size == before.st_size &&
                        total == want;
    const int closed = close(fd);
    if (!stable) return HOST_IO_EUNSTABLE;
    return closed == 0 ? HOST_IO_OK : HOST_IO_EREAD;
}

int host_save_io_read_bounded(int dirfd, const char *name, uint8_t *buf, size_t cap, size_t *out_len) {
    if (name == NULL || buf == NULL || out_len == NULL || cap == 0u) return HOST_IO_EREAD;
    int fd = -1;
    struct stat before;
    const int opened = open_regular_nofollow(dirfd, name, &fd, &before);
    if (opened != HOST_IO_OK) return opened;
    /* st_size is never used to size anything: the caller's buffer is the bound. */
    size_t total = 0u;
    while (total < cap) {
        const ssize_t count = read(fd, buf + total, cap - total);
        if (count > 0) { total += (size_t)count; continue; }
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) { (void)close(fd); return HOST_IO_EREAD; }
        break;
    }
    struct stat after;
    const bool stable = fstat(fd, &after) == 0 && after.st_dev == before.st_dev &&
                        after.st_ino == before.st_ino && after.st_size == before.st_size;
    const int closed = close(fd);
    if (!stable) return HOST_IO_EUNSTABLE;
    if (closed != 0) return HOST_IO_EREAD;
    *out_len = total;
    return HOST_IO_OK;
}

#ifdef GBB_HOST_TESTING
/* Test builds only (gabbaboy_host_testing). One file-static, one-shot fault: the next writer call that
 * reaches `stage` fails with `err`, mirroring session.c's consume_test_fault. The shipped library and
 * the runner are built without GBB_HOST_TESTING and define none of these symbols. */
static int test_fault_stage = HOST_IO_OK;
static int test_fault_errno = 0;
static unsigned test_sync_calls = 0u;

void host_save_io_test_fail_next(int stage_code, int err) {
    test_fault_stage = stage_code;
    test_fault_errno = err;
}

unsigned host_save_io_test_sync_calls(void) { return test_sync_calls; }

static bool consume_test_fault(int stage) {
    if (test_fault_stage != stage) return false;
    test_fault_stage = HOST_IO_OK;
    errno = test_fault_errno;
    return true;
}
#endif

/* True when a test build asked this stage to fail (errno is already set); constant false otherwise. */
static bool injected(int stage) {
#ifdef GBB_HOST_TESTING
    return consume_test_fault(stage);
#else
    (void)stage;
    return false;
#endif
}

static bool write_all(int fd, const uint8_t *bytes, size_t size) {
    size_t written = 0u;
    while (written < size) {
        const ssize_t count = write(fd, bytes + written, size - written);
        if (count > 0) { written += (size_t)count; continue; }
        if (count < 0 && errno == EINTR) continue;
        return false;
    }
    return true;
}

/* Flushes the temp file to stable storage. fsync is never retried on the same descriptor after a
 * failure: after EIO the kernel may already have dropped the dirty pages, so a second success would
 * be a lie (D-09 step 3). */
static int sync_file(int fd) {
#ifdef GBB_HOST_TESTING
    ++test_sync_calls;
#endif
    if (injected(HOST_IO_ESYNC)) return -1;
#ifdef F_FULLFSYNC
    if (fcntl(fd, F_FULLFSYNC) == 0) return 0;
    if (errno != ENOTSUP && errno != ENOTTY && errno != EINVAL) return -1;
#endif
    return fsync(fd);
}

int host_save_io_replace(int dirfd, const char *name, const uint8_t *bytes, size_t len) {
    if (name == NULL || (bytes == NULL && len != 0u)) { errno = EINVAL; return HOST_IO_ETEMP; }
    const size_t name_len = strlen(name);
    /* The name is one component of a host-built stem; a separator would escape the directory. */
    if (name_len == 0u || name_len > 240u || strchr(name, '/') != NULL) {
        errno = EINVAL;
        return HOST_IO_ETEMP;
    }

    /* The temp is created owner-only, and the rename would make that the published mode. A save that was shared
     * (0644, 0664) or read by a supervisor under another uid must not lose its access on the first flush, so the
     * permission bits of an existing regular target are carried over to the temp. Best effort and bits only: a
     * mode that cannot be applied (a filesystem without modes) leaves the owner-only default, and the owner and
     * group of the target are not reproduced. */
    mode_t publish_mode = 0600;
    struct stat existing;
    if (fstatat(dirfd, name, &existing, AT_SYMLINK_NOFOLLOW) == 0 && S_ISREG(existing.st_mode))
        publish_mode = existing.st_mode & 0777;

    char temp[320];
    int fd = -1;
    const long pid = (long)getpid();
    for (unsigned seq = 0u; seq < GBB_HOST_TEMP_RETRIES; ++seq) {
        (void)snprintf(temp, sizeof(temp), ".%s.tmp-%ld-%u", name, pid, seq);
        if (injected(HOST_IO_ETEMP)) return HOST_IO_ETEMP;
        fd = openat(dirfd, temp, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
        if (fd >= 0) break;
        if (errno != EEXIST) return HOST_IO_ETEMP;
    }
    if (fd < 0) { errno = EEXIST; return HOST_IO_ETEMP; }
    if (publish_mode != 0600) (void)fchmod(fd, publish_mode); /* fchmod ignores the umask, unlike the create */

    int code = HOST_IO_OK;
    int failure_errno = 0;
    struct stat target;
    if (injected(HOST_IO_EWRITE) || !write_all(fd, bytes, len)) {
        code = HOST_IO_EWRITE;
        failure_errno = errno;
    } else if (sync_file(fd) != 0) {
        code = HOST_IO_ESYNC;
        failure_errno = errno;
    }
    const bool close_failed = close(fd) != 0 || injected(HOST_IO_ECLOSE); /* the real close always runs */
    if (close_failed && code == HOST_IO_OK) { /* checked, never retried */
        code = HOST_IO_ECLOSE;
        failure_errno = errno;
    }
    if (code == HOST_IO_OK && injected(HOST_IO_ETARGET)) {
        code = HOST_IO_ETARGET;
        failure_errno = errno;
    }
    if (code == HOST_IO_OK) {
        if (fstatat(dirfd, name, &target, AT_SYMLINK_NOFOLLOW) == 0) {
            if (!S_ISREG(target.st_mode)) { code = HOST_IO_ETARGET; failure_errno = EINVAL; }
        } else if (errno != ENOENT) {
            code = HOST_IO_ETARGET;
            failure_errno = errno;
        }
    }
    if (code == HOST_IO_OK && (injected(HOST_IO_ERENAME) || renameat(dirfd, temp, dirfd, name) != 0)) {
        code = HOST_IO_ERENAME;
        failure_errno = errno;
    }
    if (code != HOST_IO_OK) {
        (void)unlinkat(dirfd, temp, 0); /* nothing was published; do not leave the temp behind */
        errno = failure_errno;
        return code;
    }
    /* The rename happened. A directory-sync failure is reported but the temp is already the target. */
    if (injected(HOST_IO_EDIRSYNC)) return HOST_IO_EDIRSYNC;
    if (fsync(dirfd) != 0 && errno != EINVAL && errno != ENOTSUP && errno != EOPNOTSUPP)
        return HOST_IO_EDIRSYNC;
    return HOST_IO_OK;
}

/* D-10. The directory is read through a duplicate descriptor so closedir cannot close the caller's
 * dirfd, and rewound first so a shared file offset cannot hide entries. unlinkat without
 * AT_REMOVEDIR removes a symlink itself and never follows it to its target. */
int host_save_io_sweep(int dirfd, const char *stem) {
    if (stem == NULL || stem[0] == '\0') return HOST_IO_EREAD;
    char prefix[GBB_HOST_STEM_MAX_BYTES + 16u];
    const int length = snprintf(prefix, sizeof(prefix), ".%s.sav.tmp-", stem);
    if (length <= 0 || (size_t)length >= sizeof(prefix)) return HOST_IO_EREAD;
    const int duplicate = fcntl(dirfd, F_DUPFD_CLOEXEC, 0);
    if (duplicate < 0) return HOST_IO_EREAD;
    DIR *directory = fdopendir(duplicate);
    if (directory == NULL) { (void)close(duplicate); return HOST_IO_EREAD; }
    rewinddir(directory);
    int removed = 0;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL) {
        if (strncmp(entry->d_name, prefix, (size_t)length) != 0) continue;
        if (unlinkat(dirfd, entry->d_name, 0) == 0) ++removed;
    }
    (void)closedir(directory);
    return removed;
}

#else /* _WIN32: host mode refuses before any filesystem access (D-05); these satisfy the linker. */

int host_save_io_open_dir(const char *path, int *out_dirfd) {
    (void)path;
    (void)out_dirfd;
    return HOST_IO_EMISSING;
}

int host_save_io_read_exact(int dirfd, const char *name, uint8_t *buf, size_t want) {
    (void)dirfd;
    (void)name;
    (void)buf;
    (void)want;
    return HOST_IO_EMISSING;
}

int host_save_io_read_bounded(int dirfd, const char *name, uint8_t *buf, size_t cap, size_t *out_len) {
    (void)dirfd;
    (void)name;
    (void)buf;
    (void)cap;
    (void)out_len; /* left untouched: nothing was read */
    return HOST_IO_EREAD;
}

int host_save_io_sweep(int dirfd, const char *stem) {
    (void)dirfd;
    (void)stem;
    return HOST_IO_EREAD;
}

int host_save_io_replace(int dirfd, const char *name, const uint8_t *bytes, size_t len) {
    (void)dirfd;
    (void)name;
    (void)bytes;
    (void)len;
    return HOST_IO_ETEMP;
}

#endif
