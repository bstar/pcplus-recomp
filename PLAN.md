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

Live receive integration now adds Alt-R XMODEM CRC/checksum128/1024 with
checked DOS staging and final ACK after installation. The full-sized shadow and
history arrays move far while the receiver arena stays near; PROGRAM retains
both static extents. Alt-S also supports ordinary XMODEM/1K uploads through
checked read-only DOS sources and actual-ACK progress. F2 selects maintained
CRC YMODEM batch receive/send with checked per-file ownership and exact declared
lengths. Alt-F1/F2 text capture now uses the native logger, a checked DOS append
owner and serviced prompt; see `docs/LIVE_CAPTURE.md`. Alt-G appends a frozen
80x25 screen to PCPLUS.SCR through an independent checked owner; see
`docs/LIVE_SNAPSHOT.md`. Ctrl-backslash now opens a serviced raw monitor with
explicit binaryDMP replacement through a third checked owner; see
`docs/LIVE_MONITOR.md`. Physical modem and
remaining protocol/application gates remain open. See
`docs/TRANSFER_INTEGRATION.md` and `docs/LIVE_UPLOAD.md` for ownership and evidence.

The first source-only interactive `TERMINAL.EXE` connects the recovered UART,
keyboard, parser and display engine. Its synthetic DOSBox-X tests verify actual
video memory, DSR replies, both DECCKM arrow modes, stalled/partial input and
Alt-X cleanup, including independent before/after UART/PIC/vector snapshots.
Command options validate COM1..4, baud, line format and flow control before
touching hardware. Real Synchronet and Mystic login/navigation tests exposed a
missing form-feed handler; deeper ENiGMA½ testing exposed SOH/VT/CAN controls in
a malformed stock theme's metadata. Those handlers are now recovered and tested;
the source-owned defaults select the proved original ANSI profile. Earlier
checkpoints passed all three local servers through login and menu navigation through a modeled Hayes/Telnet
modem; Mystic also passes indexed-screen arrows and Escape return. The historical
036a8092 checkpoint passes Synchronet/Mystic menus and Synchronet FSEditor.
ENiGMA login-matrix arrows and message/file menus pass with the paced retry;
the initial schedule's incomplete menu workflow is retained with its failed audit. Its real editor
still fails Home/Insert despite correct outgoing bytes (docs/validation/bbs-matrix.json
and bbs-editors.json). An explicit byte-transparent modem packet-buffering
experiment is tracked separately in `lab/bbs/packetization.md`: Home/Insert pass
with30ms grouping and fail again in the immediate control on the same9d90aa1a
DOS build. It does not replace the immediate-bridge failure or establish physical
modem compatibility. An
isolated maintained-source snapshot builds the identical interactive executable
with no original executables or installation present. These tests do not establish
physical modem compatibility or close the remaining application gates below.

- [x] Combine the source driver, parser, screen and keyboard into a DOS terminal.
      Native keyboard integration now includes all79 recovered raw binding slots,
      maintained network defaults, strict explicit `/K` import and `/B` automatic
      BDA/manual BIOS selection. Low-E0 keypad aliases are maintained compatibility
      behavior. Ten actual DOS key cases and95 linked inputs pass.
      Global /T KEY import supports nonblocking TEXT and maintained PROGRAM
      command-processor execution with bounded UART/child handoff. ASPECT/HOOK,
      original PROGRAM heap/UI services, directory bindings, historical defaults
      and physical BIOS testing remain open. ESC c restores captured startup
      state for profiles 4/6 through a maintained RAM-only policy; the native
      nonzero reset KEY/profile-loading pipeline remains unresolved.
      Recovered line helpers are live through `/A:NETWORK` bounded line editing
      or `/A:ORIGINAL` serviced36-tick discard wait. Eight synthetic policy groups
      pass; complex attribute repair remains an explicit2d98 boundary and full
      editor interaction requires separate runtime evidence.
- [ ] Support dialing/connect/hang-up and configurable serial/modem settings.
      Progress: explicit read-only PRM import now validates serial/flow/profile and
      display settings before UART access, with tested CLI precedence. The
      maintained live controller now initializes/dials an explicit target,
      cancels, times out, hangs up and applies response/autobaud decisions through
      actual UART code. BIOS midnight, flow stalls and first-banner preservation
      are tested. Directory selection/browser now applies entry settings and
      supports MODEM/DIRECT plus explicit literal/legacy targets. Native record
      editing uses staged save; successful-call accounting persists after UART
      restoration. Passwords remain metadata and are never automatically sent;
      unsupported SCRIPT/KEY/META bindings still fail before hardware access.
      Directory-driven cycles, full modem policy and settings UI remain open.
      Preserve the full
      settings/directory/UI/transfer/script/Host scope below.
- [ ] Capture representative BBS sessions and verify interaction, display and transfers.
      Progress: frozen036a actual DOS XMODEM-1K/CRC uploads and downloads pass on
      both Synchronet and ENiGMA½, including exact padded bytes, official server
      metadata, post-transfer menu interaction and hardware/config restoration.
      ENiGMA uses an explicitly documented single-file lab protocol configuration.
      The first harness failure remains retained; full-screen editor failures,
      other protocols and physical modem validation remain open. See
      `lab/bbs/transfers.md` and `docs/validation/bbs-transfers.json`.
      Later2dafc08b YMODEM checks pass current selected upload/download workflows
      on both servers, including ENiGMA two-file batches and post-transfer menus.
      Both upload helpers omit the final empty-header ACK: exact installed files
      and compatible menu handoff pass, while standard final ACK is explicitly
      false. The terminal preserves the first application byte and shows an
      unconfirmed-batch notice. Historical failed attempts remain recorded in
      `docs/validation/bbs-ymodem.json`. The6b69f9b0 capture checkpoint repeats
      actual editors: Synchronet passes, ENiGMA still fails Home/Insert with
      correct wire bytes. No server decoder/coalescing fix is claimed.
- [ ] Validate on the actual modem and failing BBS/key sequence supplied by the user.

## 4. Remaining application reconstruction

- [x] Inventory advertised original features/resources and define an initial
      16-gate completeness matrix in `docs/FEATURES.md`; continue auditing for
      additional features as native tracing proceeds.
- [ ] Recover startup, memory/overlay behavior and application services.
      Progress: `docs/FAR_CODE.md` establishes one static far-code module with
      seven resident entry interfaces,15 service bridges and an explicit PRN
      stack-argument adapter. MZ/map guards verify22 bridge pairs, distinct CS,
      relocations and PROGRAM retention. It frees1,232 resident code bytes;
      near data/stack remains64,368 bytes. Actual DOS allocation/fill preserves
      far-code samples and parent operation. The bdeb347c checkpoint passes
      all36 terminal regression commands,14 dedicated-print DOS cases and23
      linked YMODEM inputs; a fresh source-only checkout reproduces57 outputs.
      Dynamic overlays, broader code/data
      migration, resource startup and complete F01 coverage remain open.
      Private browser/editor/PROGRAM screens now move to a distinct far UI
      group, retaining three4000-byte owners and their formats. Shared
      data/stack falls to52,368 bytes with13,168 available. Builder guards check
      extents, nonaliasing and relocated segment words; PROGRAM retains every
      frame end. Actual DOS child allocation/fill preserves all three samples.
      The8b38144e checkpoint passes37 terminal commands,11 standalone UI DOS
      cases and14 dedicated-print DOS cases. Six linked UI groups/2031 inputs,
      including eight malformed-layout rejections, cover private ownership/bounds;
      source-only rebuilding reproduces57 outputs. BBS editor results retain
      their separate bdeb347c identity.
      See `docs/UI_FAR_STORAGE.md` for source and verification boundaries.
- [ ] Reconstruct configuration persistence, dialing directory and application UI.
      Progress: original-code replay proves the 1,264-byte PRM load/save block
      and ten-byte serial prefix; a partial lossless host codec preserves unknown
      fields and validates proved serial settings with synthetic tests. A
      maintained DOS backend also passes strict load/save and failure-path
      tests. A staged DOS replacement backend now preserves the prior file on
      tested write/install failures and reports rollback/cleanup recovery state.
      A lossless host directory codec now covers the proved200-record format;
      a DOS streaming selection/page reader and native startup browser now
      connect supported entries. Native staged record editing and expected-record
      replacement preserve other directory bytes and expose recovery failures.
      Successful-call date/count updates accumulate in RAM and flush after UART
      restoration; the maintained patch fixes the original year2000 counter-byte
      overwrite. Exit9 reports accounting save trouble unless a prior error
      exists. Complete original directory commands, automatic restart recovery,
      automation/key bindings and selection cycles remain open. See
      `docs/DIRECTORY_EDITING.md` and `docs/DIRECTORY_ACCOUNTING.md`.
      PRM modem fields and the original caret decoder are also mapped/tested.
      Original window snapshots and flow-message services are recovered and
      linked into the terminal. DOS C status returns are verified from an
      assembly-owned startup. Complete defaults/schema, restart recovery,
      full settings/original directory UI and complete modem policy remain open. The response matcher and dial-attempt
      instructions are recovered; only the bounded matcher diagnostic is linked,
      with full-attempt service dependencies still explicit. The original
      sender/calibrated/BIOS-delay routines also have exact source and a real-UART
      DOS diagnostic, distinct from the maintained nonblocking live controller.
      See `docs/CONFIGURATION.md`.
- [ ] Reconstruct file transfers, capture/logging and supporting tools used by the app.
      Progress: native protocol routing, CRC/framing and packet validation are
      source-built. Native sender adds1,240 exact bytes; CRT/receiver file paths
      add1,657; session owner/context/handshake adds1,027; transfer UART helpers
      reuse the resident core with90 exact clock/header bytes. One continuous
      native ordinary receiver now composes handshake, repeated blocks, retries,
      real setjmp/longjmp and EOT. Source tests cover CRC/checksum, mixed block
      sizes, duplicate/retry/cancel paths and explicit metadata boundaries.
      Maintained streaming DOS storage checks exact writes and close before
      exclusive target installation. A real-DOS composition proves periodic/final
      output, final short-write/close failure gates, cancellation/timeout cleanup,
      and79x128+1024 at the flush threshold. Its UART/time remain peer fixtures;
      a separate real-UART DOS test sends1,024 exact binary bytes.
      Native final EOT write/close results are ignored; the maintained owner
      independently gates installation. Live Alt-R now connects the real UART and
      filename/progress UI, services bounded waits/cancellation and suppresses
      the final ACK until checked installation. HARD/NONE binary reception and
      actual DOS owned-peer tests are documented in TRANSFER_INTEGRATION.md.
      Alt-S now connects the native ordinary sender to checked read-only DOS sources,
      bounded live UART callbacks and actual-ACK progress. Native batch metadata
      now adds 1,140 exact bytes, with 127 original comparisons and an actual
      8086 DOS diagnostic. A maintained bounded codec distinguishes unknown/zero
      length, parses optional metadata and rejects unsafe filenames; 1,611 host
      checks and 221 DOS checks pass. Checked batch upload/download owners and
      maintained live CRC YMODEM now add per-file storage, safe enumeration,
      exact lengths and truthful final-ACK policy. Thirty actual DOS protocol
      cases and linked kernel-failure/UART tests also pass on6b69f9b0 after
      capture/serial-poll integration. BBS transfer workflows retain their
      separately recorded2dafc08b identity; current6b69 editor tests do not
      substitute for repeating BBS transfers. See
      `docs/LIVE_YMODEM.md` and `docs/TRANSFER_METADATA.md`. Other protocol
      families, full settings/UI, physical peers and F09 remain open.
      See `docs/TRANSFER_SESSION.md`, `docs/DOWNLOAD_STORAGE.md`,
      `docs/TRANSFER_SEND.md`, `docs/TRANSFER_FILES.md`, `docs/TRANSFER_UART.md`.
      `docs/TRANSFER_INTEGRATION.md` records the implemented far-shadow/history
      relocation, PROGRAM retention floor and serviced binary-UART owner.
      LIVE_UPLOAD.md adds ordinary source-file uploads through the native sender
      and checked read-only DOS source ownership; remaining protocol families,
      capture/logging and application gates stay open.
      Text capture now has a native REA inventory and maintained live owner:
      Alt-F1 append/create/close, Alt-F2 hold/resume, Alt-F3 native CR-adds-LF,
      checked writes/closes, partial-file retention and failure-aware shutdown.
      DOS PROGRAM closes capture before child execution; transfers flush the
      pending text and exclude protocol bytes. Sixty-six DOS sink cases,
      134 session assertions, 24 linked logger/PROGRAM inputs and11 selected
      actual UART/DOS/UI cases pass on6b69f9b0. The initial readonly-denial
      shutdown bug and two fixture/oracle failures remain in the evidence.
      The fd68875e checkpoint adds Alt-G screen append using381 recovered native
      bytes and a private2000-byte far image. Its69 backend cases,134 capture
      session assertions,60 owner assertions,31 linked snapshot inputs and
      11 actual DOS snapshot cases pass; the11 DOS capture cases also pass again.
      Canonical DOS paths prevent the two owners from opening the same file.
      Native recovery passes24 original-instruction comparisons and an8086 DOS
      diagnostic. A linked negative exposed an unbounded CGA notice-rendering
      wait; unsupported CGA geometry now returns without entering that path.
      Synchronet's current full-screen editor probe passes; ENiGMA still fails
      Home/Insert despite correct outgoing bytes. Those failures remain visible.
      Native printer recovery now adds79 exact bytes and reuses the132-byte
      logger. Sixty-six CPU/original comparisons and an actual8086 DOS memory-CRT
      diagnostic pass; native ignored errors remain explicit, not live policy.
      The Ctrl-backslash raw-monitor and binaryDMP route is now mapped from
      retained REA assembly, including byte transformations and modal ownership.
      See `docs/PRINTER_NATIVE.md` and `docs/RAW_MONITOR_NATIVE.md`.
      The9d90aa1a checkpoint implements live Ctrl-backslash monitor with optional
      binaryDMP replacement, native character rendering, serviced prompt/cancel,
      bounded buffering and a third canonical-path checked file owner. Its15
      selected actual DOS cases pass; the initial configured-attribute oracle
      failure remains retained. Nine linked groups cover all256 bytes, UART mask/
      software flow,18-tick flushing, ownership and storage failures. The third
      owner adds160 assertions while69/134/60 existing backend/session/owner
      assertions remain green. Eleven actual DOS capture and11 snapshot cases
      pass again, as does the32-command terminal target. Native monitor recovery
      adds503 exact bytes,27 original comparisons and an8086 DOS diagnostic.
      Current Synchronet editing passes; ENiGMA immediate Home/Insert still fail.
      See `docs/LIVE_MONITOR.md` and `docs/validation/terminal-monitor-dos.json`.
      The f2c75bf7 checkpoint adds Alt-L processed printer copy with the native
      logger, a checked fixed-PRN device owner and128-byte queue. Main RX dequeue
      reserves two queue slots;16-write polling and18-full-tick no-progress
      bounds keep busy devices serviced. PROGRAM waits for a checked close;
      transfer entry waits for queued text without logging protocol bytes.
      Eleven linked groups/293 inputs and nine actual DOS virtual-PRN cases pass.
      The backend adds57 fault assertions; native screen/media printing adds365
      exact bytes and38 CPU/original comparisons as a separate diagnostic.
      The33-command terminal regression and23 linked YMODEM inputs also pass.
      See `docs/LIVE_PRINTER.md` and `docs/PRINT_SCREEN_NATIVE.md`.
      The d4cfa4dc checkpoint adds serviced screen printing via incoming CSI0/1
      and private4/5, using native mode18/19 state and an immutable2000-byte
      far character frame. It preserves active printer copy or closes its own
      temporary PRN, queues FF before close, defers ordinary local keys and
      supports Escape/Alt-X. Nine linked groups/2037 inputs,11 actual DOS
      screen-print cases and3 stream-copy regressions pass; the34-command
      terminal target and23 linked YMODEM inputs also pass. Native CEAC is now correctly identified as the transient private-prefix flag.
      See `docs/LIVE_SCREEN_PRINT.md` and `docs/SCREEN_PRINT_POLICY.md`.
      The dedicated native controller now adds416 exact bytes,28 CPU/original
      comparisons and an actual8086 DOS diagnostic. Its raw-byte filtering,
      buffered escape grammar, unchecked CRT errors and unbounded wait are
      preserved as evidence in `docs/PRINT_CONTROLLER_NATIVE.md`.
      Maintained CSI5i dedicated mode now uses a bounded32-byte prefix,
      checked PRN ownership and serviced modal polling. Literal raw output
      bypasses rendering/capture; double Escape cancels after sending the first.
      Connected-on-entry state closes the carrier-loss-before-first-poll race.
      Fourteen actual DOS cases and11 linked groups/300 inputs pass on51b94da6;
      all35 terminal commands and23 linked YMODEM inputs pass. Synchronet
      passes12 editor behavior checks; ENiGMA still fails Home/Insert with
      immediate forwarding and passes7 checks with explicit30ms buffering.
      See `docs/LIVE_PRINT_CONTROLLER.md` and
      `lab/bbs/modern-compatibility.md` for current hash-bound validation.
      Full F10 still requires a proved local screen-print binding,
      remaining snapshot/monitor geometry,
      complete settings/status UI, ASPECT/HOOK and physical validation. See
      `docs/CAPTURE_NATIVE_INVENTORY.md`, `docs/LIVE_CAPTURE.md` and
      `docs/validation/terminal-capture-dos.json`.
      The fresh maintained-source snapshot reproduces57 byte-identical
      component/diagnostic outputs, including the current interactive executable
      and capture/owner/screen/printer/monitor diagnostics, with originals/install/REA
      databases absent. This checkpoint does not close the full application gate.
- [ ] Reconstruct scripting interfaces and required interpreter/compiler integration.
      Keyboard file structures and original TEXT caret/pause consumers are proved,
      and explicit global /T KEY import now supports bounded nonblocking TEXT.
      Maintained PROGRAM now executes stored commands through COMSPEC `/c` and a
      bounded source-owned DOS process backend, with serial/vector/video handoff.
      Current checkpoint `036a8092` linked regressions and separate actual DOS synthetic-child
      tests cover restoration and failures. Native PROGRAM has 3,102 exact bytes,
      including its EXEC/environment/PATH core, but heap and broader application
      services remain external; native reset has 2,301 exact bytes with its
      nonzero KEY/profile-loader boundary preserved. Complete ASPECT/HOOK,
      original PROGRAM integration, directory bindings and editing remain open.
      See `docs/PROGRAM_EXEC.md`, `docs/TERMINAL_RESET.md` and
      `docs/LIVE_TERMINAL_RESET.md`. Unimplemented original local keyboard
      commands stop explicitly
      with errorlevel4; unmapped/no-op keys remain ignored.
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
