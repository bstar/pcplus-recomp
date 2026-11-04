# Original display-mode service

608 additional native bytes now assemble from source: dispatcher2EAA, commit2F16
(including its alignment NOP), policy2F58, reflow476A, row selector6EF6,
baseline6F76, font leaves7E72 and font reset7F0F. Flat output matches the genuine
PCPlus2.01 original; each new unit also assembles as relocatable OMF. Normal
build/test inputs are committed assembly and provenance, not an original EXE.
These services are not yet enabled in the maintained terminal.

## Dispatch and fallback

Every request first homes the cursor through1BBE, including invalid selectors.
Selectors outside0..4 then return without committing3252 or changing video mode.
The valid paths are:

| Selector | Video service | Row argument used by commit |
| --- | --- | --- |
| 0 | Retain current mode | Current physical rows7A74 |
| 1 | Reset baseline mode | Physical rows after baseline probe |
| 2 | Reset baseline mode | Caller second WORD |
| 3 | Set configured video mode2070 | Physical rows after mode probe |
| 4 | Set configured video mode2070 | Caller second WORD |

For3/4, signed WORD2070 must be positive and font capability7A6E nonzero.
Otherwise the dispatcher resets baseline and explicitly passes selector1 to
commit. The saved selector3252 therefore becomes1. This differs from the
Ctrl-minus cycle's unsigned zero/nonzero test: a high-bit2070 value selects the
four-choice cycle but still fails this signed display admission test.

2070 is a configured/preferred video-mode WORD passed to the mode service,
not simply an adapter-class identifier. Its configuration/import mapping still
needs recovery. Baseline uses BIOS mode3, or7 when the runtime mono WORD7A86 is
nonzero. The existing vendor mode branch6F3E and scanline capability rules are
composed in the tests rather than replaced by stubs.

## Commit, reset and actual geometry

A nonzero third argument skips terminal reflow/reset, but still changes rows if
its chosen row WORD differs from physical7A74. A zero third argument always
calls the reflow wrapper. That wrapper temporarily substitutes3254 for reset
policy1D2E, calls476A, and restores the exact old policy WORD afterward.

Reflow requests a font change only when desired and physical row WORDs differ.
It preserves hidden/shown status as a normalized boolean while executing the
original status toggle46BA to recompute bounds from physical geometry. It then
calls the terminal reset20A4 with argument1. This is a reset path, not a promise
that terminal pixels, scrollback or margins survive intact.

Commit stores the resulting selector in3252 even if BIOS effects leave physical
rows unchanged. A saved selector is therefore not a hardware-success result.
The maintained integration must probe and use actual geometry, independently of
its requested mode. The existing native geometry6D1A executes in these tests;
its BIOS/BDA inputs are explicitly modeled.

## Font and scanline decisions

The row service gates on nonzero7A6E and reads only the low byte of the requested
WORD. In its7A70-nonzero path it selects explicit28,43 and50-row font sequences;
other bytes select the baseline sequence. In the7A70-zero path only43 selects
the8-pixel font; other bytes select14-pixel. Calling these paths VGA/EGA describes
the BIOS sequences; full capability detection and physical compatibility are not
proven here.

The VGA-style sequences request350 scanlines for43 rows and400 for the other
choices, reset the current mode with its preserve-video-memory bit, then select
the14/8-pixel ROM font or reset the cursor. BIOS/BDA scanline capability bits can
suppress the request. Font installation modifies bit0 of BDA487 and font reset
clears bit7; these are distinct operations. Physical row count is then reprobed.
Under the test BIOS model these produce25/28/43/50 rows; physical behavior still
requires DOS/card acceptance.

## Evidence and tests

[Provenance](../reconstruction/display_modes/provenance.json) binds eight units,
608 bytes and six REA Evidence IDs to original SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The ignored bundle is `analysis/display-modes-20261103.rea.json`; the session was
exported and closed. Static reads establish bytes, not observed BIOS behavior.

The [receipt](validation/display-modes-native.json) records separate source-only
and original-comparison runs. Each executes1440 composed inputs, all65531 invalid
selectors,512 low-byte aliases, signed mode boundaries, four noncanonical hidden
WORDs,60 modeled BIOS refusal cases, two vendor-mode paths,96 direct row/capability
combinations, all768 BDA scanline-byte/selection combinations and48 monochrome
baseline cases. ABI checks
retain DS=SS, BP/SI/DI, caller/callee stack cleanup and a stack guard. Actual
geometry/status/scanline/mode helpers execute; BIOS effects, terminal reset and
cursor/scroll/status/rectangle rendering remain modeled boundaries.

```sh
./tools/dev --command python standalone/check_display_modes_native.py \
  --output build/NEW-display-modes
./tools/dev --command python standalone/check_display_modes_native.py \
  --output build/NEW-display-modes-original \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

## Integration remains open

The next gate is maintained canonical geometry: status suppression, CSI bounds,
cursor/margins, RIS/reset policy, history/frame sizing and child screen loans.
Keep notice/Auto Answer underlays coherent when status disappears, and coordinate
ANSI reporting with the Linux bridge's size/NAWS policy. A refused font/mode must
leave a usable verified fallback. Then run DOS, owned Enigma/Synchronet, package
and physical gates before enabling the controls. See
[status/line integration constraints](STATUS_LINES_RECOVERY.md).

This change adds no executable to a package and updates no remote files. Ready
terminald9eae89d and archive4950ab99 remain unchanged. Hardware acceptance and the
full PCPlus feature inventory remain open.
