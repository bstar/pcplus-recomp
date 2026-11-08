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
