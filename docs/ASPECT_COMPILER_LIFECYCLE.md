# Compiler cleanup and repeated leases

The subsequent [close-error checkpoint](ASPECT_COMPILER_CLOSE.md) covers real
backup closure followed by a reported error, before lending and after restore.
Its scope is separate from the unlink and successful-chain cases below.

The next [preparation checkpoint](ASPECT_COMPILER_PREPARATION.md) verifies failed
backup creation, a partial-backup write error and a short count before lending.
It uses the same application artifacts; the lifecycle evidence below keeps its
scope.

The same experimental application artifacts now pass backup-deletion failure
and two/three real source compilations inside one interpreter process. This
checkpoint adds tests and source-replay support; it changes no application
binary and promotes no package. It extends [restore recovery](ASPECT_COMPILER_RECOVERY.md).
See the [validation record](validation/aspect-compiler-lifecycle.json).

## Safe cleanup error after restored memory

Two cases deny the kernel's backup unlink after source startup or EXECUTE.
The owned observer authenticates the kernel caller CS, parent MCB/full extent,
CLEANUP phase, valid memory and the exact compact-state filename pointer. It
passes the real backup close to DOS. Immediately before unlink, duplicating that
old child handle must fail with DOS6, independently confirming it is closed.
Only the targeted unlink returns synthetic DOS5/CF.

The source compiler has already succeeded and published exact ASX. The
interpreter must then report I/O5 and stop before executing that output. END
must restore all2000 display cells and BIOS cursor/shape before compiler scope
cleanup; its state must become valid1/phase4/busy0 with DOS error5. There is no
BIOS quarantine or retry key because parent memory is already valid.

Exactly one backup must remain, closed and intact: its size equals the complete
lent tail and its contents match the checksum captured by the real kernel.
Compiler log/staging files retire. Parent file owners/history, observed hardware
state and terminal keyboard return remain required. This preserves recovery
data instead of demanding that a denied deletion somehow succeed.

This is an injected unlink failure, not an actual read-only disk or failed
close. It does not establish automatic recovery of the orphan, nor compilation
again after this error within the same parent.

## Multiple real compiler runs in one interpreter

Two authored chains start from source and execute a second, or second and third,
source program. Every secondary ASX starts as deliberately stale output. One
ASPECT EXEC must contain exactly two/three ASPCOMP EXECs and their child exits.
Every generated ASX must match the independent host compiler exactly; neither
stale output, trailing caller instructions nor policy-error markers may reach
the peer. Native SET/FETCH confirms break policy1234 across the chain.

At each actual compiler EXEC the passive observer records child SS/DS and
CurrentPDB plus the retained kernel prefix and actual parent MCB. All captures
must have the same interpreter owner/DS and authenticated parent; MCB extent
and kernel full/keep must match the trusted link metadata. Every compiler must
run while the parent is genuinely lent: phase2, valid0, busy0 and created1.
The kernel tokens must be1,2 and optionally3, proving fresh initialization and
arena acquisition within the same parent process.

Real streams opened by callers must close with exact `BEFORE|` and `HOP|`
contents. The final GET/value/password/cursor interaction, final parent keyboard,
file-owner/history/hardware checks and absence of compiler/backing leftovers are
required. This validates successful repeated leases; it does not yet compose
compiler use with Meta/Line or another shared-arena consumer.

## Harness and source replay

The first chain attempt exposed a bootstrap fixture collision: two cases used
NEXT.ASP for different programs, and the later case overwrote the earlier
input before the DOS batch ran. Bootstrap secondary inputs now use distinct
DOS8.3 names and map back to each case's actual runtime leaf. Real DOS/host ASX
comparison remains exact. Runtime filenames are unchanged.

The current18-case test set covers two cleanup errors, two repeated chains,
two ordinary source controls, four grow/read recovery cases and eight module/
syntax refusals. The product bytes are the same as the prior41-case checkpoint;
its27 precompiled GET regressions remain evidence for those unchanged binaries.
A clean1,039-file public source export rebuilds all six exact artifacts and replays this
18-case lifecycle set. Across runs the mutable parent checksum/backup digest is
not required to be constant; every preserved backup must match its own captured
kernel checksum, and every normal END must pass actual kernel CRC/EOF checks.

No physical Boca/SPA2102/SynthModem/Enigma or Synchronet, selected-package or full
language/application acceptance follows. Failed BEGIN file operations, actual
close failure, repeated/partial restore faults, corrupt-backup repair, unexpected
child termination, reuse after a cleanup error and shared-arena composition
remain open. The installed program, DOS card, boot configuration, dialing files
and private call history are unchanged.
