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

## Integration remaining

The parent must import the configured field without altering opaque PRM bytes,
select the external route only when configured, reproduce the48-character
parameter prompt, and release the modal owner before the existing guarded
PROGRAM/COMSPEC handoff. A transient stack command can avoid expanding the
nearly full near-data bank. Cancellation must never queue a child. Reconnect,
file owners, capture/printing, traps, UART and display restoration need checks
through this composed path, including missing interpreter/program and allocation
failures. The maintained parent's live external-viewer route is not enabled by
this component checkpoint. Physical acceptance and all remaining feature-parity
gates remain separate.
