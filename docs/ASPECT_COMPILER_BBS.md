# Compiler-bridge BBS regression payload

The capability23 compiler-bridge parent passes fresh stock Enigma and Synchronet
ZMODEM downloads and uploads through the actual SynthModem Telnet proxy. It has
a nine-file lab payload with
matched interpreter, compiler, modules and Help resources. The lab stager does
not select a release, create an installer/archive or update the DOS machine.
Exact identities and acceptance scope are in the
[validation record](validation/aspect-compiler-bbs.json).

## Payload and companion contract

`standalone/package_compiler_bridge_lab.py` validates the parent/child/compiler
source manifests and copies their exact artifacts. It builds PCHELP.RTE and
PCPLUS.HLP from public source using the pinned toolchain. The nine files are:
TERMINAL.EXE, ASPECT.EXE, ASPCOMP.EXE, PCCOMP.OVL, PCLINE.OVL, PCMETA.OVL,
PCCHAT.OVL, PCHELP.RTE and PCPLUS.HLP. The original magenta splash/LoC annotation
and all current parent features remain the same application bytes.

The BBS product resolver now includes and hashes PCCOMP.OVL alongside existing
companions. These transfer runs mount the complete validated payload as C:;
other lab workflows use the resolver’s staging helper. A compiler-bridge manifest must declare its whole-kernel module.
File-contract tests reject a missing, truncated or corrupt module and an omitted
module declaration. The omitted-declaration test keeps the separate Help-bundle
manifest hash coherent, so rejection must concern the compiler contract rather
than an unrelated binding mismatch. An initial contract run exposed this missing
mandatory check; the corrected resolver rejects it.

This is corruption/matching validation, not authentication of hostile manifests.
The payload is for the current laboratory workflows; complete release packaging,
settings tools, startup launchers, installation and physical admission remain
separate work.

## Owned BBS workflows

The transfer harnesses exercise the actual parent in DOS8086 with COM3/IRQ5,
VGA25 and a visible status row. A serial Hayes shim supplies modem commands;
the actual installed SynthModem Telnet proxy connects to stock owned Enigma
and Synchronet on loopback. The proxy and server sources/configuration are
hashed before and after each run. No BBS source or configuration is patched.
These are software protocol tests, not SIP/audio or physical modem calls.

Downloads require the exact 11521-byte fixture, validated ZMODEM CRC/offsets,
ZFILE/data/ZEOF/ZFIN/OO closure, post-transfer BBS menu response, normal exit,
hardware/configuration preservation and no staging residue. Uploads use unique
synthetic 65539-byte files with all256 byte values, Telnet IAC patterns and ANSI
size-report patterns. Server-installed bytes and official server metadata must
match, with protocol closure and subsequent menu input. The stock Enigma wrapper
also requires unchanged message count: no post is saved by these workflows.

The current proxy source identity is recorded per run, rather than assumed to
match earlier checkpoints. Download runs preceded the final mandatory-declaration
check; their frozen resolver hash remains explicit. Upload and payload-contract
runs use the final resolver. Application and payload bytes are identical across
those checks. A rejected Enigma fixture option stopped before connection and is
excluded from accepted transfer evidence. A first large-upload run completed
ZMODEM but failed file-base commit/menu checks with a30-second fixture wait.
Its failure is retained; the repeat uses the established60-second wait and a
fresh filename rather than counting protocol closure alone as success.

## Reproduction

```sh
./tools/dev --command python standalone/package_compiler_bridge_lab.py \
  --parent build/compiler-bridge-parent-recovery-final-20261108 \
  --child build/compiler-bridge-child-256-20261108 \
  --compiler build/get-compiler-enabled-20261107 \
  --output build/compiler-bridge-lab-new
```

The cold-source prover accepts `--lab-payload` to include the Help/stager source
closure, rebuild every payload file and rerun the companion contract. Its DOS
compiler controls and expected termination stops remain separately counted.
The owned transfer wrappers require already-running stock loopback lab servers
and the actual SynthModem runtime; use a fresh label and directory for each run.

## Review and remaining gates

A fresh REA/Ghidra inspection of the original resident3F9C string callback finds
only Enter→99 and other key→0 through a near word-pointer argument. This is
consistent with the prior1527-case field corpus exercising original79D4/3F9C/
F479. It does not justify changing the maintained editor or calling its callback
identity tag as native code. The private snapshot retains full Evidence; no
original executable or analysis database enters the public source build.

These transfer receipts retain their original scope. The later
[connection checkpoint](ASPECT_COMPILER_CONNECTION.md) verifies this exact
parent's selected LoC main menu, cancel/retry and live-source Enigma compilation,
carrier loss/redial/retry. It does not establish every foreground mode or layout.
Earlier-parent receipts keep their own scope.
The [complete connection package](ASPECT_COMPILER_PACKAGE.md) now has separate
source/launcher acceptance. Physical Boca/SPA2102/SynthModem/LoC Enigma and
Synchronet acceptance, complete language/emulations/protocols/Host parity and
selected-package promotion remain open. Private settings, call history, boot profiles and installation are unchanged.

## Child Help companion contract (2026-11-08)

The schema2 lab bundle adds LOCHELP.HLP when the selected ASPECT manifest
requires its authored Help resource. It validates the resource hash and public
source closure against help-resource.json before staging. ASPECT.json and
LOCHLP.JSON are host-side evidence: their hashes bind the selected interpreter
and resource metadata in package.json; they are not DOS runtime companions.
The ten runtime products include the original nine above plus LOCHELP.HLP.

The BBS resolver checks that bound ASPECT metadata matches the actual interpreter,
then checks the resource bytes against both resource metadata and product hashes.
It returns LOCHELP.HLP through the ordinary companion-staging path and includes
the metadata in the frozen evidence inputs. Schema1 bundles keep their previous
contract; they are not retroactively credited with the new resource guarantee.
This remains consistency/corruption validation, not hostile-manifest authentication.

The contract requires all ten products and exact staging of all seven companions.
It retains four compiler-module rejection cases and adds six Help cases: missing,
truncated, corrupt, undeclared, wrong interpreter and wrong resource metadata.
The latter two retain coherent outer metadata hashes so they exercise the semantic
binary/resource binding rather than merely a stale metadata digest. All13 checks
pass. No DOS installation, selector or archive changes.

A1072-file Git-free source export rebuilds all ten exact runtime products,
regenerates coherent package metadata, repeats the13 contract checks, and
replays93 full Help checks plus two source compiler-loan/GET cases. This is a
lab package reproduction proof, not complete release or hardware acceptance.

The unchanged parent/new overlay child pair also passes a fresh stock Synchronet
session:22 checks cover actual ASPECT automatic login, editor input, unsaved
abort and preserved server/configuration state. The independent10-check screen
reference and size audit match all1920 logical cells and cursor5,8 exactly,
with negotiated80x24. These are DOS8086 serial-side software checks.

The new Enigma live-source carrier run passes both authentications, actual runtime
source compilation, exact generated ASX, virtual carrier-loss notice, staging
cleanup and same-process redial. Its initial60000ms retry window cancels before
EOF: RX-complete/exact-file/protocol-finish checks fail, despite48128 bytes of
CRC-valid, source-exact retry data. It is not an accepted transfer result. The
previously admitted carrier profile uses150000ms. Its separate repeat now passes
all18 checks: both runtime-compiled logins, virtual DCD loss after4096 partial
bytes, clean staging, same-process redial, exact65539-byte retry, full protocol
closure, subsequent menu input, normal exit and restored hardware/configuration.
No application/protocol changes were made in response to the short-window
failure, which remains a failed historical receipt.

The independent current-image audit validates the raw Telnet/proxy/relay bytes,
source/product identities, DCD notices, partial-prefix timing, generated ASX,
protocol CRC/offset/finish and exact installed file. Its controls accept the
original and reject15 altered copies, including coherently changed payload
bytes, source counts, compiler output, hardware state, partial timing, NAWS and
incorrect startup/CPU claims. These establish the selected serial-side Enigma
workflow with the current overlay child; SIP/audio/physical and full release
acceptance remain separate.

Exact current products, source/contract receipts and the accepted versus failed
software gates are bound in the
[Help companion validation record](validation/aspect-help-companion.json).
