# Compiler backup close-error handling

The subsequent [reuse checkpoint](ASPECT_COMPILER_REUSE.md) checks a second
source launch in the same connected PCPlus parent after these startup errors.

Four full-parent cases exercise a close error after the owned backup handle has
actually been closed. Source startup and EXECUTE each pass before memory lending
and after complete verified restoration. The unchanged application returns
interpreter I/O5, preserves the display and resumes ordinary terminal input.

The [validation record](validation/aspect-compiler-close.json) binds artifacts,
source hashes and test scope. This extends the
[preparation](ASPECT_COMPILER_PREPARATION.md),
[cleanup](ASPECT_COMPILER_LIFECYCLE.md) and
[unexpected termination](ASPECT_COMPILER_TERMINATION.md) checkpoints.

## Supplied close result

The owned observer authenticates the loaded kernel's caller segment, parent
MCB/identity, exact backup handle and valid memory. It intercepts only that
handle's DOS AH3E call in BACKING or CLEANUP. BACKING requires zero compiler EXEC
attempts and no parent resize. CLEANUP requires one actual successful compiler
EXEC and the restored full parent extent.

Before closing, it records the actual backup position as 116752 bytes. It then
calls the original DOS close implementation and requires success. Duplicating
the old handle must fail with DOS6, independently proving it is closed. Only
then does it return synthetic DOS5/CF to the product. This models the ambiguous
case where close reports an error despite having closed the handle. It is not a
physical flush error, disk-full simulation or still-open-handle failure.

## Required behavior

At the capture boundary the kernel still holds the old handle. At scope
retirement the kernel handle must be 65535: the application discards the ambiguous
handle rather than using or closing it again. Exactly one supplied close is
observed, with no unsafe repeated match.

Before lending, compilation must never run, the parent remains full and valid,
cleanup retires phase/busy to zero, and the backup is removed. Startup publishes
no ASX; EXECUTE preserves its exact stale ASX without executing it.

After restoration, compilation has actually succeeded and published the exact
expected ASX. It must not execute following the cleanup error. Parent memory is
valid; the complete backup remains, matching its captured full-tail CRC. State
remains in CLEANUP with busy zero and DOS error5. Compiler staging/log files are
removed. The leftover backup is deliberate evidence, not successful unlink.

Both paths must preserve every captured character/attribute cell and BIOS cursor
position/shape. There is no invalid-memory quarantine or retry key. Parent file
owners/history and ordinary keyboard return remain checked; EXECUTE must close
its caller stream with exact BEFORE| contents and skip trailing instructions.

## Reproduction and limits

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/compiler-bridge-parent-recovery-final-20261108 \
  --child-dir build/compiler-bridge-child-256-20261108 \
  --get-compiler-dir build/get-compiler-enabled-20261107 \
  --source-lease-close-cases --allocation-probe --watchdog \
  --output build/compiler-bridge-close-new
```

The output directory must be new. A clean 1041-file source export rebuilds all
six exact application artifacts and replays 20 normal-return cases: four close
errors, two source controls, six preparation errors, two unlink errors, four
restore/retry cases and two repeated compilation chains. Four unexpected-child
termination cases are replayed separately as expected fatal stops. Generic intermediate
source-case diagnostics use old delegated expectations; the final exact checks
and process exit are authoritative.

These tests cover a real close followed by a synthetic error report. They do not
prove physical media behavior, close failures leaving the handle open, reuse
after an error, repeated/partial restore faults, corrupt-backup repair or shared
Meta/Line/snapshot composition. Selected package, physical modem/SPA2102/
SynthModem/LoC Enigma and Synchronet acceptance and full feature parity remain
open. No application bytes, installed files or private call history changed.
