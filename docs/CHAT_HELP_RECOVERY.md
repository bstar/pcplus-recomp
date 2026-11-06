# Chat Help recovery and BBS regressions

The [opt-in Chat Help build](CHAT_GLOBAL_HELP.md) now passes24 normal-main
DOS8086 sessions:25/28/43/50 rows, each covering ordinary Help, two Help calls,
missing PCHELP, missing HLP, damaged HLP and software flow control. All four
products remain unchanged. [The receipt](validation/chat-help-recovery.json)
binds the current tests, cold rebuild and current-parent BBS evidence.

```sh
./tools/dev --command python standalone/test_chat_help_matrix.py --package build/chat-help-review-20261106 --output build/my-chat-help-matrix
```

Use a fresh output directory. The matrix gives each run a unique capture name
and runs at most two independent DOS processes concurrently. Each session
uses the normal main loop, real BIOS keys and a synthetic UART peer. Its
passive observer copies complete Chat/Help-or-error/Chat frames and the BDA
cursor. It never writes product or video state.

## Failure and repeated-use coverage

Each resource failure must show the ordinary PROGRAM error acknowledgement,
then return the complete Chat frame and cursor. The unfinished `AB` line must
still transmit once. A repeated-use case observes two helper entry/return
cycles in one process before sending the line. Every case then leaves Chat,
sends ordinary terminal input and checks a fresh parser reply. The original
PRM, staged files and hardware snapshot remain unchanged.

The error prompt uses BIOS teletype output below the saved local-pane cursor.
An initial observer wrongly assumed row1, as in the command-reference fixture.
After correcting its row, it still mistook Chat visible underneath the error
prompt for a returned Chat screen. A delayed diagnostic capture confirmed the
visible prompt and cursor at row21 for the25-row case. The accepted observer
requires prompt dismissal and the original cursor before admitting its return
capture, then separately compares every visible cell and cursor state. The
failed matrix and diagnostic captures remain in ignored build storage. No
application change was needed to make the failure cases pass.

## Live receive and flow control

The flow case schedules seven raw bytes, `RXLIVE` followed by CP437 byteF0,
while Help owns the screen. The peer must observe actual XOFF before the
scheduled time and hold the update until actual XON. The return observer waits
for those bytes to appear in Chat's remote pane. The entire returned frame
must equal the saved frame with exactly those seven character cells changed;
attributes, local input, all other cells and the local cursor must match.
This proves resumed raw Chat reception after the Help pause, not physical
RTS/CTS behavior, line saturation or analog-modem acceptance.

## Current-parent compatibility

The same6fd8aafc parent passes the existing40-key pressure regression's four
cases: completion, Escape, hangup and quit during native TEXT/echo waits.
It retains the32-key FIFO prefix, rejects excess keys, clears abandoned
typeahead on cancellation and restores ordinary input/parser behavior. This
regression does not queue Alt-Z during the native wait; that remains open.

Synchronet passes25 stock editor/display checks, including the external-viewer
DOS child and exact screen/cursor return, with the required terminal-size probe.
Enigma passes16 carrier/reconnect/transfer checks. Its independent raw-stream
audit verifies the deliberate first-transfer carrier loss, cleanup before
redial, two ASPECT logins in one parent process, CRC/finish/control ordering
and an exact65539-byte retry. These use the actual SynthModem proxy path in
the owned loopback labs. They do not invoke Chat/Help during the BBS session,
and do not exercise the SPA2102's SIP/audio or the physical Boca modem.

A new source-only export reproduces all four products and repeats reference
Help normal/flow plus normal Chat Help at25/50 rows with the extended checker.
The24-case matrix runs separately against the identical products; it is not
claimed as a24-case cold-export run.

The [native-wait follow-up](CHAT_HELP_BUSY.md) tests Help behind real typeahead
at exact FIFO capacity and samples loaded-image identity before/at/after Help.
Other wait states, Help beyond FIFO capacity, continuous module lifetime and
allocation faults, geometry-fault recovery, Help during a real BBS session, physical acceptance,
other contexts and full original feature parity remain open. No physical
deployment or selected-package change occurred.
