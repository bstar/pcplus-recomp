# Serviced Alt-M integration

The opt-in `--meta-editor` parent now opens the source-built Meta Keys editor
through Alt-M, the Alt-Z reference and the Setup browser. It loads the matched
PCMETA overlay and keeps the existing UART/parser/live-screen owner running.
This is application integration of the recovered components, with authored
window decoration; it does not establish original pixel equivalence or physical
Boca/Enigma acceptance. The installed RCE81708 package is unchanged.

## Ownership and publication

The resident frontend lives in FILE_CODE with code-based state, adding no
DGROUP storage. It borrows the existing 63,000-byte redisplay snapshot only in a
direct command-menu context with no frozen snapshot/search/export. The Line/Port
loader must be empty, idle and free of fatal recovery. A frozen-history context
is refused rather than overwritten. The Meta state occupies the lower arena;
verified executable code begins at offset16,384. Line/Port cannot acquire this
arena while Meta owns it. PROGRAM/EXEC and macro starts also refuse entry.

The existing foreground admission predicate gates file work, with an additional
recording-owner check. Meta must not use its own external EXEC guard to admit
its file operations: its claim deliberately makes that predicate false. Loader
steps read at most512 bytes; UART/parser service resumes between steps. Repeated
loading steps do not repaint unchanged text. Existing Bind/Load/Save remain
synchronous checked operations, not one DOS call per turn. No child runs to
perform editor IO.

Opening freezes the live540-byte definition table and current selector. An
empty selector resolves PCPLUS.KEY through the checked current/PCPLUS lookup;
an explicit selector preserves its qualified identity. Binding a disk baseline
does not replace unsaved live definitions. Load selects a new disk file; Save
uses the checked file owner. Closing offers a proposal only after the lease
ends. The frontend compares the frozen table/selector, copies the proposal out
of the arena, checks release, then publishes resident definitions and selector
without intervening DOS or foreground callbacks. A stale comparison keeps the
runtime table unchanged. Escape accepts already-completed row edits; only S
writes the KEY file. Global exit discards an unfinished draft.

Cancellation releases an unclaimed module. An ambiguous close or retained file
owner latches HELD; code/state cannot be reused and the recovery message exits
to DOS. Missing or mismatched modules return a local notice and allow a clean
return to the terminal. The original CLI selector/provenance is not rewritten.
The directory-resource-cache build is rejected until cache adoption is added.

## Verification

[The receipt](validation/meta-frontend.json) binds the exact parent, both
payloads, source inputs, disabled control and runtime reports. The disabled
parent remains byte-identical to the installed baseline. Size-profile digests
were refreshed for conditional source edits; that disabled equality verifies
unchanged compiled behavior/capacities for the original profile.

Eight real DOS8086 cases cover live editing, explicit save, load, reference and
browser access, reopen, early Escape/reopen and missing-module recovery. An
independent serial peer verifies actual emitted adopted text and ANSI replies;
a passive timer observer captures the open window over incoming live text.
Saved synthetic KEY bytes and absence of implicit writes/staging leftovers are
checked separately. These are synthetic UART tests, not physical connections.

An isolated declared-source export reproduces the executable and both overlays
exactly without original executables, private files, prior objects or ancestor
Git. It repeats save/cancel/missing Meta cases and four existing Line/Port
regressions (save, serviced input, read-only refusal, port busy).

The current parent requires483,616 retained bytes (baseline479,024), with no
stack/history/receive/frame capacity reductions. DGROUP remains65,520 bytes.
The Meta payload is21,644 code bytes plus17 relocation words, occupying the
already-retained arena. Resident _TEXT remains65,050 bytes. See the receipt for
all exact identities and capacity comparisons.

Build with the pinned Nix toolchain and a fresh output label:

```sh
./tools/dev --command python3 -c 'import json, subprocess; from pathlib import Path; flags=json.loads(Path("standalone/line_port_profile.json").read_text())+["--line-port-overlay","--meta-editor"]; subprocess.run(["python3","standalone/build_terminal.py",*flags,"--output-dir","build/meta-ui-LABEL"],check=True)'
./tools/dev --command python3 standalone/test_meta_front_dos.py --terminal build/meta-ui-LABEL/TERMINAL.EXE --output build/meta-ui-save-LABEL --case save
./tools/dev --command python3 standalone/prove_line_port_terminal_source.py --terminal build/meta-ui-LABEL/TERMINAL.EXE --output build/meta-ui-source-LABEL
```

## Remaining acceptance

Physical Enigma/Boca integration, other video geometries, frozen-history entry,
directory-resource-cache adoption and the full original KEY/HOOK/UI lifecycle
remain open. Existing component fault-injection tests cover ambiguous file and
loader closes; this frontend checkpoint does not add physical fault injection.
No deployment selector or machine configuration changes in this milestone.
