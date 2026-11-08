# Full-parent compiler refusal checkpoint

The next [restore-recovery checkpoint](ASPECT_COMPILER_RECOVERY.md) exercises
full-parent grow/read failure, BIOS quarantine and retry, and fixes display
restoration after repair. The earlier refusal results below retain their scope.

The capability23 bridge now returns the correct interpreter I/O result when its
module cannot load. Eight full-parent failure cases cover startup and source
EXECUTE with a missing, corrupt or truncated kernel, and a source syntax error.
The normal source controls still run and return through GET. This experiment is
not the selected connection package and has not been installed on the DOS PC.

This advances the [live compiler bridge](ASPECT_COMPILER_BRIDGE.md). The
[validation record](validation/aspect-compiler-refusals.json) binds the current
artifacts, supplied failures and check results.

## Correct result namespace

`src/aspect/runtime.h` defines I/O as5 and stack error as9. The original bridge
used `E009` for safely intact/restored I/O failures, mixing up that namespace.
The refusal tests and the compiler's actual syntax-error path exposed the
mismatch. The bridge now uses a named `ASPECT_RUN_IO` constant and returns
`E000 | ASPECT_RUN_IO` at both safe I/O retirement sites. State remains10.

The rebuilt parent differs from the previous accepted normal-path parent by
exactly two bytes, both9→5 immediates, at file offsets258258 and258331. Size,
relocations and memory layout are unchanged. ASPECT, ASPCOMP and all three
module files are byte-identical. The END safe-error mapping is corrected in
source too; these cases do not inject a restored END cleanup failure.

## Failure checks

Each failure runs the actual full terminal, interpreter, UART, renderer and DOS
compiler path with an owned modem peer. No proprietary original is an input.
The tests deliberately supply the fault before execution and keep the original
parent/module production inputs intact.

Missing/corrupt/truncated modules must produce no compiler EXEC or interpreter
compiler-call count, result5, no new ASX and no backup/log/staging leaks. The
changed module fixture must remain unchanged by the application. The runtime
must resume the parent keyboard, preserve parent file owners/history and restore
the observed interrupt/serial hardware state.

The syntax-error case supplies an invalid command to the real DOS compiler.
One nested compiler EXEC must return1 with no DOS execution error. The interpreter
must return5 after restoring memory; a startup target stays absent and the
EXECUTE target retains the exact deliberately stale ASX. Neither stale target
nor trailing caller instructions may run. A real open stream in the EXECUTE
caller must close with its exact `BEFORE|` contents. Compiler scratch, log and
parent backing files must all retire.

The parent also passes the two successful source controls and all27 precompiled
GET regressions. `standalone/prove_compiler_bridge_source.py` now accepts the
failure family and replays the two normal controls plus all eight failures from
a clean1,037-file public source export, comparing exact binaries, serial bytes, probes,
observer code and test results. The normal and failure checks share the same
parent/child/compiler identities.

## Limits and next work

Startup failures restore the prior terminal view. The passive child exit probe
establishes the exact error; the retained-screen sample does not prove the
message was visible before acknowledgment. Startup prompt visibility remains
unverified and is not silently treated as a passing UI claim.

These tests prove pre-lend module refusal and a normally restored compiler
syntax failure. They do not prove the BIOS quarantine path, invalid-memory
containment, recovery after disk read/grow failure, a restored cleanup error,
unexpected child exit, or repair/retry and arena reuse within one parent.
Dedicated full-parent injections for those paths remain next. Earlier kernel
component fault tests do not substitute for that integration evidence.

The full language/application, selected-package regressions and physical
Boca/SPA2102/SynthModem/LoSs oF CoNtRoL Enigma and Synchronet gates remain open.
No workstation networking, remote DOS files, boot profile, private dialing data
or call history is changed by this checkpoint.
