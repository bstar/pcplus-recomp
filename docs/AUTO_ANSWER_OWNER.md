# Typed answer-on sender component

The optional `--auto-answer-owner` build extends the shared bounded modem-command
owner with a typed answer-on entry and local echo. It implies
`--manual-init-owner`, requires original-reference and can coexist with the
integrated manual Init candidate. It does **not** bind Alt-Y, read the configured
answer-on field, display the Auto Answer notice or request its sound. These
remain the next integration steps, followed by application acceptance gates.

The component executable SHA256 is
`344832bbe26e2974b6c071f45421b9f2770f69496a1293624a96c7cfc4829bda`.
The normal hardware-test image and package have not changed. Disabling this
component reproduces8f76cc4f exactly. Near data/stack remains65008 bytes and
resident CS65234 bytes; added state fits existing alignment and the code stays
in MODEM_CODE, using the existing resident echo bridge.

This checked image also enables `--manual-init`, supplying its existing UART
scheduler and root cancel/carrier/exit hooks. An owner-only build without that
integration still requires caller-supplied write grants and event notifications.

## API and maintained differences

`terminal_auto_answer_begin_far` uses the existing begin register/return ABI:
DS:SI encoded source, CX source capacity1..25, DL pause marker and AX whole-command
BIOS-tick budget. DS must equal SS. The caller supplies the answer-on string;
this API does not choose a PRM field or enable a modem setting. Validated begin
stores `terminal_manual_command_kind`1; manual Init stores0. Busy or invalid
requests retain the old identity and command. Both entries share one output
lease, expansion buffer, private clock, limits, cancellation and result state.

Auto Answer captures the local-echo WORD when begin succeeds. It never changes
or restores the application setting. Manual Init always selects no echo. The
capture policy intentionally differs from the original sender, which reads the
setting for each ordinary byte. UI/key changes remain under the eventual guarded
caller; an external setting change does not retroactively alter this send.

Only a physically accepted ordinary byte enters the existing native terminal
echo renderer, exactly once. Pauses and FF/NUL never echo. This intentionally
differs from the original blocking sender's pre-write echo: bounded THRE/CTS/
XOFF/grant retries produce neither repeated echoes nor an echo for an unsent
byte. Native control/ANSI echo rendering is retained. Its recursive foreground
polling cannot re-enter command transmission while an echo callback is active.
Cancel/loss/exit can still stop the owner; returning from echo does not restart
it. A new begin refuses while the old echo callback still owns its stack frame.

The existing one-BIOS-tick ordinary/ten-tick pause policy,36-tick stall deadline,
whole-command budget and partial-line handoff remain. They are maintained
behavior, not equivalence to the original50 calibrated units. No dial, ACK wait,
escape prefix, answer-off toggle or call event is introduced.

## Evidence and remaining work

The [receipt](validation/auto-answer-owner.json) binds262 linked answer inputs.
They execute the real bounded expander, UART/IRQ, native echo renderer and ANSI/
keyboard paths without replacing product callbacks. Cases cover idle/online,
all zero/nonzero duplex classes, pause/FF/control/embedded-zero behavior,
capture versus later setting changes, identity/capacity/shared lease, withheld
grant and THRE/CTS/XOFF stalls, timeout, cancel/loss/exit, renderer recursion,
Escape during ANSI echo, actual root-key cancellation, qualified DCD loss and
same-process redial using existing resynchronization. Wire writes must precede
their corresponding echo callbacks. No echo is added during startup redial.

The same executable passes117 manual Init inputs,31 dispatcher inputs and22
elapsed-window regressions. An empty Git-free source export reproduces it
exactly. The disabled component reproduces the previous application. BIOS/DOS/
hardware boundaries are models; none of these results claim actual DOS, BBS,
SIP/analog/physical or complete original behavior.

Next integrate the saved answer-on field, configured information sound and
serviced notice before sending, then guarded direct/reference/browser admission
with correct view restoration. Preserve the echo distinctions, capture policy,
exclusive output, normal RX/CPR/flow/carrier, typed cleanup and retry behavior.
Keep sound/notice ownership bounded and restore the current underlay rather than
old cells over newer received data. Then repeat DOS/BBS/source/package gates.

Alt-Y remains one of14 unavailable reference entries. The ready8f76cc4f package,
archivece1a3265, active selection93a9db94 and installed9f2a37e7 remain unchanged.
No physical/private-file or bridge/BBS service changes occurred. The full goal
and physical acceptance remain open.

```sh
./tools/dev --command python standalone/check_auto_answer_owner_live.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-answer-owner
```
