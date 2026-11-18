# Handoff: PCPlus screen-command work stopped in this session

Snapshot: 2026-11-18 03:49 UTC (November17 local time).
Repository: `/home/bstar/projects/pcplus-recomp`.
HEAD at inspection: `72e533a`; branch `main`, ten commits ahead of origin.

Resume note: the user subsequently confirmed that the apparent other worker was
this same resumed session and authorized continuing. The persistent goal is
active again. The stop status and build details below are a historical snapshot;
the current work includes the overlaid scalar gateway and complete DOS8086
screen-family execution. See [the current screen-command record](ASPECT_SCREEN_COMMANDS.md).

## Stop and coordination status

The user said another session is already working on PCPlus and explicitly told
this session to stop. I interrupted my active worker and set this session's
persistent goal to **paused**. This document is a handoff, not a resumption.
I am leaving the uncommitted changes intact for the other session to review.
I did not identify the other session before doing this work.

The older persistent objective was: “resume decompiling and recompiling pcplus,
I'm sure the plan is not complete.” It automatically continued after the
separate BBS-repository task. The private BBS repository is a different project:
`/home/bstar/projects/black-flag-bbs`, remote `bstar/lossofcontrolbbs`.

Do not assume every current worktree edit belongs to this session: another
session may overlap or continue changing files. The file list below describes
what I intentionally worked on. I did not edit these pre-existing changes:

- `docs/MACHINE_BOOT_PROFILES.md`
- `tools/machine-profiles/compile.py`

No installed selector, physical DOS installation, private configuration/history,
live SynthModem, ATA or SIP/audio settings were updated. No cap27 package was
published, deployed or committed. Earlier cap26 work was committed locally.

## Last committed checkpoint

Earlier in this thread I completed the opt-in FROMDDIR/MONO work and its
combined capability26 software qualification:

- `d974c9e`: native FROMDDIR/MONO, compiler/runtime bindings and origin lifecycle.
- `2aec3a7`: capability26 complete-package cold-replay gate.
- `72e533a`: qualification records and next-family plan.

The committed package source base is `2aec3a7`. Its17 files and ZIP reproduced
from1115 actual committed Git blobs, with51 package controls, eight packaged
DOS workflows/50 checks, Enigma18 and Synchronet22 checks. The temporary BBS
servers used for that checkpoint were stopped. This is a software checkpoint;
hardware and full original application parity remain open.

Read these existing documents for the committed state:

- [ASPECT_STATE_CONNECTION.md](ASPECT_STATE_CONNECTION.md)
- [ASPECT_STATE_BUILTINS.md](ASPECT_STATE_BUILTINS.md)
- [ASPECT_RECOVERY_NEXT.md](ASPECT_RECOVERY_NEXT.md)
- [FEATURES.md](FEATURES.md), the full F01–F16 checklist; Host stays last.

The prepared cap26 ZIP is
`build/state-committed-archive-v2-20261118/PCPLUSSE.ZIP`. Do not confuse it with
the unfinished cap27 prototypes below.

## Uncommitted work: native screen family, capability27

I moved on to seven original commands, through actual native handlers and
parent display operations rather than ANSI-string substitutes:

| Command | Opcode | Original handler | Operands |
| --- | --- | --- | --- |
| BOX | 0C | overlay17:E6D1 | row1,col1,row2,col2,attribute |
| CLEAR | 12 | overlay17:E700 | optional attribute, with explicit presence byte |
| HOME | 57 | resident1F56 | none |
| LOCATE | 6A | overlay17:E7E5 | row,column |
| SCROLL | 9C | overlay17:E847 | count,row1,col1,row2,col2,attribute |
| GETVATTR | 52 | overlay18:EA23 | row,column,writable integer destination |
| PUTVATTR | 8C | overlay18:EA3C | row,column,attribute |

All inputs are atomic integer operands under the original grammar, not arbitrary
arithmetic expressions. The original hex-width/sign and comma-spacing rules
have dedicated oracle cases. GETVATTR's third operand is a destination.

An important dependency was added coherently: writable `N0`–`N9` frontend
support, including expressions/assignments/parameters and exact separation from
ordinary identifiers such as `N01`. The VM already had that numeric bank.

### Runtime alias bug fixed

In `src/aspect/runtime_bridge.asm`, `aspect_operand_integer_bank_a` previously
preceded the conditional `aspect_emulation_selector` word, whereas
`_runtime_integer_a` followed it. Under EMULATE that made native N0 access the
selector, shifting the bank. I moved the native bank label to the same location
as `_runtime_integer_a`, after the selector. The storage size is unchanged.
This is an intentional correctness fix, including in EMULATE profiles without
screen commands; do not claim all old runtime binaries must remain identical.

## Files intentionally edited or created

### Compiler

- `src/aspect/compiler.py`
- `src/aspect/compiler_commands.c`
- `src/aspect/compiler_emit.c`
- `src/aspect/compiler_expr.c`
- `src/aspect/compiler_unit.c`
- `standalone/check_aspect_screen_compiler.py`
- `standalone/fixtures/aspect_screen_compiler_vectors.json`
- `standalone/fixtures/aspect_numeric_register_compiler_vectors.json`

### Native handlers and child bank

- `src/aspect/screen_commands.asm`
- `reconstruction/aspect_screen_commands/provenance.json`
- `src/aspect/screen_bank.asm`
- `src/aspect/screen_runtime.c`, `screen_runtime.h`
- `src/aspect/runtime_bridge.asm`
- `src/aspect/resident_render.c`, `resident_render.h`
- `standalone/build_aspect_screen.py`
- `standalone/build_aspect_runner.py`, `build_aspect_process.py`
- `standalone/build_aspect_standard_overlay.py`

### Parent display, RPC and admission

- `src/terminal/script_screen_platform.asm`
- `src/terminal/script_screen_rpc.asm`
- `src/terminal/aspect_renderer.asm`
- `src/aspect/renderer_policy.c`
- `standalone/build_script_screen_platform.py`
- `standalone/build_terminal.py`
- `standalone/terminal_size_profile.json`
- `src/chat/echo_size.json`

The last two JSON edits refresh the reviewed renderer-policy source hash;
optimization choices were not changed. Both profiles contain an entry for that
source: the Chat profile overrides the general one when enabled.

### Tests

- `standalone/check_aspect_screen_native.py`
- `standalone/check_script_screen_rpc.py`
- `standalone/check_aspect_screen_parent.py`
- `standalone/aspect_screen_client_driver.c`
- `standalone/test_aspect_screen_client_dos.py`
- `standalone/test_aspect_screen_policy_dos.py`
- `standalone/test_aspect_screen_dos.py`

Most of these new files are still untracked. Nothing from this cap27 stage has
been staged or committed by me.

## Architecture currently implemented

### Feature selection and code placement

- Parent builder: `--aspect-screen-commands`, requiring the full state-builtin
  capability26 profile. C and assembly publish capability27.
- Child process/runner API: `aspect_screen_commands=True`; attached builds
  define `ASPECT_SCREEN_PARENT`, requiring `ASPECT_STATE_BUILTINS_PARENT`.
- Native handlers and the C screen wire adapter live in `SCRIPT_SCREEN_CODE`.
- The private-owner-check gateway in `resident_render.c` is a FAR function in
  **`SCREEN_CLIENT_CODE`**, always resident. It still accesses the real private
  attached/owner/wait fields from that translation unit.
- `screen_bank.asm` has ROOT_ONLY/OVERLAY_ONLY variants. Seven command entry
  gates, operand/error/wire adapters and12 data bytes stay resident.
- New `--screen` in the standard-overlay builder shares the existing overlay
  area with GET/Help/Notice/PROGRAM. The screen section is931 bytes; it is
  section5 in the full `--notice --program --screen` profile.

Native callee-cleanup bridges matter: bounded integer is RET4, destination
store RET2, and other readers have their own register/stack ABI. When a bank
near wrapper calls a resident FAR reader, original arguments start at BP+8
after the resident PUSH BP. Do not replace these with generic cdecl thunks.

Errors must enter resident `_TEXT` before native `session_longjmp`, which
restores SP/IP but not CS. The failure adapter sets the typed runtime error and
jumps to the ordinary `aspect_abort` external/GET/alarm unwind chain.

### Scalar protocol

The outer existing renderer performs child PSP/DS/client/MCB authentication.
The new module keeps transaction state in parent CS, adding no parent DGROUP.

| Operation | Payload / effect |
| --- | --- |
| 32 | Metadata index0..5, with0100 selecting high byte; returns F000\|byte |
| 33 | Begin primitive0..7 |
| 34 | Append one full WORD argument, up to4 |
| 35 | Commit with payload0; enforce exact arity and live bounds |
| 36 | Cancel with payload0; idempotent |

Metadata: normal attribute, configured-wide binding, physical row count,
physical last row, physical last column, physical stride. The current wide
binding derives from the admitted canonical132-column layout.

Primitive order: scroll rectangle, box frame, reset normal/current attribute,
clear/home, locate, read attribute byte, write attribute byte, HOME.
Arity is4/3/1/0/2/1/2/0. Commit retires staging before invoking helpers.
GETVATTR receives one zero-extended attribute byte, not a full cell WORD.

Other authenticated renderer operations retire screen staging. END, revoke,
prepare and the typed-abort path retire it. An early outer PROGRAM/compiler
refusal can retain an existing stage until cancellation/END/revoke; the linked
checker records this distinction. Bad outer authentication must not mutate
another valid stage. Broker-level admission errors retire the transaction.

### Display semantics and important limits

- BOX uses exact BIOS6EDC clear and exact6FEC frame dependencies. The old
  `script_window.asm:local_window_draw` paints fixed Alt-Z help and is not BOX.
- The verified original default border is `C9 CD BB BA BC CD C8 BA`, selected
  by original DS3352→1B7A. The parent passes eight stack-local glyph bytes to
  native frame code, preserving DS=SS and avoiding scarce near DATA. Runtime
  frame selection/complete PRM mapping is still unimplemented.
- GET/PUTVATTR target physical video attributes, including status row24, and
  preserve the character byte. They are not logical viewport edits.
- LOCATE uses the real cursor kernel and may pan a132-column viewport. A
  captured local scope sets ASPECT/parser ownership and restores it without
  feeding parser bytes or deliberately adding history/log output.
- Native LOCATE accepts the physical last row. Under the new feature only,
  renderer policy now admits coherent physical cursor positions outside the
  logical scroll window while retaining logical origin/scroll bounds and
 4096-cell capacity checks. GET's narrower adopter is not reused.
- Native zero/reversed BOX rectangles are finite wrapped-count operations.
  No extra ordering guard was added. The native checker executes the full
  kernels: coincident corners make262144 WORD writes across a modeled64K ES
  range; reversed corners also write outside the visible4000 bytes. The exact
  modeled writes/DI wraps match; actual VGA/ROM response outside the visible
  aperture remains unproven. Do not mislabel this as nontermination or silently
  claim full hardware equivalence.

## Current prototype products

At the handoff inspection, every recorded source hash in these two manifests
matched the current files. Recheck that after the other session edits anything.

| Product | Path | SHA256 |
| --- | --- | --- |
| Parent | `build/screen-parent-v5-20261118/TERMINAL.EXE` | `7f5b3b0303eac3f4e4a1ee1bb15715015221ec6a656ad128830045de1c5619d5` |
| Overlay child | `build/screen-child-overlay-v3-20261118/ASPECT.EXE` | `16f910333ee66c9061fd635f3ca8f79fc5e6070d02827579a279d931fd1f5245` |
| GET compiler | `build/screen-compiler-v2-20261118/ASPCOMP.EXE` | `00fb07d154bb356145ed7696faa2e93c437188928da10f270c14ddccdca6c23b` |

Parent: DGROUP65520, resident CS65224 (312 bytes spare), minimum retained module
484336 bytes. Child: near code65492 (44 spare), DGROUP40640,8192-byte stack,
exact DOS minimum including PSP126816, page minimum126832. Both stacks and
existing buffer capacities remain unchanged. The resident screen client bank
is192 bytes; the shared screen overlay is931 bytes.

The v3 parent had duplicate screen RPC/platform definitions because the generic
terminal ASM glob also included the explicitly built modules. This is fixed:
those two files are excluded from the glob, then included once through the
feature/helper paths. v4/v5 builds have no W1027 duplicates. Do not reuse v3
parent as the final candidate. v5 also preserves AX at screen scope end.

## Evidence already obtained

These are bounded proofs, not blanket qualification of cap27. Match each
receipt's binary/source identities to the product being discussed.

| Boundary | Result | Receipt |
| --- | --- | --- |
| Original compiler observations |1426 observations;1394 unique new fixtures | `analysis/aspect-screen-commands-20261118/original-oracle-receipts.json` |
| Host + actual DOS compiler |1394 cases,557 accepted/837 rejected, exact successful bytes | `build/screen-compiler-oracles-v2-20261118/result.json` |
| Full ordinary DOS compiler |4670 cases,1882 accepted/2788 rejected;1693 API checks; ownership checks | `build/screen-compiler-regression-v2-20261118/checks.json` |
| Default-profile N bank | exact `0\|32768\|-32767\|7\|9\|10`; no attached EMULATE claim | `build/screen-numeric-bank-dos-20261118/result.json` |
| Native commands/helpers |133442 CPU cases;220 new native bytes +630 reused bytes match optional original | `build/aspect-screen-native-final-original-20261118/result.json` |
| Source-only native check | same133442 cases | `build/aspect-screen-native-final-source-20261118/result.json` |
| Parent platform component |540 cases/5690 checks; external BIOS effects modeled | `build/script-screen-platform-check-v5-20261118/result.json` |
| RPC component |277 cases/1150 operations; peer admission/scope/platform modeled | `build/script-screen-rpc-cpu-final-20261118/result.json` |
| Linked parent v4/older child |40 cases/213 operations +6 child handshakes; C policy/BIOS modeled | `build/screen-parent-linked-cpu-receipt-20261118/result.json` |
| Actual DOS FAR C client |2050 cases/14748 checks; eight bad prerequisite profiles rejected | `build/aspect-screen-client-bank-v1-20261118/result.json` |
| Pure policy | default58978 checks unchanged;750 added checks;303 CPU states/909 calls | `build/screen-policy-v2-20261118/result.json` |
| Split-bank placement | resident adapters/data vs actual section5 vectors | `build/screen-bank-split-v3-20261118/linked-placement-checks.json` |
| Overlay option disabled | same closed base: old/new builder produce exact same EXE/link script | `build/screen-overlay-disabled-identity-20261118/result.json` |

Default policy machine bytes also match the saved baseline exactly. The overlay
disabled check is an old/new overlay-builder comparison on the same base; it
does not establish that the whole new non-screen runtime equals the prior cap26
binary (the N-bank alias fix is an intentional change).

### Full DOS success versus the remaining failure

1. **Latest baseline source/GET succeeds:**
   `build/screen-base-source-lease-v2-20261118/checks.json` passes two DOS8086
   source-start/source-EXECUTE workflows and105 checks with final parentv5 /
   overlay-childv3. This result completed as this session was being stopped.
   It checks older terminal/HITKEY/state probes and allocation preservation;
   it does **not** exercise the new screen-command family.
2. **Whole-family supplemental386 success:**
   `build/screen-full-get-386-v1-20261118/result.json` passes one GET workflow
   with older parentv4 / non-screen-overlay childv2. Actual BOX/SCROLL pixels,
   all seven commands, status-row attributes/cursor, CLEAR behavior,
   N-register/EMULATE separation and held FILE/GET checks pass. This is one
   CPU386 case, not final8086, source-EXECUTE or error-suite qualification.
3. **Whole-family8086 still fails with the richer observer:**
   `build/screen-full-overlay-get-v1-20261118/result.json` is false using final
   v5/v3 products. Earlier attempts include clean pre-child EXEC8 refusals;
   after the screen overlay, the child starts but FOPEN appears unable to get
   its buffer, followed by native stream-lookup error4/runtime7 at FPUTS65.
   Do not interpret that as a native screen failure: no screen operation had
   executed at the failing point.

The latest enriched-observer negative recorded largest free128976 bytes,
environment73 paragraphs, child PSP7987 paragraphs and near break only41152
from DGROUP40640. The successful386 case reached near break41906. Observer
cost and conventional headroom are the current working diagnosis; a complete
causal fix remains unproven. Preserve the failed receipts. Do not trim the
user environment or reduce stacks/buffers to obtain a passing result.

The worker was considering lossless reuse of observer-only diagnostic storage
to save268 bytes, but had not produced a verified8086 whole-family success
when stopped. Inspect the current test script instead of assuming it matches
an older receipt. The latest fixture intentionally uses PUTVATTR46 (not31,
which matched the initial status attribute and would have been a no-op),
checks it through GETVATTR, then restores and verifies the saved attribute.

The base GET harness sometimes prints preliminary `FINAL FAIL` because source
compilation regenerates NEXT.ASX. Its outer source-compilation checks replace
that preliminary immutable-fixture comparison. Check the final `checks.json`
and every labeled assertion; do not waive a real failure based on this note.

## Useful reproduction entry points

Read `AGENTS.md`. Use `./tools/dev --command` or `./tools/build`; no original
executable, original install or generated analysis DB may enter normal builds.
Never execute `*.analysis.exe`. Keep DS=SS for DS:BX stack accesses. Originals
and private data stay ignored and out of this public repository.

The current full child base is `build/screen-child-base-v3-20261118`. Overlay
linking (use a fresh output directory):

```sh
./tools/dev --command python3 standalone/build_aspect_standard_overlay.py \
  --base build/screen-child-base-v3-20261118 \
  --output build/CHOOSE-A-FRESH-OUTPUT \
  --notice --program --screen --checked-io
```

Whole-family harness (this is a pending test entry point, not a claim it passes):

```sh
./tools/dev --command python3 standalone/test_aspect_screen_dos.py \
  --parent-dir build/screen-parent-v5-20261118 \
  --child-dir build/screen-child-overlay-v3-20261118 \
  --compiler-dir build/screen-compiler-v2-20261118 \
  --suite all --cpu 8086 --output build/CHOOSE-A-FRESH-OUTPUT
```

Individual suites are `get`, `source`, `errors`. The wrapper retains the base
GET checks and adds passive BOX/SCROLL samples tied to script/wire milestones.
It does not draw the expected image or inject parser replies.

For a parent rebuild, use `standalone/keymap_connection_candidate_recipe.json`
terminal flags plus `--aspect-get-display --aspect-get-policy
--compiler-lease-bridge --chat-send-mode --aspect-terminal-query --aspect-hitkey
--aspect-state-builtins --aspect-screen-commands`. For the child use the
existing full process profile plus `aspect_screen_commands=True` and
`overlay_ready=True`; preserve all preceding cap26 options. Source manifests
and `GETVM.lnk` retain the exact last inputs/options. Do not restart an existing
build merely because an observation times out; poll its actual live handle.

## Suggested next checks for the other session

1. Reconcile this work with your own changes before editing or committing.
   Revalidate current files/manifests; do not reset another session's work.
2. Resolve or precisely explain the8086 whole-family observer/FILE headroom
   failure while retaining the original assertions and capacities.
3. Run all whole-family source-start, source-EXECUTE and typed-error cases.
   Explicitly verify far/overlay abort recovery, N0/EMULATE separation and
   resource cleanup. Passing baseline GET alone does not prove screen overlay
   execution or unwind.
4. Cover actual132-column LOCATE/viewport changes and larger physical layouts
   as appropriate. Existing pure-policy/model tests do not prove the entire
   native viewport/display path. Frame configuration and physical ROM/aperture
   behavior remain open boundaries.
5. Update cold proof/package tooling for capability27 and the new screen-overlay
   flag before claiming complete release qualification. I have **not** updated
   `prove_compiler_bridge_source.py` or the package/archive contract tools for27;
   they still describe the cap26 checkpoint. No fresh cap27 cold export,
   committed-source audit, complete package/ZIP or BBS qualification exists.
6. Only after the implementation and evidence are ready, record a bounded
   checkpoint and continue the original F01–F16 scope. Screen commands do not
   finish ASPECT; scripted modem control/transfers, other emulations/protocols
   and Host-last work remain.

This document was written after the stop request. It does not resume this
session's paused goal or authorize changes to the installed application.
