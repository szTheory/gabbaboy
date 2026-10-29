#include "limitations.h"

#include <stdio.h>
#include <string.h>

int main(void) {
    static const char expected[] =
        "Audio uses a scoped DMG-CPU-B digital APU software model with 48 kHz signed 16-bit interleaved stereo output; CGB/VIN, physical hardware, revision equivalence, analog output, and listening quality are not qualified. Battery saves are kept for MBC1, MBC2, MBC3 (RAM and clock) and MBC5 battery cartridges; MBC1 type $03 saves keep the v0.1 file format and every other type uses a versioned v2 file. Saves are checksummed and atomically replaced; cooperating GabbaBoy processes are serialized with an advisory lock. Changed RAM autosaves after 2 seconds quiet or 10 seconds maximum age. Save failures require retry or an explicit continue-without-saving choice. The game clock of a timer cartridge catches up from the time stored in the save when a save is reopened; time spent paused while the player stays open is not recovered. The player runs DMG and CGB software with --model auto|dmg|cgb (default dmg) and colour presentation on the CGB profile; DMG software on the CGB profile uses the core's fixed original compatibility palette and the player has no palette flag. There is no colour correction: each 5-bit channel is expanded with (c << 3) | (c >> 2). CGB-profile audio uses the DMG APU model; native CGB guest reads on the CGB-CPU-E software model expose FF76/FF77 digital DAC inputs, while compatibility mode reads $FF. CGB double speed is implemented; GDMA and HBlank DMA run on the selected bootless CGB-CPU-E software model. CGB mode-3 timing is not claimed; physical CGB-E remains UNKNOWN/POLICY. General game compatibility is not claimed. This is software evidence, not physical hardware proof. State slots are bound to the exact GabbaBoy release that saved them, and a slot saved by any other release is refused. The slot message appears in the window title, which is hidden in fullscreen and is not announced by VoiceOver.";

    if (strcmp(GBB_PLAYER_LIMITATIONS_TEXT, expected) != 0) {
        fprintf(stderr, "player limitation text differs from the supported preview claim\n");
        return 1;
    }
    return 0;
}
