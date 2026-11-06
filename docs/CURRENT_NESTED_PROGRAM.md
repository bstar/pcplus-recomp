# Current nested PROGRAM checkpoint

The installed packed terminal `72f3ced9` and unchanged ASPECT runner `23caac93`
execute two actual nested DOS children with NOCLEAR in an8086 DOS session.
Between the children, separate scripts open all six numbered streams and recover
from a missing input file. Both children append their own six-byte marker; the
expected twelve-byte output, both script completion messages, six stream files,
recovery file, subsequent keyboard wire, unchanged staged inputs/settings and
42-byte UART/PIC/vector restoration all pass. This is evidence of basic nested
execution in the current build, beyond interpreter startup alone.

Two stronger gates fail and remain explicitly recorded in the
[checkpoint receipt](validation/current-nested-program.json):

- SAVE with a child designed to leave BIOS mode13h active produces no child log
  and neither surrounding script reaches its completion marker. The other
  six-stream and missing-file recovery scripts still complete, subsequent input
  reaches the wire, and hardware/settings checks pass. No graphics child
  execution or saved-frame restoration is established by this attempt.
- The existing register-handoff fixture, given an explicit admitted80x25
  configuration, produces only one of five required paired owner/live snapshots.
  The wire identifies that snapshot with the final OBSERVE control script;
  BANK1/BANK2 completion messages are absent. The full830-byte bank sequence
  remains unaccepted. Its integer bank-A destinations remain explicitly patched
  native operands rather than a compiler feature claim.

Missing output files establish failure of these workflows. They do not identify
the failing opcode, allocation or guard. In particular, do not carry forward the
older state10 observation as the measured error for these new runs. The next
diagnostic must sample the actual interpreter error/last opcode and external
ownership state without replacing successful cleanup or injecting a child result.
For SAVE, distinguish parent lease admission, display capture/allocation and
native process admission before changing memory policy. Keep the two failures
separate until evidence establishes a shared cause.

The register harness now retains a structured failed result when snapshots are
missing, rather than stopping at an uninformative FileNotFoundError. Display
defaults are opt-in, preserving preceding fixture behavior.

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

The minimal child cases use synthetic COM3/IRQ5; the existing register fixture
uses COM1/IRQ5. These are emulated serial assignments, not hardware changes.
Application binaries, installed files, private settings, boot profiles and live
SynthModem remain unchanged by this checkpoint. Physical acceptance, resident
compilation, complete PROGRAM options/fault recovery, larger geometries and full
original language/application parity remain open.
