# Independent ANSI comparison and status geometry

An independent whole-cell comparison found a real geometry error in the
directory-adoption application: it displayed its status on physical row25,
but its terminal scrolling/addressing/erasure bounds still included that row.
After insert/delete-line operations, a hidden line reappeared above the status.
After bottom scrolling, the terminal reported row25 while the visible terminal
area had only24 rows.

The candidate now initializes24 terminal rows, last-row/origin-bottom23 and
1920 erase cells. The modal UI still owns the full25-row physical display.
The existing reset snapshot captures this corrected geometry. The change is
guarded by `DIRECTORY_RESOURCE_ADOPTION`; all seven earlier terminal control
executables retain their accepted bytes. No renderer algorithm, history size,
near allocation or stack size changes.

`standalone/test_ansi_reference_dos.py` feeds identical CP437/ANSI bytes to the
actual DOS8086 application through its real UART and to independent
[pyte Screen/Stream](https://pyte.readthedocs.io/en/latest/api.html). It compares
all1920 character/attribute pairs in the terminal area and the actual CPR
response, checks the status help label remains visible, verifies the PRM stays
unchanged, and compares before/after UART/PIC/vector snapshots. DSR establishes
application readiness; no product RAM, instruction or reply is supplied by the
test. Screen capture occurs after normal application exit.

The reference adapter decodes input as CP437 and maps pyte's eight-color,
bold/blink/reverse cell attributes to VGA bytes. Unsupported styles/colors
refuse conversion rather than being silently discarded. It uses an explicit
80x24 reference screen and normal attribute07. It does not implement an ANSI
parser or reuse the application parser/renderer. Nix's existing pinned Nixpkgs
input supplies pyte0.8.2 and wcwidth0.8.2; reference module and lock hashes are
recorded in each final report.

Fourteen scenarios pass with seven-byte input fragments: all128 high CP437
bytes and a BBS panel, cursor/control movement, line/display erasure,
character/line insert-delete, scrolling regions, deferred wrap, bottom
scrolling, colors/styles, cursor save/restore, origin mode, status-boundary
clamping, and RIS after dirty margins/origin/rendition. CP437, line edits and
RIS also pass with byte-at-a-time input. All32640 compared cell pairs match,
and every real cursor reply agrees with its reference. The old and fixed line
tests use exactly the same input bytes: six and thirty differing cells become
zero. The old bottom-scroll reply25;1 becomes the expected24;1.

The new candidate also passes native default Apply, a profile4/IRQ7 Apply after
a deferred PRMEDIT save, and a stock owned ENiGMA editor/directory-preview
workflow through the real SynthModem proxy. That BBS test retains the explicit
250ms key framing and20ms serial pacing of its earlier acceptance; it is not
an unframed, SIP/DSP or analog test.

See [the receipt](validation/ansi-reference-geometry.json) for exact package,
source and evidence identities. The application binary is
`c41df22fcc928bef5d0ab220a58e39eff69c2d68520d0578c7428d25fab442b6`.
Earlier receipts remain evidence for their recorded older binaries.

Pyte models Linux/VT-style ANSI behavior; it is not the behavioral authority
for every PCPlus profile. These tests cover the enumerated profile6 ANSI
scenarios, not every terminal emulation, every chunk/timing, custom palette,
exact status-row contents, font pixels, complete stock BBS screens, transfers,
sustained pressure or physical Boca/SPA2102/card operation. Full rendering and
application acceptance remain open. No live BBS, bridge, network or removable
card was changed.
