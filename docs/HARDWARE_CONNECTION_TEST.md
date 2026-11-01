# Boca / SPA2102 / SynthModem / Enigma acceptance record

Status: **not run on physical hardware**. Software readiness is recorded in
[CONNECTION_TEST_READY.md](CONNECTION_TEST_READY.md). This record does not turn
emulator results into physical acceptance. Fill it from observations during the
real connection, keeping account passwords out of notes and captures.

## Preserve the working setup

Back up the current PCPlus application and its configuration before installing
the candidate. Retain the old executable as a fallback. Keep the working PRM,
dialing directory, keyboard and translation resources; do not overwrite them
with a generic profile. Record the actual settings below before changing any.

| Item | Observed value |
| --- | --- |
| Test date and DOS version | Pending |
| Machine / CPU / available conventional memory | Pending |
| Candidate TERMINAL SHA256 | `99f0a1ac69b851082bf601d3daaa568b8588cc8dfec6f6aceaaabfc4dc775744` |
| Boca model / firmware | Pending identification |
| UART / IRQ | Previously working COM3 / 3E8h / IRQ5; verify |
| DTE baud / framing / flow control | Pending; preserve working settings |
| Modem initialization string | Pending; preserve working string |
| Reported carrier speed | Pending; record separately from DTE baud |
| SynthModem revision / backend | Pending; current planned backend slmodemd-pjsip |
| Enigma revision / terminal setting | Pending; candidate expects ANSI 80x24 |

Use the launch instructions in the readiness document. After carrier and
`CONNECT>`, enter `LOC` or `1`. The hostname is selected after the analog
connection. Do not copy the bridge VM's modem initialization into the Boca.

## Checks in order

For each row record **pass**, **fail**, or **not tested**, plus the observed
behavior. Stop and capture a reproducible failure before changing settings.
Change one setting at a time, recording both its old and new values.

| Check | Required observation | Outcome |
| --- | --- | --- |
| Initialize and dial | Commands receive responses, UI remains responsive, carrier is established | Not tested |
| Select LoSs oF CoNtRoL | CONNECT prompt accepts LOC and reaches the intended Enigma instance | Not tested |
| Login focus | Existing account can enter username and password, use backspace, and submit without a missing input field or extra focus keystrokes | Not tested |
| ANSI and CP437 | Frames, extended glyphs, colors and cursor placement render correctly; no stray control sequences | Not tested |
| Screen geometry | Bottom row, status line, clears, scrolling and redraws do not overwrite BBS content or leave stale text | Not tested |
| Editor navigation | In a private test message, type/correct text, use arrows, Home/End and Page Up/Down, then cancel without posting | Not tested |
| Original shortcuts | Alt-Z reference, L log pane, Escape return, setup and return to the session preserve the screen and input | Not tested |
| Sustained display | Browse long BBS output for at least five minutes, interrupt/resume it and type commands; no missing text, lockup or input lag | Not tested |
| Remote disconnect | Remote logout releases carrier cleanly and returns control without freezing | Not tested |
| Local hangup | Local hangup drops carrier and allows a new call | Not tested |
| Reconnect | Three consecutive dial, LOC, login, logout cycles work without restarting PCPlus | Not tested |
| File download | An owned binary file downloads with identical size and SHA256 | Not tested |
| File upload | The same owned file uploads to a private test area with identical size and SHA256 | Not tested |
| Transfer cancellation | Cancel an owned test transfer, return to the BBS, then complete another transfer | Not tested |
| Exit and restart | Exit to DOS, restart, and confirm serial configuration and keyboard still work | Not tested |

Start file checks with a small binary containing arbitrary bytes, then a larger
file that exercises sustained flow control. Record protocol, sizes, hashes,
elapsed time and any retries. A text file that merely looks correct does not
prove binary integrity. Test each protocol actually needed; one passing
protocol does not establish the others. Verify hashes on the workstation after
copying the received files back if DOS has no checksum utility.

Speaker sound is a separate observation from carrier and data compatibility.
An inaudible handshake does not prove that modulation failed. Likewise a
displayed CONNECT result does not establish a successful login or transfer.

## Failure record

For a failure, record the row above, exact keystrokes, expected result, observed
result, whether carrier remained asserted, and whether returning to DOS or a
redial recovered it. Note any settings changed since the last passing run.
Keep a short sanitized display capture and relevant bridge/BBS log timestamps
when available. Compare the old PCPlus installation with the same route and
settings only after preserving the candidate's evidence.

Known candidate limitation: compile `.ASP` files with `ASPCOMP` at the DOS
prompt before starting the terminal, then run `.ASX`. Nested compilation can
exhaust conventional memory. Dim original-reference commands are unavailable.
Neither limitation is waived by a passing connection test.

## Acceptance

Physical connection compatibility remains **unverified** until the required
rows have observed outcomes and every failure affecting normal use is resolved
or explicitly accepted by bstar. Broader original PCPlus feature parity remains
a separate, unfinished requirement.
