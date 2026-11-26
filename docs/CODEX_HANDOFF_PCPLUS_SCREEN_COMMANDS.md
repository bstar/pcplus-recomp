# PCPlus reconstruction checkpoint: capability27 qualified

The user requested “pause when it makes sense.” Work is being saved at the
component/optional-overlay boundary; resume only on the user's instruction.
The objective remains: “resume decompiling and recompiling pcplus, I'm sure the
plan is not complete.” This checkpoint does not finish PCPlus or F01–F16. Host
remains the final implementation stage.

Repository: `/home/bstar/projects/pcplus-recomp`, branch `main`.
Core screen implementation: `62a7690`. Final RPC/qualification-gate source:
`bd99894c65539bcbfeb4beaba636b1339f49bc47`. The following documentation commit
records the completed package qualification at `e619ed0`. Subsequent connection
component work changes the compiler and adds unlinked native source; keep the
qualified payload frozen rather than mixing development artifacts into it.
Tested connection components are committed at `1ea81d9`; their source and eight
receipt hashes were rechecked before the pause.
Nothing was pushed or installed. Preserve unrelated pre-existing edits in
`docs/MACHINE_BOOT_PROFILES.md` and `tools/machine-profiles/compile.py`.

The separate private BBS-repository request is already complete at
`/home/bstar/projects/black-flag-bbs`, remote `bstar/lossofcontrolbbs`.

## Current qualified software checkpoint

The capability27 profile implements BOX, CLEAR, HOME, LOCATE, SCROLL, GETVATTR
and PUTVATTR through both compilers, the interpreter and admitted native parent
helpers. Writable N0–N9 and EMULATE selector separation are recovered. Native
handlers, adapters and scalar client share overlay section5; operand readers,
owner admission, wire and abort gates remain resident.

- [Feature semantics and limits](ASPECT_SCREEN_COMMANDS.md)
- [Complete connection candidate](ASPECT_SCREEN_CONNECTION.md)
- [Package/Git/cold/DOS/BBS receipt](validation/aspect-screen-package.json)
- [Current BBS qualification](ASPECT_SCREEN_BBS.md)
- [Native/compiler/client/integration ledger](validation/aspect-screen-commands.json)

`build/screen-committed-package-v1-20261118/PCPLUS` contains17 files, source base
bd99894. `build/screen-committed-archive-v1-20261118/PCPLUSSE.ZIP` is389199 bytes,
SHA256 `e620d99a86a566c6329c033f80f9e617a50c3ff676813ca5fa59022138ad1de7`.
A cold export reproduces the entire payload/ZIP from1128 actual Git blobs,
without originals, prior objects or ancestor Git. Receipt:
`build/screen-complete-cold-v1-20261118/result.json`.

It repeats57 package controls,13 lab/Help controls, four source/WHEN cases, five
full screen/source/operand-error cases, canonical132-column execution, actual
parent-refusal/resident-abort/same-parent reuse, and63 Help/FILE/frame/handle
checks. Screen families use DOS8086; the established nested Help observer uses
386/UMB. The eight packaged DOS8086 workflows add50 checks on COM3/IRQ5 with no
BIOS UART entry. Seven Chat/settings controls bind the current parent/editor;
two recorder controls reject different real product identities.

Enigma passes18 checks, strict wire audit and16 capture controls. Synchronet
passes22 checks; independent audits match1920/1920 cells, CPR5,8 and NAWS80x24
for physical25/status shown. Temporary owned servers/proxies are stopped and
ports23231/23233 verified free. No private/live BBS or physical modem was used.

## Frozen products and evidence

| Product | Folder | SHA256 |
| --- | --- | --- |
| TERMINAL.EXE | `build/screen-parent-v6-20261119` | `7f5b3b0303eac3f4e4a1ee1bb15715015221ec6a656ad128830045de1c5619d5` |
| ASPECT.EXE | `build/screen-child-overlay-v4-20261119` | `1a0369887a08084365cbd04dc3f41daa2545088b5a01382f22d3ee9179519fa4` |
| ASPCOMP.EXE | `build/screen-compiler-v2-20261118` | `00fb07d154bb356145ed7696faa2e93c437188928da10f270c14ddccdca6c23b` |

Child near65508/spare28, DGROUP40640, stack8192, screen overlay1016. Exact
minimum including PSP126640; page accounting126848. Full DOS cases reach heap
41906. Parent DGROUP65520. Do not reduce buffers, stack or environment to fit
new features or observers.

The matched ten-product lab payload remains `build/screen-lab-v1-20261119`.
Older `build/screen-stage-v2-20261119` is provisional; use the committed package
above. Stable companions are `build/directory-baud-setup-20261117`,
`build/directory-baud-translation-20261117` and
`build/directory-baud-keymap-20261117`.

Earlier detailed receipts remain linked from the ledger:1394 original compiler
oracles, ordinary compiler4670 cases,133442 native CPU cases, six DOS client
suites, linked parent, full screen5/254, wide1/58, RPC1/65, source2/105 and
WHEN2/82. The actual RPC fixture temporarily changes one policy WORD, observes
real return3 and resident abort/longjmp, then starts another interpreter through
real Alt-F5 in the same parent. It explicitly records active injection. Its
six-case/14-check generated-code proof preserves3538 failure-snapshot bytes and
256 BDA bytes and prevents executing scratch code after failure capture.

## Current scripted connection development

Both compilers match311 unique original connection sources (82 accepted/229
rejected); public fixture/checker and the
[compiler/component record](ASPECT_SCRIPT_CONNECTION_COMPILER.md) bind them.
Development GET compiler is `build/connection-compiler-v1-20261118`, SHA256
`ce833af2eb8bf56acb61ee89b7a5f659d668882e5530cfe65fe8c2a901e2f459`.
Ordinary regression4981 and checked-stack4999/18 deep cases pass. Five existing
full-parent screen/source cases pass254 checks with the larger compiler.

The isolated native family adds11 exact units/1527 bytes plus reused576-byte
attempt. Source-only and original-byte comparisons each pass241 cases/4330
checks. New ASM is not selected by an application builder; these runtime opcode
slots still explicitly refuse. Full UART/DOS/application integration is open.
Source-only receipt `build/aspect-connection-native-source-20261119/result.json`.

Compact symbolic OMF linkage now passes40 CPU cases/657 checks with71 data
aliases and856 controlled FAR callbacks. Its10880-byte allocation retains4096
stack bytes and all buffers; it fits16KiB, not8KiB. Actual parent services and
state persistence across module unloads remain open. Receipt
`build/aspect-connection-compact-omf-final-20261119/result.json`. A source-built PCCONN
module could borrow inactive snapshot storage instead of adding resident code.
Its owner, callback/PSP/stack transitions and persistent REDIAL state need the
[owner audit](ASPECT_SCRIPT_CONNECTION_OWNER_AUDIT.md). Do not treat current
PROGRAM pause/resume, ordinary RIS or foreground adoption as a complete lease.
To replay capability27, use the recorded bd99894 source export/checkout; current
development compiler source hashes intentionally differ from that checkpoint.

## Optional ASIO overlay at the pause

The opt-in `serial_overlay_ready` / `--serial` build moves the three ASIO code
contributions together into the existing shared overlay workspace. Four hot
directory/translation getters remain resident; DATA, buffers and the8192-byte
stack retain their sizes. Connection runtime commands remain disabled.

Disabled-option controls reproduce both qualified child executables exactly:
base `a46cabb419da041539dbc4ca91d8fadeaa0ba39f4e55c62dde6cd9cb2a0af344`
and ordinary overlay `1a0369887a08084365cbd04dc3f41daa2545088b5a01382f22d3ee9179519fa4`.
Receipt: `build/asio-overlay-v1-20261119/disabled-controls.json`.

Experimental product: `build/asio-shared-overlay-v1-20261119/ASPECT.EXE`, SHA256
`47a3a7f961a67b0fda1e916e1e63c35e65a5d984b56cabb267e309f156f07004`.
Exact minimum including PSP is121600 bytes (5040 fewer); page minimum121760
(5088 fewer). Near code65492/spare44; DGROUP40640 and stack8192 unchanged.
This is measured allocation savings, not a qualified package or measured
application heap margin. See [the ASIO audit](ASPECT_ASIO_OVERLAY_AUDIT.md).

The focused actual8086 hot-function v2 probe passed four cases provisionally,
but lacks an independent positive control for its overlay-read counter. The
current v3 probe adds counter controls/register canaries and fails assembly
before DOS because generated `read-root.asm:32` uses an8086-invalid immediate
PUSH. That failure is retained; current probe source is not validated. Fix that
instruction and rerun the focused proof before broader testing. No build/test
or owned DOS processes remain at this checkpoint.

Before selecting this product, finish the five-case full screen/source suite,
wide-screen, Help, RPC refusal/reuse and loader-failure/abort/close/register
publication checks with current source/product identity. Use development GET
compiler `build/connection-compiler-v1-20261118`; the frozen capability27
compiler's source hashes intentionally differ. Preserve the qualified package.
Then return to the dedicated one-UART connection lease and real PCCONN module;
neither exists yet. The compact native proof requires at least16KiB and full
persistent REDIAL state outside any overwriteable module workspace.

## Durable job records

Long test jobs persist commands, source/product hashes, exact PID/PGID,
stdout/stderr and atomic terminal exit receipts. Current completed records:

- Cold proof: `build/screen-complete-cold-job-v1-20261118`.
- Packaged DOS matrix: `build/screen-committed-package-dos-v1-20261118`.
- Enigma: `build/screen-bbs-v1-20261119/enigma-v3-job`.
- Synchronet/server: `build/screen-bbs-resume-v1-20261119`.

An earlier Enigma producer disappeared during continuation, losing in-memory
relay traces and closing its retry early. That incomplete result remains
unqualified; no traces were reconstructed. Earlier oversized observer/startup
failures also remain negative evidence. Never restart solely on observation
timeout; inspect exact live process/handle and terminal receipts first.

## Next reconstruction work

The next coherent family is scripted DIAL/MDIAL/REDIAL/HANGUP, then scripted
GETFILE/SENDFILE. Existing foreground engines alone do not establish script
ownership, cancellation, results or resumption. Retained native/grammar recovery
is in progress; preserve its concrete findings before implementing.

Known distinctions from the recovered dialer code: DIAL passes mode0, MDIAL2,
REDIAL1 into shared5695. DIAL and REDIAL optional output strings receive a
selected-entry index; MDIAL's optional string is input. Escape produces failed
connection/resumption rather than an automatic fatal runtime cancellation.
The script path adopts relevant directory terminal/protocol/Meta/key settings
without the foreground path's automatic-script handoff. Confirm exact indices,
write timing and dependency closure in the recovery ledger before coding.

HOME checked-attribute activation/marker-plane initialization and runtime PRM
frame-style selection remain unlinked. Native overlay13:F59E enables checked
attributes, F5C2 disables them and ECD2's token26 arm calls the producer; outer
emulation/profile routing still needs recovery. Do not seed a flag and call it
integration. Physical VGA/CGA aperture behavior and the physical modem path
remain separate gates. The broader plan is [ASPECT_RECOVERY_NEXT.md](ASPECT_RECOVERY_NEXT.md)
and [F01–F16](FEATURES.md); full ASPECT, other emulations/protocols and Host remain
required.

Use `./tools/dev --command` / `./tools/build`. Normal builds must remain source
only; never execute `*.analysis.exe`. Preserve DS=SS ABI, exact flat addresses
and symbolic OMF linkage. No installed selector, physical DOS machine, private
configuration/history, live SynthModem, ATA or SIP/audio setting changed.
