# Live line editing and ANSI CSI M policy

Recovered insert/delete-line helpers are connected to the source-built terminal
through a maintained bounds and scheduling layer. The historical instruction
ranges and their limitations remain in [LINE_EDIT.md](LINE_EDIT.md). CSI L
inserts lines; CSI M depends on the selected live policy:

```text
TERMINAL /A:NETWORK
TERMINAL /A:ORIGINAL
```

`/A:NETWORK` is the default for BBS use. CSI M deletes lines even when the ANSI
profile would enter the historical alternate operation. CSI L/M default omitted
or nonpositive signed16-bit counts to1, clamp the effective count to the remaining active
scroll region, and preserve the current cursor column. A cursor outside a valid
region causes no line operation. Recovered per-line video/scroll helpers perform
the actual movement and clearing; the maintained policy does not substitute a
no-op renderer.

`/A:ORIGINAL` retains the recovered per-line helpers' original column behavior.
When ANSI alternate state8ff6 selects the historical CSI M service, it enters a
**bounded maintained discard wait**, rather than the original indefinite loop.
Incoming bytes are discarded until Control-N (0eh), local Escape cancels, and
Alt-X remains responsive. A36-BIOS-tick deadline ends the wait even without a
terminator. The loop continues servicing foreground UART/flow and live
connection work; if a modem operation takes RX ownership it returns that control.
This is deliberate scheduling/timeout policy, not byte-for-byte original timing.

The exact original daf2 wait is assembled in its separate diagnostic and remains
unlinked from the live terminal. It has no timeout and discards bytes while
waiting for Control-N or local Escape. Selecting `/A:ORIGINAL` therefore does
not restore that unbounded failure mode. On profiles that do not select the
alternate branch, CSI M uses the original ordinary delete-line path.

Protected attribute-check state returns without edits as in the recovered
helpers. Complex900c attribute-plane handling still has an explicit2d98 service
boundary; the maintained NETWORK path stops rather than invoking an unsafe
incomplete repair. This milestone does not close all protected attributes,
terminal modes, column widths or emulations.

`test-line_edit` checks exact flat recovery, source-only linked video helpers,
controlled historical wait behavior and actual DOS insertion/deletion.
`standalone/check_line_edit_live.py` adds current-terminal NETWORK/ORIGINAL
policy checks using synthetic UART/keyboard/video input. Captured wire replay,
when requested explicitly, is supplementary; no private capture is a default
test input. Its synthetic groups pass for region/count/column behavior,
protected and invalid-region no-ops, explicit2d98 boundary, original column
homing, serviced wait termination/deadline/modem yield and register ABI. An
explicit replay of the earlier local Synchronet editor capture also passes the
CSI M boundary that previously stopped parsing; this replay alone does not
establish a successful complete interactive editor session.
Recorded runtime/semantic evidence must match the tested binary,
and does not imply full application or physical modem compatibility.

```sh
./tools/build test-line_edit
./tools/build terminal test-terminal
```
