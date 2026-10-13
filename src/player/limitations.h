#ifndef GBB_PLAYER_LIMITATIONS_H
#define GBB_PLAYER_LIMITATIONS_H

#define GBB_PLAYER_LIMITATIONS_TEXT \
    "Audio uses a scoped DMG-CPU-B digital APU software model with 48 kHz signed 16-bit interleaved stereo output; CGB/VIN, physical hardware, revision equivalence, and listening quality are not qualified. Battery saves are kept for MBC1, MBC2, MBC3 (RAM and clock) and MBC5 battery cartridges; MBC1 type $03 saves keep the v0.1 file format and every other type uses a versioned v2 file. Saves are checksummed and atomically replaced; cooperating GabbaBoy processes are serialized with an advisory lock. Changed RAM autosaves after 2 seconds quiet or 10 seconds maximum age. Save failures require retry or an explicit continue-without-saving choice. The game clock of a timer cartridge catches up from the time stored in the save when a save is reopened; time spent paused while the player stays open is not recovered. There is no colour correction on the CGB profile. This is software evidence, not physical hardware proof."

#endif
