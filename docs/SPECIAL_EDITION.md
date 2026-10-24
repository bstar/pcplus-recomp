# LoC Special Edition

The `--special-edition` terminal build displays an authored magenta BIOS text
splash headed `PROCOMM PLUS` and `LoC SPECIAL EDITION`. It waits for a key before
mouse or UART acquisition. It uses no additional DGROUP storage. Other builds
retain their existing startup behavior.

Build with the pinned Nix toolchain and the current application feature flags,
adding `--special-edition` to `standalone/build_terminal.py`. The output has a
`-special` suffix; diagnostic probe builds must never be installed as applications.

The card installation is `C:\PCPLUSSE\START.BAT`. It uses a private copy of the
card's existing PCPLUS.PRM, PCPLUS.DIR and PCPLUS.XLT, preserving the original
`C:\PCPLUS` installation. START runs `TERMINAL @PCPLUS.PRM`; SETUP runs
`TERMINAL /S @PCPLUS.PRM`. Sibling source-built ASPECT, ASPCOMP, PRMEDIT and
XLTEDIT executables are included. The LoC catalog supplies a separate favorite.

DOSBox checks on October 23, 2026 verified the splash, the existing card profile
(COM2, 19200, 8N1), command-menu access, clean exit, and shell launch/return.
These checks do not establish live BBS interoperability or physical modem
acceptance. Full original application parity remains unfinished. The prior
helper acceptance receipt describes its unbranded binary; it is not a receipt
for this optionally branded executable.

## Current package

The card still has the earlier October 23 installation. The newer full helper
build can now be packaged with the same splash, guarded exits/traps and filename
lookup, plus the current register interpreter and smaller DOS source compiler:

```sh
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --output build/special-package-next
```

Choose a new output directory for each run. The command builds with the pinned
Nix tools, checks every product's complete declared source hashes and binary
hash, and stages nine files under `PCPLUSSE`. It writes a separate JSON manifest
and a DOS `VERSION.TXT`. It does not access a card or include PRM, DIR or XLT
files. START/SETUP preserve the existing PCPLUS environment and accept up to
nine additional DOS arguments, for example `START /T:ACTIONS.KEY`.

The [package receipt](validation/special-package.json) distinguishes three
actual DOS8086 workflows: START with nested source compilation and exact ASX,
START with an independently captured magenta splash, and SETUP/cancel/splash/
return. Each checks COM2/PIC/vectors, environment restoration, unchanged local
PRM/DIR/XLT sentinels and unchanged packaged executables. The source-compilation
run has no resident observer: an earlier instrumented run exhausted the child's
conventional memory. The receipt retains that failure and its captured error;
a normal final DOS exit was insufficient to accept that run.

An empty tree of718 declared source files also reproduces all nine packaged
files exactly, including all five DOS executables, without originals or prior
objects. This reproduction uses the same pinned toolchain:

```sh
./tools/dev --command python3 standalone/prove_special_package_source.py \
  --package build/special-package-next --output build/special-source-next
```

Reproduce each workflow in a fresh output directory:

```sh
./tools/dev --command python3 standalone/test_special_package_dos.py \
  --package build/special-package-next --output build/special-start-next
./tools/dev --command python3 standalone/test_special_package_dos.py \
  --package build/special-package-next --output build/special-splash-next --splash-only
./tools/dev --command python3 standalone/test_special_package_dos.py \
  --package build/special-package-next --output build/special-setup-next --setup
```

This receipt covers the packaged launcher paths with dummy UARTs. The earlier
unbranded helper/BBS receipts remain evidence for their exact products; they do
not automatically prove live BBS behavior of this branded binary. No card was
connected or written during packaging. On the next installation, back up
`C:\PCPLUSSE`, replace only the nine manifest-listed files, preserve all local
configuration/dialing/script resources, verify copied hashes, then unmount the
card. The existing Favorites entry needs no path change.

## ISA modem IRQ gap

Setup, startup import and live validation currently require the standard
IRQ4/3/4/3 mapping. Supporting a jumper-selected IRQ5/7 requires changes beyond
the setup field: `port_handoff.asm` rejects same-UART ownership transfers,
`hook_apply_bridge.asm` admits only IRQ3/4, and `script_launch.asm` plus the child
`serial_backend.asm` assume the standard COM IRQ. The current ASIO descriptor
does not carry a selected IRQ. The recovered ISR acknowledges only the master
PIC. Keep this limitation explicit until configuration, parent/child ownership,
saved vectors/masks, refusal paths and actual UART traffic are tested together.
The Boca model/jumper settings and physical adapter tests remain outstanding.
