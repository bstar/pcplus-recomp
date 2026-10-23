# ASPECT KEY actions

The optional `--aspect-keys` terminal build supports kind0 ASPECT records in the
explicit global `/T:FILE.KEY` import. Alt-1 through Alt-9 select records0..8;
Alt-0 selects record9. An empty ASPECT definition is a no-op. A nonempty record
stages its script filename and queues the existing direct Script handoff.
TEXT and PROGRAM retain their preceding routes; HOOK remains unsupported.

Build with the pinned Nix toolchain:

```sh
./tools/build aspect-keys
./tools/build test-aspect-keys
./tools/build test-aspect-keys-source
```

The terminal is `build/terminal-aspect-keys/TERMINAL.EXE`. Install the matching
`build/aspect-help-resource-parent/ASPECT.EXE` beside it. Install the maintained
`build/aspect-compiler-dos/ASPCOMP.EXE` beside ASPECT to compile explicit ASP or
missing-ASX source siblings. The optional `LOCHELP.HLP` resource is read from the
DOS working directory when a PROGRAM notice opens help. The ordinary/default
terminal and the preceding capability16 terminal retain their executable bytes.

For example, a synthetic KEY record with kind0 and `LOGIN.ASX` runs that script
when its Alt-digit is pressed. The field has52 bytes, including its terminator;
the staging routine scans at most52 and copies at most51 filename bytes plus
NUL. It does not apply TEXT caret/pause expansion or invoke COMSPEC. Filename
validation, namespace resolution, source compilation and errors use the existing
Script/ASPECT services. Script arguments, directory KEY/META import and HOOK
exchange records are outside this integration.

## Scheduling and memory

The transport keyboard callback only stages a filename and queues kind4 in the
existing PROGRAM scheduler. Actual EXEC runs at its foreground safe point.
Shared macro/program/monitor/controller/break ownership checks run before the
copy. Unterminated text leaves the shared filename unchanged. Normal pending
keys, cancellation, transmit drain, flow ownership, UART handoff and returned
raw bytes follow the existing Script owner. Escape, exit, hangup and redial can
cancel a pending action before EXEC. An already running child retains the
existing cancellation and cleanup contract.

The staging routine is in CONFIG_CODE and reuses the existing64-byte menu script
buffer. There is no added DGROUP storage. The optional near branch adds30 bytes:
_TEXT is65,460 bytes, leaving76. DGROUP remains65,520 bytes including the8KiB
stack, leaving16. CONFIG_CODE remains below64KiB. These are limited budgets;
additional features require careful bank placement.

Missing helper and child/script errors return through the serviced Script
prompt, then restore the parent. An empty definition does not launch a child.
The existing unsupported-action policy still handles HOOK and invalid KEY kinds;
this change does not replace that application error UI. It does not let a KEY
action nest another ASPECT interpreter inside an active child.

## Original evidence and acceptance boundary

The recovered native dispatcher in `reconstruction/meta_keys/invoke.asm` calls
resident4B1F with0,text for kind0, after checking the active-script word.
Previously retained REA/Ghidra evidence establishes its loader path:

| Evidence | Observation |
| --- | --- |
| `ev_f1ccb47215fbb7289459555f728d0389ee603464ffc83a18771449c48e131ab8` | Resident4B1F owns the interpreter loop and calls the overlay loader through C21F. |
| `ev_8ff21649bd3d277b6ca23c7d15e7906e380bcad2d87b3318ecb71c9c666c3e01` | Overlay2 loader initializes script state and delegates the supplied text. |
| `ev_d7b6d1b1b0cda4408eed7653c42dd6ec108171417055a031f680b4d6f171cee5` | Overlay2 entry rejects null/empty input without launching, inspects a filename extension, resolves/compiles and loads a script. |

These are static observations from the SHA-pinned2.01 target, not original
runtime comparisons. Saved complete records remain under ignored analysis
storage. The maintained direct child/safe-point architecture is an explicit
replacement for native in-process interpreter/overlay scheduling.

The new linked suite executes40 inputs through the actual terminal code with
DOS/BIOS/UART boundaries modeled. It covers all ten BIOS Alt-digit events,
empty/unterminated text, owner refusals, filename bounds, pending cancellation,
helper/child/memory errors and raw binary handback under three translation
policies. No product callback is replaced in that model.

Seven actual DOS workflows exercise COM1/2, serial WAITFOR and unread suffix
rendering, missing helper, empty definition, repeated invocation, invalid bytecode,
and real DOS ASP compilation followed by execution. Raw42-byte hardware samples
match before/after; ordinary typing resumes. The [independent receipt](validation/meta-aspect.json) decodes these raw inputs,
wire and hardware samples and preserves their source/product custody. Four
current loopback ENiGMA/Synchronet record/replay sessions compile the recording
in DOS, invoke the derived script through Alt-1, run missing/successful DOS
children and resume manual navigation. The BBS audit binds the actual imported
kind0 record and `/T` command to the recorded keyboard schedule. This accepts
selected global KEY ASPECT integration. Physical
UART/modem, other DOS kernels, arbitrary combined failures and full F01–F16
application acceptance remain open.

## Optional directory bindings

The separate [directory-key terminal](DIRECTORY_KEY_BINDINGS.md) now accepts
selected-entry KEY action and META KBD resources during startup. Explicit `/T`
and `/K` independently override them. Baseline unsupported-directory statements
above describe the unchanged earlier variants. Native post-connect switching,
KEY auto-creation and full application requirements remain open.
