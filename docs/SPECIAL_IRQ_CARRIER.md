# Special Edition carrier recovery

The exact branded selectable-IRQ terminal staged for the card now passes one
interrupted-download recovery in a single DOS8086 process against the isolated
framed ENiGMA fixture. The [receipt](validation/special-irq-carrier.json) binds
the captured session to all nine files of the existing Special Edition package.
No application executable or card file changed in this checkpoint.

The terminal SHA256 remains
`413e274e826a314e7f9ec388072f763836a1d7beeea49e7b930878ce28ca7217`.
The runner and compiler match the package's declared manifests. The harness
selects the branded terminal explicitly and sends a startup Enter for its
splash; the separate [package checks](SPECIAL_EDITION.md) establish magenta
splash rendering and START/SETUP behavior. This test invokes the terminal
directly and does not repeat those launcher checks.

Sixteen checks pass on COM2/IRQ5, 19200 baud and hardware flow control:

- The source-built DOS compiler produces the exact login script before terminal
  startup. Both connections authenticate through that script.
- A source-matching 4,096-byte partial receive causes the first network link to
  abort. DOSBox-X's built-in modem drops emulated DCD; PCPlus displays carrier
  loss and removes the partial staging file before reconnect.
- The same process redials and receives all 34,169 bytes exactly. Independent
  capture replay checks protocol CRCs, positions, verified replay traffic and
  receiver completion before the sender's final `OO`.
- `RX complete` is captured with no unconfirmed-finish notice. Subsequent input
  opens the NFO page; both directory connection updates, unchanged PRM and all
  42 sampled hardware bytes verify. No unrelated output file or post is saved.

Thirteen damaged-capture variants reject, including incorrect payload/CRC,
retained staging, missing carrier/completion evidence and missing NFO content.
Five fresh socket relay checks also pass. The checked server decoder export has
four passing test groups, uses synthetic users and generated archives, and
reuses installed dependencies. It does not change the LAN board or stock BBS
services. The temporary instance is stopped and its port was verified free.

## Reproduction

Prepare a fresh decoder export and search fixture with `--transfer-bytes 32768`
as in [the carrier workflow](../lab/bbs/enigma-carrier.md). The search fixture
prepares the instance itself; do not call instance `setup` separately. Start
only that owned candidate with `--private-tmp`, then run:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_carrier_dos.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_BRANDED_CARRIER \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps-custom-irq-special/TERMINAL.EXE \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --compiler build/aspect-compiler-dos/ASPCOMP.EXE \
  --cpu 8086 --irq 5 --mouse-scales 8 4 --splash-key
```

Run `check_enigma_carrier_current_audit.py` for the same candidate/label, stop
the owned instance, and use `standalone/record_irq_carrier.py` with `--package`
pointing to the matching package root, alongside the candidate, result label,
fresh relay-check label and output receipt. The recorder verifies the package
files, manifests, actual captured products, startup recipe, raw hardware and
notice records, authentication/accounting, complete traces and independent
protocol replay. The original unbranded receipt remains a separate checkpoint.

This closes one branded emulated recovery case. Repeated recovery in the same
process, sustained load, other disconnect conditions, stock ENiGMA's input
fragmentation behavior, physical Boca/SPA2102/SynthModem acceptance, card
deployment and complete application parity remain open. The BBS network-dial
syntax and `AT&K3` belong to the emulator fixture, not a verified Boca profile.
