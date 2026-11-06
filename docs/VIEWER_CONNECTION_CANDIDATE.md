# Reviewed viewer connection candidate

Build the current reviewed connection-test payload with the pinned Nix toolchain:

```sh
./tools/build-connection-candidate
```

The command creates `build/connection-candidate/archive/PCPLUSSE.ZIP`, plus
executable manifests, package identity and a build log. It refuses an existing
output directory. For another build, choose a fresh directory:

```sh
./tools/build-connection-candidate --output-dir build/connection-candidate-02
```

The [tracked recipe](../standalone/connection_candidate_recipe.json) specifies
the complete terminal flags and expected application/package hashes. It builds
TERMINAL, ASPECT, ASPCOMP, PRMEDIT and XLTEDIT from source, generates the authored
help resource, stages the launchers and creates a deterministic ordinary ZIP.
The reviewed package source identity remains pinned to commit e74425e; changes
that alter reviewed payload bytes fail the identity checks. A new application
revision needs validation and an explicit recipe update.

The archive has ten public files under `PCPLUS/`, totals286274 bytes and has
SHA256 `76da9ea0b6c5323606b6b2f6e621d810379bd6f934c94d87a04537d66e9939e2`.
It contains no private PRM/DIR/FON/KEY/KBD/XLT, disk image, original executable
or laboratory capture. Every extracted byte is checked against the package
manifest. Building does not install files or change the selected package.

## Recorded software gates

The [release-candidate receipt](validation/viewer-connection-release.json)
binds five exact cold-built executables, ten package files, the archive and three
actual DOS8086 COM3/IRQ5 launcher cases. These cover START's original magenta
splash with LoC annotation, SETUP with preserved configuration/environment, and
DOS precompilation followed by script execution when COM3 is absent from the
BIOS table. The earlier setup probe collided with the helper build directory
and stopped before DOS; the accepted check uses its own fresh output.

The same executable uploads and downloads the same65539-byte all-values payload
through the isolated SynthModem proxy and stock Enigma's actual transfer helper.
Independent replays verify raw Telnet/application equality, NAWS80x24, CRC,
length, ZEOF/ZFIN/OO, opposite controls and exact stored/catalog destination.
Binary window-size lookalikes remain payload bytes.

A separate actual download is canceled after a nonempty4096-byte disk stage.
The receive directory is empty before retry, then the exact same65539-byte file
arrives in the same DOS process, proxy connection and authenticated session.
Both server-helper exits and post-transfer search/list transitions are audited.

The [tracked-builder proof](validation/viewer-candidate-build.json) also exports
2270 public files without originals, prior objects, private settings or Git
metadata and executes the canonical Python builder inside the pinned Nix
environment. All five executables, ten files and ZIP match. The shell wrapper's
Nix bootstrap is separately exercised in the working checkout. This distinction
does not claim a new Nix-shell bootstrap from the metadata-free source export.

## Physical integration remains separate

This candidate has not replaced the physical installation or its selector.
Preserve the working modem configuration and PCPLUS.FON call history. The
established hardware path remains Boca COM3/3E8h/IRQ5 through SPA2102 and the
Linux SynthModem bridge. Reboot out of network management before modem testing
because the NIC and Boca share IRQ5.

The tested bridge is the isolated `menu-size-accepted-20261104` snapshot. Its
[menu-owned size-negotiation patch](../lab/bbs/patches/synthmodem-menu-size/README.md)
adds WindowSizeReply and differs from the workstation SynthModem checkout.
That checkout also has unrelated VM/backend work in progress. These tests do
not establish equivalence to that runtime or install/restart its service.
Preserve local aliases, SIP/audio configuration and existing work when
integrating the patch.

SIP/audio/DSP/analog behavior, physical CTS timing, full sustained hardware
display/editor/transfers and remaining original PCPlus parity remain open.
The separate [carrier recovery](FILE_VIEWER_EXTERNAL.md#carrier-loss-during-transfers-and-children)
and [BBS editor](FILE_VIEWER_EXTERNAL.md#external-child-inside-stock-bbs-editors)
receipts retain their own scopes and exact executable identities.
