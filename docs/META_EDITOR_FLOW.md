# Composed serviced Meta Keys editor

The separate Meta components now form one working editor controller: overview,
kind/text revision, filename input, current/PCPLUS picker search, checked load,
missing-file default creation, save, cancellation and a close proposal. A DOS/VGA
probe exercises actual loading, editing and saving with exact screen/cursor
restoration. The interactive terminal is not yet linked to this controller.

## Controller and admission boundary

`meta_editor.c/.h` uses 12,870 bytes of inspect-only caller-owned far storage.
It contains the dialog, filename prompt, picker/table, scan continuation, file
owner, loaded/expected records and frozen paths. Its code/labels add no DGROUP
data. Open, keyboard input, drawing and proposal queries are memory-only; no
blocking keyboard, BIOS or UART access is performed by the controller.

The caller grants each file step explicitly. A refused grant leaves queued file
work pending; Escape can cancel it before execution. Directory scan steps retain
their one-find-call/64-sort-comparison bounds. Owner Bind/Load/Save remain
synchronous checked operations, not a claim of one DOS call per turn or measured
connected-terminal latency. The terminal must admit these operations through its
existing file/EXEC handoff and service UART/parser/replies between turns.
Internal admission must allow work by this owner while its lease is active;
using its blocked external-EXEC predicate to gate its own steps would deadlock.

Open stages the supplied active records without publishing anything to runtime.
Initial disk binding preserves unsaved live edits. Explicit Load replaces staged
records only after checked IO. Missing-file creation uses current/PCPLUS lookup:
when a bare name is absent locally and PCPLUS is selected, the new file is created
there, not silently redirected to the current directory. Corrupt current files
fail without fallback or record/name replacement.

Empty filename Enter starts current-directory enumeration. Only an empty list
tries the PCPLUS pattern. A picked stem binds to the frozen selected directory.
Escape cancels filename input, planning, scanning, picker selection and queued
file work without a false file-error notice. A dedicated `meta_dialog_cancel`
operation clears the deferred request while preserving definitions/name. Existing
native dialog behavior is unchanged.

Close retains accepted in-memory edits, without implicit saving. It first closes
the file lease and only then exposes a proposal. The expected initial raw table
and canonical path can be checked against runtime with `meta_editor_matches`.
The caller must perform the remaining admitted live-table commit and namespace/
configuration checks before restoring/unloading the modal module. The controller
does not change terminal globals, PRM selection provenance or action execution.

Any owner quarantine, failed lease close or inconsistent post-IO completion is
fatal: no normal close/proposal/restart is offered. Owner callback/state/code
must remain alive while the application returns to DOS. Forced stop also respects
this requirement. The component cannot make an unsafe module unload safe.

## Rendering and the actual VGA probe

Draw composes the main dialog, eight-cell name prompt, picker and notices into a
supplied 80x25 frame. Cursor/shape queries follow the active field; pending/fatal
operations hide the cursor. Decoration is authored, not native VGA equivalence.
Frame ownership and restoration remain the caller's responsibility.

The owned `METAVGA.EXE` test host saves its screen/cursor/shape, polls BIOS keys,
steps the controller, paints changed cells and restores the entire prior frame
before returning. A passive timer observer independently captures overview,
blank/typed filename, selected name, kind/text revision and the changed definition.
Real checked Save produces the exact edited NEXT.KEY and matching proposal while
TEST.KEY stays unchanged. Separate BEFORE/AFTER samples match all 4,000 video bytes
and the BIOS cursor/shape. This is a probe, not a replacement PCPlus launcher.
Its bounded watchdog reports test failure rather than waiting indefinitely.

## Verification

```sh
./tools/dev --command python standalone/build_meta_editor_flow.py \
  --output build/NEW-meta-flow
./tools/dev --command python standalone/test_meta_editor_vga.py \
  --build build/NEW-meta-flow --output build/NEW-meta-vga
```

The ordinary DOS8086 workflow passes 3,069 assertions, including frame bounds,
file admission refusal, cancellation, load/create/save, opaque tails, corrupt-load
preservation, current/fallback/no-file pickers, stale expected-table/path checks,
close without saving and proposal publication after lease release. A separate
fatal session passes 981 assertions, refusing further steps/stop/input/proposal
after an injected close uncertainty. Assertions include individual frame cells
and tail bytes, not thousands of independent user scenarios.

Nine actual DOS/VGA checks pass. The existing frozen original-reference dialog
gate still passes 328 cases, 3,341 states/views and eight guards with the new
cancel API. An isolated 53-file source export rebuilds all three executables
exactly and repeats the workflow, actual VGA and native-reference gates without
original executables, private data, prior objects or ancestor Git. The outer
pinned Nix environment supplies tools. See the
[receipt](validation/meta-editor-flow.json).

The workflow driver is `meta_editor_flow_driver.c`; the earlier recovered-component
`meta_editor_driver.c` remains unchanged.

## Terminal integration still required

The current parent has no spare resident-code capacity and only 16 DGROUP bytes.
The controller must be placed in a matched transient module, with explicit
resident service adapters and state/arena lifetime. The modal/menu and direct
Alt-M entry, global file/EXEC readiness, queued-action and live-table adoption,
normal/fatal exit paths, other views/geometries/colors and native pixel comparison
remain open. Module memory/capacity, connected traffic/flow, Enigma/Synchronet,
application rendering and physical acceptance must pass before deployment.
No parent/package, remote service or installed RCE81708 file changed; no complete
feature-parity gate is closed by this component checkpoint.
