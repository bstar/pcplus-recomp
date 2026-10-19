# Directory-bound ASPECT scripts

The source-built terminal can launch a selected directory entry's compiled
script after a successful connection. This checkpoint does **not** complete
automatic modern BBS login: a real Synchronet test authenticates but exposes a
missing terminal-rendering service during ASPECT WAITFOR. All full-application
gates remain open.

## Selection and launch

The directory SCRIPT field accepts a bounded DOS name with an optional drive
and path. Each component must satisfy the maintained DOS 8.3 policy; device
aliases, traversal, shell syntax and unterminated fields are rejected before
UART ownership changes. A bare final name gets `.ASX`. An explicit extension
must be `.ASX`. KEY and META bindings remain unsupported by this decoder.

On connection, the terminal queues the existing foreground Script owner once.
Missing helpers, missing scripts and unsupported bytecode return through that
owner's error path. A failed connection does not launch the script. Existing
foreground/modal owners prevent nesting. Returning from a script does not
redial or rerun it. ASPECT.EXE is resolved through the existing resource policy;
the script file is tried in the current directory, then the PCPLUS directory.
An existing malformed file is reported rather than replaced by another search
result. There is no PATH search.

Native evidence establishes post-connect selection, uppercase filename
resolution, current-directory/PCPLUS lookup and compiled-ASX preference. The
original also has an ASP compilation path. This checkpoint requires a compiled
ASX; it does not silently substitute a host compiler for that DOS application
behavior. Build authored scripts with the maintained compiler in Nix.

## Retained raw input and selected record

ASIO version 3 is a maintained **40-byte** parent/child interface. Versions 1
and 2 retain their 28-byte format. Offsets 0–27 retain the existing base layout;
on v3 entry, count/status at 16/18 mean initial circular FIFO count/read index.
The appended words are:

| Offset | Meaning |
| --- | --- |
| 28 | Selected entry, zero or 1–200 |
| 30 | Parent-DS offset of the retained 114-byte record; zero without selection |
| 32 | Optional pending accounting year; zero means no projection |
| 34 | Month |
| 36 | Day |
| 38 | Pending connection-count delta |

The v3 guard additionally binds the initial FIFO fields, selected record and
all four accounting words. The child checks parent ownership, extents,
non-aliasing, bounded record strings and a valid Gregorian date before UART
I/O. A zero year requires the other three projection words to be zero. The
projection requires a selected entry. A nonzero year with delta zero still
updates the date: the 16-bit pending counter can wrap.

The child copies the effective input table, record and circular raw FIFO before
enabling its IRQ. It applies the existing maintained accounting patch to its
private record. This matches native ordering: original PCPlus updates date and
count before arming the script. Parent context and the expected disk-write
baseline remain unchanged, preserving the deferred save's comparison guard and
the maintained Y2K correction. `$D_LDATE` consequently sees the current call.

Raw preload precedes live IRQ input. Effective translation runs at dequeue,
exactly once. Unread return bytes remain raw for the parent's real mapper.
The parent verifies publication and its original policy before adopting the
returned FIFO. Password transmission requires an explicit script expression;
there is no automatic credential output. See [selected expressions](ASPECT_DIRECTORY.md)
for the eight string getters, entry expression and unsupported baud binding.

## Verification and the remaining rendering gap

The source-only checks exercise native getters, compiler outcomes, diagnostic
runtime, bounded child admission, raw preload, private accounting projection,
actual DOS child execution, real parent mapping and directory-triggered launch.
The integration record binds these reports to exact source and executable hashes.
It also binds a fresh build reproducing 91 outputs without original executables
or REA databases. These are component and integration results, not whole-program
compatibility evidence.

The strict owned Synchronet workflow sends each scripted credential once and
authenticates, but does not reach the expected full-screen editor. ASPECT consumes
the initial ANSI queries without invoking the renderer or transmitting replies;
Synchronet therefore selects its line editor. The test remains failed. The
earlier manual-launch workflow, where the terminal negotiates before script
launch, passes the editor audit. Synthetic prompt/suffix tests do not cover this
initial negotiation and cannot supersede the failed real-server result.

Native WAITFOR invokes the full display engine. Its mapped lead byte reaches
the renderer; ESC continuation bytes are read raw by the parser and do not
reach the matcher. DA/DSR replies are sent synchronously. COMGETC normally
suppresses display. The required fix is a shared renderer with session-state
continuity, ordered child UART reads/replies and correct screen adoption after
return. Fixed query replies or server configuration changes would not reproduce
this behavior. WHEN dispatch, complete script scheduling, unsupported expression
and opcode families, original compile-on-demand and hardware testing also remain.

## Reproduction

```sh
./tools/dev --command python3 standalone/build_terminal.py
./tools/dev --command python3 standalone/build_aspect_runner.py
./tools/dev --command python3 standalone/check_script_launch_live.py
./tools/dev --command python3 standalone/test_aspect_script_directory_dos.py
./tools/dev --command python3 standalone/prove_source_build.py
# Requires the existing owned Synchronet lab; choose a fresh label.
./tools/dev --command python3 lab/bbs/directory_script_dos_probe.py --label directory-check-01
```

The BBS command currently reports the rendering failure described above. Retain
its output and wire evidence. Do not weaken its editor assertions to mark this
checkpoint as a complete login workflow.
