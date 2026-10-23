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
