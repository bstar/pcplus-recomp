# Recovered SOH, VT and CAN controls

Actual ENiGMA½ compatibility testing exposed an unimplemented VT handler while
the stock Mystery Skull oneliner screen sent malformed SAUCE metadata. The
renderer received byte `0b` in that metadata and stopped at resident service
`0f62`. This module recovers the complete original helper and the SOH/CAN
helpers needed by the following metadata bytes, rather than discarding them.

| Original resident range, end exclusive | Export | Bytes |
| --- | --- | --- |
| `0e62..0e70` | `terminal_control_0e62` | 14 |
| `0f62..0fb0` | `terminal_control_0f62` | 78 |
| `11a8..123c` | `terminal_control_11a8` | 148 |

All 240 bytes assemble exactly to recorded original hashes. Flat mode preserves
original addresses; `INPUT_CONTROLS_OMF` uses named linker symbols. Entry points
take no arguments and return near. VT preserves no additional registers;
SOH/CAN may clobber AX/BX/CX/DX and flags via their services. DS=SS and a clear
direction flag remain the real-mode integration requirements.

The two new DS words are `terminal_control_mode_9026` (`9026`) and
`terminal_control_mode_1fb0` (`1fb0`). Both default to zero in the maintained
application; names remain neutral because their complete emulation/protocol
semantics were not yet reconstructed at that checkpoint. The later
[automatic-reception investigation](ZMODEM_AUTOSTART_NATIVE.md) proves that
DS1fb0 is the saved Auto Download word. The maintained terminal uses its
separate CRC-validating recognizer and leaves the recovered native lookahead
gate disabled. Existing `terminal_dec_keys` (`8fe8`),
`terminal_newline_mode_9020` (`9020`), `terminal_tab_wrap` (`903e`), current
attribute/cursor/profile state retain their existing aliases.

SOH homes only when DS9026 is enabled. VT moves up for profile IDs20 and above;
otherwise it may read an encoded row when DS9026 is set, call real linefeed
when DS8fe8 is set, or select another emulation callback when DS9020 is set.
Its ordinary all-zero gate branch returns unchanged. CAN may call emulation
callbacks, move right, or perform a guarded protocol-recognition sequence.
Its ordinary all-zero gate branch also returns unchanged. These return paths
are recovered original behavior, not replacement no-ops.

Unrecovered callbacks remain explicit application traps:
`terminal_control_ba33`, `terminal_control_b9eb`, `terminal_control_6dca`,
`terminal_control_aad9`, `terminal_control_0dae`, `terminal_control_bb83`.
The complete CAN recognition path, specialized emulations and transfer
launching remain unfinished.

Run public source-only CPU regressions after building the terminal:

```sh
./tools/dev --command python3 lab/bbs/check_enigma_controls.py
```

Tests check exact flat hashes, original default/nondefault home/linefeed/up/
encoded-row/right branches, explicit unsupported-service traps and a synthetic
malformed-metadata byte fixture. They require no original executable or captured
BBS session. An optional `--wire PATH` replays a local capture; the original
21,271-byte ENiGMA failure stream is now consumed completely in linked CPU
replay. Actual DOS/BBS tests and stock art evidence are described in
[the ENiGMA lab](../lab/bbs/enigma.md).
