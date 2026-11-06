# Configured external viewer

The original2.01 Alt-V command has two distinct routes. With an empty external
command at DS1EE1 it opens the internal viewer. With a configured command it
opens an **Enter parameters** dialog, then runs the configured command through
COMSPEC. The parameter field is not restricted to one filename.
[Provenance](../reconstruction/file_viewer/external-provenance.json) binds the
native regions, REA Evidence IDs, analysis bundles and source component.
The [receipt](validation/viewer-external.json) binds seven original runtime
cases and36,147 source-only DOS command-construction checks.

## Original contract

- PRM offset035Dh maps to DS1EE1. The original configuration reader at
  overlay19:EE2B supplies a64-character limit and terminates at byte64, requiring
  65 storage bytes. Its shared reader at E72A enforces the configured limit.
- Overlay3:DE2C obtains a command label through resident3EA4 and calls the
  parameter controller at DE80. The actual dialog title is
  `VTEST.COM Parameters`, or `VTEST.COM /Q /X Parameters` with those switches.
  It displays `Enter parameters:` and places the cursor at row12,column25.
- The controller accepts48 parameter characters. Escape cancels the launch.
  Empty Enter launches the command with no extra effective child arguments.
- The wrapper copies the configured command, appends one space and the entered
  text, then calls resident433D with the command-processor flag set. It does
  not add quotes or perform TEXT caret/pause expansion.
- Actual owned-child DOS tails confirm relative and absolute paths, configured
  `/Q /X` before the entered text, literal spaces and48 entered characters.
  The child retains drive C: and its root current directory. Full terminal
  character/attribute cells, cursor position and shape restore in all seven
  normally exited workflows, including cancellation.

The runtime tests execute the unmodified original with only a copied PRM and
owned files mounted. The small source-built COM child records its actual PSP
command tail and DOS current directory. A passive timer captures the native
prompt and terminal frames. The proprietary executable, private baseline,
analysis images, raw frames and REA bundles remain ignored. Early exploratory
exit recipes timed out; the final recipe adds Escape before the normal Alt-X
sequence and reaches its DOS completion marker in all seven cases. Those early
probes are not counted as accepted lifecycle evidence.

## Checked source component

`viewer_external_build` reads the65-byte field from the supplied1264-byte PRM,
validates termination and combines it with a bounded parameter string. Empty
configuration returns DISABLED. Malformed fields, insufficient output capacity,
segment/20-bit wrap and output/input aliases fail without changing output or
length. No persistent state or near DATA is allocated; the code resides in
FILE_CODE. It performs no DOS/BIOS calls, path lookup, quoting or execution.

The native wrapper uses an80-byte temporary, although its configured command
and parameter limits can require114 bytes including separator and NUL. The
source component checks that full bound. This avoids reproducing a static
bounds concern; no original crash at those limits has been established.

The DOS8086/FPU-off diagnostic covers every command length0..65, parameter
length0..49, minimum/full output capacities, literal OEM bytes, guards,
unchanged inputs, disabled/error transactions and pointer bounds. It is a
component gate, not acceptance of external viewing in the interactive parent.

## Opt-in parent integration

`--external-viewer` now implies `--file-viewer` and requires the accepted session
baseline and existing Gateway/large-frame parent. Alt-V, the native Alt-Z entry
and browser V all inspect the same opaque PRM field. An empty field retains the
internal viewer; malformed configuration produces a local refusal. No PRM bytes
are rewritten by viewing. The accepted copied baseline is checked again before
launch so a changed command cannot silently replace the one shown to the user.

The external editor has a48-character field, native default box/cursor and
literal parameter handling. Escape queues no child. Enter releases the modal
screen owner before queueing the existing foreground PROGRAM transaction. That
transaction keeps its serial, file, trap, mouse and display safeguards. The new
COMSPEC wrapper accepts the full113-character command; ordinary PROGRAM keeps
its existing51-character limit. Successful external viewing restores the terminal
without an extra acknowledgement. Parameter editing repaints just48 cells on
each key; the initial full-box redraw caused rapid BIOS input to overflow the
test queue and was corrected before accepting the final candidate.

State uses128 retained FILE_CODE bytes and a two-byte near admission marker;
the command is transient stack storage. The candidate uses65488 DGROUP bytes
(48 spare) and65516 resident code bytes (20 spare). All four cross-bank dispatch
gates have linked relocation checks and rejected, unexecuted damaged controls.

The parent acceptance checkpoint is recorded separately in
[viewer-external-parent.json](validation/viewer-external-parent.json). It covers
eleven actual DOS launch/cancel/refusal routes, ten internal fallback workflows,
seven native710-byte prompt comparisons and thirteen linked lifecycle cases.
Actual child PSP tails establish configured switches, literal spaces, empty
parameters,48 entered characters and the maximum113-character command. Each
runtime case verifies complete terminal cells/cursor/shape restoration, fresh
keyboard/CPR service, unchanged PRM and normal UART/PIC/vector restoration.
The public-source export gate reproduces both the enabled executable and the
previous internal-viewer executable with the external feature disabled.

This candidate has not replaced the physical installation. Default25-row colors
are the runtime reference; long titles use bounded clipping, whose exact native
behavior is not established. Missing interpreter/program, allocation failure,
nonzero child-exit presentation, live BBS pressure, transfer recovery and
same-process reconnects through this external-child path remain separate work.
The previous internal-viewer BBS and transfer receipts retain their original
executable identity. Physical acceptance and the broader parity inventory remain
open.

## Failure recovery and core Enigma regression

The unchanged external-viewer candidate has a separate
[recovery receipt](validation/viewer-external-recovery.json). Five actual DOS
cases cover a missing viewer followed by a successful retry in the same parent,
missing configured COMSPEC with ordinary and empty PATH, a valid MZ interpreter
requesting65535 extra paragraphs, and an owned child that exits37. The allocation
refusal displays the local PROGRAM failure acknowledgement; the test then checks
all2000 terminal cells, cursor/shape, fresh keyboard/CPR and final hardware
restoration. Shell-handled missing-command and nonzero-child cases return without
an extra application acknowledgement. This observes the composed COMMAND.COM
policy; it does not establish direct propagation of the viewer's exit code.

The passive timer only reads video and keeps an error-prompt flag. It rejects a
still-visible failure prompt as a restored terminal frame. An early two-byte MZ
probe timed out and is excluded: it did not establish malformed-header refusal.
The accepted allocation fixture has a complete MZ header and a valid exit stub.
An empty-PATH exploration initially prevented the keyboard utility from running;
accepted tests qualify its existing Z:\\BIN path. DOSBox still resolves its own
COMMAND.COM with that empty PATH, so absent-interpreter rejection remains open.

The same terminal executable passes the stock Enigma login and unsaved-editor
workflow through the isolated, previously accepted SynthModem proxy snapshot.
The independent reference audit matches1920 cells and cursor with zero differing
cells across48365 delivered bytes. This checks the core terminal path: it does
not open an external viewer inside the editor, exercise SIP/audio, or validate
the physical modem. No application, live SynthModem service, installed selection
or private configuration changed for this recovery checkpoint.

## External child inside stock BBS editors

The [BBS composition receipt](validation/viewer-external-bbs.json) records
external Alt-V execution inside unsaved stock Enigma and Synchronet editors.
An owned COM child records its real PSP tail and current drive/directory,
switches to mode13h, then signals a private passive-observer completion marker.
The observer will capture the restored editor only after this marker. Restoring
the screen before EXEC cannot satisfy this gate. The child and observer do not
write product memory or supply terminal replies.

Each run checks all2000 editor cells, cursor position/shape and video geometry
after the graphics child returns, then continues ordinary editing and aborts
the draft. Independent final-screen audits compare1920 cells per server. The
parameter prompt, configured title, literal child arguments and unchanged owned
configuration/child are separate checks. Five copied-data controls damage an
editor cell, cursor, completion flag, child tail or local-parameter wire; each
must be rejected. Six prior observer/key-producer variants retain exact bytes.

Enigma runs with the8086 CPU model. Synchronet performs actual ASPECT login
using a fresh source build matching the earlier accepted ASPECT executable,
with the386/XMS/UMB lab configuration. Both passive observer and BIOS keyboard
producer must record actual upper-memory segments. The first Synchronet attempt
loaded only the observer high and did not launch ASPECT. The new parent retains
about3KB more memory; moving the remaining test producer high permits the same
parent/runner to launch the script. The failed run remains excluded. This
establishes a lab memory constraint without claiming a captured DOS error number
or changing the application's memory-loan policy. Conventional-memory ASPECT
acceptance on an8086 remains open.

The application executable, installed release and live SynthModem service are
unchanged by these tests. BBS pressure during a running child, transfer/cancel/
carrier-loss and reconnect composition through this path, other viewers/video
settings, real DOS-kernel failure behavior and physical acceptance remain open.

## Redial correction and transfer composition

The [corrected-candidate receipt](validation/viewer-external-composition.json)
binds executable `2d626fb001bed53d3fb3c3a49ea1859f17e69b6ade07792c3a160043ff0a6c02`.
The previous external-viewer candidate reused private action F600, which already
belonged to browser redial. The first carrier/prompt run correctly closed the
dialog but never reconnected: the viewer dispatcher consumed the redial request.
The viewer now uses F300; browser redial retains F600. These two action bytes
are the only executable differences from the prior candidate. A linked guard
and a rejected, never-executed collision copy protect this namespace boundary.

The corrected candidate repeats all21 external/internal-fallback UI workflows,
seven710-byte native prompt comparisons and13 linked lifecycle cases. Both stock
BBS editor tests repeat on these exact bytes, with zero differences across3840
independently audited terminal cells and matching cursors. The original-free
public source export reproduces this executable; disabling the external feature
still reproduces the prior internal-viewer image exactly.

Six further actual DOS workflows run the external graphics child before
XMODEM upload/download, YMODEM upload and local cancellation followed by a
successful retry on the same connection, and ZMODEM download/escaped-byte upload.
Each child records its PSP arguments and current directory, enters mode13h and
signals its private completion marker. The passive observer cannot capture the
restored live frame until that marker arrives. Independent protocol peers check
binary payloads and continued keyboard/query service, with final UART/PIC/vector
restoration. ZMODEM escaping here describes wire-byte quoting, not cancellation.

The carrier test drops the actual DOSBox modem socket while the external
parameter prompt owns the screen. No Enter or Escape is supplied. The observer
records active/pending/cookie state around automatic closure, then witnesses a
second connection in the same parent. Fresh replies/input, two initializations,
directory accounting and owned call-log records all pass. This establishes
virtual DCD loss before child execution; loss during an external child or a
transfer remains separate work on this candidate.

Twelve earlier observer/child variants still compile byte-for-byte identically.
All results above are software evidence. The physical installation and package
selector are unchanged; SIP/audio, Boca CTS timing, analog modem and remaining
feature-parity acceptance remain open. Earlier receipts retain their original
candidate hashes and do not imply acceptance of this corrected executable.
