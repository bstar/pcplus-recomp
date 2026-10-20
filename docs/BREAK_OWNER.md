# Guarded Ctrl-Break ownership

The source-built owner wraps the recovered INT1B/INT23 services with an explicit
parent/child lifetime. This addresses reliable child return, a prerequisite for
using external programs from the terminal. It is currently a separate diagnostic;
normal PROGRAM and ASPECT do not yet publish this owner.

`native_break_open(0/1)` captures the caller's vectors, extended-break setting,
PSP and the native routines' nine saved bytes. It rejects reentry. Policy1
disables extended checking while the parent owns its handlers; policy0 preserves
the initial setting. Both policies install the recovered IRET handler.

Suspend restores the caller's baseline before child execution. Resume first
restores the captured baseline, then reinstalls the parent handlers. A child's
vector addresses therefore cannot become the parent's saved baseline. Close
restores the exact original vectors and break setting, including when the
native routine's conditional break restore alone would leave a child's setting.
This exact snapshot restoration is an intentional maintained behavior change.

Entry requires foreground DS=SS=the linked DGROUP and IF1. A mismatched PSP,
corrupted native saved pool or unexpected foreground vector quarantines the
owner. Recovery retains the original snapshot and admits only the known parent
handler or baseline vectors outside a declared child window. It never invokes
unknown vectors. Code/data must remain resident until the owner is CLOSED;
quarantine is not permission to release them.

Run through the pinned Nix toolchain:

```sh
./tools/build test-break-owner
./tools/build test-break-owner-source
```

The [validation receipt](validation/break-owner.json) records132 checks under
DOSBox-X's8086 core. Four real DOS EXEC children cross initial break0/1 with
policy0/1. Each child writes the actual inherited vectors/break setting to a
witness, replaces vectors, changes break checking and exits42 after changing DS.
The parent verifies inherited baseline, child mutations, correct resume, exact
close and restoration of the native saved bytes. Additional cases cover reentry,
IF0, invalid policy, unknown-vector quarantine/repaired recovery, saved-pool
corruption and closing while suspended.

The PSP mismatch case temporarily uses an allocated DOS block's segment as a
controlled foreign-PSP token. Only the owner's PSP query runs in that interval;
the diagnostic immediately restores the real PSP before cleanup. This models
admission rejection, not a genuine second-process callback.

The runner requires both successful ERRORLEVEL and the exact diagnostic summary,
uses a fresh label directory, and checks source hashes before and after execution.
A fresh tree containing only43 declared source/provenance files reproduces both
BRKOWN.EXE and BRKCHLD.COM without originals, existing objects or REA databases.
All31 previous DOS products retain their hashes.

Foreign-DS/SS instruction-level checks, interruption during individual install
steps, integration with the foreground unwind/PSP owners, full PROGRAM execution,
BBS sessions and physical modem/keyboard operation remain unproven by this test.
No full application gate closes here.
