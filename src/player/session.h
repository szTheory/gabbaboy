#ifndef GABBABOY_PLAYER_SESSION_H
#define GABBABOY_PLAYER_SESSION_H

#include "gabbaboy/gabbaboy.h"

#include <stdbool.h>
#include <stddef.h>

#define PLAYER_SESSION_PATH_LIMIT 4096u

/* Replaces both the guest ROM and owned path only after bounded validation succeeds. */
bool player_session_replace_rom(gbb_instance *machine, char **in_out_path,
                                const char *path, char *out_error,
                                size_t error_capacity);

#endif
