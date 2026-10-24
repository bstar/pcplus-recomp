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

## Selectable ISA modem IRQ package

An optional package now joins the tested IRQ-capable parent, register interpreter
and setup editor with the magenta Special Edition splash:

```sh
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --custom-irq --output build/special-irq-package-next
```

The standard package retains standard COM IRQ mapping. `--custom-irq` selects
matching master-PIC IRQ3/4/5/7 products throughout startup, configuration,
ASPECT ownership transfer and helper return. The underlying configuration and
ownership work is documented in [parent custom IRQ checks](PARENT_CUSTOM_IRQ.md).
Physical jumper settings still need to match the selected COM/IRQ; the Boca
model and adapter acceptance remain outstanding.

The [branded IRQ receipt](validation/special-irq-package.json) verifies:

- START, nested DOS source compilation and return on IRQ5.
- Independently captured magenta splash and SETUP/cancel/return on IRQ7.
- Unchanged PRM/DIR/XLT sentinels, restored PCPLUS environment and all 42 sampled
  hardware bytes in each DOS8086 launcher workflow.
- All nine package files reproduced exactly from 719 declared source files and
  the explicit source-base identifier, with ancestor Git unavailable.
- This exact branded terminal's DOS source login, 65,539-byte plus empty upload,
  installed data/metadata/dates and subsequent NFO input on isolated framed
  ENiGMA. Fourteen damaged-capture cases reject. The temporary server is stopped.

The branded terminal SHA256 is
`413e274e826a314e7f9ec388072f763836a1d7beeea49e7b930878ce28ca7217`.
The [branded carrier-recovery checkpoint](SPECIAL_IRQ_CARRIER.md) now separately
verifies this exact package's partial download, emulated DCD loss, cleanup,
redial, second script login, exact retry and NFO return in one DOS8086 process
on IRQ5. Sixteen checks and thirteen damaged-capture controls pass. Repeated
recovery/load and physical modem acceptance remain open.

The initial package proof inherited the surrounding Git checkout to populate
VERSION.TXT. A retained control fails when ancestor Git is disabled. Packaging
now accepts `--source-base-commit`; the source checker supplies that declared
identifier and forbids discovery of ancestor Git. The strengthened proof and
launcher repeats produce the same nine payload files. Interactive packaging may
still infer the base from the current checkout when the option is omitted.

The verified host copy is
`/home/bstar/projects/DOS/staging/pcplus-special-irq-20261024/PCPLUSSE`.
It includes no local PRM, DIR or XLT files. The card remains disconnected and
has not received this package. Its existing `C:\PCPLUSSE\START.BAT` and Favorites
paths require no change when the nine verified files are installed. Back up the
existing installation, preserve all local resources, verify copied hashes and
unmount after installation. Full native application and hardware gates remain
open.
