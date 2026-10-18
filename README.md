# PCPlus DOS reconstruction

An incremental source reconstruction of ProComm Plus 2.01, focused first on
serial communication, ANSI terminal handling and BBS compatibility.
The complete task list and current work are tracked in [PLAN.md](PLAN.md).

**This is not yet a complete PCPlus source rebuild.** Current outputs:

| Output | Inputs | Current purpose |
| --- | --- | --- |
| `build/transfer-metadata/METADATA.EXE` | Recovered source only, explicit diagnostic callbacks | Native YMODEM/TELINK headers, parsers and batch terminator; not a live batch owner |
| `build/batch-header/HEADER.EXE` | Maintained source only | Bounded 128/1024-byte metadata codec, safe DOS basenames and optional fields |
| `build/transfer-storage/TRANSFER.EXE` | Recovered and maintained source only | One native receive owner through actual staged DOS storage; UART/time are controlled peer fixtures |
| `build/upload-file/{UPLOAD,UPFAULT}.EXE` | Maintained source only | Read-only binary upload sources, DWORD length/read accounting and close/failure diagnostics |
| `build/download-file/{DOWNLOAD,DLFAULT}.EXE` | Maintained source only | Streaming binary storage, checked close/install and deterministic failure/recovery diagnostics |
| `build/transfer-{send,files,session,uart}/` | Recovered and maintained source only | Sender, CRT file handling, nonlocal session ownership and real UART transfer-component diagnostics |
| `build/transfer-blocks/BLOCKS.EXE`, `build/transfer-receive/RECEIVE.EXE` | Recovered and maintained source only | CRC/framing and receiver validation diagnostics; UART/time/file-session boundaries remain explicit |
| `build/program-exec/EXECUTOR.EXE`, `build/terminal-reset/RESET.EXE` | Recovered and maintained source only | Native PROGRAM/EXEC and terminal-reset diagnostics with unresolved application services |
| `build/process/PROCESS.EXE`, `build/process/PROGRAM.EXE` | Maintained source only | Bounded DOS process execution and owned-child diagnostics |
| `build/ui-windows/WINDOWS.EXE` | Recovered and maintained assembly source only | Packed window snapshots and original flow-message service |
| `build/modem-commands/MODEMCMD.EXE` | Recovered and maintained assembly source only | Original caret decoder with bounded source-owned wrapper |
| `build/modem-responses/MODEMRSP.EXE` | Maintained and recovered assembly source only | Response matching and classification; dial-attempt object remains unlinked |
| `build/xlt-editor/XLTEDIT.EXE` | Maintained C source only | Offline 256-byte translation-table editor with checked save/recovery; see [XLT editor](docs/XLT_EDITOR.md) |
| `build/setup/PRMEDIT.EXE` | Maintained C source only | Offline five-page editor for46 mapped PRM fields with staged validation and checked replacement; see [setup editor](docs/SETUP_EDITOR.md) |
| `build/terminal/TERMINAL.EXE` | Maintained C and recovered/maintained assembly source only | Serial terminal with PRM startup, directory editing, staged saves and bounded modem dialing |
| `build/standalone/SERIAL.EXE` | Maintained assembly source only | Independently linked DOS diagnostic exercising the recovered UART module |
| `build/ansi/PARSER.EXE` | Maintained assembly source only | Independently linked parameter-reader diagnostic with bounds checks |
| `build/keyboard/KEYBOARD.EXE` | Maintained assembly source only | Recovered BIOS keyboard acquisition/normalization diagnostic |
| `build/keyboard-mapping/MAPPING.EXE`, `build/keyboard-detection/KBDMODE.EXE` | Recovered and maintained source only | Raw key mapping and BDA-based enhanced BIOS selection diagnostics |
| `build/line-edit/LINES.EXE` | Recovered and maintained source only | Original insert/delete-line helpers and controlled historical wait diagnostic |
| `build/csi/CSI.EXE` | Maintained assembly source only | Combined ESC, parameter, CSI, attribute and cursor self-check |
| `build/{escape,attributes,screen,text,reports,erase}/` | Maintained assembly source only | Separate DOS diagnostics for each recovered component |
| `build/{scroll,modes,render,cursor-shape}/` | Maintained assembly source only | Scroll, mode, character-rendering and BIOS cursor-style diagnostics |
| `reconstruction/dist/tech-net-candidate/PCPLUS.EXE` | Recovered source plus a locally supplied original executable | Full application with the historical CSI-q lockup fix |

Original executables, dialing/configuration files, disk images, downloaded
support archives and generated disassembler databases are excluded from Git.
No original executable is required to build the standalone diagnostic.

The terminal now supports [static far code](docs/FAR_CODE.md), starting with
the dedicated-print controller and [modem services](docs/MODEM_FAR_CODE.md).
Resident near-call interfaces and DS=SS remain
compatible; the builder checks far-call relocations, segment bounds and retained
code across PROGRAM. [Private UI screens](docs/UI_FAR_STORAGE.md) also live
in far storage: browser, nested editor and PROGRAM retain separate full frames,
leaving13,152 bytes of capacity for more shared data/stack definitions. Full application
and dynamic-overlay work remains open.


Alt-Z opens the [command menu](docs/COMMAND_MENU.md), with File, Connection,
View, Setup and Help groups. Use arrows/Tab, Enter or a listed letter; F1 shows
contextual help and `/` searches topics. Escape returns to the live terminal.
Incoming data continues while browsing. If a partial ANSI sequence is being
received, Alt-Z waits for parsing to finish and retains following keys locally;
Escape cancels that pending request.

Ctrl-PgUp now opens [serviced redisplay](docs/LIVE_REDISPLAY.md): 63,000 characters
of history, line/page navigation, case-insensitive search and a preserved live
screen. Incoming input and terminal replies continue while browsing. Escape
returns to the updated terminal. **W** appends the frozen history to a DOS file
while incoming data continues; see [history export](docs/HISTORY_EXPORT.md) for
path, cancellation and partial-write behavior. Alt-= opens the filename clipboard;
C enters it from redisplay. A/E/D/U edit the list, Space tags, C selects screen
filenames, R changes the session separator (PRMEDIT saves its default), and P/S/T paste all/one/tagged entries.
Single removal follows actual UART writes; Escape cancels unsent bytes. See
[filename clipboard](docs/FILENAME_CLIPBOARD.md) for behavior and current limits.
The [clipboard transfer checks](docs/CLIPBOARD_TRANSFERS.md) cover filename
selection, XMODEM/YMODEM ownership and reuse after transfers, with separate
stock BBS evidence.

## Build and run in DOS

Requires Nix with flakes; the wrapper enables its required experimental features.
The flake pins NASM, Open Watcom, DOSBox-X, REA, Ghidra, Java and Python tooling.
The current development host is x86_64 Linux. Its first toolchain build can take
some time, particularly Open Watcom.

```sh
./tools/build
```

The interactive milestone can be built and tested separately:

```sh
./tools/build terminal test-terminal
```

In DOS, `TERMINAL COM1 38400 8N1 SOFT` selects software flow control.
`TERMINAL @PCPLUS.PRM` imports a validated read-only subset of an explicit
2.01 configuration; serial CLI categories override it. See
[startup configuration](docs/STARTUP_CONFIGURATION.md).
`TERMINAL @PCPLUS.PRM /D:bbs.example:23` uses validated configured initialization,
dial prefix/suffix and response strings. `TERMINAL @PCPLUS.PRM /E:PCPLUS.DIR` opens a native
directory browser and uses the selected entry. Press E to edit, F10 to accept/save
or Escape to discard the edit. Successful directory connections save date/count
after UART restoration at exit; the PRM remains read-only. See
[directory editing and recovery](docs/DIRECTORY_EDITING.md) and
[live directory selection](docs/DIRECTORY_LIVE.md). Escape cancels, Alt-H hangs up, and
Alt-D repeats the target after cleanup. Alt-B sends a [serviced UART BREAK](docs/LIVE_BREAK.md),
keeping receive/keyboard service active and releasing before hang-up or exit.
See [connection management](docs/CONNECTION.md).
Use `HARD` for RTS/CTS or `NONE` to disable flow control; match the modem's
settings. Alt-X exits. Navigation, keypad and function/modifier keys now use all79
recovered binding slots with maintained network defaults. `/K:MYKEYS.KBD`
imports the effective profile from an explicit file; `/B:AUTO` detects enhanced
BIOS support through the original BDA check, with STANDARD/ENHANCED overrides.
See [live keyboard behavior](docs/LIVE_KEYBOARD.md). Recognized original local
commands without an implemented handler stop explicitly with errorlevel4.
`/A:NETWORK` is the default CSI M delete-line policy; `/A:ORIGINAL` selects the
bounded serviced historical alternate wait. See
[live line editing](docs/LIVE_LINE_EDIT.md). This executable does not yet provide the
complete original menus, directory cycles, advanced transfers or scripting engine.
Alt-R receives ordinary XMODEM CRC/checksum128/1024 downloads into an explicit
new DOS8.3 destination, with checked staging/close/install before the final ACK.
Use HARD or NONE; SOFT rejects binary reception before staging. Escape cancels.
See [live transfer policy and recovery](docs/TRANSFER_INTEGRATION.md).
Alt-S uploads an existing file through checked read-only DOS IO and the native
ordinary sender, with automatic1K blocks and actual-ACK progress.
See [upload behavior and limits](docs/LIVE_UPLOAD.md).
Press F2 inside either transfer prompt to select CRC YMODEM. For downloads,
enter an existing directory, such as `D:\RECV\`. For uploads, enter a DOS8.3
filespec, such as `D:\SEND\*.BIN`. Select YMODEM on the BBS as well. Files are
checked individually; earlier installed files survive a later batch failure.
See [batch transfer behavior](docs/LIVE_YMODEM.md).
Alt-F1 opens an append-text capture (empty Enter uses `PCPLUS.LOG`) or closes
the current log; Alt-F2 pauses/resumes and Alt-F3 toggles CR-adds-LF. Capture
uses checked DOS writes and preserves partial files on errors; a genuine
write/close failure reports exit12 unless an earlier error takes precedence.
PROGRAM closes capture before launching a child. See
[capture controls, exact bytes and limits](docs/LIVE_CAPTURE.md).
Alt-G appends a character-only screen snapshot to `PCPLUS.SCR`, with trailing
spaces trimmed and CRLF per row. It preserves open/held text capture and refuses
an internal same-file conflict. See [screen-file snapshots](docs/LIVE_SNAPSHOT.md).
Ctrl+backslash opens the [raw monitor](docs/LIVE_MONITOR.md). Y explicitly
replaces `PCPLUS.DMP` with binary received bytes; N/Enter/Escape selects view-only.
Escape inside the monitor returns to normal ANSI processing. Existing text
capture stays open or held and excludes received monitor bytes.

Alt-L toggles [processed printer copy](docs/LIVE_PRINTER.md) through a checked
DOS `PRN` owner. A bounded queue keeps serial service active; failures retain
an errorlevel12 status, and PROGRAM closes the device before child execution.
The virtual printer tests do not establish physical printer compatibility.
Incoming ANSI media-copy commands now print the full screen, scroll region or
current row through the same checked owner. Modes18/19 retain their recovered
form-feed and region behavior. See [screen printing](docs/LIVE_SCREEN_PRINT.md)
for exact commands and cancellation. Unprefixed CSI5i enters the
[dedicated printer controller](docs/LIVE_PRINT_CONTROLLER.md): received bytes
go to checked PRN without rendering or capture until the native stop grammar
or local cancellation returns to the terminal. It preserves a borrowed copy
owner, bounds escape buffering and services serial/keyboard/capture timers.

The separate [native printer diagnostic](docs/PRINTER_NATIVE.md) reconstructs
printer-copy instructions with explicit memory-device fixtures. The
[raw-monitor ledger](docs/RAW_MONITOR_NATIVE.md) maps Ctrl-\\ and the binary DMP
path. The exact native monitor remains a separate diagnostic; full original
monitor/UI/HOOK modes remain unfinished.
Global `/T:MYKEYS.KEY` imports ten Meta actions; Alt-1..Alt-0 execute
nonblocking TEXT or maintained PROGRAM actions. PROGRAM passes a validated
1..51-byte stored command through COMSPEC `/c`, suspends terminal UART ownership
while the child runs, then restores serial/video state and resumes queued keys.
Its flow handoff is tested with synthetic children; NONE flow cannot ensure a
remote peer pauses. ASPECT and HOOK actions remain explicit unsupported actions.
See [TEXT actions](docs/LIVE_META_KEYS.md) and
[native PROGRAM evidence](docs/PROGRAM_EXEC.md). ESC c uses a separate
[maintained startup-state reset](docs/LIVE_TERMINAL_RESET.md) for profiles 4/6,
including the imported keymap, without file IO or redialing. Stored passwords remain metadata
and are never automatically sent; directory SCRIPT/KEY/META bindings remain unsupported. An exit-time accounting save problem reports
errorlevel9 unless a prior application error exists; inspect retained
`PCPSTG.$$$` / `PCPBAK.$$$` recovery files as described in the editing guide.
Local Synchronet, ENiGMA½ and Mystic interoperability work is documented in
[lab/bbs/README.md](lab/bbs/README.md). The current
[matched flow comparison](lab/bbs/flow-control.md) isolates the software-XON
conflict with Synchronet Ctrl-Q; HARD passes that editor workflow.

The initial key defaults are authored for network use; they are not recovered
factory KBD tables. KBD slot strings and KEY action/macro files are different
formats. Complete ASPECT/HOOK execution, original PROGRAM application services,
settings, remaining transfer protocols and original menus remain part of the reconstruction goal.

Copy `build/standalone/SERIAL.EXE` to DOS and run:

```text
SERIAL       COM1 / IRQ4 / 38400 baud / 8N1, flow control off
SERIAL S     Same settings with XON/XOFF
SERIAL H     Same settings with RTS/CTS
```

It echoes incoming serial bytes; **Escape on the local keyboard exits**.
This is a diagnostic, not a terminal UI. It saves/restores the IRQ vector and
UART state. Port selection, additional UART types and physical-hardware
validation remain work in progress. Do not use it inside another serial program.

Run the bounded, headless DOSBox-X integration suite:

```sh
./tools/build test
```

The test first replays the linked driver with controlled UART/PIC/DOS state,
including overflow, flow-control watermarks, CTS/transmitter stalls, timeouts and
hardware restoration. It then sends binary data across the 4096-byte receive-ring
boundary in DOSBox-X, checks XON/XOFF transmit pause/resume and checks DOS exit,
IRQ restoration and ring invariants. Use `./tools/build test-driver` for replay only. Emulator results do not establish physical modem/BBS compatibility.
Test artifacts and exact executable hashes are recorded under `build/serial-tests`.

The build also produces `build/ansi/PARSER.EXE`, which runs self-checks for the
linked parameter reader when started in DOS. Run its replay and DOS tests with:

```sh
./tools/build test-parser
```

Original-vs-maintained parser comparison is optional and requires local originals:
`./tools/build test-parser-compat`. See `docs/ANSI.md` for exact scope and fixes.

The keyboard unit has its own source-only DOS diagnostic and injected-key tests:

```sh
./tools/build test-keyboard
```

It covers acquisition and normalization, not terminal-specific escape-sequence
mapping. See `docs/KEYBOARD.md`. The full application acceptance inventory is
tracked in `docs/FEATURES.md`, including non-terminal features and dependencies.

The combined ANSI path and separate screen/reporting components build and test
through `./tools/build test-csi`, `test-screen`, `test-attributes`, `test-text`,
`test-erase`, `test-reports`, `test-cursor_state` and `test-escape`. The default `test` target includes
these diagnostics. See [docs/CSI.md](docs/CSI.md) for integration scope and gaps.
Additional targets `test-scroll`, `test-modes`, `test-render`, `test-cursor_shape`
and `test-terminal-services` verify real scrolling, terminal modes, ordinary
character output, cursor visibility/style and key-map/tab/reset helpers. These
are source-built components; a complete interactive application remains open.
`./tools/build test-input_dispatch test-input-relocation` verifies continuous
text/ESC/CR/LF/TAB/BS through the recovered input, renderer and history paths.
Selected controls and ANSI profiles are implemented; this diagnostic uses a
memory byte provider. See [docs/INPUT_DISPATCH.md](docs/INPUT_DISPATCH.md).
`./tools/build test-config` verifies a partial lossless host codec for proved PRM
settings. It preserves unknown bytes and uses synthetic data.
`./tools/build test-config-dos` builds source-owned DOS load/save routines with
Open Watcom and tests real files plus injected I/O failures in DOSBox-X.
`./tools/build test-config-replace` verifies staged replacement, rollback and
reported recovery states under DOS I/O failures. Complete defaults, restart
recovery and the full settings UI remain work in progress.
See [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
`./tools/build test-config-abi` verifies the actual DOS C APIs from assembly-owned
startup. `test-directory` checks the recovered lossless directory codec, and
`test-modem_commands` checks the source-built modem decoder. The UI window and
flow services pass `test-ui_windows test-ui-flow` and are linked into the
interactive terminal. `test-modem_responses` tests the response matcher separately;
see [response recovery](docs/MODEM_RESPONSES.md). `test-modem_send` checks the
recovered original sender and real UART; `test-modem-import` checks the DOS
settings decoder. The maintained [connection controller](docs/CONNECTION.md) now
dials explicit or selected-directory targets. A native storage editor, staged
record replacement and deferred date/count accounting are integrated; the
maintained date patch fixes the original year2000 counter overwrite. Full
settings/original directory menus and automatic cycles remain open. See
[editing and accounting](docs/DIRECTORY_EDITING.md), [directory](docs/DIRECTORY.md),
[modem settings](docs/MODEM_CONFIGURATION.md) and [window services](docs/UI_WINDOWS.md).

`test-keyboard_mapping`, `test-keyboard-mapping-raw` and `test-keyboard_detection`
check recovered classification and BIOS selection. `test-keymap test-keymap-dos test-key-actions-dos`
check lossless KBD/KEY codecs and strict DOS import. `test-line_edit` checks
recovered line helpers. `test-meta_keys test-character_edit` checks exact
recovered action/character helpers. `test-terminal` also runs linked keyboard,
TEXT and line/character-policy regressions plus actual DOS delivery/import. See
[mapping evidence](docs/KEYBOARD_MAPPING.md), [file formats](docs/KEY_MAPPING.md)
and [line recovery](docs/LINE_EDIT.md).

`./tools/build test-translation test-translation-dos` builds176 exact native
XLT instruction bytes and tests a separate checked256-byte DOS table loader.
There are2,082 CPU cases with optional genuine-original comparison, nine actual
DOS filesystem checks and22 declared API fault checks. The interactive terminal
accepts `/X:FILE.XLT` and saved PRM modes0/1/2 (identity/table/7-bit mask).
PRMEDIT exposes the mode; Alt-F10 offers a separate confirmed
[live mode handoff](docs/LIVE_TRANSLATION_SETUP.md). Default table mode
uses bounded current-directory then `PCPLUS` directory lookup; see
[resource lookup](docs/RESOURCE_LOOKUP.md). Explicit `/X` bypasses fallback. Normal table-mode characters translate
while parser continuations, output and binary/dedicated owners remain raw. See
[translation recovery](docs/TRANSLATION.md) and [live selection](docs/LIVE_TRANSLATION.md).
`./tools/build xlt-editor test-xlt-editor` builds and checks the offline
[XLTEDIT table editor](docs/XLT_EDITOR.md), including failed-save recovery.

Native recovery now includes 93 exact CRC instruction bytes plus an independently
generated, original-verified 512-byte polynomial table, and 886 exact receiver
bytes. `./tools/build test-transfer_blocks test-transfer_receive` exercises
block framing, payload/trailer validation, duplicate ACK, sequence/integrity NAK,
EOT and double-CAN boundaries. Optional original comparison is explicit; ordinary
builds need no original files. The receiver diagnostic models UART/time/UI
boundaries and stops before file commit. It does not yet transfer files between
peers. See [block primitives](docs/TRANSFER_BLOCKS.md) and
[receiver recovery](docs/TRANSFER_RECEIVE.md).

`./tools/build test-program_exec test-terminal_reset test-process` checks
3,102 native PROGRAM/EXEC bytes, 2,301 native reset bytes and the separate bounded
DOS process backend. Native PROGRAM still depends on unrecovered heap and
application handoff services; native nonzero reset still stops at its KEY/profile
loader. The maintained live PROGRAM/process and RIS policies close selected
terminal use cases without claiming those native pipelines are complete.
Current live checkpoint `036a8092` passes linked PROGRAM handoff regressions;
actual DOS owned-child and reset checks have separate artifact identities.

## Full-application compatibility build

To use this optional path, supply your own original PCPlus 2.01 executable with
SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`
at `analysis/pcplus-originals/PCPLUS-main-2.01.EXE`. For full-application tests,
place your supporting installation files, including ASPCOMP.EXE, in
`analysis/pcplus-install`. These locations are ignored by Git.

```sh
./tools/dev --command python3 analysis/inspect_pcplus.py
./tools/build compat
./tools/build test-compat
./tools/build test-modem
./tools/pcplus-run
```

The compatibility build verifies and inserts 10,129 recovered source bytes (including 130 startup pointer-table bytes) into the
original container, then replaces exactly two bytes using the archived Datastorm
TECH_NET recipe. Other maintained parser/input bounds fixes apply to source-built
diagnostics; this compatibility container still changes only those two bytes. It retains the original program's other code and resources.
The launcher uses a separate private installation under `reconstruction/lab`.
Type `ATDThost:port` to dial its emulated Hayes modem; Alt-X exits. Its generated
startup script and executable are refreshed on launch.

## Source and evidence

- `reconstruction/uart/core.asm`: recovered resident UART block, with exact
  baseline and relocatable OMF modes sharing the same instruction source.
- `reconstruction/uart/layout.inc`: original DS addresses versus linkable symbols.
- `src/uart/api.asm`: bounded transmit and foreground flow-control service.
- `reconstruction/ansi/parameters.asm`: exact original recovery plus maintained OMF mode with bounds checks.
- `reconstruction/ansi/transition.asm`: shared parameter-to-dispatch state transition.
- `standalone/`: newly written DOS host, state allocation, host services and tests.
- `docs/UART.md`: interfaces, observed behavior, evidence and known limitations.
- `analysis/`: REA MCP client, binary/overlay analysis scripts and evaluation.
- `nix/`: pinned toolchain, global REA package and compiler check.

Generated `.analysis.exe` files are synthetic disassembler inputs. Never run or
deploy them. Decompiled pseudocode is evidence, not recovered original source.

## Next milestones

1. Extend driver validation to physical UARTs and the intended Wi-Fi modem;
   controlled watermark, overflow and stall regressions now pass.
2. Recover the terminal parser and keyboard module behind explicit interfaces.
3. Reconstruct application startup, settings, UI, dialing, transfers and scripting.
4. Link the complete application from source, removing the original executable
   from every build input.

PCPlus and ProComm Plus are names of the original product. This repository is an
independent reconstruction effort; original program rights are not reassigned.

## Transfer reconstruction checkpoint

One native ordinary receiver now stays active across handshake, multiple blocks,
CRC/checksum validation, retries, genuine setjmp/longjmp cancellation and EOT.
The separate real-DOS-storage composition verifies periodic/final file writes,
short-write and close-error installation gates, cancellation/timeout cleanup,
and mixed128/1024-byte blocks at the flush boundary. Native sender and real UART
component tests also pass. The terminal now has live Alt-R/Alt-S ordinary
XMODEM receive/send; actual DOS uploads/downloads pass against local Synchronet
and ENiGMA servers with the documented lab configuration. The new native batch
metadata module and maintained codec are complemented by checked batch owners
and live CRC YMODEM receive/send. Remaining advertised protocols, the complete
settings/UI and physical modem transfers remain open. See
[live YMODEM](docs/LIVE_YMODEM.md),
[batch metadata](docs/TRANSFER_METADATA.md), [BBS transfers](lab/bbs/transfers.md),
[session contracts](docs/TRANSFER_SESSION.md),
[download storage](docs/DOWNLOAD_STORAGE.md), [sender](docs/TRANSFER_SEND.md),
[native file behavior](docs/TRANSFER_FILES.md) and [UART callbacks](docs/TRANSFER_UART.md).


For an existing2.01 PRM in the current DOS directory, build both applications
with `./tools/build terminal setup`, then run `TERMINAL /S @PCPLUS.PRM` in DOS.
This opens setup before connecting; see [setup startup](docs/SETUP_STARTUP.md)
for save/cancel, path limits and CLI precedence.

From the running terminal, **Alt-F10** opens the same editor for an explicit
`@` current-directory8.3 PRM. Valid display, pacing, future modem settings and
BREAK edits apply during the session. A separate Y/N choice applies baud,
line format and flow on the current port. Profiles4/6 have a separate confirmed
keyboard/view reset. An idle COM move has its own confirmation and restores the old port before acquiring the new one; see [COM changes](docs/PORT_HANDOFF.md) and [setup from the terminal](docs/SETUP_LIVE.md).
