# Guarded manual Init Modem integration

The experimental `--manual-init` candidate enables original Alt-J, the
reference-menu entry and browser search through the same send-only owner.
SHA256:
`8f76cc4fd7843c3ca203d6ce241e3272cac1c82d8230f8b50634c4cd5dda3ad8`.
This is separate from the staged hardware-test package and installed application.
It includes `--manual-init-owner` and requires original-reference/local-controls.
The component-only flag still has no keyboard or scheduler binding.

## Foreground behavior

The old view is restored before beginning initialization. Existing parser,
macro, PROGRAM, transfer, ASPECT, ANSI wait, snapshot, Break, screen, monitor,
controller and recording owners defer admission. Ordinary queued output drains
before Init starts. During sending, the UART scheduler grants command output
exclusive access to ordinary payload writes; it does not grant a second write
to queued CPR or keyboard bytes on the same completion poll. UART flow service
and qualified carrier detection continue. Incoming ordinary bytes, including
OK replies and ANSI queries, retain their normal parser route.

Typed keys wait in the existing bounded foreground FIFO. Repeated Alt-J is
consumed without replacing or queueing another initialization. Escape cancels
locally. Alt-H cancels the sender and uses the existing configured hangup path;
Alt-X records exit cancellation and uses the existing exit path. Qualified
carrier loss records reason7 before normal flow/call retirement. Programmatic
connection start/cancel and the actual shutdown path also unwind the sender.
The command does not dial, wait for ACK, echo locally, alter configuration or
start/stop/log a call on its own.

A deferred Init cannot starve the BIOS keys that release recording or cancel
a dial/ACK wait: those states bypass FIFO dispatch until the owner releases.
The sender's whole-command budget comes from the saved modem timeout, converted
to BIOS ticks with rounding and WORD saturation. Its independent36-tick stall
limit still bounds THRE/CTS/XOFF. Ordinary pacing is one BIOS tick, pauses ten;
this is not equivalence to original calibrated minimum30 units.

Unterminated physical output debt transfers once to the existing connection
retry flag. Startup then uses its established separator/guard path; manual Init
itself inserts no separator, escape, hangup or DTR drop. A completed manual
command is only physically sent, not confirmed modem acceptance. Sending a
configured command while online retains the original send-only contract; no
data-mode escape is silently added.

## Evidence

The [live receipt](validation/manual-init-live.json) binds this exact image:

- 117 linked sender inputs and31 dispatcher inputs, including direct/reference/
  browser routes, receive/CPR and keyboard exclusion, deferred admission,
  recorder/dial-release key availability, stalls, cancel/loss/exit and redial.
- All39 original reference labels with14 still-unavailable command refusals.
- 22 elapsed-window, six call-clock and41 Screen Pause regressions.
- A clean, Git-free source-only exact reproduction.
- Two actual DOS8086 COM3/3E8h/IRQ5 workflows. Direct and reference-menu Init
  produce exact bytes without extra dialing, retain typeahead, render incoming
  data, answer real CPR, preserve PRM and restore UART/PIC/vector state on exit.

The dispatcher/owner CPU checks model DOS/BIOS/hardware boundaries; the DOS
workflows use a synthetic serial Hayes peer. The code-bank checker validates16
cross-bank call sites and their relocation/caller ownership. Near data/stack
remains65008 bytes (528 spare); resident CS is65234 bytes (302 spare).
Original native evidence and the component API remain in
[native recovery](INIT_MODEM_RECOVERY.md) and [owner component](MANUAL_INIT_OWNER.md).

Enigma/Synchronet, exact screen/cursor, source-matched package/START/SETUP and
physical gates require their own scoped evidence. No full original-feature or
analog/SIP acceptance follows from these results. The installed application,
private PRM/DIR/KEY/KBD/XLT/FON, bridge/BBS services and card are untouched.
Hardware-test candidate340cb4ba/ZIP04b6ce69, active selection93a9db94 and installed
9f2a37e7 remain unchanged. File/DOS, directory/key, Chat, broader ASPECT,
emulations/protocols and Host stay in the full-parity inventory.

```sh
./tools/dev --command python standalone/check_manual_init_dispatch_live.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-dispatch-check
./tools/dev --command python standalone/test_manual_init_dos.py \
  --terminal build/SELECTED/TERMINAL.EXE --label new-manual-init
```
