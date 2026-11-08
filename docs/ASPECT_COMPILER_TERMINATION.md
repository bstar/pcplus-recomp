# Unexpected interpreter termination during compilation

Four expected-stop tests now cover ASPECT terminating through DOS while the
compiler bridge has an active memory loan. Startup and EXECUTE each pass at two
points: immediately after the real compiler returns, and after one real 4096-byte
block has been restored to the parent. The existing application guard contains
these interruptions; no application bytes or installed package changed.

Exact artifacts, source identities and replay evidence are in the
[validation record](validation/aspect-compiler-termination.json). This extends the
[backup preparation](ASPECT_COMPILER_PREPARATION.md) and
[restore recovery](ASPECT_COMPILER_RECOVERY.md) checkpoints.

## What the fixture does

A separate owned COM observer runs in upper memory. It authenticates the actual
parent, ASPECT process, compiler EXEC/exit, kernel state and allocation extent.
At the selected DOS interrupt boundary it redirects ASPECT's interrupt return
to a resident trampoline that issues real DOS termination with exit code 55h.
DOS terminates ASPECT under its actual CurrentPDB. The fixture does not fabricate
an outer EXEC return, arbitrarily switch process identity or alter the product.

At the first point the parent is lent, valid=0, phase=2, busy=0 and its allocation
is 22868 paragraphs. At the second it has regrown to 30165 paragraphs, but remains
invalid in phase=3, busy=1. The first restore read passes through DOS; the second
is intercepted at the next parent segment with the backup position verified as
4096. This interrupts an in-progress parent call as well as leaving memory only
partially restored.

## Required outcome

The parent must display exactly:

```text
Parent memory restore incomplete. Reboot required.
```

The observer requires the notice in actual VGA memory and five timer ticks in
that state. It verifies parent process/allocation ownership, the unchanged invalid
kernel prefix, UART interrupt enable zero, and an IRQ vector outside the freed
child. Retained attributes, cursor and history-pointer values must stay unchanged.
No trailing script text may reach the wire; no further BIOS display operation
other than the exact fatal text is allowed. Observed parent DOS calls must use
retained code and issue no file reads or writes. The complete 116752-byte backup
must remain and match its own recorded CRC. The real compiler's ASX output must
match the source compiler's expected output.

After termination the observer never follows a parent history pointer, reads the
lent tail or samples the freed interpreter. It atomically publishes its report
only after observing the required state. The host then stops only its owned
DOSBox process. This is an expected fatal stop, not successful restoration or
normal application exit. Ordinary exit, cleanup and hardware-return checks are
kept separate and are expected to fail in this harness.

## Reproduction

Use the pinned toolchain with matching bridge artifacts:

```sh
./tools/dev --command python standalone/test_compiler_bridge_termination_dos.py \
  --parent build/compiler-bridge-parent-recovery-final-20261108 \
  --child build/compiler-bridge-child-256-20261108 \
  --compiler build/get-compiler-enabled-20261107 \
  --output build/compiler-bridge-termination-new
```

All four cases run by default; `--case` selects individual cases. Each output
folder must be new. The clean-source prover accepts this report through
`--termination-checks` alongside normal source controls. Expected-stop cases are
counted separately from normal DOS-return cases.

## Limits and remaining work

These are controlled interruptions at two specific DOS boundaries, not proof
for every instruction window or a complete trace of all CPU memory reads. The
retained return path is inspected and the stated boundaries are observed. The
fixture's pause keys do not substitute for positive evidence: a timeout fails.
Early experiments with delayed bootstrap keys timed out before application
launch and are excluded from acceptance.

The prior unchanged-artifact preparation, refusal and GET regressions remain
separate evidence; this checkpoint does not claim to rerun all of them. Close
failures, further repeated/partial restore faults, corrupt-backup repair, reuse
after errors, shared Meta/Line/snapshot composition and broader ASPECT behavior
remain open. Physical modem/SPA2102/SynthModem/LoC Enigma, Synchronet, selected
package acceptance and full application parity remain separate gates.
