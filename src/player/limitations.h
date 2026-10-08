#ifndef GBB_PLAYER_LIMITATIONS_H
#define GBB_PLAYER_LIMITATIONS_H

#define GBB_PLAYER_LIMITATIONS_TEXT \
    "Audio is not implemented. Battery saves support standard MBC1 type $03 with 8 or 32 KiB RAM. Saves are checksummed and atomically replaced; cooperating GabbaBoy processes are serialized with an advisory lock. Changed RAM autosaves after 2 seconds quiet or 10 seconds maximum age. Save failures require retry or an explicit continue-without-saving choice. This is software evidence, not physical hardware proof."

#endif
