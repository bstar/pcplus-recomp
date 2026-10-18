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
      Progress: the parameter reader, transition helper, 477-byte ESC entry and
      complete 2,018-byte CSI dispatcher are recovered exactly. The linked
      ESC-to-CSI-to-cursor/attribute path passes CPU and DOSBox-X self-checks.
      Screen erase and reporting also pass through the combined parser; full
      ESC cursor/state and position-only CSI save/restore are linked and tested.
      The independent text-output backend passes CPU and DOSBox checks;
      the recovered high-level character renderer also wraps and scrolls, with
      531 operations matched against the original. Scroll/index and mode
      handlers, keyboard-mode/tab/reset helpers and BIOS cursor-shape routines
      now pass independent and combined tests. The actual continuous input
      dispatcher, ordinary CR/LF/TAB/BS, history and guarded logging paths
      run in source-only DOS; specialized controls/sinks remain explicit gaps.
      A maintained byte-normalization guard prevents proven negative-word
      control-table indexing. See `docs/INPUT_DISPATCH.md`.
      remaining application services still prevent complete parser coverage.
      See `docs/ANSI.md`, `docs/CSI.md` and component documentation.
- [ ] Reconstruct independently buildable complete parser and keyboard modules.
      The parameter-reader and BIOS keyboard acquisition/normalization submodules
      build without original artifacts. Terminal-specific key maps remain open.
- [ ] Test cursor movement, erase/scroll, attributes, modes, terminal replies,
      split/malformed sequences, escape timing, keyboard mappings and known CSI-q fault.
- [ ] Verify complete reconstructed parser behavior against the original.
      Parameter-reader replay matches 11 ordinary cases and documents four
      deliberate bounds/timeout fixes.

## 3. Usable terminal integration

Next implementation priority: wire the recovered continuous input entry to the
real UART and keyboard in an interactive DOS executable. Replace memory byte
fixtures with a bounded receive provider, service transmit/flow/keyboard while
parsing fragmented escapes, and restore UART/vector state on every exit/error.
Use source-owned initial settings and the proved configuration subset; do not
require original install files. Validate against a synthetic BBS peer with
rendered menus, DSR replies, DECCKM arrow keys, stalled links and Alt-X cleanup.
This terminal milestone does not close the remaining application gates below.

- [ ] Combine the source driver, parser, screen and keyboard into a DOS terminal.
- [ ] Support dialing/connect/hang-up and configurable serial/modem settings.
- [ ] Capture representative BBS sessions and verify interaction, display and transfers.
- [ ] Validate on the actual modem and failing BBS/key sequence supplied by the user.

## 4. Remaining application reconstruction

- [x] Inventory advertised original features/resources and define an initial
      16-gate completeness matrix in `docs/FEATURES.md`; continue auditing for
      additional features as native tracing proceeds.
- [ ] Recover startup, memory/overlay behavior and application services.
- [ ] Reconstruct configuration persistence, dialing directory and application UI.
      Progress: original-code replay proves the 1,264-byte PRM load/save block
      and ten-byte serial prefix; a partial lossless host codec preserves unknown
      fields and validates proved serial settings with synthetic tests. A
      maintained DOS backend also passes strict load/save and failure-path
      tests. Complete defaults/schema, transactional replacement, directory
      and UI integration remain open.
      See `docs/CONFIGURATION.md`.
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
