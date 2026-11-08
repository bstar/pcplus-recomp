# Compiler backup preparation failures

The subsequent [close-error checkpoint](ASPECT_COMPILER_CLOSE.md) also checks
failure reported after the complete backup has actually been closed.

Six full-parent cases now verify failure before memory lending: exclusive backup
creation denied, a write error after one real block, and a reported short write,
each at source startup and EXECUTE. The same application binaries abort safely;
this checkpoint adds tests, not a new product build or deployment.

It advances the [lifecycle checkpoint](ASPECT_COMPILER_LIFECYCLE.md). Exact
artifacts and check scope are bound by the
[validation record](validation/aspect-compiler-preparation.json).

## Supplied faults

`--source-lease-begin-cases` uses the actual terminal, interpreter and compiler
bridge. Its owned observer authenticates parent PSP/MCB, caller CS inside the
loaded kernel, BACKING phase1, valid memory and the target operation arguments.
No compiler EXEC may have happened yet.

* Creation: target AX6C00 and the compact state's exact DS:SI filename; return
  synthetic DOS5/CF. No backup handle or file is created.
* Write error: pass the first4096-byte backup write through to DOS. On the
  second write, authenticate the handle,4096-byte extent and next parent-tail
  source segment; query the actual file position as4096, then return DOS5/CF.
* Short write: the same real first block and position check, but report4095 bytes
  with carry clear on the second write. That second write is synthetic; the
  fixture does not pretend actual media accepted those4095 bytes.

The short count must be treated as interpreter I/O5 even though the DOS boundary
reports no error. This tests returned-count handling, not a real full disk.

## Required outcome

Every case must record exactly one supplied fault and zero parent resize calls
from the kernel. The actual parent MCB remains at the trusted full extent;
kernel keep/full and parent identity must match the linked parent. The sampled
kernel remains valid1 while busy in BACKING, under the authenticated child owner.

The actual compiler call counter and observed ASPCOMP EXEC count must both stay
zero. Source startup publishes no ASX; EXECUTE keeps the exact deliberately
stale ASX, which must not run. The caller's real file stream closes with exact
`BEFORE|` contents and no trailing caller instructions may execute.

Preparation cleanup must retire phase/busy to0, remove any partial backup and
compiler log/staging files, preserve the exact2000 display cells and BIOS
cursor/shape, and return interpreter I/O5. There is no quarantine or retry key
because the parent was never lent. DOS error is5 for denied creation/write and0
for the short count. Parent file owners/history, observed hardware state and
ordinary terminal keyboard return remain required.

## Reproduction and scope

The current sixteen-case set includes these six failures plus two normal source
controls, two restored unlink failures, four restore/retry cases and two repeated
compilation chains. A clean1,039-file public source export rebuilds all six exact artifacts
and replays those sixteen cases. The mutable parent checksum is compared within
its own run, not required to be constant between executions.

No application bytes change from the prior41-case restore checkpoint. Its27
precompiled GET cases and the prior module/syntax refusal cases remain evidence
for those same artifacts; they are not claimed as newly rerun by this checkpoint.

These are precisely scoped synthetic DOS failures with one real partial block,
not actual permission, write-protection, full-disk or damaged-media tests. Failed
close, repeated/partial restoration faults, corrupt-backup repair, unexpected
child termination beyond the two boundaries covered by the subsequent
[termination checkpoint](ASPECT_COMPILER_TERMINATION.md), reuse after an error
and shared Meta/Line/snapshot composition remain open. Physical
Boca/SPA2102/SynthModem/Enigma and Synchronet, selected package and full language/application acceptance remain separate gates. Installed
files, boot configuration and private call history are unchanged.
