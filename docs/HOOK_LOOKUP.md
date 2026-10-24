# Native helper lookup and literal batch targets

The optional `--hook-lookup` terminal extends supported KEY kind2 helpers with
the original two-stage filename policy. It keeps the existing owned exchange,
trap suspension, returned-state validation and atomic publication. The preceding
plain-helper and guarded-helper terminal controls retain their executable bytes.

## Filename policy

The native resident resolver at 353Dh first opens the exact supplied name in
read mode and closes it. If that fails and `PCPLUS` exists, it prefixes that
directory, appending a backslash unless the value already ends in one.
This precedes extension search: a current-directory `HELP.EXE` does not win for
a bare `HELP` when the resolver has already selected `PCPLUS\HELP`.

The native PROGRAM service then enters the CRT search path. An explicit
extension selects that target; an extensionless name tries COM, EXE and BAT in
that order. A missing unqualified target can search uppercase `PATH`, whereas
a drive or slash in the resolved name blocks that search. Missing-file/path
errors permit continuation; ordinary access errors stop, with the native UNC
exception retained. Consecutive semicolons after a component are skipped;
an initially empty PATH component ends the native search.

The maintained route follows that ordering without requiring a C runtime or
heap allocation in its lookup code. It scans the complete bounded PSP
environment, takes the first exact uppercase variable, validates near-pointer
geometry and admits only the foreground DS=SS/IF1/DF0 context. Pending owned
cancellation prevents child execution and stops further search. Expanded names
are bounded to 259 bytes; the older raw executor retains its 127-byte limit
unless this build option is selected. KEY payload and exchange limits stay
unchanged.

The original resolver performs unchecked concatenation and reads before an
empty environment value. The maintained route rejects oversized/malformed
environments and treats empty `PCPLUS` as absent. Those bounds are deliberate
adaptations, not claims that the original routine validated these conditions.

## Batch behavior

BAT targets use the inherited `COMSPEC`; no missing-COMSPEC fallback is
invented. The selected batch suffix remains in the shell command. Relative
targets receive a dot and backslash prefix, so a valid
filename such as `CALL.BAT` cannot become the shell's CALL command.

This intentionally corrects native 65CAh, which overwrites the last four batch
filename bytes while appending arguments. The paired native cases record that
difference explicitly. Native argv serialization also adds a delimiter before
its one argument containing the generated HOOK tail; delimiter normalization
is explicit in comparisons and does not establish byte-identical DOS tails.

A separate DOS control reproduced `CALL.BAT` being parsed as CALL with `.BAT`
as its target. Prefixing the same file with a dot and backslash executed it
with all five expected arguments. The composed fixture includes a same-stem
COM decoy that exits 99 without writing any helper witness; correct execution
must reach the requested batch and source-built helper instead.

## Nested compiler memory

The lookup code increases the retained parent floor. Its initial composed
source-compilation test reported ASPECT error 8 despite a normal final DOS
exit. That run is retained as a failure. The register-enabled interpreter now
defines the CRT's near `_amblksiz` before startup with a 512-byte growth quantum.
The same parent/compiler/source combination then compiled and transmitted its
expected result. This changes allocator growth, not stack reservation, language
bounds, register layout or handler behavior. The ordinary interpreter remains
byte-identical; the register-enabled interpreter has a new identity and receives
its own handback and composed regression checks.

## Evidence and limits

[Native findings](validation/hook-lookup-native.json) bind the 105-byte genuine
resolver, its PROGRAM/CRT call path and the separately mapped original data.
REA observes those static facts. Paired CPU replay uses genuine original
instructions with declared filesystem and EXEC boundaries. The synthetic
overlay analysis image is never executed and is not a build input.

The [acceptance record](validation/hook-lookup.json) records the linked policy,
actual DOS filename/decoy workflows, helper/register/trap/cancellation regression,
nested compilation, owned BBS comparisons and empty-tree source reproduction.
It keeps failed harness/memory attempts distinct from final acceptance.

Final acceptance includes 28 paired policy cases (two intentional batch
differences), fourteen context/bounds/cancellation cases, sixteen actual DOS
target workflows, 42 helper regressions, four helper trap-owner workflows,
fourteen register recovery workflows with 86 raw snapshots, ten trap cases,
fourteen cancellation cases, eight nested compiler cases and two BBS sessions.
Eleven products reproduce from 704 sources. The
[twelve negative evidence checks](validation/hook-lookup-counterexamples.json) reject
damaged targets, decoys, keys, modes, registers, bytecode, interpreter image and
observer data, plus a forged native result with its producer pass flag intact.

These are supported helper semantics, not full native-field or application
parity. Physical DOS/modem acceptance, arbitrary network/filesystem errors,
device-critical faults under this build, unbounded source sizes and the known
stock ENiGMA immediate-forwarding problem remain open. ENiGMA BBS comparisons
retain explicit buffering and observed source-login tests use a 386 profile
with verified upper-memory placement of their passive observer. The card has
not been remounted or deployed during this source checkpoint.

## Reproduction

Use the pinned Nix toolchain. The explicit build is:

```sh
./tools/build hook-lookup
./tools/build test-hook-lookup
```

The product directory is
`build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps`.
Use the newly built `build/aspect-register-parent/ASPECT.EXE` and the existing
source-built compiler alongside it.

`standalone/check_hook_lookup.py` checks linked policy and bounds; `--original`
additionally requires the ignored SHA-pinned native originals and PROGRAM
comparison fixture. Every run needs a new `--output` under `build`.
`standalone/test_hook_apply_dos.py --lookup-case` selects the actual DOS filename
fixtures; its normal mode still checks returned settings/registers and UART
recovery. `standalone/prove_hook_lookup_source.py` repeats the original-free
product reproduction in a new `--output` directory.
