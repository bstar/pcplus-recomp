# Serviced internal View a File

The opt-in `--file-viewer` terminal candidate now enables Alt-V, the original
Alt-Z reference entry and the command browser's V entry. It combines the
recovered [decoder](FILE_VIEWER_DECODER.md), [file owner](FILE_VIEWER_OWNER.md)
and [paging controller](FILE_VIEWER_SESSION.md) with the existing serviced
screen owner. The [acceptance receipt](validation/viewer-ui.json) binds this
candidate's software checks. It has not replaced the installed DOS release.

## Interface and live terminal service

The43-cell filename prompt uses the original box, colors and cursor position.
Empty Enter or Escape returns. Missing files show the original acknowledgement
message, then return to the retained filename field for another attempt. Home,
Page Up and Page Down navigate a successfully opened file; Escape closes it.
The default80-column page preserves literal CP437/control bytes, the original
footer and offscreen cursor with the saved shape. Configured external-viewer
commands and arbitrary original color preferences are not integrated here.
Path admission currently reuses the shared conservative ASCII DOS83 validator;
arbitrary OEM filenames are not established by these checks.

The existing frozen63000-byte redisplay snapshot lends3920 character bytes;
the independent live/history rings and full-size live/view frames remain owned
by their existing roles. Viewer/dialog/controller/file state totals754 bytes
in retained FILE_CODE. There is no new permanent DGROUP allocation or heap
allocation. The current candidate uses65488 DGROUP bytes (48 spare) and65458
resident code bytes (78 spare).

The shared screen owner swaps back to the live display for incoming parsing,
then recomposes the local view. Cursor/shape restoration follows the updated
live frame, including input received while the file is open. Each loading
turn performs a bounded step; the main loop avoids tick sleep while work is
pending and continues its usual serial/keyboard service. Stable loading does
not repaint on every step. Lower rows of a full-height viewer are protected
from the menu's ordinary exposed-background refresh.

The frontend accepts the parent's25/28/43/50 physical-row geometries at80
columns. Four layouts pass linked drawing/lifecycle checks; actual BIOS/UART
UI workflows in this receipt cover25 rows. Other physical geometries and
custom color preferences are not established by these results.

## Reservation and failure policy

The initial standalone file owner used the shared fixed reservation. That slot
already belongs to call logging in the full parent. The integrated viewer now
uses the existing dynamic reservation with a pure callback over its banked,
canonical identity. This coexists with the fixed call-log claim, rejects an
attempt to view the claimed call-log file and still prevents capture/replacement
of a file being viewed. The recorder's dynamic reservation cannot be replaced;
readiness/conflict checks refuse that overlap.

The opaque token is the stable address of the existing `redisplay_active`
control word. The viewer never modifies it through that token. No extra near
token allocation is required. The callback remains valid until release,
including quarantine after a failed close/release.

Read/seek errors receive a separate bounded cleanup turn before an error notice.
Ambiguous close/release retains ownership and schedules a guarded DOS exit with
code20. PROGRAM, Gateway and directory-resource admission refuse an owned view.
Shutdown closes known viewer ownership once; uncertainty bypasses ordinary file
cleanup/accounting paths while retaining the existing UART/path/mouse/trap exit
work. No automatic retry clears an ambiguous descriptor or reservation.

## Software evidence

- Ten actual8086 COM3/IRQ5 DOSBox workflows cover prompt cancellation, first/next/
  Home pages, raw binary text, empty/missing files, Alt-Z/browser entry and
  cancellation during loading. Each captures and compares the complete live
  frame/cursor/shape before and after the dialog, then verifies keyboard, fresh
  CPR, unchanged PRM/files and UART/PIC/vector restoration.
- An eleventh workflow sends text and a fresh DSR beneath the full-screen file
  page. Escape returns to the exact independently expected updated live frame
  and cursor. This establishes serviced parsing in the synthetic serial lab;
  it is not SIP/DSP or physical modem acceptance.
- The actual local first page, binary page and empty page match three original
 4000-byte captures exactly. Prompt and missing-file boxes each match710
  original character/attribute bytes. These are default reference settings,
  not a claim about every original PRM/editor option.
- 792 linked filename-editor cases preserve field/cursor semantics and all
  non-stack DGROUP bytes. Ten further frontend cases cover four geometries,
  readiness, read/seek cleanup and close/release quarantine with modeled DOS
  errors. The actual parent functions, callbacks and assembly execute.
- Static layout checks bind all754 retained banked state bytes, the existing
  snapshot loan and four resident pending/EXEC/shutdown/uncertainty gates.
  Four damaged copies are inspected and rejected, never executed.
- The dynamic-reservation owner passes902 actual DOS checks, including
  coexistence with a fixed claim, plus25 linked fault cases. The updated
  controller repeats all21727 DOS checks and26 linked cases/158 bounded steps.
- A fresh public Git export of1985 files, without originals, private settings,
  REA databases, Git metadata or prior objects, reproduces this terminal exactly.
  Disabling only `--file-viewer` reproduces the previous File Directory terminal
  byte-for-byte.

The first integration compile caught a16-bit C pointer-type mismatch and a
C89 declaration-order issue before a terminal executable was linked; both were corrected.
The accepted passive observer additionally reads back its restored timer vector;
the final ten-workflow receipts use that stronger observer.

Reproduce the terminal using the complete current candidate flags, adding
`--file-viewer`. This option requires the composed Gateway/large-frame parent
and implies path control. Component checks alone are insufficient to create
that parent. The accepted local candidate and exact build flags are bound in
the receipt's source proof/manifest.

## Remaining acceptance

The [BBS and pressure receipt](validation/viewer-bbs-pressure.json) additionally
records this exact parent returning from Alt-V to an unchanged stock Enigma
editor, including cursor/shape, literal CP437 viewer cells and subsequent editing.
The independent screen audit reports zero different cells at the CPR boundary.
Five actual DOS8086/FPU-off pressure cases pass capture, HOLD, capture/printer,
HOLD/printer and printer alone. Each receives3202 bytes while the viewer is open,
answers fresh DSRs and returns to the exact updated1920-cell live frame/cursor.
Capture and virtual PRN output match expected bytes exactly. The passive DOS
trace verifies one read-only viewer open/close and continued capture ownership.
Printer-ready polling is excluded from that bounded trace; device classification
remains recorded. This is virtual PRN evidence, not a physical printer test.

Synchronet also passes automatic ASPECT login, the stock unsaved FSEditor
roundtrip, subsequent editing and draft cancellation with the same application
bytes. Its independent screen audit reports zero different cells. This run
uses the386 CPU model with explicit XMS/UMB enabled and EMS disabled, loading
the passive observer high; the observer records its actual resident segment
and the audit refuses a conventional-memory fallback.

The initial strict8086 run failed ASPECT EXEC with DOS error8 while the full
observer occupied conventional memory. Merely writing LOADHIGH did not help:
DOSBox disables XMS for its8086 model and loaded the observer low. The accepted
386 run verifies upper-memory placement atCC4Bh. This establishes the editor
workflow with that explicit memory setup, not an8086 conventional-memory
ASPECT/viewer pass. A separate application memory-loan experiment was not
promoted; the application's source and executable remain unchanged.

The subsequent [transfer/recovery checkpoint](FILE_VIEWER_TRANSFER_RECOVERY.md)
binds43 positive runtime cases and eight rejected copied-artifact controls for
the same application bytes. It covers X/Y/ZMODEM, viewer-before-transfer,
automatic viewer cleanup on carrier loss, same-parent redial, and large stock
Enigma upload/download/cancel/retry through the SynthModem serial-side proxy.
These are scoped software results; physical timing and other text geometries
remain separate.

The [external-viewer checkpoint](FILE_VIEWER_EXTERNAL.md) now establishes the
native PRM/parameter/COMSPEC contract and a checked source command builder;
the full parent route is still unimplemented.

Complete native DOS failure/shutdown composition, configured external-viewer
integration, exhaustive native filename-field key behavior, and remaining
editor/key/Chat/ASPECT/emulation/protocol/Host features.
Physical DOS6.22/SHARE/Boca/SPA2102/SynthModem testing and verified deployment
remain separate gates. This integration closes no full original-parity claim.
