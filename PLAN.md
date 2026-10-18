# Complete DOS rebuild plan

The goal is a maintained, source-built PCPlus application that runs in DOS and
works with the intended RS-232 Wi-Fi modem/BBS setup. A diagnostic or patched
original is an intermediate result, not completion. Public repository changes
must exclude original executables and private install/configuration data.

## 1. Serial driver — active

- [x] Recover resident UART instructions with source provenance.
- [x] Link the module into an independent source-only DOS executable using Nix.
- [x] Exercise binary echo, receive-ring wrapping and XON/XOFF pause/resume in DOS.
- [x] Validate high/low watermarks, receive overflow, CTS/transmitter stalls,
      timeouts and restoration in controlled replay; fix reproduced overflow
      and unbounded foreground/ISR transmission in maintained diagnostic paths.
- [x] Expose a documented bounded transmit/flow-service API usable by the terminal application.
- [ ] Validate supported UART/port settings and the physical Wi-Fi modem.

Evidence: `docs/UART.md`, `docs/validation`, executable/map/driver results under
`build/standalone` and DOSBox results under `build/serial-tests`. Physical testing
requires an attached DOS machine/modem and must not be inferred from emulation.

## 2. ANSI parser and keyboard — active

- [ ] Recover the complete input/parser state machine and its calls/state from REA evidence.
      Progress: the 175-byte parameter reader is recovered exactly; its state,
      external calls and boundary risks are documented in `docs/ANSI.md`.
- [ ] Reconstruct independently buildable parser and keyboard modules.
- [ ] Test cursor movement, erase/scroll, attributes, modes, terminal replies,
      split/malformed sequences, escape timing, keyboard mappings and known CSI-q fault.
- [ ] Verify reconstructed behavior against the original and document deliberate fixes.

## 3. Usable terminal integration

- [ ] Combine the source driver, parser, screen and keyboard into a DOS terminal.
- [ ] Support dialing/connect/hang-up and configurable serial/modem settings.
- [ ] Capture representative BBS sessions and verify interaction, display and transfers.
- [ ] Validate on the actual modem and failing BBS/key sequence supplied by the user.

## 4. Remaining application reconstruction

- [ ] Inventory original features/resources and define explicit completeness checks.
- [ ] Recover startup, memory/overlay behavior and application services.
- [ ] Reconstruct configuration persistence, dialing directory and application UI.
- [ ] Reconstruct file transfers, capture/logging and supporting tools used by the app.
- [ ] Reconstruct scripting interfaces and required interpreter/compiler integration.
- [ ] Recover required resources without embedding original executable code/data as
      a substitute for source reconstruction.

## 5. Complete source-only DOS application

- [ ] Build every required application module/resource from maintained source.
- [ ] Prove a clean checkout builds without original PCPlus executable/install files.
- [ ] Validate feature and regression suites on DOSBox-X and actual DOS hardware.
- [ ] Publish reproducible build/run instructions, limitations and verification evidence.
- [ ] Audit every requirement in this plan and the original feature inventory before
      marking the goal complete.

Use `./tools/build` and `./tools/build test` for the source diagnostic. Optional
compatibility targets continue to require ignored local originals. Record newly
verified work here; do not check an item based on static inference alone.
