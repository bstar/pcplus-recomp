# PCPlus DOS reconstruction

An incremental source reconstruction of ProComm Plus 2.01, focused first on
serial communication, ANSI terminal handling and BBS compatibility.
The complete task list and current work are tracked in [PLAN.md](PLAN.md).

**This is not yet a complete PCPlus source rebuild.** The current terminal
passes logged-in ZMODEM uploads and downloads against local Synchronet and ENiGMA,
including 8 KiB reception and bounded windowed sending.
[Results, replay recovery and remaining interaction limits](docs/WINDOWED_ZMODEM.md).
Saved Auto Download and Download directory now support
[automatic ZMODEM reception](docs/ZMODEM_AUTOSTART.md) on both local BBS fixtures.

ASPECT recovery now includes a [literal codec](docs/ASPECT_LITERAL.md),
[native dispatcher](docs/ASPECT_DISPATCH.md) and
[global-string primitives](docs/ASPECT_GLOBAL_STRINGS.md).
[Compiler flow probes](docs/ASPECT_CONTROL_FLOW.md) establish call/branch and
parameter encodings. [Stack and error-unwind composition](docs/ASPECT_EXECUTION.md)
now verifies real native context restoration after an overflow.
[File-backed calls and frames](docs/ASPECT_FILE_FLOW.md) now use actual DOS
stdio, including nested returns and targets beyond64KiB.
The [standalone execution owner](docs/ASPECT_RUNTIME.md) now runs selected
compiled scripts through real DOS files and far-heap allocation, including
integer/long assignments, comparisons, branches, loops and procedure frames.
The [arithmetic extension](docs/ASPECT_ARITHMETIC.md) adds signed integer/long
math, compound assignments and scoped DOS divide-fault recovery.
[Typed parameters and strings](docs/ASPECT_PARAMETERS.md) now execute mixed
arguments, nested calls, by-value mutation and real far-string assignment.
[String commands and comparison status](docs/ASPECT_STRING_COMMANDS.md) now add
concatenation, case conversion, byte operations, substrings and SUCCESS/FAILURE
conditions, with CP437 behavior preserved.
[Decimal conversions](docs/ASPECT_CONVERSIONS.md) add ATOI/ATOL/ITOA/LTOA.
The [maintained host compiler](docs/ASPECT_COMPILER.md) now emits the tested
ASPECT subset directly from authored source. The diagnostic build compiles all
377 fixtures and compares them with the original oracle before DOS execution.
Full script compilation, application command coverage and terminal scheduling
remain unfinished.
[WHEN compiler support](docs/ASPECT_WHEN_COMPILER.md) adds 40 separately checked
outputs. The [DOS event runtime](docs/ASPECT_WHEN_RUNTIME.md) now executes native
matching and deferred calls, including local frames and disconnect actions.

[Directory-bound scripts](docs/DIRECTORY_SCRIPTS.md) now receive a private selected
record, current-call date and queued raw input. The native directory expressions
are documented [here](docs/ASPECT_DIRECTORY.md). Automatic Synchronet login
now passes automatic login and all 12 stock-editor checks through draft abort.
The [shared renderer](docs/ASPECT_RENDERER.md) uses the parent's actual ANSI
engine and retains screen, cursor and scrollback across the child process.
Its supported profile and owner restrictions remain explicit.
[Current BBS workflows](docs/ASPECT_BBS_WORKFLOWS.md) retain the ENiGMA
immediate-forwarding editor failures alongside a passing automatic script/editor
run with explicit 30 ms modem buffering and standard keys.

The [DOS script runner](docs/ASPECT_RUNNER.md) now adds File → A → Run script
through the terminal's Alt-Z menu. `ASPECT.EXE` runs as a separate DOS child
with MESSAGE/EXIT/PAUSE support and returns through the PROGRAM owner. Selected serial scripts now use the active port through a checked child
handoff. [Serial scripting](docs/ASPECT_SERIAL.md) adds TRANSMIT, WAITFOR,
flow control and exact unread-byte return; full application services remain
unfinished. [Character and line input](docs/ASPECT_RECEIVE.md) adds
COMGETC/COMGETCD, RGET and WAITQUIET, with the native timing and status rules
kept distinct from the raw child platform services. [Input policy](docs/ASPECT_INPUT_POLICY.md)
now inherits the terminal's XLT or seven-bit setting while returning unread
bytes unchanged. Shared rendering and native WHEN events are available for
admitted connected scripts; other application services remain unfinished.
[Connected script sessions](docs/ASPECT_SCRIPT_SESSION.md) use the selected COM
port and resume automatically on success; a live script login followed by stock
Synchronet editor interaction is verified in DOS.
Stage the terminal, sibling helpers and
an authored HELLO example with `./tools/build package`; files appear in
`build/dos-package` without original executables or private profiles.

The [native SET runtime](docs/ASPECT_SET_RUNTIME.md),
[FIND/SWITCH/CASE integration](docs/ASPECT_FIND_CASE_RUNTIME.md) and
[BREAK/FETCH runtime](docs/ASPECT_BREAK_RUNTIME.md) now connect twelve setters
and getters, checked near temporary ownership, configured serial BREAK and
native notice/status rendering. TXPACE and BREAK use bounded IRQ-live
calibration around the recovered delay loop. The current DOS suite passes
1116 cases/26796 checks; five actual parent/child BREAK pulse/cancel cases also pass.
Physical UART timing and full-application requirements remain open.

[Filesystem commands](docs/ASPECT_PATHS.md) add CHDIR, MKDIR, RMDIR and DELETE
with the original comparison/error semantics. Both maintained compilers support
their atomic string operands; real DOS tests cover file/directory effects,
retained current drive/directory and the terminal's login-child handoff.

[Filesystem queries and rename](docs/ASPECT_FILE_INFO.md) add ISFILE, GETFSIZE
and RENAME with native comparison behavior and independent temporary-file
ownership. DOS compiler, repeated VM cleanup, parent login and eighteen-check
owned ENiGMA regressions pass. That checkpoint implemented92 slots; file enumeration below extends it to94.

[File enumeration](docs/ASPECT_ENUMERATION.md) adds FINDFIRST/FINDNEXT and the
native filename/extension/attribute/date/time/size builtins. Shared FOUND state,
DOS DTA ownership and EXECUTE continuation are covered in actual DOS. The runtime
implemented94 slots; attributes below extend this to96/119; full scripting remains unfinished.

[File attributes](docs/ASPECT_FILE_ATTRIBUTES.md) add GETFATTR/SETFATTR with
native DOS result policy and corrected far-global destination writeback. An
actual DOS native-wrapper control separates that correction from exact recovery;
279 repeated VM invocations cover masks, destinations and cleanup.

[File date/time commands](docs/ASPECT_FILE_TIMES.md) add GETFDATE/GETFTIME and
SETFDATE/SETFTIME through a separate temporary stream owner. Actual DOS controls
separate native lost-global/destructive-input behavior from corrected writeback
and private setter copies;248 repeated VM runs cover timestamps and cleanup.
The [DOS system queries](docs/ASPECT_SYSTEM_QUERY.md) add GETDIR/DISKFREE/DOSVER,
with native free-space arithmetic and corrected DOSVER far-global writeback.
The dispatcher now supports103 of215 slots; full ASPECT remains unfinished.

The [integrated script-file commands](docs/ASPECT_SCRIPT_FILE_RUNTIME.md) now
connect both compilers and the interpreter to the owned DOS backend. Thirteen
file commands and FGETS_CRLF SET/FETCH cover real file I/O, retained EXECUTE
handles, normal/error/cancel cleanup and terminal-child handoffs. DOS-compiled
login and subsequent custom ENiGMA search/DIZ/NFO navigation also pass in isolation.

Current outputs:

| Output | Inputs | Current purpose |
| --- | --- | --- |
| `build/aspect-receive-policy/POLICY.EXE` | Recovered assembly and controlled callbacks | Native receive mapping and displayed adapter; production mapping inherits the parent input policy |
| `build/aspect-conversions/CONVERT.EXE` | Recovered assembly and controlled services | Four conversion commands and scanner with actual CRT/string/frame/writeback code |
| `build/aspect-conversion-services/CONVERT.EXE` | Recovered assembly | Native decimal parser, integer formatter and strcspn bitmap |
| `build/aspect-string-services/SERVICES.EXE` | Recovered assembly and controlled operand/address callbacks | Actual CRT helpers and compare-status services |
| `build/aspect-string-commands/STRCMD.EXE` | Recovered assembly and controlled services | Eleven native command handlers with actual string/CRT/frame/copy dependencies |
| `build/aspect-parameters/PARAM.EXE` | Recovered assembly and controlled readers | Typed parameter pushes with actual native numeric/frame/stack/copy code |
| `build/aspect-strings/STRINGS.EXE` | Recovered assembly and controlled services | String operands, literals and assignment, including actual far copy and DOS far heap |
| `build/aspect-long/LONG.EXE` | Recovered assembly only | Native signed long multiply/divide/remainder and shift helpers, including independent actual DOS checks |
| `build/aspect-arithmetic/ARITH.EXE` | Recovered assembly and controlled services | Native arithmetic component; controlled long/float boundaries are distinct from composed execution |
| `build/aspect-runtime/EXECUTE.EXE` | Maintained source compiler, recovered assembly and maintained DOS resource owner | Fixed source-compiled suite;103 opcode slots including native DOS/directory/free-space and filesystem queries/rename/path/stream commands, EXECUTE/BREAK/FETCH/FIND/SWITCH/CASE and thirteen SET setters;112 unsupported slots and243 unsupported SET subcommands |
| `build/aspect-runner/ASPECT.EXE` | Recovered instructions and maintained DOS CLI/resource owner | Execute trusted compiled scripts; raw stdout, Escape cancellation and an optional checked UART lease |
| `build/aspect-receive-commands/RECEIVE.EXE` | Recovered assembly and controlled platform callbacks | Character, line and quiet-line input, native delayed read and DOS time, COMDATA/FOREVER |
| `build/aspect-serial-commands/SERIAL.EXE` | Recovered assembly and controlled device/time callbacks | TRANSMIT/WAITFOR and native formatter, timeout, case, clock and result primitives |
| `build/aspect-serial/SERIAL.EXE` | Maintained DOS owner and recovered UART core | Checked UART ownership, flow control and parent unread-byte handback |
| `build/aspect-console/CONSOLE.EXE` | Recovered assembly and controlled platform callbacks | MESSAGE/EXIT/PAUSE, caret transform, print loops and native BIOS delays |
| `build/aspect-operands/OPERANDS.EXE` | Recovered assembly and controlled services | Integer/long operand decoding; unchecked native indexing and external builtins remain explicit |
| `build/aspect-operations/OPERATE.EXE` | Recovered assembly and controlled services | Assignment, logical/comparison and increment/decrement diagnostics; float services are unavailable |
| `build/aspect-flow/FLOW.EXE` | Recovered assembly and modeled callbacks | Native reads/calls/frames/returns; unchecked historical behavior remains explicit |
| `build/aspect-file/FILE.EXE` | Recovered assembly and maintained C file adapter | Actual DOS file-backed control flow, checked short operands and nonlocal abort; no complete interpreter |
| `build/aspect-stack/STACK.EXE` | Recovered assembly and source-owned error callbacks | Typed value-stack and native copy diagnostic; native unchecked arithmetic/pop behavior retained |
| `build/aspect-unwind/UNWIND.EXE` | Recovered assembly and source-owned callbacks | Real dispatcher/abort/setjmp/longjmp composition, including a native stack-overflow case |
| `build/aspect-literal/LITERAL.EXE` | Maintained C source only | Bounded nonempty ASPECT literal payload codec diagnostic |
| `build/aspect-dispatch/DISPATCH.EXE` | Recovered assembly and source-owned callbacks | Exact215-slot dispatcher diagnostic; opcode handlers and application services remain unresolved |
| `build/aspect-globals/GLOBALS.EXE` | Recovered assembly and source-owned callbacks | Native allocation/release diagnostic; complete heap/error owner and loader remain unresolved |
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
| `build/xlt-editor/XLTEDIT.EXE` | Maintained C source only | 256-byte translation-table editor, offline or launched with Alt-F8, with checked save/recovery; see [XLT editor](docs/XLT_EDITOR.md) |
| `build/setup/PRMEDIT.EXE` | Maintained C source only | Offline five-page editor for 48 mapped PRM fields with staged validation and checked replacement; see [setup editor](docs/SETUP_EDITOR.md) |
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
with the builder enforcing the shared64KiB data/stack boundary. Full application
and dynamic-overlay work remains open.


Alt-Z opens the [command menu](docs/COMMAND_MENU.md), with File, Connection,
View, Setup and Help groups. Use arrows/Tab, Enter or a listed letter; F1 shows
contextual help and `/` searches topics. Escape returns to the live terminal.
Incoming data continues while browsing. If a partial ANSI sequence is being
received, Alt-Z waits for parsing to finish and retains following keys locally;
Escape cancels that pending request.

**Alt-F8** opens [XLTEDIT for the selected table](docs/TRANSLATION_EDIT.md).
Place XLTEDIT.EXE beside TERMINAL.EXE. F1 saves in the editor; after Escape,
Y applies a checked snapshot to the terminal. Other answers retain the active
mapping. The selected absolute table path survives directory changes.

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
and [line recovery](docs/LINE_EDIT.md). NETWORK line editing now also has a
[bounded attribute-plane owner](docs/LINE_ATTRIBUTES.md) with region-limited
native field repair and physical last-row handling; exact recovery remains separate.

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
Alt-F9, or Setup → Reload input table, stages the frozen active file and asks
before replacing its table during the session. Decline and errors retain the
active mapping; see [table reload](docs/TRANSLATION_RELOAD.md).
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

ZMODEM downloads accept [long wire filenames](docs/ZMODEM_NAMES.md) through
deterministic DOS aliases, with full retry identity and checked existing-file skip.
The transfer footer shows the remote name and local Save/Skip filename; remote
names wider than46 columns end with `~` on screen. The full wire identity is retained.
ZMODEM is available through Alt-R/Alt-S: press F2 in the prompt until ZMODEM is
selected, then enter a receive directory or send filespec. The live engine uses
checked batch storage/source seeking and serviced UART ownership; independent
actual DOS peer transfers pass. See [live ZMODEM](docs/LIVE_ZMODEM.md),
[sessions](docs/ZMODEM_SESSION.md), [wire codec](docs/ZMODEM_WIRE.md) and
[native evidence](docs/ZMODEM_NATIVE.md). [Windowed sending](docs/WINDOWED_ZMODEM.md)
and [automatic reception](docs/ZMODEM_AUTOSTART.md) pass selected local BBS
workflows. Enable Auto Download and set an existing Download directory in
PRMEDIT to skip the local receive prompt; select ZMODEM at the remote BBS.
Other invitation forms, persisted resume, broader UI/protocols and physical
modem validation remain open.


For an existing2.01 PRM in the current DOS directory, build both applications
with `./tools/build terminal setup`, then run `TERMINAL /S @PCPLUS.PRM` in DOS.
This opens setup before connecting; see [setup startup](docs/SETUP_STARTUP.md)
for save/cancel, path limits and CLI precedence.

From the running terminal, **Alt-F10** opens the same editor for an explicit
`@` current-directory8.3 PRM. Valid display, pacing, future modem settings and
BREAK edits apply during the session. A separate Y/N choice applies baud,
line format and flow on the current port. Profiles4/6 have a separate confirmed
keyboard/view reset. An idle COM move has its own confirmation and restores the old port before acquiring the new one; see [COM changes](docs/PORT_HANDOFF.md) and [setup from the terminal](docs/SETUP_LIVE.md).

Current matched terminal/ASPECT packages use renderer capability6 to display the
current script name after `EXECUTE`; see [the label protocol and checks](docs/ASPECT_SCRIPT_LABEL.md).
The same capability inherits the parent's standard/enhanced BIOS selection;
see [ASPECT keyboard acquisition](docs/ASPECT_KEYBOARD.md).
Ordinary keys during scripts now use the parent's selected profile and the
child UART through [shared key output](docs/ASPECT_KEY_OUTPUT.md), including
checked native half-duplex Insert/Delete and reverse-Tab echo with
[field repair](docs/ATTRIBUTE_REPAIR.md) during marker deletion and scrolling.
Local commands, complete line-edit metadata ownership and viewport handling
remain unfinished.

The [DOS compiler port](docs/ASPECT_DOS_COMPILER.md) provides `ASPCOMP.EXE`
for the maintained ASPECT language subset. `ASPECT` compiles explicit ASP files
and missing-ASX source siblings using the compiler beside it. ASPLEX, ASPINV
and ASPEXP remain developer diagnostics. Full native language and recorder
coverage remain unfinished.
