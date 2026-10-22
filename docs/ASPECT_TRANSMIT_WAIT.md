# Configurable ASPECT transmit stalls

The maintained ASPECT runner now defaults to a 30-second per-byte transmit
stall limit. Set the DOS environment before launching the application:

~~~
SET PCPLUS_TXWAIT=60
~~~

Accepted values are decimal 1 through 3600, up to four digits, including leading
zeros. A missing setting selects 30. Empty assignments normally delete a DOS
environment entry; an actual empty value, zero, signs, whitespace, suffixes and
out-of-range values are rejected. Invalid configuration returns 64 before
opening the script or acquiring the UART. Help remains available.

The runner reads the setting once per invocation. Script RESET and EXECUTE
retain it; a script PUTENV does not change the active limit. Each pending byte
gets its own deadline, using 18 BIOS ticks per configured second. This is an
approximation to elapsed seconds. Accepted bytes are not retried. The existing
36-tick close/cleanup bound is unchanged. This setting does not configure the
parent's modem dialing timeout or any transfer protocol's deadlines.

Longer waits exposed a cancellation gap: native BIOS peek sees only the oldest
key, so ordinary typeahead hid a later Escape. The maintained owner now removes
the first Escape from a validated standard IBM 16-word BIOS ring, preserving
all other raw key words and their order. Work is bounded with interrupts
disabled, and caller registers, interrupt state and direction flag are restored.
Unknown/relocated ring layouts are left untouched. The usual BIOS head-key
Escape path remains available. Modal confirmation and script windows retain
their own keyboard ownership.

The queue offsets and standard bounds were checked against pinned
[DOSBox-X BIOS keyboard source](https://github.com/joncampbell123/dosbox-x/blob/dosbox-x-v2026.07.02/src/ints/bios_keyboard.cpp).
The maintained scanner is independently authored; this does not establish
compatibility with every physical or replacement BIOS.

## Focused evidence

Ignored raw evidence is under these build directories:

| Check | Result |
| --- | --- |
| aspect-txwait-dos/baseline-01 | Old runner expires at 36 ticks with no setting and with setting 6. |
| aspect-txwait/escape-baseline-01 | Six linked cases reproduce ordinary q hiding Escape. |
| aspect-txwait-dos/baseline-02 | Preserved failed baseline report: third wire expectation omitted the original's transmitted Escape. Actual wire contains q, Escape, then ready; do not treat this report as accepted. |
| aspect-txwait-dos/configured-01 | Six actual 8086 DOS sessions pass: default/6/3600 survive a four-second XOFF hold and send exactly 2048 bytes; setting 2 times out; both cancellation cases return 13, preserving q in the queued-key case. Exact complete wire, parent return, JFT, file owners and hardware restoration are checked. |
| aspect-txwait/escape-fixed-01 | Six real transport-service cases pass across normal/enhanced BIOS selection and queue wrap. |
| aspect-txwait/policy-01 | Linked 8086 parser accepts every value 1–3600; malformed input preserves the prior policy. 8704 ring position/length/Escape/IF/DF combinations and nine malformed/legacy/multiple-Escape cases pass. BIOS/UART boundaries are modeled. |
| aspect-txwait/policy-02 | Repeats the parser/ring coverage and adds 18 native sender checks: normal/midnight deadline arithmetic at 1/30/3600 settings, no blocked payload, exactly one accepted byte, and first-error preservation. Long configured waits use a modeled advancing clock. |
| aspect-txwait-cli/policy-01 | 23 real DOS child launches, 138 checks pass: inherited environment, exact diagnostics/output, invalid policy before invalid UART/file admission, accessible help and deleted-setting recovery. |
| aspect-process/runs/txwait-01 | All 56 actual DOS COM/flow/process diagnostic cases pass. Near code has 80 bytes spare; keyboard cancellation lives in its own far segment. |
| aspect-parent-process/txwait-01 | All 13 actual DOS attached PROGRAM cases pass with the new external-render child. |
| aspect-parent-process/source-proofs/txwait-01 | 26 application products reproduce from a fresh declared-source tree without originals. |
| aspect-process/source-proofs/txwait-01 | 23 diagnostic/component products reproduce from a fresh declared-source tree without originals. |
| aspect-flow-fault-dos/txwait-01 | Four existing SOFT/BOTH timeout/cancel cases pass with explicit setting 2, including retained parent pause until XON. |
| modem-reconnect-dos/txwait-01 | Both existing SOFT/BOTH reconnect cases pass with explicit setting 2 and clean second modem commands. |
| aspect-runner/checks.json | Existing 21-case DOS CLI suite passes 105 checks with updated exact help output. |
| aspect-abort-{confirm,yes,events,pressure}-dos/txwait-01 | All ten confirmation workflows pass, including deferred WHEN/RGET ownership and 44 parser replies under pressure. |
| aspect-abort-carrier-dos/txwait-01 | Four real virtual-modem carrier-loss workflows pass, including explicit two-second XOFF timeout and clean OFF-LINE parent return. |

The focused normal runner identity is
183f852dfe0a992faa29515e124eb3b6570e44578bdc25880a8a792a2bf7da3f.
The parent remains
6075bc182ae9821ae077e78a56a42741d81016cb82e79365556c36ee4782f62a.
These tests hold CTS high. Setting 3600 establishes parsing and short-stall
behavior, not an hour-long wall-time run. ASIO version/size and capabilities
remain unchanged.

Existing short timeout fault/reconnect fixtures explicitly request setting 2;
their former fixed-key schedules intentionally exercise a short deadline.
The [independent component audit](validation/aspect-transmit-wait.json)
accepts all six software-flow and six HARD/BOTH CTS cases. The new CTS cases
hold hardware flow low for four seconds, exercise default-limit resume,
explicit two-second expiry and queued-key Escape cancellation, then verify
manual parent input/query return. The peer sends no XOFF in these CTS cases.
Independent FF/status decoding distinguishes emulator control framing from
actual UART bytes. [Eight semantic corruption controls](validation/aspect-transmit-wait-audit-guards.json)
are rejected despite green producer flags and updated capture hashes.

[Four fresh BBS recorder/replay sessions](validation/bbs-txwait-compat.json)
pass on owned stock Synchronet/ENiGMA, including normal manual navigation after
replay. [Two stock script-window workflows](validation/bbs-txwait-window.json)
also pass, retaining exact user streams and normal parent-menu return.
Current audio acceptance remains pending. Its
[sealed preparation](validation/recording-txwait-audio-preparation.json) binds
the passing DOS/Telnet helper control, pinned software-modem runtime and all
606 unchanged admission inputs; it does not claim an audio outcome.
Sustained CTS/RTS pressure, sustained RX, physical modem timing and all full
F01–F16 requirements remain open.

The earlier [progress record](validation/aspect-txwait-progress.json) retains
its pre-audit scope and identities. Prior accepted audio records describe the
preceding runner and do not establish the current runner's audio behavior.
