# Guarded Ctrl-Break ownership

The source-built owner wraps the recovered INT1B/INT23 services with an explicit
parent/child lifetime. This addresses reliable child return, a prerequisite for
using external programs from the terminal. It is currently a separate diagnostic;
normal PROGRAM and ASPECT do not yet publish this owner. A separately selected
composed PROGRAM build now binds it around real child execution.

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

## Transition recovery and composed PROGRAM

`standalone/check_break_owner.py` executes the actual linked owner instructions
with modeled DOS21 services. Eighteen admission cases cover foreign SS,
DS=SS outside the linked DGROUP, IF0 and an invalid policy. They require no DOS,
BIOS or port calls and guard data outside the active stack. Recovery after each
of195 DOS-service boundaries covers open, suspend, resume and close crossed with
both policies and initial break settings. Resume cases include foreign child
vectors and a changed break flag. Two further quarantine cases retain unknown
foreground vectors and reject a foreign PSP until the caller repairs ownership.
Each abandonment discards the near stack and invokes recovery on a fresh
foreground DS=SS stack; this is an explicit checkpoint model, not an injected
hardware interrupt or a corrupt DOS-kernel simulation.

```sh
./tools/build test-native-program-break
./tools/build test-native-program-break-source
```

The opt-in `NATIVE_PROGRAM_BREAK_OWNER` controller captures a per-call baseline,
suspends before EXEC/SYSTEM, reinstalls parent handlers before WAIT, and closes
after restoring the view. It skips WAIT on a break-owner failure. Failed cleanup
retains the busy controller and recovery metadata rather than permitting reuse.
The unwind recovery branch requires the process owner to restore PSP first and
closes the break owner before UART/view recovery. It still needs actual full-VM
unwind validation; its presence is not proof of that integration.

The [composed receipt](validation/program-break-owner.json) binds eight actual
DOS routes: COM1/COM2 crossed with no, software, hardware and combined flow
control. Each route passes47771 assertions, including real child mutation of
INT1B/23 and extended checking, inherited-vector/break witnesses, both initial
break settings, WAIT/reentry, saved and unsaved views,40-column and43/50-row
views, missing programs, allocation failures, SYSTEM and a closed UART. The
independent peer verifies the exact wire and queued input. A fresh source tree
reproduces22 products including the guarded controller and source-owned children.

The ordinary controller also passes all eight routes. Its diagnostic executable
has a new hash after conditional diagnostic code shifts `CHECK` line constants;
the other30 baseline executables, including the normal terminal, keep their
hashes. Neither the normal terminal nor ASPECT gains published external commands
from this option. Application-wide parent ownership, actual VM nonlocal recovery,
asynchronous fault boundaries, physical modem/keyboard testing and all full
application gates remain open.
