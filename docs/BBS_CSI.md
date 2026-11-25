# Modern BBS CSI compatibility (opt-in, 2026-11-25)

`--bbs-csi` (`TERMINAL_BBS_CSI`) is maintained compatibility code, not
original PCPlus behaviour. It changes how unknown control sequences are
handled for modern BBS hosts (Synchronet, Mystic, ENiGMA½ and SyncTERM-aware
software).

Without the flag every object is unchanged. The default minimal (`e25e0bd7…`)
and qualified (`7f5b3b03…`) parents rebuild byte-identically. The flat
assembly of `reconstruction/ansi/dispatch.asm` still matches its provenance
hash `3a1524f4…`.

## What the original does

The recovered dispatcher ends a sequence at the first byte the parameter
reader does not collect, and dispatches on that byte. The original ignores
these terminators:

- the private prefixes `<` and `=` (and `?`/`>` after parameters);
- `:`;
- every intermediate except `"`, `$` and `'`.

The rest of the sequence is then printed as text. For example:

| Host sends | Original screen shows |
| --- | --- |
| SyncTERM `ESC[=255h` | `255h` |
| CTerm font select `ESC[0;40 D` | `D` |
| `ESC[1:2m` | `2m` |

The finals `` ` `` (HPA), `a` (HPR), `d` (VPA) and `e` (VPR) are ignored.

## What the flag changes

All changes are entries in the recovered command table, selected by
`%define`.

- **Unknown sequences are consumed.** The 18 unhandled terminator bytes go to
  `csi_bbs_skip`. Its far routine (`src/terminal/bbs_csi.asm`, segment
  `BBS_CSI_CODE`) consumes the rest of the sequence through its final byte
  (40h..7Eh), as ECMA-48 5.4 defines it:
  - C0 controls inside the sequence still execute, as in the parameter reader;
  - CAN, SUB or a receive timeout abandon the sequence;
  - ESC and bytes 80h and above are put back;
  - at most 64 bytes are consumed.
- **Cursor finals reuse native handlers.**
  - HPA uses CHA `G`, HPR uses CUF `C` and VPR uses CUD `B`.
  - VPA is a 16-byte near stub. It keeps the cursor column and enters CUP, so
    origin mode and the row clamp are native.

Near `_TEXT` cost: about 33 bytes, including one trampoline. No DGROUP data.

The `"`, `$` and `'` intermediates keep their recovered native handlers. For
example, `ESC[?1$p` (DECRQM) still leaves `p`.

## Actual DOS evidence

`standalone/test_bbs_csi_dos.py` runs in DOSBox-X with an 8086 CPU, actual
COM1 and a synthetic modem peer, using profile 6 (ANSI). It checks:

- **Replies:**
  - the save/move/CPR/restore size probes, answered `24;80`;
  - DSR `0n`, DA, secondary DA and XTWINOPS `8;24;80t`.
- **Native drawing:** SCO save/restore, ECH, CHA, EL 1/2, CNL, SGR blink and
  bold attribute `9E`, CP437 blocks and cursor hide/show.
- **Flag cases:** the private and intermediate sequences, a BEL inside
  `ESC[=…c`, HPA/HPR/VPR and VPA, including the clamp to the last text row.

A parent without the flag must instead show the native printed tails.

| Parent | Result |
| --- | --- |
| qualified flag set + `--bbs-csi` `3cdf023a` | PASS (maintained) |
| qualified `7f5b3b03` | PASS (native) |

Results are in `build/bbs-csi-dos/`.

## Not covered

- REP (`b`) needs the last printed character, and keeping it needs a hook in
  the print path. SU/SD (`S`/`T`) are not handled.
- iCE colours (blink bit as bright background) are not implemented.
- No physical terminal, modem or live BBS acceptance.
