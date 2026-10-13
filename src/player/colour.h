#ifndef GABBABOY_PLAYER_COLOUR_H
#define GABBABOY_PLAYER_COLOUR_H

#include <stddef.h>
#include <stdint.h>

/* Pure presentation helpers for the CGB frame (D-27, D-28). No SDL, no core. */

/* Expands a 160x144 RGB555 frame (native uint16_t R | G << 5 | B << 10, rows
 * pitch_bytes apart) into tightly packed RGBA32 bytes, 160 * 144 * 4 of them.
 * Each channel uses (c << 3) | (c >> 2) and alpha is 255. The player applies no
 * colour correction, so what the guest wrote to colour RAM is what is shown. */
void player_rgb555_frame_to_rgba(const uint16_t *pixels, size_t pitch_bytes,
                                 uint8_t *rgba);

/* Window-title token for a gbb_exec_mode value: "DMG", "CGB",
 * "CGB (DMG-compat)", or "-" when no ROM is loaded. */
const char *player_model_token(uint32_t mode);

#endif
