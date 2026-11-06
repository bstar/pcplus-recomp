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
