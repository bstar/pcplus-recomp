# PCPlus pause checkpoint: native ASPECT screen commands

The user confirmed that the apparent second worker was this same resumed
session and authorized continuing. They subsequently requested: “pause when it
makes sense.” This checkpoint finishes the in-flight RPC and Enigma tests and
stops before new cold-export, connection-package or Synchronet work.

Persistent objective: “resume decompiling and recompiling pcplus, I'm sure the
plan is not complete.” Preserve that full objective; do not mark it complete.
Resume only when the user asks. Host remains the final implementation stage.

Repository: `/home/bstar/projects/pcplus-recomp`, branch `main`.
Core implementation is committed at `62a7690`. The following checkpoint commit
adds the final RPC checker, stricter qualification gates and current receipts.
Nothing was pushed. No installed selector, physical DOS machine, private BBS,
private configuration/history, live SynthModem, ATA or SIP/audio setting changed.

The separate BBS repository request was already completed at
`/home/bstar/projects/black-flag-bbs`, private remote `bstar/lossofcontrolbbs`.
Do not confuse those two repositories.

## Completed source and execution work

The capability27 profile now implements native BOX, CLEAR, HOME, LOCATE, SCROLL,
GETVATTR and PUTVATTR through both compilers, the interpreter and admitted parent
screen helpers. Writable N0–N9 works throughout the frontend; the separate
EMULATE selector no longer aliases N0. The screen gateway/adapter/native bodies
share overlay section5, with resident operand, wire, admission and abort gates.

[Current feature documentation](ASPECT_SCREEN_COMMANDS.md) and
[validation ledger](validation/aspect-screen-commands.json) retain the complete
provenance and limits. Important passing receipts:

| Evidence | Receipt |
| --- | --- |
| 1394 compiler oracles,557 accepted/837 refused | `build/screen-compiler-oracles-v2-20261118/result.json` |
| Ordinary compiler4670 cases,1693 API checks | `build/screen-compiler-regression-v2-20261118/checks.json` |
| 133442 native CPU cases | `build/aspect-screen-native-final-source-20261118/result.json` |
| Six controlled DOS client suites/placement | `build/screen-client-capacity-20261119/result.json` |
| Current linked parent40 cases/213 operations | `build/screen-parent-linked-current-v1-20261119/result.json` |
| Full screen/source/GET/errors:5 DOS8086 cases/254 checks | `build/screen-full-reused-v1-20261119/result.json` |
| Canonical132 columns:1 DOS8086 case/58 checks | `build/screen-wide-dos-v6-compact-20261119/result.json` |
| Actual RPC refusal/resident abort/same-parent reuse:65 checks | `build/screen-rpc-failure-final-20261119/result.json` |
| Baseline source startup/EXECUTE:2 cases/105 checks | `build/screen-base-source-lease-v3-20261119/checks.json` |
| Plain/framed WHEN:2 cases/82 checks | `build/screen-when-v3-20261119/checks.json` |
| Nested Help/FILE/handles/frame:63 checks,386/UMB | `build/notice-help/screen-help-v3-20261119/result.json` |
| Capability27 package controls57 / legacy26 controls51 | `build/screen-contract-v1-20261119/result.json`, `build/screen-package-legacy26-v1-20261119/result.json` |
| Chat/settings2 matched+5 refused pairs, explicit identities | `build/screen-chat-pair-v1-20261119/result.json` |

The RPC failure fixture is explicitly active: one temporary parent policy WORD
at a valid LOCATE commit, restored at the real return3; a bounded INT1 trace
observes the resident failure gate/abort/longjmp. It then launches a second
interpreter through real Alt-F5 in the same parent and verifies pixels/GET.
Its generated-code overwrite protection passes6 CPU cases/14 checks. It is not
a passive observer or a claim about a real profile producer.

Conventional-memory pressure was in added measurement code. Lossless reuse of
idle3538-byte admission-snapshot storage preserves full failure capture and256
BDA bytes; generated-code checks prove guards refuse overwritten scratch code.
Successful cases retain original buffers,8192-byte stack and73-paragraph DOS
environment. Earlier failed/timeout observers remain negative evidence. Do not
trim capacities, weaken checks or treat those runs as qualified.

## Frozen current products

| Product | Folder | SHA256 |
| --- | --- | --- |
| TERMINAL.EXE | `build/screen-parent-v6-20261119` | `7f5b3b0303eac3f4e4a1ee1bb15715015221ec6a656ad128830045de1c5619d5` |
| ASPECT.EXE | `build/screen-child-overlay-v4-20261119` | `1a0369887a08084365cbd04dc3f41daa2545088b5a01382f22d3ee9179519fa4` |
| ASPCOMP.EXE | `build/screen-compiler-v2-20261118` | `00fb07d154bb356145ed7696faa2e93c437188928da10f270c14ddccdca6c23b` |

Child near code65508/spare28; DGROUP40640; stack8192; screen overlay1016.
Exact minimum including PSP126640; page accounting126848. These are different
measures. Full DOS cases reach near heap41906. Parent DGROUP65520. All1053
application source files match actual Git blobs at62a7690:
`build/screen-core-committed-source-20261119.json`.

`build/screen-lab-v1-20261119` is the matched ten-product lab/Help payload.
`build/screen-stage-v2-20261119` and its archive/57 controls are provisional
fixtures based on the older source-base declaration. They are not the final
committed connection candidate. Do not promote them.

## BBS boundary and durable execution

The current Enigma run is `screen-builtins-carrier-v3-20261119`, using the exact
three frozen hashes and unchanged strict386/UMB/live-source/150000ms recipe.
Its durable supervisor exit receipt reports0, and carrier-checks.json passes18
checks. [The companion BBS documentation](ASPECT_SCREEN_BBS.md) records the independent
wire audit,16 capture controls and cleanup. Root verification confirms both lab
ports free and all six recorded owned PIDs absent.
Synchronet was deliberately not started after the pause request. Full combined
BBS/package qualification remains incomplete.

An earlier producer disappeared during session continuation, orphaning its proxy
and closing the relay before retry completion. Its DOS PASS.TXT did not qualify
it; final snapshots/traces existed only in lost process RAM and were not
reconstructed. The preserved diagnosis is
`build/screen-bbs-v1-20261119/incomplete-enigma-v2.json`.

Use explicitly owned durable jobs for long future labs: persisted command,
PID/PGID, source/product hashes, stdout/stderr and atomic exit receipt. Current
job metadata is under `build/screen-bbs-v1-20261119/enigma-v3-job`.
Never restart on observation timeout alone. Check exact process/handle and
terminal evidence first; clean up only processes established as owned.

## Resume sequence

1. Check goal status, Git status and current processes/ports. Preserve the two
   unrelated pre-existing edits: `docs/MACHINE_BOOT_PROFILES.md` and
   `tools/machine-profiles/compile.py`. Do not discard or commit them here.
2. Finish current-byte Synchronet editor/cell/CPR/NAWS checks using the previous
   state-checkpoint recipe. Start only owned stock loopback lab servers with
   free ports23231/23233; stop them and verify ports afterward. No private/live
   board or physical machine changes.
3. Stage a fresh17-file connection package using the actual checkpoint commit
   as source base and the frozen lab/child/compiler above. Stable companions:
   `build/directory-baud-setup-20261117`, `build/directory-baud-translation-20261117`
   and `build/directory-baud-keymap-20261117`. Re-run57 controls/archive.
4. Run `standalone/prove_compiler_bridge_source.py` in the pinned toolchain.
   Use `--parent`, `--child`, `--compiler`, `--lab-payload` and the new
   `--connection-package`; baseline `--checks` source2 plus WHEN2; `--help-checks`
   Help63; `--screen-checks` full5; `--screen-wide-checks` wide1; and
   `--screen-rpc-checks` RPC65. All receipt paths are in the table above.
   The exporter now requires all three screen gates for cap27 and reproduces
   selected baseline case names exactly. This extension is syntax/read-only
   reviewed, but its complete cold execution has not yet been run.
5. Run the eight packaged DOS8086 workflows with common flags
   `standalone/test_special_package_dos.py --package PACKAGE --output OUT/CASE
   --com 3 --irq 5 --bios-absent`. Cases/extra flags: splash `--splash-only`, setup
   `--setup`, source none, commands `--precompile`, line `--native-line-port`,
   meta `--meta-editor`, keymap `--keymap-editor --keymap-profiles 7 --keymap-help`,
   chat `--chat-help`. Reuse the current seven-pair receipt only while its
   explicit parent/setup identities and sources remain current.
6. Record complete qualification only after current BBS, archive, cold proof,
   Git blobs and all eight packaged workflows agree. The recorder now checks
   actual Git blob bytes and binds Chat controls to this package's parent/editor.
   No cold replay, final committed package or package DOS matrix was started at
   this pause boundary.

Use `./tools/dev --command` / `./tools/build`. Normal builds must remain source
only; never execute `*.analysis.exe`. Preserve DS=SS real-mode ABI and exact flat
addresses with symbolic OMF linkage. Original binaries/retained analysis are
optional comparison evidence, never application build inputs.

## Required work beyond this checkpoint

HOME's checked-attribute branch is component-tested, but its canonical producer
and marker-plane initialization are unlinked. Retained overlay13:F59E enables
it, F5C2 disables it and ECD2's token26 arm calls it; outer emulation/profile
routing still needs recovery. Do not seed the flag and call that integration.
Runtime PRM frame-style selection and physical aperture behavior remain open.

[The broader plan](ASPECT_RECOVERY_NEXT.md) continues with scripted DIAL/MDIAL/
REDIAL/HANGUP ownership and script-owned GETFILE/SENDFILE transfers, then the
remaining compiler/runtime, UI, emulation/protocol and [F01–F16](FEATURES.md)
requirements. Physical Boca/SPA2102/SynthModem acceptance remains separate.
Host stays last. This checkpoint does not complete PCPlus.
