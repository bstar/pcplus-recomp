# Current nested PROGRAM checkpoint

The installed packed terminal `72f3ced9` and unchanged ASPECT runner `23caac93`
execute two actual nested DOS children with NOCLEAR in an8086 DOS session.
Between the children, separate scripts open all six numbered streams and recover
from a missing input file. Both children append their own six-byte marker; the
expected twelve-byte output, both script completion messages, six stream files,
recovery file, subsequent keyboard wire, unchanged staged inputs/settings and
42-byte UART/PIC/vector restoration all pass. This is evidence of basic nested
execution in the current build, beyond interpreter startup alone.

The initial checkpoint recorded two stronger failing gates in the
[checkpoint receipt](validation/current-nested-program.json):

- SAVE with a child designed to leave BIOS mode13h active produces no child log
  and neither surrounding script reaches its completion marker. The other
  six-stream and missing-file recovery scripts still complete, subsequent input
  reaches the wire, and hardware/settings checks pass. No graphics child
  execution or saved-frame restoration is established by this attempt.
- The existing register-handoff fixture, given an explicit admitted80x25
  configuration, produces only one of five required paired owner/live snapshots.
  The wire identifies that snapshot with the final OBSERVE control script;
  BANK1/BANK2 completion messages are absent. That attempt did not establish
  the full830-byte bank sequence. Its integer bank-A destinations are patched
  native operands rather than a compiler feature claim.

Missing output files establish failure of those test workflows. They do not identify
the failing opcode, allocation or guard. In particular, do not carry forward the
older state10 observation as the measured error for these new runs. The next
diagnostic must sample the actual interpreter error/last opcode and external
ownership state without replacing successful cleanup or injecting a child result.
For SAVE, distinguish parent lease admission, display capture/allocation and
native process admission before changing memory policy. Keep the two failures
separate until evidence establishes a shared cause.

The register harness retains a structured failed result when snapshots are
missing, rather than stopping at an uninformative FileNotFoundError. Display
defaults are opt-in, preserving preceding fixture behavior.

## Refreshed register and exit evidence

The [new diagnostic receipt](validation/program-exit-diagnostic.json) supersedes
the register failure above. Its old keyboard schedule omitted the restored
special-edition splash: the first shortcut dismissed the splash and the next
arrived during startup. The passive UMB capture observed only the final OBSERVE
control script launching; it did not establish a failure inside either missing
script. The harness now reads the actual parent's special-edition manifest and
explicitly dismisses that splash before starting the shortcut sequence. Parents
without the special edition retain their preceding schedule.

Seven actual8086 COM1/IRQ5 cases now pass43 paired snapshots: normal, bad token,
missing script, missing helper, divide, execution budget and user abort. Each
pair checks all830 accepted/live bytes, reset/scratch tails, owner token, epoch,
seal and prepared exchange. Same-parent subsequent scripts, the real RX/parser
reply after the last child, continued keyboard wire, expected directory updates,
private fixture bytes and UART/PIC/vector restoration pass. These are current
source-built binaries, not recreated successful snapshots. The explicit bank-A
operand patches remain a fixture boundary, not new compiler syntax support.

An optional passive INT21 observer records an attached ASPECT child's exit,
error, opcode, external-call count and retired ownership words. It makes no DOS
calls or product writes inside the hook. Twenty-eight assembled-hook cases
check path/function/child/stack filtering, bounded records and preserved
registers, stack and flags against a modeled predecessor IRET. Those are
component checks, separate from actual DOS observations.

Low-memory installation perturbs the otherwise passing NOCLEAR workflow. Those
captures are excluded from causal claims. An attempted high load in the8086
profile still loaded low and was rejected by the explicit segment check. The
separate386/XMS/UMB diagnostic profile loads the observer atCC4Bh, verified in
its own report. With that same placement, NOCLEAR passes all four script exits
with error0; SAVE fails its two nested calls at opcode9Bh/error10. Both other
scripts complete normally. Cleanup error and scope/display/program/process
ownership words are zero on all four exits. The diagnostic identifies the
PROGRAM boundary and successful retirement; it does not distinguish display
allocation from later native process admission. The next diagnostic must retain
that distinction. No physical timing or unobserved8086 error-word claim follows.

A fresh unobserved8086 NOCLEAR control also passes after the harness changes.
The upper-memory settings are opt-in emulator configuration. No application,
physical memory-manager configuration or installed payload is changed.

## Repeat

Run through the pinned Nix environment, choosing fresh output names:

```sh
./tools/dev --command python standalone/test_aspect_heap_startup_dos.py \
  --terminal build/editor-packed-ui-v3-20261106/TERMINAL.EXE \
  --runner build/aspect-packed-ui-v3-default-20261106/ASPECT.EXE \
  --nested-program --output build/nested-noclear-new
```

Add `--nested-graphics` and a different output directory for the failing SAVE
case. It uses default SAVE and its authored child changes BIOS video mode only
after successfully appending the marker. The current NOCLEAR child leaves video
mode unchanged; neither case runs a proprietary executable.

```sh
./tools/dev --command python standalone/test_register_handoff_dos.py \
  --terminal build/editor-packed-ui-v3-20261106/TERMINAL.EXE \
  --runner build/aspect-packed-ui-v3-default-20261106/ASPECT.EXE \
  --irq 5 --valid-display --label nested-register-new
```

For diagnostic exit telemetry add `--exit-watch`. To require verified upper-memory
placement use `--exit-watch --exit-watch-high --cpu 386`; an ineffective high load
is rejected. Default runs retain the8086 profile and no resident observer.

The minimal child cases use synthetic COM3/IRQ5; the existing register fixture
uses COM1/IRQ5. These are emulated serial assignments, not hardware changes.
Application binaries, installed files, private settings, boot profiles and live
SynthModem remain unchanged by this checkpoint. Physical acceptance, resident
compilation, complete PROGRAM options/fault recovery, larger geometries and full
original language/application parity remain open.
