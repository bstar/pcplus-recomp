# Full application reconstruction checklist

This inventory preserves the scope of a maintained, source-built PCPlus 2.01
application for DOS. A serial diagnostic, an ANSI terminal, and a patched original
are useful milestones; none satisfies this checklist alone. The application build
must eventually stop reading the original executable, installation, proprietary
resources, and REA databases. Missing original helpers require recovered or newly
implemented source equivalents, with behavior differences documented.

This is an initial feature inventory, not a claim that every feature has been
found or implemented. A help heading or executable string establishes an
advertised surface, not working code or observed runtime behavior. Runtime
verification below must use source-built modules where it claims reconstruction.

## Evidence register

| ID | Artifact and search boundary | What it establishes |
| --- | --- | --- |
| E1 | Original `PCPLUS-main-2.01.EXE`, 214,016 bytes, SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904` | Selected baseline identity. File offsets below refer to this image, never Ghidra addresses. |
| E2 | Original `PCPLUS-main.HLP`, 23,558 bytes, SHA-256 `6aa2a38b1bae7c81d082d4efae4c7cd2becaf048bbdb93af4467b74bba9543d5` | Condensed help: 47 fixed-width topic records at file offset `0x0003`, 38 bytes each; 32-byte NUL-padded title, two-byte count, four-byte text offset. The meaning of the count field is not established here. Text begins at `0x06fe`. Many topics contain only an unavailable-content notice. |
| E3 | Original `PCPLUS-2.01-READ.ME`, 4,777 bytes, SHA-256 `c7b2f81fdcfab8ec0eb2f27c6efa60b8b2812912d37537ff233d87c4f793226b` | Vendor installation, upgrade, memory restrictions, external helper names, and modem database notes. Documentation claims, not reproduced runtime guarantees. |
| E4 | Local `analysis/pcplus-install/inventory.json` and filename/size comparison against its directory | The private active installation contains 32 files. Contents of dialing, host-user, and customized configuration files were not used for this inventory. An installed filename alone does not prove its format or role. |
| E5 | Local `analysis/pcplus-overlays/manifest.json`, `analysis/pcplus-main/functions/0x1b081-asm.json`, `0x1afba-asm.json`, `0x1b106-asm.json` | Target-specific loader analysis validates 31 code overlays, one startup-data overlay, and 502 unique exported entries. Loader assembly Evidence IDs: `ev_53e06cc9c3281f158eda3f282a442269d91c0cff17d87638b666cdb17c87c56d`, `ev_7915864172378f8b10c23a93718d7731503c165e0faca362d59a530d4f69739f`, `ev_85caa95f12a4e3af9cfe656ab210956e3c02814837163abbcffeb0c75d7fba58`. |
| E6 | [UART ledger](UART.md), [ANSI ledger](ANSI.md), [validation summaries](validation), and [evaluation](../analysis/PCPLUS-EVALUATION.md) | Existing reconstruction and test coverage, with explicit original-versus-maintained distinctions. These documents must be updated as coverage grows; their existence is not a whole-application pass. |

E1 strings cited here were read directly from the verified original, including
startup-data overlay 32 at file offset `0x25950` (60,080 initialized bytes).
They complement the saved REA exports; this inventory did not start a duplicate
native analysis session. The local originals and generated exports are ignored
by Git. Public evidence includes identities, offsets, paraphrases, recovered
source provenance, and test summaries; it must exclude private entries, passwords,
license data, and full copied help/manual text.

## Feature and acceptance matrix

All gates are open unless their exact covered subcase is supported by E6. Each
gate needs an automated regression or a repeatable DOS interaction transcript,
input/output artifacts, and an executable/source/toolchain identity. Static
discovery alone cannot close a functional gate.

| ID | Surface and evidence | Completion checks |
| --- | --- | --- |
| F01 | Startup, memory, exit, and overlays: E1/E5; E3 low-memory section; E1 references `PROFILE.ASX` at `0x29964` and `PCPLUS.PRM` at `0x2b810` | Recover entry initialization, segment/stack invariants, allocation and overlay lifetime, interrupt ownership, resource lookup and failure unwinding. Build from source; start and exit repeatedly in DOS; prove vectors/serial state restored after success, allocation failure, failed child execution and user cancellation. Exercise cold startup, missing/invalid configuration, missing resources and optional startup script. Account for every required original overlay/export or document its replacement, including data/resources. Synthetic analysis executables must never run. |
| F02 | UI and desktop services: E1 menu strings `0x25f50..0x26216`; E2 Menu Line `0x3227`, Setup `0x46ae`, Terminal Help `0x4f05`, help navigation `0x55f1` | Reconstruct main commands, pull-downs, popups, hotkeys, field editing, window save/restore, status toggles and contextual help. Test keyboard-only paths and advertised mouse paths, focus/escape behavior, error prompts, nested windows and return to terminal without display or connection loss. Help must be source-owned content with topic navigation/search rather than copied proprietary text. |
| F03 | Serial configuration and modem: E2 Line/Port Setup `0x309d`; modem topic headings; E1 current-settings format `0x26246`; E6 UART tests | Recover supported COM selection, baud/parity/data/stop-bit mappings, UART/IRQ setup and flow control; initialization, result parsing, direct/modem distinction, auto-answer, break, carrier loss, hang-up and timeouts. Validate malformed settings and unsupported UARTs without lockup. Exercise sustained traffic and stall recovery in DOS, then actual target UART/modem. Emulated baud is not physical throughput evidence. |
| F04 | Terminal emulations and screen engine: E2 terminal description `0x5355`; E1 model labels `0x2669a..0x267ba`; E6 partial ANSI work | Inventory each advertised emulation, state transitions, supported controls and keyboard profile. Reconstruct screen/cursor/attributes/erase/scroll/modes/terminal replies, reset, duplex, CR/CR-LF conversion, translation and monitor behavior. Test chunked input, malformed/oversized sequences, timeout/cancellation, display boundaries and known CSI-q lockup. ANSI alone does not close this gate; each other advertised emulation needs implementation plus fixtures or an explicit unresolved deviation. |
| F05 | Keyboard, Meta keys, translations and fonts: E2 Key Mapping/Meta Keys/Translation headings and `0x54cf`; E1 `PCPLUS.KEY` at `0x27b28`, `.KBD` at `0x28bb2`, `.FON` at `0x28c70`, `.XLT` at `0x274bf` | Recover field layouts, key binding precedence, control/Alt/function/extended keys, terminal-specific sequences, macro expansion and any font selection/loading behavior actually used. Test mappings per emulation, literal control bytes, changed/invalid mappings, saved/reloaded selections and raw-input/monitor paths. Determine whether companion keymap/font tooling is required to edit every supported setting. |
| F06 | Configuration persistence and setup: E2 Setup `0x46ae`; E3 `PCSETUP`, upgrade/reconfigure notes; E1 save error `0x2622d` and `.PRM` references | Define all settings with ranges/defaults/encoding; reconstruct load/save, cancel versus accept, paths/environment precedence, per-session overrides and external setup integration. Round-trip sanitized synthetic files and recover safely from wrong version, truncation, write failure and invalid fields. Define whether original configuration import is supported; do not silently overwrite user files. |
| F07 | Dialing directory and call accounting: E2 directory `0x15b4`, revision `0x261b`, dialing codes `0x12b5`; E1 sorting prompt `0x2c798`, directory name `0x2c022` | Recover 200-entry directory behavior, add/revise/delete/load/save/print, sorting and display modes, per-entry line/emulation/key/script/protocol options and credentials, manual dialing, up to 15 selected entries, retry/cancel and ten dialing-code substitutions. Test successful/busy/no-carrier/error outcomes, accounting and persistence with synthetic contacts only. Preserve original data/import behavior where established; prevent credentials entering capture/test/public output. |
| F08 | Transfers and protocol selection: E2 Receive `0x371f`, Send `0x446a`; E1 protocol menus `0x26d8a..0x27119`, host menu `0x2a8d9..0x2a9c2`; E3 external Kermit/B+ notes | Recover per-protocol framing, CRC/checksum, retries/timeouts, batch names/metadata, progress, abort, auto-download and free-space/path handling. Verify byte-for-byte upload/download against an independent peer, including binary/control bytes, empty/large files, cancel, bad blocks, line loss, duplicate names and disk-full. Complete every advertised built-in and external-protocol integration, not only ZMODEM. |
| F09 | External protocol/helper execution: E2 External Protocol heading; E1 runtime names at `0x2a0a1`, `0x2a0ac`, `0x2a2ce`, `0x2a2d8`; E3 low-memory restrictions | Recover command construction, environment/handle sharing, serial/vector handoff, child return/error handling and memory release/reacquisition. Provide source-built equivalents or compatible interfaces for required helpers. Test a successful and failing child, missing executable, low memory and cancellation; resume terminal without lost ownership or corrupted state. Never infer an executable interface from its filename alone. |
| F10 | Capture, logging, snapshots and printer: E1 commands `0x26081..0x260c7`, `PCPLUS.LOG` at `0x2776e`, log error `0x29970`; E2 status description `0x5059` | Recover open/close/pause/resume, append/overwrite behavior, data versus screen capture, snapshot format, printer toggle/device output and any timestamp/control filtering. Verify exact bytes and failure behavior under pause, disk-full, unavailable printer and lost carrier; status display must agree with actual capture state. |
| F11 | Redisplay, screen search and clipboard: E2 Redisplay `0x3e1f`, Clipboard `0x0973` | Reconstruct advertised up-to-63,000-character scrollback, line/page/end navigation, case-insensitive search, buffer write and snapshot behavior. Recover filename extraction, list editing, one/tagged/all paste and separators. Test wrap, long lines, control sequences, stale filenames and clipboard use during batch and single-file transfers. |
| F12 | Chat, elapsed time, monitor and miscellaneous terminal actions: E1 `0x25f95..0x26037`, `0x261e3..0x26205`; E2 Chat `0x0842`, elapsed/monitor headings | Recover split-screen chat and its send modes, screen clear/reset/pause, elapsed timer, incoming/outgoing monitoring and status/line-count toggles. Test no dropped serial input while navigating modes, correct local/remote panes, exit behavior and timer rollover. Some controls are currently known only by labels and require call/data tracing before expected semantics can be fixed. |
| F13 | ASPECT scripts and recorder: E2 Script Selection `0x41af`, Record `0x3c69`; E1 startup script at `0x29964`, errors `0x2a16f..0x2a2ea`; E6 full-original startup/compiler test | Recover compiled format, VM/interpreter, types/variables/control flow, command inventory, I/O/timing/UI/transfer bindings, invocation arguments, compiler diagnostics, cancellation and recorded-script generation. Supply a source-built compiler/interpreter or an explicitly compatible source toolchain; original `ASPCOMP.EXE` cannot be the final build/runtime dependency. Test startup/manual/per-directory scripts, `.ASX` selection and PCPLUS environment search, recorded script compilation/replay, blocking input and terminal scheduling. A working three-command startup script does not prove language completeness. |
| F14 | Host mode: E2 Host headings (body omitted); E1 commands/status `0x2a830..0x2b031`, resource names `0x2cc7a..0x2ce19` | Recover inbound answering, authentication/new-user/sysop roles, permissions/time limits, caller state, file listing/view/transfers, chat/page, read/leave mail, shell/remote shutdown authorization, idle timeout and recycle/disconnect. Recover host storage/resources from formats/code using synthetic users. Test two independent callers, privilege boundaries, invalid login, dropped connections and persistence. Host mode remains in full application scope despite not being needed for outgoing BBS dialing. |
| F15 | DOS/filesystem/editor integration: E2 Change Directory `0x076c`, File Directory/View/PCEDIT headings; E1 `0x26167..0x261ae`, `PCEDIT /N` at `0x27872`; E3 helper and DOS Gateway notes | Recover file picker/viewer, drive/path changes, default upload/download paths, external/internal editing contract and DOS Gateway spawn/resume. Test DOS path/drive semantics, wildcards, 8.3 names, absent media, read-only files, invalid paths, child exit codes and resource/IRQ restoration. Keep file operations confined to test media during validation. |
| F16 | Compatibility and build distribution: E3 memory/upgrade notes; E1/E5 image layout; E6 pinned Nix toolchain | Establish supported CPU/DOS/video/memory configurations and produce buildable source/resources, DOS executable(s), packaging and run instructions. Verify clean checkout with originals physically unavailable, reproducible input/toolchain identity, no embedded original executable blobs and every linked dependency accounted for. Test conventional-memory behavior, font/video variants and target DOS hardware; publish measured limits and unresolved compatibility instead of claiming the old requirements were met by an 8-MB emulator run. |

## Named terminal and protocol coverage

Verified source-built subcases, with every whole-feature gate still open:

| Gate | Implemented subcase | Evidence and remaining boundary |
| --- | --- | --- |
| F01 | Static printer/modem far-code modules with resident ABI and checked PROGRAM retention | `FAR_CODE.md`, `MODEM_FAR_CODE.md`; current MZ/map checks verify87 bridge pairs, distinct code segments, register/cdecl adaptation, relocation/return forms and retained extents. Linked IRQ/IRET and nested far calls are tested; an actual DOS child samples PRINT/MODEM/CONFIG modules before/after allocation/fill. `CONFIGURATION_FAR_CODE.md` adds the small-model C configuration code segment and explicit caller-cleaned entry/callback frames. `UI_FAR_STORAGE.md` keeps three distinct4000-byte browser/editor/PROGRAM frames outside DGROUP. Current resident code is65,298 bytes and near data/stack64,480; pending menu entry reuses the existing typeahead FIFO. Full startup/resources, broader segmentation, dynamic overlays and every original export remain open. |
| F02 | Maintained command menu/help, original snapshot/flow services and directory editor | `UI_WINDOWS.md`;389 exact bytes, maintained rectangle bounds,28 snapshot and32 full flow-chain original comparisons, actual DOS nested/cursor/timed-message tests, and terminal-linked UART save/paint/restore. `DIRECTORY_EDITING.md` adds native staged record editing with masked passwords and screen/cursor restoration. `SETUP_EDITOR.md` adds an offline46-field staged DOS settings editor. `SETUP_STARTUP.md` adds direct setup-before-connect with post-child validation. `SETUP_LIVE.md` adds Alt-F10 direct editor invocation and validated selective display/mapping/modem/BREAK application during the session; confirmed same-port serial changes and idle COM moves are supported. `PROFILE_LIVE.md` adds confirmed4/6 switching, staged canonical KBD selection and a clean view/RIS baseline. `COMMAND_MENU.md` adds a maintained Alt-Z five-group command menu, contextual topic help and bounded ASCII prose search, sharing serviced live/frozen frames and dispatching existing commands after close. 151 menu and36 pending-entry linked inputs and four actual DOS observer/file/PRMEDIT/partial-CSI workflows cover navigation, replies, checked command owners, hangup/redial and ownership. Selected stock menu-to-clipboard downloads also pass; a refused early Synchronet attempt remains explicit. Original layout/mouse paths, full settings/key editing and other geometries remain open. |
| F03 | UART receive ring, bounded transmit, software/hardware flow service and restoration | `UART.md`, source-driver replay and DOSBox serial tests; interactive `TERMINAL.EXE` validates COM/baud/line/flow options and restores hardware on normal and unsupported-operation exits. The connection workflow now supports explicit/directory dialing and serviced carrier/hang-up state. `BREAK_NATIVE.md` records the native helper/calibration; `LIVE_BREAK.md` adds serviced Alt-B with TEMT drain, held TX/flow, conservative BIOS-tick duration, raw PRM delay and checked cancellation/restoration. Linked and actual DOS LCR/video samples cover the owner; `PORT_HANDOFF.md` adds confirmed idle COM1–4 moves, preserved target DTR, repeat-at-commit preflight and command/profile rollback: 69 primitive cases,33 foreground transactions and six actual DOS cases check repeated/shared-IRQ migration, traffic and final restoration. Connected moves remain deferred until hangup/drain. The retained matched stock Synchronet comparison in `lab/bbs/flow-control.md` holds COM2/19200 and all other inputs fixed: SOFT consumes Ctrl-Q as modeled XON, while HARD delivers it and aborts the editor. Physical UART/BREAK validation and full F03 remain open. |
| F04 | ESC/CSI parsing, cursor positioning, SGR helpers, J/K/X erase and status/device replies | `CSI.md`, component ledgers, `validation/csi-*.json`; memory I/O and modeled BIOS in CPU tests, real BIOS erase in DOSBox. Direct modes, DECCKM key rewriting and mode25 BIOS shape now pass; continuous serial integration now passes local Synchronet/ENiGMA½/Mystic menu workflows; native nonzero reset/profile loading, remaining width/protected-attribute services and other emulations remain open. |
| F04 | Low-level direct/BIOS character, packed-cell and fill output | `TEXT.md` and `evidence/text`; the recovered high-level renderer now wraps/scrolls, with 531 original-comparison operations; continuous input/ESC/CR/LF/BS/TAB/history now passes DOS and 330 original-comparison operations; specialized controls/mode/font paths remain open. |
| F04 | Full-state versus position-only cursor save/restore | `CURSOR_STATE.md` and `validation/cursor-state-*.json`; standalone source instructions match 48 original scenarios. Unknown saved-state semantics and complete terminal integration remain open. |
| F04 | Recovered insert/delete-line helpers and maintained live policy | `LINE_EDIT.md`, `LIVE_LINE_EDIT.md`;504 exact original bytes, real video helpers and a separately retained indefinite historical wait. Live NETWORK bounds counts/regions and preserves columns; ORIGINAL supplies a serviced36-tick alternate wait. Eight linked synthetic policy groups pass; complex900c repair still stops at2d98. Full interactive editor success requires its own current runtime evidence. |
| F04 | Character insert/delete and HTS | `CHARACTER_EDIT.md`;1,095 exact bytes,43 native CPU cases and real DOS video checks. Live wrappers bound repetition, validate geometry and preflight unsupported repair; nine linked parser/video groups pass. Viewports and complex repair remain open. |
| F04 | Native reset reconstruction and maintained current-profile RIS | `TERMINAL_RESET.md`, `LIVE_TERMINAL_RESET.md`; 2,301 exact native bytes with original comparisons. Native nonzero reset stops at its unrecovered KEY/profile-loader boundary. Live ESC c restores captured startup state/keymap/tabs for profiles 4/6, clears/homes via real helpers and preserves transport/configuration ownership. `PROFILE_LIVE.md` now adds confirmed4/6 profile changes with staged target keyboard selection, clean local view/reset state and no serial reconnection. This maintained RAM policy does not implement all original reset modes or emulations. |
| F05 | Raw79-slot keyboard classification, explicit KBD import and enhanced BIOS selection | `KEYBOARD.md`, `KEYBOARD_MAPPING.md`, `KEY_MAPPING.md`, `LIVE_KEYBOARD.md`; recovered mapping code plus36-byte BDA detector, lossless KBD/KEY codecs, strict read-only profile import and bounded live output. Maintained network defaults are source-owned rather than factory tables.95 linked raw-key inputs and ten actual DOS delivery/import cases pass, including F11/F12 modifiers and NUL. KEY dispatch/TEXT/HOOK construction now has978 exact recovered bytes; global /T KEY import and nonblocking TEXT are integrated (LIVE_META_KEYS.md). Maintained PROGRAM/process execution now supports stored commands with bounded child/UART handoff; native PROGRAM dependencies are tracked separately below. ASPECT/HOOK, full keymap editing, factory defaults and physical BIOS validation remain open. |
| F05/F06 | XLT native operations and checked standalone DOS import | `TRANSLATION.md`;176 exact recovered bytes and2,082 CPU/original comparisons cover file operations, identity and a translated receive helper. Main-loop mapping, raw parser continuation and overlay3 selection are traced separately. The maintained exact256-byte loader passes nine actual DOS filesystem and22 declared error/argument checks with destination preservation. `LIVE_TRANSLATION.md` adds explicit `/X` startup selection and normal receive mapping,783 linked inputs and seven actual DOS cases; continuation/TX/monitor/binary owners retain raw bytes. Saved PRM modes0/1/2 and the46-field editor now preserve, validate and classify translation selection;12 actual DOS cases and561 mode inputs cover startup, driver masking and live deferral. The maintained offline `XLT_EDITOR.md` adds table editing/save/reload with checked persistence and 19 actual DOS cases; bounded default XLT environment fallback is covered by `RESOURCE_LOOKUP.md` with117 linked inputs,30 DOS assertions and12 actual DOS startup cases; confirmed live mode adoption is covered by `LIVE_TRANSLATION_SETUP.md` with331 linked inputs and10 actual DOS workflows. `TRANSLATION_RELOAD.md` adds explicit Alt-F9/menu same-table reload from the frozen actual source,66 linked inputs and eleven production DOS workflows. `TRANSLATION_EDIT.md` now covers Alt-F8/menu invocation of the sibling XLTEDIT for the frozen actual selected table, checked post-editor reload,55 linked inputs and eight actual DOS workflows. Lookup for other resources remains open. |
| F06 | Proved PRM/modem fields, lossless host codec, DOS load/save/replacement and assembly/C ABI | `CONFIGURATION.md`, `MODEM_CONFIGURATION.md`; original replay, synthetic codec and real-file/fault/ABI DOS tests. `SETUP_EDITOR.md` adds offline mapped-field validation, staged editing and checked replacement. `SETUP_STARTUP.md` adds explicit setup before UART acquisition with existing CLI precedence. `LIVE_CONFIGURATION_PLAN.md` adds pure validated candidates, retained-directory decoding, CLI precedence and semantic change classification. `SETUP_LIVE.md` adds canonical identity binding, current-rate snapshots, validated selective live adoption, confirmed same-port serial changes, supported4/6 profile switching and confirmed idle COM moves; `CONFIGURATION_FAR_CODE.md` links the candidate decoder in its own code segment. Complete defaults/schema, restart recovery, path precedence and connected cross-port migration and complete profile/emulation coverage remain open. |
| F07 | Canonical250+200×114-byte directory, native editor and deferred accounting | `DIRECTORY.md`, `DIRECTORY_LIVE.md`, `DIRECTORY_EDITING.md`; lossless codec, strict streaming IO, startup browser/editor, expected-record staged replacement and MODEM/DIRECT dialing. `DIRECTORY_ACCOUNTING.md` proves220 original bytes and the year2000 count-byte defect; bounded maintained patch fixes it. Actual DOS covers save/cancel/conflict/recovery, accounting and password metadata without transmission; current terminal passes local Synchronet/ENiGMA½/Mystic audited menu navigation. `DIRECTORY_CONTEXT.md` adds retained raw headers/records and logical request identity for future live setup, separate from accounting. Complete original directory commands, cycles, script/key/transfer bindings, automatic restart recovery and DTP conversion remain open. |
| F08 | Native sender, receive-session composition, file handling and maintained DOS storage | `TRANSFER_BLOCKS.md`, `TRANSFER_RECEIVE.md`, `TRANSFER_SEND.md`, `TRANSFER_FILES.md`, `TRANSFER_SESSION.md`, `TRANSFER_UART.md`, `DOWNLOAD_STORAGE.md`; CRC/framing/receiver helpers plus1,240 sender,1,657 file,1,027 owner and90 UART-helper exact bytes. One native owner now spans multiple CRC/checksum blocks, actual setjmp/longjmp, retry/cancel/EOT and periodic/final file control. Actual DOS composition checks binary storage and installation/failure gates; separate UART component sends1,024 exact binary bytes. Standalone composite UART/time remain fixtures. Live Alt-R now uses the real UART/native owner with checked staged DOS files, CRC/checksum128/1024 and deferred final ACK after installation; see `TRANSFER_INTEGRATION.md`. Full shadow/history arrays moved far without changing the near receiver ABI, with PROGRAM retention and actual DOS memory-canary tests. Alt-S now connects the native ordinary sender to checked read-only DOS source ownership, with DWORD input accounting, binary1Ah preservation, exact-once close and actual-ACK progress; see `LIVE_UPLOAD.md` and `UPLOAD_SOURCE.md`. Maintained live CRC YMODEM is now integrated; see `LIVE_YMODEM.md`. Physical peers, window/streaming/other protocol families, logging and full transfer/settings UI remain open. |
| F08 | Native batch metadata and bounded maintained codec | `TRANSFER_METADATA.md`, `TRANSFER_BATCH_SEND.md`, `TRANSFER_BATCH_RECEIVE.md`; 1,140 newly recovered header/parser/terminator/CRT bytes pass 127 comparisons against original instructions and an actual 8086 DOS diagnostic. The separate bounded DOS codec passes 1,611 host-oracle and 221 DOS checks, with optional metadata and unknown-length flags. The metadata checkpoint reproduced 39 outputs; the current batch-owner proof extends this to 43. Maintained checked per-file owners, DTA-preserving enumeration and live CRC YMODEM receive/send now complement these exact native diagnostics; see `LIVE_YMODEM.md`. Standard final ACK is distinguished from a peer returning application text with its ACK missing. Other protocol families, full settings/UI and physical peers remain open. |
| F09/F05 | Native PROGRAM core and maintained live child execution | `PROGRAM_EXEC.md`; 3,102 exact native bytes include EXEC, environment/tail and extension/PATH behavior, with explicit heap/application dependencies. Separate maintained process/COMSPEC policy and live Meta PROGRAM suspend/reacquire UART/vector/video ownership; current checkpoint `036a8092` linked regressions and separate actual DOS owned-child tests cover success/failure/restoration. The maintained command policy now executes in CONFIG_CODE with a checked resident DOS EXEC callback; `CONFIGURATION_FAR_CODE.md` and `validation/program-far-code.json` bind60 linked inputs and four actual DOS workflows to that placement. This does not establish the HOOK pointer protocol, external transfer-module ABI, full original PROGRAM/UI lifecycle or ASPECT execution. |
| F10 | Native capture/snapshot and maintained checked live owners | `CAPTURE_NATIVE_INVENTORY.md`, `LIVE_CAPTURE.md`, `SCREEN_SNAPSHOT_NATIVE.md`, `LIVE_SNAPSHOT.md`; retained REA assembly establishes original append-text/newline and distinct printer/snapshot/raw/script paths. Native snapshot adds381 exact bytes,24 comparisons and an actual8086 DOS diagnostic. Alt-F1/F2 text capture and Alt-G screen files use independent checked DOS owners with canonical internal-conflict exclusion. Eleven actual DOS cases pass for each feature; linked failure/shadow/NUL/SUB/PROGRAM tests and file-fault suites remain separate. Native printer adds79 exact bytes plus the reused132-byte logger,66 CPU/original comparisons and an actual8086 DOS memory-CRT diagnostic (`PRINTER_NATIVE.md`). `RAW_MONITOR_NATIVE.md` and `LIVE_MONITOR.md` add503 exact native bytes/27 comparisons, a stateful Ctrl-backslash raw view, third checked replacement owner,160 file assertions, nine linked groups and15 selected actual DOS cases. Received monitor bytes bypass processed capture; initial PRM oracle failure remains in history. `LIVE_PRINTER.md` adds Alt-L checked PRN copy,128-byte queue,18-tick no-progress bound and PROGRAM/transfer ownership gates: eleven linked groups/293 inputs,57 backend fault assertions and nine actual DOS virtual-printer cases pass on f2c75bf7. `PRINT_SCREEN_NATIVE.md` adds365 exact screen/media-copy bytes and38 CPU/original comparisons, retaining the native stale-FILE defect in diagnostics only. `LIVE_SCREEN_PRINT.md` adds incoming CSI0/1 and private4/5 with a frozen2000-byte raw character frame, the recovered mode18/19 state and checked PRN reuse/close. Nine linked groups/2037 inputs,11 actual DOS screen-print cases and3 stream-copy regressions pass on d4cfa4dc. CEAC is the transient private prefix, not a saved policy; see `SCREEN_PRINT_POLICY.md`. `PRINT_CONTROLLER_NATIVE.md` adds416 exact dedicated-controller bytes,28 CPU/original comparisons and an8086 DOS diagnostic, preserving native raw/escape/CRT quirks. `LIVE_PRINT_CONTROLLER.md` adds maintained standard5i raw mode with bounded escape buffering, checked PRN reuse/close, serviced keyboard/serial/capture polling and cancellation. Its hash-bound report distinguishes linked models from actual DOS virtual-device evidence. The local screen-print binding, complete snapshot/monitor geometry/status modes, ASPECT/HOOK and physical validation remain open. |
| F11 | Serviced maintained redisplay over the native history format | `LIVE_REDISPLAY.md`; separate63,000-byte live ring/frozen snapshot, Ctrl-PgUp line/page/Home/End navigation, ASCII case-insensitive search/F3, bounded foreground search and live-screen/cursor preservation. Linked native writer checks full ring wrapping; linked viewer and independent actual DOS video/UART tests verify browsing/search with incoming data. W adds serviced checked append/CRLF history export; `HISTORY_EXPORT.md` binds27 linked inputs and three actual DOS workflows, including append past70KB and canonical four-owner exclusion. `FILENAME_CLIPBOARD.md` adds Alt-= and redisplay C,15-entry editing/tagging, recovered bounded extraction and one/all/tagged packets with runtime separators.46 linked inputs and two actual DOS observer/peer workflows cover serviced output, partial cancellation, UART-completion Single removal and connection-queue discard. The core passes614 linked inputs,321 optional original comparisons and559 actual8086 DOS assertions. `CLIPBOARD_SETTINGS.md` adds validated PRM04EA startup import,46th editor field, live adoption and session-R preservation:805 linked inputs and7 actual DOS workflows. `CLIPBOARD_TRANSFERS.md` adds six actual DOS Single/Tagged/All selection workflows across strict XMODEM/YMODEM peers, stale-name/canceled-prompt recovery, post-transfer reuse and external BIOS ownership observation. Selected stock Single/download workflows pass Synchronet Filespec/XMODEM and ENiGMA search/YMODEM plus a second post-transfer clipboard search (`validation/bbs-clipboard-transfers.json`); four failed ENiGMA fixture attempts remain explicit. Stock uploads/multi-name conventions, full original UI, other video geometries and physical modem validation remain open. |
| F16 | Source-only builds of current diagnostics and interactive terminal through pinned Nix tooling | `validation/isolated-source-build.json`, `validation/application-components-source-build.json` and `validation/terminal-source-build.json`; the current snapshot reproduces64 byte-identical outputs, including the filename clipboard core, retained-directory-context and pure live-configuration candidate diagnostics, offline PRMEDIT settings and XLTEDIT table editors, bounded resource-path and settings-CWD diagnostic children, capture, three file owners, screen-file, checked printer device, native screen-print/controller and monitor diagnostics. The complete application still depends on unrecovered code/resources and has no source-only whole-application build. |

ZMODEM now runs from Alt-R/Alt-S/F2 through CONFIG_CODE engine/codec/far callbacks,
serviced UART and checked batch storage/source seek. `LIVE_ZMODEM.md` records
linked workflows, prior-owner exclusion, independent actual DOS lrzsz transfers,
failed initial large-upload fixture attempts and the current source rebuild.
`ZMODEM_SESSION.md` and `ZMODEM_WIRE.md` retain independent component evidence;
`ZMODEM_NATIVE.md` records original common/send/receive overlay analysis.
Component corruption recovery passes lrzsz and a selected stock Synchronet
helper. Actual stock BBS sessions, fuller recovery/timing coverage, full
streaming/window behavior, auto-download and physical modem remain open;
F08 remains open.

The application now admits supported line attributes under NETWORK policy through
`LINE_ATTRIBUTES.md`: bounded active-region shifts, native video-only callbacks
and region-limited native field repair, with512 linked cases,45 pre-edit geometry
rejections and explicit-fixture actual DOS video/backing checks. Exact standalone
line helpers and ORIGINAL semantics retain their historical constants. This is
additional F02 coverage, with no whole-application gate closure.

E2 advertises TTY; DEC VT52/100/102/220/320; ANSI X3.64; IBM
3101/3161/3270/PC; TeleVideo 910/912/920/922/925/950/955; DG 100/200/210;
ADDS 60/90; ADM 3A/5/31; Wyse 50/75/100; ATT 605/4410; Heath 19; and
ESPRIT 3. E1 labels the 3270 selection `3270/950`, so its precise relationship
to IBM 3270 is unresolved. Menu labels and help are not a protocol specification;
compare dispatch code and original runtime fixtures before assigning behavior.

E1 protocol labels advertise XMODEM, 1K-XMODEM, WXMODEM, 1K-XMODEM-G, YMODEM,
YMODEM-G, ZMODEM, KERMIT, COMPUSERVE B+, ASCII, RAW ASCII, TELINK, MODEM7,
and IMODEM. The Host menu additionally names SEALINK. External protocol slots
are visible at `0x270f6..0x27119`. Map selection values to actual handlers and
resources before treating any label as implemented. Record any directional
restrictions or differences between terminal and Host transfers in the matrix.

## Supporting artifact inventory

The table describes required investigation, not permission to redistribute
original files. Keep all installed user/configuration data private. Required
default resources should be generated or authored from source; compatibility
with a user's original resource can be an optional, documented path.

| Artifact/interface | Local evidence and state | Work required |
| --- | --- | --- |
| `PCPLUS.EXE` | E1/E4 present; resident module plus overlays (E5) | Recover full application or explicit maintained equivalents, including generated resources; remove original from final inputs. |
| `.PRM`, `.DIR`, `.KEY`, `.KBD`, `.XLT` | Named in E1/E3; corresponding active-install files present | Format-aware parsers/serializers with synthetic fixtures, version/error handling and private-data exclusions. `TRANSLATION.md` establishes the selected 2.01 XLT's headerless256-byte table and checked DOS loader and explicit live `/X` selection; saved PRM modes and mode editing are integrated; the maintained offline `XLT_EDITOR.md` now covers table editing and reload, while confirmed live mode changes are covered by `LIVE_TRANSLATION_SETUP.md` and explicit same-mode reload by `TRANSLATION_RELOAD.md`. Explicit Alt-F8/menu invocation and checked return adoption are covered by `TRANSLATION_EDIT.md`. E3 says upgrade can convert older formats; older format/version distinctions remain unknown. |
| `PCPLUS.FON` | E1 reference; E4 present, 144,365 bytes | Trace format and supported video/font paths; source-build required font resources or document supported alternatives. The extension alone does not establish its contents. |
| `PCPLUS.HLP`, `PCHELP.RTE` | E2 plus E1 names at `0x27dfc`, `0x27e22`; both installed | Recover help index/access/runtime integration; author maintainable help without publishing the original text. |
| `PCSETUP.EXE` | E3/E1; installed | Reconstruct settings coverage and invocation/persistence interface; decide integrated versus separate maintained executable after tracing. |
| `PCKEYMAP.EXE`, `PCEDIT` | E1/E3; not found among the 32 active-install filenames | Recover interfaces/features; absence from one copied install does not establish unsupported original behavior. `TINYEDIT.EXE` is installed but has not been established as the configured substitute. |
| `ASPCOMP.EXE`, `.ASP`, `.ASX`, `FLOAT.RTE` | E1 names; compiler installed; floating runtime not in active install | Compiler/VM format and full command surface remain open. Trace when FLOAT.RTE is required; no assumption that startup-script success covers floating operations. |
| `KERMIT.RTE`, `CISB.RTE` | E1 names and E3 external-protocol note; not in active install | Recover loader/protocol interface and source equivalents; test missing-module behavior and actual transfers. |
| `HCOMMAND.RTE`, host `.HPM/.HRM/.HST/.HXM/.NWS/.USR/.NUF/.HDR/.MSG/.HDL/.HHP/.ULD/.HMM` | E1 names; `.HST/.NWS/.HDR/.MSG` installed, other listed filenames absent | Trace format and purpose per file; do not assign roles merely from extensions or inspect private user/message content. Build synthetic host fixtures and source-owned prompts/help/defaults. |
| `PCPLUS.LOG`, `.SCR`, `.DMP` | E1 names; `.SCR` installed, other two absent from copy | Establish produced-file format and consumers without publishing captured sessions. |
| `PCINSTAL`, `MODEMS.DAT` | E3 references; absent from active install | Determine initialization/upgrade obligations and modem-profile schema. A maintained installer need not reproduce old distribution disks, but must generate valid initial resources without proprietary inputs. |
| Custom wrappers and utilities | E4 includes `.BAT` wrappers, TXZM, TINYEDIT, SNIPPER, Greek text and an archive | User-install additions, not established core PCPlus components. Inspect command/handle contracts separately, preserve configured integrations or identify incompatibility. Do not claim every adjacent utility is a required original product feature. |

## Memory and compatibility evidence to preserve

E3 claims a 192-KB-free-memory limited configuration and recommends 295 KB for
the full original configuration. Below 295 KB it describes restrictions on
external setup/keymap/editor/compiler invocation, Kermit/B+ modules, DOS Gateway,
help, redisplay size and video modes. It names 25-by-80 operation and warns
against 132-column software emulation in the limited configuration. E1 also has
a 132-column allocation-failure message at `0x285a4` and the candidate token
`NOEMS` at `0x29c22`; no complete command-line or EMS contract is established by
that token. Recover option parsing and memory/video services before asserting
compatibility, and distinguish required historical behavior from documented new
limits. Low-memory external execution must fail cleanly even if the maintained
application eventually has different measured memory needs.

## Evidence gaps and next actions

1. Map every menu selection, help topic, terminal type and protocol selector to
   entrypoints, state and external dependencies. The 502 export-entry inventory
   is a useful finite audit set; exported-function count does not measure feature
   completion. Keep overlay-parent/lifetime constraints in that map.
2. Trace `.PRM` and default initialization first, followed by `.KBD/.KEY/.XLT`
   and `.DIR`. Record fields read/written and validation branches, then create
   synthetic fixtures. Do not derive defaults from this user's customized files.
3. Capture sanitized original runtime scenarios for the features with condensed
   help bodies. UI screen captures, serial streams and DOS child-process traces
   should identify exact inputs and expected outcomes; do not contact real
   callers or BBS accounts as an incidental inventory step.
4. Enumerate the ASPECT interpreter dispatch and compiler format, protocol
   handlers and Host command loop. Identify required missing helpers explicitly;
   a successful minimal original install launch does not establish feature
   availability or full dependency closure.
5. Add one implementation/evidence row per feature as source modules land. Close
   F01–F16 only against verified source-built behavior and clean-input builds.
   Physical UART/Wi-Fi modem/BBS and original DOS-hardware checks remain open
   until the actual setup is available and exercised.

No original source/build project, complete uncondensed manual, distribution disk
inventory, documented companion-module ABI, or complete behavioral specification
was established by this pass. The active install is therefore evidence of what
this machine contains, not the complete PCPlus distribution. Revisit this
inventory when code/resource tracing discovers additional features; do not treat
the initial matrix as permission to omit them.

The [ASPECT path-command checkpoint](ASPECT_PATHS.md) extends F13 with CHDIR,
MKDIR, RMDIR and DELETE in both maintained compilers and the DOS runtime.
Native byte/grammar conformance, real DOS file/directory effects and retained
drive/CWD are verified separately from the actual terminal login-child handoff.
This adds four supported slots (76 total, 139 unsupported); it does not close
F13, F15 or any whole-application gate.

The [stream-command integration](ASPECT_SCRIPT_FILE_RUNTIME.md) subsequently adds
thirteen file commands and FGETS_CRLF SET/FETCH, with both compilers and real
normal/error/cancel/EXECUTE file ownership. The current runtime has 89 supported
slots and 126 unsupported slots. Actual DOS repeated-invocation and parent-child
tests plus the isolated owned ENiGMA source login pass; complete language/recorder,
original warning/CRT equivalence and all whole-application gates remain open.

The modem segmentation checkpoint in `MODEM_FAR_CODE.md` extends F01 with a
separate controller/sender CS and explicit caller-cleaned stack adapters. It
frees1,184 resident code bytes and validates44 bridge pairs plus retained modem
code under DOS allocation. This is additional F01 progress; it does not close
the complete startup/overlay/UI or source-only whole-application gates.


The subsequent `d0274a22` checkpoint adds8 KiB reception without another resident
payload buffer and validates logged-in local Synchronet/ENiGMA upload/download
workflows. The ENiGMA selector-first fixture bypasses the unresolved fragmented
arrow issue. Exact scope, all failed attempts, memory and artifact identities
are recorded in [ZEDZAP_BBS.md](ZEDZAP_BBS.md). All F01–F16 gates remain open.


The `d791eb10` maintained sender adds bounded asynchronous windows and separate
receiver-capacity accounting. Confirmed replay refreshes the live inactivity
watchdog; the engine separately bounds repeated rewinds. Paired counterexamples,
DOS files/far callbacks and selected modern BBS flows are documented in
[WINDOWED_ZMODEM.md](WINDOWED_ZMODEM.md). This advances F08 without closing
any F01–F16 whole-application gate.

The automatic-reception prerequisite recovers the original Auto Download trigger
and separately tests a maintained CRC-valid canonical invitation recognizer.
It preserves rejected/truncated bytes across 6,510 host and 8086 DOS vectors;
[ZMODEM_AUTOSTART.md](ZMODEM_AUTOSTART.md) distinguishes recognition policy from
original behavior and lists pending settings, ownership and BBS integration.
Automatic reception is not enabled, and F08 remains open.

At checkpoint `fd2b490`, the mapped PRMEDIT editor exposed Auto Download and Download directory,
with a separate checked transfer-settings decoder and 48 mapped fields.
[TRANSFER_SETTINGS.md](TRANSFER_SETTINGS.md) records 450 model inputs, 19 DOS
editor/owner workflows, seven production clipboard/settings regressions and a
fresh 64-output source-only rebuild. At that checkpoint the preferences were not yet adopted
by the terminal; the integration below advances that work.


The `731418bd` runtime adds canonical CRC-valid automatic ZMODEM reception,
one-image startup staging and live-child preference adoption. Serviced partial
prefixes return to the normal parser on expiry or local-owner changes; BIOS
midnight preserves the inactivity interval. The checked file owner now handles
drive-relative current directories. All 80 terminal commands, 60 preference
inputs, 384 damaged-MZ guards, three actual DOS and two stock BBS automatic
workflows pass; 64 outputs rebuild byte-identically without originals. See
[ZMODEM_AUTOSTART.md](ZMODEM_AUTOSTART.md). The ENiGMA fragmented-key issue,
other invitation forms, wider protocols/UI, ASPECT, Host, physical peers and
all F01–F16 whole-application gates remain open.


The isolated [ENiGMA keyboard experiment](../lab/bbs/patches/enigma-key-stream/README.md)
adds actual Client/editor evidence for the chunk-local decoder boundary: 74 stock
key-event and nine editor-state failures are reproduced; the candidate passes
112 checks against stock unfragmented results, 1,638 framing checks and 123
selected upstream regressions. This changes no DOS code or running stock server.
Patched-server/DOS/transfer integration and physical modem validation remain
open, so it does not resolve the stock interaction issue or close F04/F05.


[Actual DOS paired ENiGMA evidence](ENIGMA_KEY_STREAM_DOS.md) extends the isolated
parser experiment: the same binary/recipe with immediate forwarding fails Home
and Insert on stock and passes seven editor checks on the patched instance. A
same-session draft discard, automatic ZMODEM download and post-transfer file
search passes 20 checks, with exact bytes, restored hardware, unchanged message
count and one official download-count increment. The failed initial menu recipe
is retained. No DOS code changed, and broader timing/physical modem and F04/F05/F08
completion remain open.


F13 now has a source-owned [nonempty ASPECT literal codec](ASPECT_LITERAL.md),
with91 whole-compiler probes,44 exact payload vectors,725 native/C comparisons
and52 native first-pass cases. The maintained component passes2,080 host and
1,403 actual8086 DOS checks; it joins a65-output original-free source rebuild.
This does not compile or execute a script. Full loader/VM/grammar/commands,
recorder, floating runtime and application scheduling/invocations remain open.

F13 also has a source-built224-byte native dispatch loop,590 CPU scenarios and
3,616 linked8086 DOS assertions. The loop's callbacks substitute real opcode,
loader, file and UI services. Selected original application flow probes and120
compiler declaration probes provide baseline evidence, while the keyword/table
inventories bound further reconstruction. See [ASPECT_DISPATCH.md](ASPECT_DISPATCH.md).
This component joins a66-output original-free rebuild; full ASPECT execution,
compiler, recorder and all whole-application gates remain open.

[ASPECT global-string primitives](ASPECT_GLOBAL_STRINGS.md) add101 recovered
bytes and a separate linkedDOS diagnostic to F13.616 CPU scenarios cover
far pointers and allocation-failure models;705,369 DOS byte/state assertions
cover counts0..128 and cleanup ordering. Heap/error callbacks remain models,
with native bounds/rollback/double-release limitations explicit.67 outputs now
rebuild from maintained source; F13 and all whole-application gates remain open.

F13 now includes [native stack and nonlocal unwind composition](ASPECT_EXECUTION.md):
197 typed-stack bytes,63 abort bytes,786 CPU scenarios,2,286 standalone stack
DOS assertions and72 composed DOS cases/1,968 assertions. Real setjmp/longjmp
restores dispatcher state after modeled faults and a genuine native stack guard
failure, while file/UI/opcode/resource callbacks remain diagnostic substitutes.
The current69-output source rebuild still does not implement full ASPECT or
close any whole-application gate.

F13 gains [file-backed native control flow](ASPECT_FILE_FLOW.md):330 exact bytes,
457 CPU scenarios and631 native-diagnostic DOS assertions. A separate maintained
file adapter uses actual host/DOS stdio (113/218 checks), composing buffered
word/DWORD reads, targets beyond64KiB, nested frames/returns and real abort on
short reads/position failures. No opcode loop/full script owner or expression
execution is claimed.71 outputs now reproduce without originals; all
whole-application gates remain open.


## ASPECT compiled-script execution checkpoint

A standalone source-built owner now executes authored original-compiler ASX
fixtures through the real recovered dispatcher, numeric operands/operations,
conditional branches, frame/call/return routines and nonlocal abort. Maintained
DOS stdio and far-heap ownership replace diagnostic file/heap callbacks. Of19
compiler fixtures,15 finish successfully; float, PAUSE, endless-loop budget and
recursive-stack overflow stop with their expected distinct errors. The composed
suite passes219 actual8086 DOS cases/2,179 assertions, including every191
unsupported slot, short reads, invalid headers and allocation failure/retry.

The new operand module adds381 exact bytes (4,599 CPU scenarios/16,248 DOS
assertions); operations add1,182 exact bytes (2,809 CPU scenarios covering464
native instruction addresses/4,439 DOS assertions); expression support adds501
exact bytes. Optional original-byte comparisons are separate from ordinary
source-only tests. See [ASPECT_RUNTIME.md](ASPECT_RUNTIME.md) and its frozen validation report.

Only24of215 slots are wired. General arithmetic, strings, parameters, float
runtime, application commands, compiler/recorder and terminal scheduling remain
unfinished. Native unchecked indexing/frame arithmetic limits this checkpoint
to the authored corpus. No F01–F16 gate closes; integration must also address
the terminal's near-memory limit. The interactive TERMINAL image remains731418bd.

A fresh original-free source rebuild reproduces74 outputs byte for byte, including
the three new ASPECT diagnostics. The terminal remains unchanged.


## ASPECT arithmetic and DOS divide-fault ownership

The standalone interpreter now wires36of215 native opcode slots and executes
105 authored original-compiler fixtures. Ninety finish;15 reach their expected
unsupported/float/budget/stack/division stops. The complete295-case actual8086
DOS suite passes3,794 assertions, including all179 unsupported slots and
post-fault resource restoration. General integer/long arithmetic and compiler
precedence temporaries now execute with actual recovered long helpers.

New recovery adds665 overlay17 arithmetic bytes (3,668 CPU scenarios/29,056
DOS assertions) and535 resident long-helper bytes (4,626 CPU scenarios/4,622 DOS
checks, all248 instruction addresses). Component arithmetic callbacks and actual
composed execution remain separate evidence. CPU shift masking limits are
explicit; actualDOS covers all8086 word CL counts0..255.

A maintained scoped INT0 vector turns native word MIN/-1 faults into error12,
IRETing before native nonlocal abort, then restoring the previous vector. Every
composed run checks vector and IF/DF restoration; two distinct maintained
fixtures prove file/heap cleanup with live string allocations during faults.
See [ASPECT_ARITHMETIC.md](ASPECT_ARITHMETIC.md) and `docs/validation/aspect-arithmetic.json`.

All F01–F16 gates remain open. Strings/parameters/float/application services,
compiler/recorder and terminal scheduling/memory placement remain required.
The interactive terminal stays731418bd; this checkpoint is standalone.

A fresh original-free source build reproduces76 byte-identical outputs,
including the new long and arithmetic diagnostics and expanded EXECUTE suite.


## ASPECT typed parameters and string ownership

Native parameter pushes now add66 exact bytes (3,901 CPU scenarios, all30
instruction addresses,9,731 actualDOS assertions). String selection/literals,
11-slot scratch rotation, far read/writeback and assignment add617 exact bytes
(2,251 CPU records and14,441 DOS checks). Component opaque readers/services are
explicit; the composed runtime executes actual native readers, copy routines,
real DOS files and far-heap storage.

The132 compiled authored fixtures now include typed/mixed arguments, nested
calls and locals, by-value parameter mutation, empty and80-character strings.
The full320-case DOS suite passes4,760 assertions, including all176 unsupported
slots and active-frame faults with allocated strings. String recursion hits the
native guard after376 steps; callee division/float faults unwind and free real
resources. A maintained truncated assignment preserves the committed source
and empty destination, discards pending writeback, then permits a retry.

See `docs/ASPECT_PARAMETERS.md` and `docs/validation/aspect-parameters.json`.
Only39of215 slots are wired; broad string/builtin/float/compiler/recorder and
application scheduling/memory placement remain unfinished. The terminal remains
731418bd, and all F01–F16 whole-application gates remain open.

A fresh original-free source rebuild reproduces78 outputs byte for byte.
Native E104 scratch/next-script aliasing is preserved and verified in the map;
At that checkpoint CHAIN/state999 remained unsupported; the current compiled-target EXECUTE integration is described in [ASPECT_CHAIN_RUNTIME.md](ASPECT_CHAIN_RUNTIME.md).


## ASPECT string commands and comparison status

Eleven native string/byte commands add401 exact bytes,2,058 CPU scenarios
covering all196 instructions, and27,819 actual8086 DOS assertions. All37
component code ranges compare exactly with the original. New173-byte services
and168 reused CRT bytes provide actual comparison, case conversion, fill,
operand/store and status behavior; file/error/builtin callback limits remain
explicit in component diagnostics.

The composed runtime now wires50of215 slots and executes184 authored compiled
fixtures. Its361-case DOS suite passes5,371 assertions. New fixtures cover
concatenation, comparison, length, peek/poke, fill/update/substrings, local and
parameter operands, zero counts, CP437 bytes and true/false SUCCESS/FAILURE
branches. Six native range/overflow errors preserve committed strings and free
resources; the owner retains native error1/3 while mapping to operand error7.

See `docs/ASPECT_STRING_COMMANDS.md` and its frozen validation report. Only the
selected command surface is established: other string/format/builtin services,
float/compiler/recorder and terminal scheduling/memory integration remain open.
The interactive terminal remains731418bd; all F01–F16 gates remain open.


F13 now has [decimal conversions and a maintained host compiler](ASPECT_CONVERSIONS.md):
218 exact command/scanner bytes plus312 CRT bytes,1,711 command CPU scenarios,
8,282 DOS assertions and104of104 command instruction addresses. CRT testing adds
4,943 CPU vectors and1,234 actual DOS vectors/6,694 assertions.54of215 runtime
slots now execute;161 explicitly abort. The maintained compiler emits237 authored
fixtures byte for byte against the frozen oracle, plus237 presentation variants.
The diagnostic build compiles their source before410 DOS cases/6,090 assertions.
Independent nested-expression cases establish distinct temporary indices and
boolean jump fixups; source compilation itself no longer depends on ASPCOMP.
The host compiler covers the tested grammar, not full ASPECT or a DOS-hosted
compiler. Float/formatting/recorder, serial/UI bindings and terminal memory/
scheduling remain required. See `ASPECT_COMPILER.md` and the frozen conversion
report. All F01–F16 whole-application gates remain open.


F13 now adds the [DOS runner and Script menu](ASPECT_RUNNER.md), with source-built
ASPECT.EXE, native MESSAGE/EXIT/PAUSE,267source-compiled fixtures and437actualDOS
cases/6,996assertions.16productionCLIcases and4terminalchild/resume workflows
pass.57of215slots execute;158abort. The compiler matches270acceptedvectors and
270presentationvariants. F01/F02/F09/F16 gain a checked direct sibling helper
launch/package,79configuration/128totalfarbridges and65,344nearbytes. This is
DOSchild integration, not live serial scripting. Complete application/script
scheduling and all F01–F16 whole-application gates remain open.

## ASPECT serial scripting checkpoint

The [serial scripting checkpoint](ASPECT_SERIAL.md) adds TRANSMIT/WAITFOR
and their supporting formatter, timeout, case, clock and result primitives:
523 exact native bytes, 1,261 paired CPU scenarios, all220 instructions and
11,057 DOS assertions. The source-built interpreter now implements59 slots
and explicitly rejects156;297 runtime fixtures compile from maintained source,
and302 accepted frozen compiler outputs plus302 presentation variants pass.
The composed DOS diagnostic passes465 cases/8,047 checks. The production CLI
passes21 cases/105 checks.

The Script menu now lends the UART to its separate DOS child using a validated
ASIOv1 parent allocation and4096-byte unread return buffer. Software, hardware
and combined flow policies are preserved, while vector/PIC/UART state and
unread data return to the terminal. The return-key prompt reacquires reception
and services flow control while keeping the child console visible; pre-fix
actual DOS errorlevel6 regressions remain retained. Source-owned adapters provide raw received
bytes, cooperative flow/cancel service during pauses, bounded stalls and
explicit errors for overflow or unread data without a parent. This does not
recover every original read/render/XLT/capture/scheduling service.

Independent actual DOS scripts pass28 cases/224 checks. Two owned-local
Synchronet/ENiGMA modem greeting cases pass16 checks with exact unread tails;
these cases do not log in or establish complete menu compatibility. The native
numeric-zero WAITFOR timeout prediction was corrected using E9F5: numeric0 is
invalid, FOREVER is distinct enum1A. Prior failed evidence remains retained.
Nonzero calibrated character delay, SET, most application commands, full
compiler/VM/recorder, original UI, physical modem validation and all F01–F16
whole-application gates remain open.

## ASPECT character, line and quiet-line receive

The [receive checkpoint](ASPECT_RECEIVE.md) adds COMGETC/COMGETCD, RGET,
WAITQUIET, COMDATA20 and FOREVER22. Nine native ranges contain435 exact bytes;
all60 component ranges match the original,696 paired CPU scenarios and14,500
actual DOS assertions pass, and all188 native instructions are exercised.
The source compiler matches358 frozen outputs and358 presentation variants.
The interpreter implements63 slots and explicitly rejects152;351 source-compiled
runtime fixtures pass515 cases/9,091 checks. Generated ACV1 CASES.DAT metadata
replaces unrolled test calls that exceeded the16-bit near-code limit, retaining
the full suite and DS=SS. The required test data is hash-bound and independently
reproduced with88 other outputs in the fresh source-only build.

Fifteen independent actual DOS/UART cases pass135 checks, including delayed
input, binary00/80/FF, RGET near/far/parameter storage and exact unread tails,
timeouts, contextual FOREVER, cancellation and the maintained zero-length
buffer guard. The earlier28 UART cases, two owned-local BBS greeting cases and
five terminal Script workflows pass on the same production runner. Historical
failure runner identity now comes from archived evidence instead of borrowing
the current runner hash.

The native FOREVER integer builtin returns1; only supported timeout grammar
positions use the special1A indefinite option. Native successful-open state
suppresses COMGETC display, unlike the direct4C3C receive path. Native4C74's
translation/pattern-monitor/rendering service remains an explicit application
dependency; raw child input can consume ANSI streams differently. Production
polling fixes native cancellation gaps and bounds the native RGET max0 overflow
before an81st non-CR store. These differences are documented, with original
quirks retained in bounded component tests. Full compiler, ASPECT application
services/invocation/recorder, other features, physical modem validation and all
F01–F16 whole-application gates remain open.

## ASPECT receive-policy integration

[Input-policy integration](ASPECT_INPUT_POLICY.md) composes83 exact native
policy bytes (64 reused,19 adapter) with the child UART owner. ASIOv2 retains
the28-byte descriptor and adds validated XLT/seven-bit inheritance, while unread
handback remains raw. The parent adds no DATA storage and retains DS/SS65408.
Native policy checks pass8824 paired CPU cases/424036 DOS assertions/37 covered
instructions. Independent actual DOS mapping passes24 cases/192 checks; four
backend snapshot cases and seven terminal Script workflows also pass. The
existing28 serial,15 receive and two local BBS greeting cases pass on the same
runner. Ninety outputs reproduce in the fresh source-only proof.

Production uses exact4C74 mapping with display0. Full renderer/ANSI continuation
consumption, WHEN callbacks, complete ASPECT and recorder remain unfinished.
The current interpreter still implements63 slots and rejects152 explicitly;
515 diagnostic cases/9091 checks and21 CLI cases/105 checks pass. Compiler
coverage remains358 frozen outputs plus358 presentation variants. This advances
F03/F05/F09/F13/F16 without closing any whole-application gate. Logged-in modern
BBS workflows and actual hardware remain required beyond greeting regressions.

## Connected ASPECT login and terminal resume

[Connected script sessions](ASPECT_SCRIPT_SESSION.md) fix a live COM2
handoff defect: native active IRQ-table slot0 was incorrectly used as COM1.
The child now receives the selected terminal COM number, and incompatible
standard-base/IRQ mappings fail before EXEC. Successful connected scripts resume
the terminal immediately; errors and offline console scripts retain their
serviced acknowledgement prompt. This removes a pause during incoming welcome
art that caused a retained abnormal DOS exit after successful authentication.
The exact errorlevel of that earlier exit was not captured.

An actual menu-launched source-built script now sends the synthetic local
Synchronet credentials, gates its password with native WAITFOR, then returns to
a terminal that passes all12 stock-editor checks and eight key-wire checks,
ending in draft abort. Current linked launch checks pass17 groups/65 inputs,
all seven terminal Script DOS workflows pass, and90 outputs reproduce without
originals. The runner is unchanged; parent DS/SS remains65408. Earlier ENiGMA
immediate forwarding still fails Home on its recorded de47 build; the matched
30ms buffering experiment passes, with both retained separately. Full script
rendering/events/recorder, other application work, custom IRQ inheritance and
physical Wi-Fi modem validation remain required. All F01–F16 gates remain open.

The later [WHEN runtime](ASPECT_WHEN_RUNTIME.md) checkpoint adds real resident
rendering, native receive matching and deferred handlers, including a WHEN-driven
Synchronet login/editor workflow. Its825 DOS runtime cases and eight terminal
compositions are separate from compiler-only conformance. The subsequent
[SET component](ASPECT_SET_NATIVE.md) adds225 exact native bytes,3,487 CPU cases
covering101 instructions, and a linked/original regression correcting the status
script-label relocation. The compiler emits eleven settings; production SET
still supports only WHENCASE pending native status/RPC integration. Fresh source
builds reproduce106 checked outputs, including fifteen SET component artifacts.
These increments do not close the full compiler/recorder, UI/settings, transfer,
Host, hardware or other F01–F16 requirements.

The [status memory prerequisite](STATUS_MEMORY.md) moves fixed redisplay prose
to CONFIG_CODE and its247-word row index to retained far storage, leaving1,440
near bytes instead of48. Linked full-history cases, actual DOS redisplay/export/
clipboard workflows, all eight WHEN renderer compositions, scoped Synchronet
and30ms-buffered ENiGMA editors, and106 reproducible outputs pass. Native status
and SET integration remain open.

The [full status component](STATUS_RENDERER.md) now executes recovered2FB8 and
the175-byte helpers through real text/UI routines and explicit CONFIG/resident
bridges. Nine actual8086DOS cases cover normal and alternate rows, all eight
key-label fields, hidden/message branches and three typed formatter failures;
the separate formatter/helper proof covers25 DOS format cases and nine helper
compositions. Fresh source builds reproduce112 checked outputs. This provides
the native drawing owner needed by SET; live parent state/RPC integration and
all whole-application gates remain open.


The subsequent [live status integration](LIVE_STATUS.md) connects SET WHENCASE
to the parent's bounded normal-row state through renderer capability2. Both
client and parent reject STATUS after the UART lease closes. Four actual DOS
cases/152 checks,85 linked staging cases,47 client inputs,22 parent admission
cases, five DOS callbacks, eight WHEN/315 checks and112 reproducible outputs
support this checkpoint. Other SET handlers, alternate live key labels, broader
renderer owners and all whole-application gates remain unfinished.


The [native SET runtime](ASPECT_SET_RUNTIME.md) adds all eleven selected setters
through the recovered225-byte component, actual native consumers where those
commands are already implemented, and a bounded IRQ-live calibrated TXPACE
service.853 DOS runtime cases/19000 checks include38 integration vectors; six
actual UART cases and six terminal status compositions distinguish platform,
consumer and renderer proofs. FIND/CASE command integration and shared-session
adoption remain open, as do all F01–F16 gates.


The [native FIND/SWITCH/CASE application checkpoint](ASPECT_FIND_CASE_RUNTIME.md)
now links the401-byte consumer component to real CRT/FILE and checked near-heap
ownership. The compiler matches54 accepted original outputs and72 rejections;
878 actual DOS runtime cases/20586 checks include28 consumer/failure vectors and
70KB DWORD seeks. Four actual UART/RGET/parent compositions pass152 checks;
independent near-owner DOS checks and125 reproducible outputs remain separate
scope.69 opcode slots are implemented,146 remain unsupported, and no whole-
application gate is closed.

The7ff697c F03/F13 checkpoint added [scoped BREAK recovery and a child transport owner](ASPECT_BREAK_OWNER.md):
249 exact native bytes, original compiler grammar for BREAK/SET BREAK/FETCH BREAK,
626 linked UART ownership inputs and31 linked timing/cancellation/error cases.
The source-only proof reproduces132 outputs. Interpreter dispatch for these
commands, parent duration inheritance, native notice/status integration, actual
DOS pulse scheduling and physical UART timing remain open; supported runtime
counts stay69 opcode slots and eleven SET setters. Native notice pointer0000h
is now proved valid DS:0000 (`*** BREAK ***`), rather than a missing resource.
See [native evidence](ASPECT_BREAK_NATIVE.md) and
[validation](validation/aspect-break-owner.json). No whole-application gate closes.


F03/F13 now include [live ASPECT BREAK/FETCH integration](ASPECT_BREAK_RUNTIME.md):
71 opcode slots, twelve SET/FETCH families and1147 actual DOS execution cases.
Capability3 inherits the raw configured duration once per invocation and brackets
the native notice/cursor with retained-underlay cleanup. Five DOS pulse/cancel
cases, six status compositions, eight WHEN compositions and both established
BBS workflows pass against the current parent/child.138 outputs reproduce
byte-identically without originals. [Bound validation](validation/aspect-break-runtime.json)
retains the first observer's missed post-exit clearing, the corrected observer
and the final current products. Physical modem/timing, immediate-forwarding
ENiGMA behavior and complete application gates remain open.


F13 checkpoint: compiled-target EXECUTE now runs native999 replacement in the
actual DOS interpreter, retaining settings/numeric banks and UART ownership,
releasing old far globals and resetting per-file frames/WHEN references. The
native end-wait is connected through a once-only maintained budget/cancel
owner for attached rendering; raw ASIO preserves unread input.72/215 opcode
slots are supported. DOS source compilation/fallback, chained parent filename
labels, recorder/full compiler/remaining services and F13 remain open. See
[ASPECT_CHAIN_RUNTIME.md](ASPECT_CHAIN_RUNTIME.md). No F01–F16 gate closes.

F13 current-label update: capability4 scalar transfer now refreshes native
STATUS with the accepted script basename after EXECUTE, preserving invocation
and parent configuration ownership and temporary child duplex. This closes
that specific label item, not F13. DOS source compilation/fallback and remaining
compiler/recorder/services are still required. Unconstrained emulator timing
is not verified; bounded end-wait calibration can return pacing5. See
[ASPECT_SCRIPT_LABEL.md](ASPECT_SCRIPT_LABEL.md).

F13 DOS compiler work: the streaming lexer and declaration/procedure inventory
now run as source-built8086 large-model C, matching the maintained host frontend
across1154 lexical and1164 inventory cases with real DOS files and owned heap
cleanup. These are diagnostics; ASX emission, full validation/pruning, compiler
CLI and runtime ASP fallback remain required. See
[ASPECT_DOS_COMPILER.md](ASPECT_DOS_COMPILER.md). F13 and all other gates stay open.

F13 now includes native ISFILE/GETFSIZE/RENAME through both maintained compilers
and production ASPECT. [Filesystem query/rename evidence](ASPECT_FILE_INFO.md)
covers84 original compiler outcomes,177 exact native bytes,322 component/original
cases,155 repeated actual DOS VM invocations and terminal-parent login gating.
The dispatcher has92 supported/123 unsupported slots; this does not close F13.

F13 now includes FINDFIRST/FINDNEXT and seven native file metadata builtins.
[Enumeration evidence](ASPECT_ENUMERATION.md) retains675 exact native bytes,
885 component/original cases,46 compiler outcomes and actual DOS DTA/EXECUTE/
shared FOUND ownership. The runtime has94 supported/121 unsupported opcode slots;
all F01–F16 application gates remain open.

F13 now includes GETFATTR/SETFATTR with exact native helpers and explicit corrected
far-global writeback. [Attribute evidence](ASPECT_FILE_ATTRIBUTES.md) binds100
native+203 reused bytes,1,081 component/original cases,54 original compiler outcomes
and279 repeated DOS VM invocations. A real native-wrapper control preserves the
original lost-global-write bug separately.96 slots are supported and119 rejected;
all whole-application gates remain open.

F13 now includes GETFDATE/GETFTIME/SETFDATE/SETFTIME through a native-prefix stream
adapter. [Timestamp evidence](ASPECT_FILE_TIMES.md) binds390 exact+87 reused bytes,
507 component/original cases,108 original compiler outcomes and248 real DOS VM
invocations. A native control separates lost-global/destructive-input behavior
from maintained writeback/input-copy corrections.100 slots are supported and115
explicitly rejected; every whole-application gate remains open.
