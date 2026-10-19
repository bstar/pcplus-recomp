# Complete DOS rebuild plan

The goal is a maintained, source-built PCPlus application that runs in DOS and
works with the intended RS-232 Wi-Fi modem/BBS setup. A diagnostic or patched
original is an intermediate result, not completion. Public repository changes
must exclude original executables and private install/configuration data.

## Current application work

The maintained terminal now includes directory editing/accounting, live settings
with confirmed idle serial/profile/translation changes, XMODEM/YMODEM/ZMODEM transfers,
capture/snapshots/printer/monitor and serviced63,000-character redisplay with
incremental search, serviced append/CRLF history export and a filename clipboard
with checked one/all/tagged serial output. Alt-Z adds a source-owned command menu,
contextual help, bounded topic search and parser-safe deferred entry. All sixteen whole-application gates in `docs/FEATURES.md`
remain open. The numbered sections below retain earlier component evidence and
historical checkpoints; their old run counts are not the current binary identity.

The remaining work includes complete clipboard UI and wider stock BBS transfer-prompt workflows,
complete original menus/mouse paths
and full settings/key editing; other terminal emulations and font/resource
paths; remaining transfer families/external helpers; complete directory cycles
and bindings; ASPECT compiler/interpreter/recorder; Host mode and storage; complete
startup/schema/default generation, packaging and target hardware validation.
Modern BBS interaction and independent source-only rebuilding remain required
regressions across that work. Physical Wi-Fi modem testing is still outstanding.

ZMODEM now has live Alt-R/Alt-S/F2 dispatch, CONFIG_CODE placement, ten verified
far callbacks, checked source seek/skip, exact variable receive packets and
serviced UI/UART ownership. Linked workflows and independent actual DOS lrzsz
transfers cover empty/binary/over64KiB files, CRC16 and control escaping; failed
initial large-upload fixture attempts remain explicit. Component recovery also
passes selected stock Synchronet helper tests. All64 existing source outputs
rebuild byte-identically. See `docs/LIVE_ZMODEM.md`, `docs/ZMODEM_SESSION.md` and
`docs/ZMODEM_NATIVE.md`. Logged-in stock Synchronet/ENiGMA ZMODEM workflows,
actual DOS corruption/cancel/timing coverage, windowed sending, persisted partial
resume, auto-download, broader name mapping and hardware remain required.

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

Serviced Alt-B now owns actual LCR BREAK with TEMT draining, held ordinary/flow
TX, continued receive and conservative BIOS-day timing derived from the native
startup calibration. Full modem/directory PRM plans retain01A4h, including DIRECT.
Linked and actual DOS timer/video samples cover pulse/release and early exit;
physical BREAK timing and modem behavior remain open. See `docs/LIVE_BREAK.md`.

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
      source-only rebuilding reproduces57 outputs. The8b38144e build also repeats actual BBS editors: Synchronet passes;
      ENiGMA immediate Home/Insert failures persist, while explicit30ms modem
      buffering passes the paired checks. Later runtime identities remain
      separate in the hash-bound reports.
      See `docs/UI_FAR_STORAGE.md` for source and verification boundaries.
      The modem controller/sender now share another static code segment with
      eight near public entries, ten namespaced register callbacks and four
      explicit1..4-word caller-cleaned adapters. Resident CODE falls to62,306
      bytes, leaving3,230; DATA/STACK remains52,384. Build guards validate44
      bridge pairs and disjoint CS ranges. Actual linked ABI/error/IRQ tests
      and a56-byte DOS child sample cover modem code retention alongside the
      existing printer/native/UI owners. See `docs/MODEM_FAR_CODE.md`.
      Full dynamic overlays, startup, settings/UI and F01 remain open.
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


## Current offline setup component

`PRMEDIT.EXE` now provides five DOS pages covering the44 mapped settings, typed
validation, lossless staging, explicit malformed-field repair and checked save
ownership. See `docs/SETUP_EDITOR.md` and `docs/SETUP_NATIVE.md`. Source-only Nix
build, DOS filesystem/keyboard/video and independent field-model evidence cover
this component. F02/F06 remain open for complete menus/help/schema/defaults,
path/environment precedence, live terminal integration and the original missing
PCSETUP child consumer. Offline editing does not close the full application goal.

The current isolated checkout reproduces58 byte-identical outputs, including
PRMEDIT. Its model passes383 synthetic inputs in8 groups;10 real-DOS workflow
groups include39 document-owner assertions, production save and independently
checked video restoration. These counts are component evidence, not closure of
any full-application feature gate.


The terminal now offers `/S @PCPLUS.PRM` to run the maintained editor before
connection. Direct child execution precedes configuration import and UART
acquisition; process/child failures stop startup, and successful return preserves
normal validation and CLI-category overrides. See `docs/SETUP_STARTUP.md`.
Live setup during a connection and complete PCSETUP reconstruction remain open.

This setup-startup checkpoint passes47 linked scheduler inputs,585 CLI parser
inputs,12 DOS setup workflows and all43 terminal regression commands. A fresh
checkout reproduces58 identical outputs. Modern editor reruns retain Synchronet
success and ENiGMA immediate Home/Insert failure versus the30ms-buffered pass;
login new-scan prerequisite failures and the explicit-decline retry remain in
history. See `docs/validation/setup-startup.json` and the BBS checkpoint reports.


Live setup now has a pure candidate transaction and a shared pure directory
decoder. It validates a retained selection plus PRM, applies CLI precedence and
classifies transport/profile/display/modem/target changes before any runtime
commit. See `docs/LIVE_CONFIGURATION_PLAN.md`. The running-terminal UI, hardware
handoff, parser/reset-baseline update and commit/rollback policy remain open;
this component does not close F02/F06 or claim live setup is available.

This candidate checkpoint passes389 pure API inputs,311 existing directory
inputs and all43 terminal regression commands;59 isolated outputs match. The
candidate API remains diagnostic-only. At that checkpoint the parent lacked the full250-byte header, motivating the
retained-context integration below.


Directory context retention is now integrated into startup:496-byte raw selected
header/record, entry/code mode and original request paths, published only after
successful decoding. Logical identity checks, failure rollback and independent
actual DOS PROGRAM-child allocation/fill cover retention. See
`docs/DIRECTORY_CONTEXT.md`. Canonical namespace ownership, active-generation
binding, live editor UI and serial/profile commit remain open.

The retention checkpoint passes507 linked context inputs,24 actual DOS
file/accounting assertions, an actual terminal PROGRAM-child context/allocation
check and all45 terminal regression commands. The candidate still passes389
inputs; a fresh checkout reproduces60 identical outputs. Live setup/commit and
canonical namespace/generation ownership remain explicit subsequent work.


Serviced redisplay now adds the advertised63,000-byte history capacity, a frozen
chronological view, local Ctrl-PgUp navigation and ASCII case-insensitive
incremental search/F3. Input, native capture/history and terminal replies continue
while browsing; Escape restores the updated live screen. Independent actual DOS
video/timer and peer evidence complements the linked native writer/viewer checks.
See `docs/LIVE_REDISPLAY.md`. At that checkpoint, history export, filename clipboard and full F11
remain open; no whole application gate is closed by this checkpoint.

### PROGRAM policy segmentation

The maintained PROGRAM command processor policy now runs in CONFIG_CODE with
a two-word near-cdecl public entry and a three-word resident DOS EXEC callback.
This frees1,114 resident code bytes (64,288 used,1,248 spare) without changing
DOS command handling. Near data/stack stays61,712 bytes. The expanded ABI checks
validate33 configuration bridge pairs,81 total, and164 damaged frames/layouts.
This is preparation for the remaining history export/clipboard work; all sixteen
whole-application feature gates remain open.

### Serviced frozen-history append

W in redisplay appends the frozen chronological snapshot, expands CR to CRLF
and exclusively creates a missing file. A fourth checked file owner excludes
capture/snapshot/monitor aliases, retains partial-write evidence and ambiguous
close state, and blocks child inheritance while unresolved.128-source-byte
foreground chunks keep receive/keyboard service between writes. Verification
combines27 linked inputs, three actual DOS workflows,167 ABI mutations,70 terminal
commands and63 reproducible Nix outputs. Filename clipboard/full redisplay UI,
other geometry and physical validation remain open; all F01–F16 gates remain open.


### Maintained filename clipboard integration

Alt-= and redisplay C now share the frozen/live frame owner with a15-entry
clipboard. The bounded core preserves recovered add/edit/empty-entry behavior,
name extraction and one/all/tagged packet bytes. The serviced resident transport
admits whole packets on an empty TX ring, removes Single only after actual UART
writes, cancels only its unsent prefix and treats connection queue discard as
failure. Linked46 inputs and two independent actual DOS workflows pass; the
source-only core passes614 linked inputs,321 optional original comparisons and
559 actual DOS assertions. See `docs/FILENAME_CLIPBOARD.md`.

The75-command terminal regression and64-output fresh-source proof pass for
this runtime. Saved separator/Setup adoption, complete original
clipboard UI, transfer-prompt workflows, other geometries and physical hardware
remain open. No F01–F16 gate is closed by this component.

The clipboard checkpoint's stock editor rechecks pass Synchronet's12 behavior
and8 wire checks. ENiGMA immediate forwarding retains its Home/Insert failures;
the explicit30ms control passes7 behavior/8 wire checks, with no post saved.
The first Synchronet run was rejected by the synthetic account's daily quota;
its temporary retry-only logon exemption was restored and independently read
back. Reports retain that failed prerequisite rather than calling it a pass.


### Saved clipboard separator

The maintained importer validates PRM04EA as0..255. PRMEDIT adds its46th field,
and startup/live setup apply the same value. A separate accepted-source baseline
keeps session R across canceled/no-op/unrelated saves and recognizes explicit
saved reverts after acknowledgement. The serial ABI is explicitly44 bytes and
the candidate628; all existing offsets before the appended field remain stable.
805 linked inputs,7 production DOS workflows and14 codec units pass. The expanded
77-command application regression and64-output clean-source proof pass. See `docs/CLIPBOARD_SETTINGS.md`. Original menu parity, transfer-prompt
workflows, other geometries, physical UART/modem and all F01–F16 gates remain open.

Stock editor rechecks pass Synchronet12/eight wire and ENiGMA buffered seven/eight
wire; immediate ENiGMA retains Home/Insert failures. The first buffered run missed
editor entry after timed-login misalignment; its unchanged-input retry passes,
and both attempts remain explicit. The synthetic Synchronet account exemption
was restored and independently verified. All whole-application gates remain open.

### Clipboard selection across transfers

Six actual DOS workflows now carry Single/Tagged/All filename packets through
strict independent XMODEM/YMODEM peers, verify exact download bytes and unchanged
upload sources, and reuse retained clipboard entries afterward. Stale remote
filenames and local filename-prompt cancellation recover before a subsequent
successful receive. External BIOS key/video observers verify transfer keyboard
ownership, nested-command exclusion and the empty-list notice. See
`docs/CLIPBOARD_TRANSFERS.md` and `docs/validation/clipboard-transfers.json`.
This adds test evidence without changing the runtime already covered by the
77-command regression and64-output source rebuild. Wider stock BBS prompt integration,
original UI parity, other geometries and physical hardware remain open; none of
F01–F16 is closed by these selected workflows.

Selected stock-server Single/download workflows also pass: Synchronet Filespec
clipboard selection followed by XMODEM, and ENiGMA filename search followed by
YMODEM and a second clipboard search after completion. Passive wire replay, exact
DOS bytes, official source-file metadata and ordered server/menu evidence bind
these to the same runtime. The Synchronet synthetic-account logon exemption was
restored and independently read back. Four failed ENiGMA fixture attempts remain
in the report; the latest two selected server workflows pass, while the aggregate
attempt history remains false. Stock-server uploads/multi-name conventions,
original UI parity and physical modem validation remain open.

### Maintained command menu and contextual help

Alt-Z now opens five command groups with18 entries, source-owned contextual help,
topic navigation and bounded ASCII prose search. Selected commands close the
shared redisplay frame before normal dispatch; history and clipboard reacquire
their existing guards. Incoming UART/parser/history/capture/replies continue.
The menu implementation and code-based text/table reside in CONFIG_CODE, adding
only48 bytes of near state. Resident code and85 bridge pairs remain unchanged.
Five linked groups/149 declared inputs and three production DOS observer/file/
PRMEDIT workflows pass. The isolated Nix build reproduces 64 byte-identical
outputs. See `docs/COMMAND_MENU.md`. Original layout, mouse paths, full settings/
key editing and other geometries remain open; F02 and all other whole-application
gates remain open.

The frozen menu runtime passes the77-command application regression and selected
stock menu-to-clipboard XMODEM/YMODEM downloads, including ENiGMA's second search.
An early Synchronet menu-acquisition failure is retained alongside its settled
retry; its exact transient refusal is unresolved. Stock editor rechecks pass
Synchronet and buffered ENiGMA while immediate ENiGMA still fails Home/Insert.
All synthetic logon exemptions were restored and independently read back.

### Parser-safe command entry

A controlled DOS split-CSI case reproduced parser-busy Alt-Z refusal on the
earlier c0d64834 build. The maintained request now waits for a foreground poll,
rechecks all guards and replays the existing32-word typeahead FIFO locally.
Repeated Alt-Z coalesces; Escape cancels locally and Alt-X/Alt-H retain their
ordinary paths. Late failure/stop discards owned typeahead without touching UART
replies.36 linked inputs and a fourth independent timer/video/peer DOS workflow
cover this behavior. The read-only guard diagnostic separately authenticates
the old compiled inputs against ebe18b1. Its instrumented stock attempt passed,
so it does not establish the cause of the earlier isolated BBS refusal. See
`docs/MENU_PENDING.md`; no whole-application gate is closed.

The parser-safe checkpoint passes all77 terminal regression commands, reproduces
64 source-only outputs and passes selected stock menu-to-clipboard downloads on
both servers. Synchronet uses the original1500ms acquisition interval. ENiGMA's
first post-transfer search was interrupted by its stock ten-download achievement;
the exact file and protocol checks pass, but that workflow remains failed. The
same keyboard recipe in a fresh session passes, with both attempts retained.
Synchronet editor checks pass; immediate ENiGMA still fails Home/Insert and the
explicit30ms packet-buffering experiment passes. No post was saved.

### Explicit same-table reload

Alt-F9 and Setup/Reload input table now use the existing drained PROGRAM UART
owner without launching a child. Startup and confirmed mode adoption retain the
actual canonical selected table source; reload cannot be redirected by later
CWD/environment changes or a newly appearing higher-priority file. Exact checked
staging precedes Y/N acceptance; decline/read/size/close/late-owner failure keeps
the active table. Queued raw input uses an accepted table after return. Capture
closes according to the existing foreground handoff policy. Canonical paths must
fit63 bytes; ordinary startup retains lazy environment lookup and original
missing-file-only fallback precedence. See `docs/TRANSLATION_RELOAD.md`.

The dedicated suite passes66 linked inputs and eleven production DOS workflows,
including real PROGRAM/DOS COPY or DEL, menu entry, default/environment/explicit
sources and unchanged PRM/source-file checks. Two new cdecl entry pairs bring
configuration bridges to38,87 total, with187 damaged frames/layouts rejected.
Near data/stack is64,480 bytes and resident code65,298; retained parent including
PSP is314,736. The corrected build passes the77-command application regression and reproduces
64 source-only outputs. Its66 linked reload inputs also pass in the isolated
source checkout without original/install/analysis inputs. Dedicated live XLTEDIT invocation, full settings/key editing,
other terminal emulations, remaining protocols, ASPECT, Host, packaging and target
hardware validation remain open; no whole-application gate is closed.

Final reload review reproduced an early-answer bug in linked code and actual DOS
with a controlled SOFT pause: Y was deferred while output drained, but a BIOS-only
prompt consumed the next character and later leaked Y. Reload confirmation and
failure acknowledgement now consume the existing foreground FIFO before BIOS.
Following keys stay ordered and AX0 remains a real key. The corrected build passes
the identical DOS recipe and66 linked inputs; the full eleven-case DOS suite,
77-command regression and64-output clean rebuild all pass for it.

The final reload runtime also passes stock Synchronet editor checks and both
selected menu-to-clipboard downloads, including ENiGMA post-transfer search.
Immediate ENiGMA Home/Insert failures remain; the paired explicit30ms buffering
experiment passes. Temporary synthetic Synchronet logon exemptions were restored
and independently read back. No message was saved. Resident CS has238 bytes
spare, so further resident features require extending the existing far-code
placement work. The full application/hardware checklist remains open.

### Resident code capacity for remaining application work

The maintained YMODEM engine and header codec now occupy CONFIG_CODE with four
explicit near entry pairs and eighteen resident callbacks. Their C protocol
sources are unchanged from `245e681`. Source-owned adapters include distinct
zero-argument callbacks and local Watcom DWORD arithmetic thunks; a checked
build step changes only global import names in the freshly compiled OMF object.
See `docs/YMODEM_FAR_CODE.md` for the contracts and transformation boundary.

The `18b99f97` build frees3,328 resident code bytes, leaving3,566 available.
Near data/stack stays64,480 bytes. Retained parent memory including PSP grows
by464 bytes to315,200; this creates segment capacity rather than reducing total
RAM. There are60 configuration bridge pairs and109 total. The focused suite
passes413 linked inputs and269 malformed-image rejections. A fresh checkout
reproduces 64 outputs; its413 linked migration checks use no historical build
artifacts, original executables or installation data. The baseline's297 compiled
input hashes are independently authenticated against the published source commit.

The77-command terminal regression and all30 independent actual DOS YMODEM
recipes pass. The hash-bound report is `docs/validation/ymodem-far-code.json`.
Four actual DOS menu cases, six clipboard/transfer workflows, eleven table
reload workflows and the controlled parser-split menu probe also pass. The same
executable passes selected menu/clipboard downloads on both stock servers,
including ENiGMA post-download search. Synchronet editor checks pass. Immediate
ENiGMA Home still fails while Insert passes in this run; the explicit30ms
buffered experiment passes both. No draft was saved. The synthetic Synchronet
account's temporary logon exemption is restored and independently read back.
Dedicated live XLTEDIT is the next application action enabled by
this capacity. Its current offline editor accepts only an8.3 leaf, whereas live
selection remembers an absolute path up to63 bytes, including an environment
fallback. Integration must preserve that actual selected source and same-parent
replacement/recovery ownership, retain the existing drained UART/EXEC handoff,
and offer checked acceptance after return. Merely opening a current-directory
file with the same leaf would edit the wrong table for valid fallback sources.
The complete feature gates, remaining terminal emulations,
protocols, ASPECT, Host, packaging and physical target validation remain open.

### Direct selected-table editor

Alt-F8 and Setup/Edit input table now run the maintained XLTEDIT child for the
frozen selected table. The helper is located beside the launching executable
through a bounded DOS3+ PSP environment trailer, independent of CWD and PCPLUS.
The child receives a quoted absolute filename; file save/recovery stays in that
file's directory. The existing PROGRAM UART/IRQ owner drains before execution,
quiets child state and restores readable text mode before a separate checked
snapshot/Y confirmation. Failed execution, nonzero child exit, failed reads,
decline and late ownership changes retain the active mapping. The PRM image,
mode/enabled flag and driver mask are unchanged. See `docs/TRANSLATION_EDIT.md`.

The offline document now accepts DOS8.3 leaves or absolute paths up to63 bytes,
including CP437 bytes. Both recovery filenames are siblings of that target;
separate buffers cover a73-byte recovery path for a short leaf at the target
limit. Existing baseline, exclusive creation, no-overwrite installation,
rollback and retained-recovery behavior remain enforced.

The `61db3a61` application passes55 linked action/builder inputs and eight actual
production DOS editor workflows: accept/decline, discard, environment/explicit
sources, changed CWD, menu entry and absent helper. An isolated original-free
checkout passes the same55 linked inputs. The offline suite passes22 DOS cases,
including293 filesystem assertions,931 fault assertions and87 path/trailer
assertions. All77 terminal regression commands pass and64 outputs reproduce
byte for byte. One new three-word configuration entry brings the bridges to61
configuration/110 total;276 damaged frames/layouts reject.

The action adds240 near bytes and252 resident code bytes relative to `4a1295a`.
Near data/stack is64,720 bytes, resident code62,222 and retained parent317,136
including PSP. The new component report verifies all eight exact saved PRMs as
unchanged. The four existing DOS menu workflows, six clipboard/transfer workflows,
eleven explicit reload workflows and parser-split menu probe pass. Selected
stock downloads pass on Synchronet and ENiGMA, including post-download search.
Synchronet editor semantics pass; immediate ENiGMA Home/Insert still fail while
the separate30ms buffering experiment passes. No post was saved, and the
synthetic logon exemption was restored and independently read back.
The full application gates remain open, including complete settings/key editing,
other emulations/protocols, ASPECT, Host, packaging and physical target testing.


## 8 KiB reception and logged-in ZMODEM checkpoint

The `d0274a22` runtime accepts 8 KiB packets within the existing exclusive arena
by sharing receive and response storage. Baud-dependent accepted-progress budgets
allow worst-case quoting; missing final OO has an explicit unconfirmed footer.
Both directions pass actual DOS logged-in local Synchronet and ENiGMA workflows,
with exact files, independent wire/control audits, official metadata and later
menu interaction. ENiGMA uses its inherited stock `-telnet -8 sz/rz` helper.
Its path and selector-first fixture are recorded; fragmented-arrow selection
remains unresolved. Five failed attempts remain distinct from five successes.

The current binary passes71 linked workflows,10 unresolved-owner guards and325
damaged-frame/pointer rejections. Component validation passes92 scripted checks,
22 independent peer sessions and53 DOS workflows. Two additional actual DOS
CRC16/CRC32 sessions receive full8 KiB packets with exact files. See
`docs/ZEDZAP_BBS.md` and `docs/validation/zedzap-bbs.json`. Full loss/timing tests,
windowed sending, auto-download, persisted resume, physical modem, full original
UI/emulations/protocols, ASPECT and Host remain required; no F01–F16 gate closes.


## Bounded windowed ZMODEM and confirmed replay

The `d791eb10` runtime adds a bounded asynchronous sender with separate wire,
confirmed and historical offsets. CANFDX/CANOVIO peers may stream up to an 8 KiB
window; receiver capacity is separately enforced between synchronous boundaries.
The first packet after reposition is synchronous, and open frames close before
recovery. Forward ACKs during a long replay neither exhaust nor forgive the
engine's accumulated rewind budget. The live adapter observes a rewind without
refresh, then refreshes on confirmed forward replay. A paired linked watchdog
probe reproduces the earlier 540-tick failure and completes an 800-tick replay
after the correction, with individual 100-tick ACK intervals.

Literal wire schedules and reactive peers check window/storage bounds, partial
ACKs, source failures, noise/cancel and 128 KiB rewind. Real lrzsz and stock
Synchronet helper tests also corrupt a payload within a continuing stream.
See `docs/WINDOWED_ZMODEM.md` and its validation ledger for exact final counts,
current DOS/BBS workflows and explicitly retained earlier attempts. Window
settings, adaptive original block sizing, auto-download, persisted receive
resume, physical modem/line-loss timing, remaining protocols/emulations/UI,
ASPECT, Host and all F01–F16 completion gates remain open.

## Automatic ZMODEM reception: recognition prerequisite

The original terminal trigger and Auto Download PRM word are now identified;
see `docs/ZMODEM_AUTOSTART_NATIVE.md` for exact evidence, the saved download
prefix and unresolved path-validation semantics. A separately maintained canonical hex invitation recognizer validates
CRC16 before proposing ownership transfer and preserves rejected/incomplete
bytes. It passes 6,510 independent host/8086 DOS vectors with a 22-byte DOS state
and a byte-identical source-only diagnostic rebuild. See
`docs/ZMODEM_AUTOSTART.md` and its validation ledger. It is not yet connected to
terminal input, settings or destination selection. Actual automatic downloads,
modern BBS workflows and all F01–F16 gates remain open.

## Automatic reception: saved transfer settings

PRMEDIT now edits the two proved transfer preferences without changing the
existing serial-settings ABI. The separate checked decoder normalizes the
original zero/nonzero enable word and resolves an empty prefix to current
directory at transfer time. Paths and opaque tail bytes round-trip; malformed
paths remain repairable without implicit normalization. The 63-byte path field
scrolls during editing. See `docs/TRANSFER_SETTINGS.md` and its validation ledger.

The model passes 450 inputs in 12 groups; all 12 existing DOS editor workflows,
seven new transfer-setting UI flows, seven existing production clipboard/settings
flows and 15 configuration unit tests pass. A fresh source-only snapshot again
reproduces 64 outputs. Runtime remains d791eb10. Startup/live transfer-setting
adoption, checked destination reconciliation and automatic transfer entry remain
required, followed by actual DOS/Synchronet/ENiGMA workflows. All F01–F16 gates
remain open.

## Canonical automatic ZMODEM reception

Runtime 731418bd now uses the proved saved preferences for CRC-valid hex ZRQINIT
reception without local Alt-R/F2/filename keys. Startup stages serial, optional
modem, retained directory context and transfer settings from one PRM read.
Successful settings children adopt checked preferences from the same frozen
image; invalid requests/files preserve existing plans. The existing 44-byte
serial and 628-byte live-plan layouts stay intact.

The foreground recognizer preserves rejected/expired bytes before translation
and native parsing, services a 36-tick inactivity deadline across BIOS midnight,
and flushes before local key owner changes. Existing exclusive transfer/file
owners perform UI restoration, exact writes, checked close and no-overwrite
installation. Drive-relative current-directory paths now agree across directory
and per-file validation, with actual DOS verification in a separate CWD.

All 80 terminal commands pass, alongside 60 preference inputs, 384 damaged ABI
images, 21 normal/38 fault storage cases, three actual DOS/lrzsz automatic batches
and automatic downloads on both stock Synchronet and ENiGMA. A fresh source-only
snapshot reproduces 64 outputs. Earlier startup, midnight and path-extension
failures remain explicit in the retained evidence. See `docs/ZMODEM_AUTOSTART.md`
and `docs/validation/zmodem-autostart.json` for exact hashes, bounds and scope.

Near data/stack use 65,296 bytes with 240 spare; resident CODE uses 63,630 bytes
with 1,906 spare. Additional placement work remains necessary as the application
grows. Canonical invitations are implemented; binary/noncanonical automatic
invites, persisted resume, broader timing/physical modem testing, remaining
protocols/emulations/UI, ASPECT and Host remain required. The ENiGMA fragmented
key interaction remains unresolved. No F01–F16 gate is closed by this component.

## ENiGMA incremental keyboard experiment

A separately exported candidate of pinned ENiGMA revision 6c253171 reproduces
and addresses chunk-local keyboard decoding without changing the running stock
fixture or DOS runtime 731418bd. Actual stock Client checks demonstrate 74 key
event and nine editor-state fragmentation failures. The candidate passes 112
Client/editor checks against stock unfragmented baselines, 1,638 deterministic
framing checks and 123 selected upstream regressions. A broader parity test
caught and corrected an Escape-prefixed UTF-8 regression in the first prototype.

`lab/bbs/patches/enigma-key-stream/README.md` provides the isolated patch and
pinned Nix reproduction command; `docs/validation/enigma-key-stream/report.json`
binds inputs, source identities and logs. The 100 ms ambiguous-input policy and
raw-owner lifecycle remain experimental. A separately configured patched-server
DOS session, post-editor transfer checks, physical modem validation and remote
stock BBS compatibility remain required. This is server-side evidence, not a
DOS-client fix, and no F01–F16 gate closes.
