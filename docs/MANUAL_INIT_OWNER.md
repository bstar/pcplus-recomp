# Manual Init send owner component

The optional `--manual-init-owner` build now contains a bounded, send-only
foreground component in the existing MODEM bank. This is the next implementation
step after [native Alt-J recovery](INIT_MODEM_RECOVERY.md). It does **not** enable
Alt-J, the reference entry or the command browser. Its caller integration remains
required before an application release can advertise the command.

The linked executable is SHA256
`90e23558aa0c21b3ee70f307cb866248aa7eaa4d743b0c80fdc5a5bcc6ccb46f`.
It uses65008 near data/stack bytes (528 spare) and65194 resident CS bytes
(342 spare). The component adds144 near bytes and no resident CS bytes to the
previous candidate. Its own code lives in MODEM_CODE. With the flag disabled,
the rebuilt executable remains exactly340cb4ba, the existing elapsed-view
candidate. No package selection, private configuration or installed file changed.

## API and behavior

`terminal_manual_init_begin_far` takes DS:SI encoded input, CX capacity1..47,
DL configured pause marker and AX total BIOS-tick budget1..65535. DS must equal
SS. The actual bounded native expander validates the source extent, terminator
and caret syntax before creating a private plan. Changing caller input after
begin does not change the send. Empty expanded input completes immediately.
Active invocation, queued ordinary output and connection states other than
idle0/online6 refuse admission without sending. This is only component-level
admission; transfer, parser, PROGRAM, ASPECT and view guards belong to the
dispatcher integration, which is not present yet.

`terminal_manual_init_poll_far` takes AX0/1, an explicit physical-write grant.
It attempts at most one UART write per call. Ordinary bytes wait one BIOS tick,
pause markers wait ten ticks and the native FF representation sends a NUL
without an additional character delay. Pause-marker matching precedes FF
matching. An embedded zero from native expansion terminates the command, as in
the original sender. This BIOS pacing is maintained behavior, not equivalence
to the original calibrated minimum30 units.

The owner uses a private full-day BIOS clock, including midnight wrap. A36-tick
no-progress limit bounds unavailable write grants, THRE, CTS and software XOFF;
intentional delays are excluded from that progress interval. The total command
budget includes delays and expires even if bytes continue to make progress.
It neither borrows the connection clock nor changes echo/pacing settings.

`terminal_manual_init_cancel_far` accepts3 cancel,7 carrier loss or8 exit. The
caller must detect and supply these events; the component does not poll DCD or
intercept keys. Every entry preserves non-AX registers and FLAGS. Public status
values are0 idle,1 sending,2 sent,3 cancelled,4 timed out,7 carrier loss and8
exit. Invalid requests return5 and busy begin returns6 without replacing the
current status. `terminal_manual_init_active` and `_accepted` expose active
state and the count of physically accepted bytes.

Completion means sent, not modem acknowledgement or a connection. Incoming
replies remain ordinary data. No dial command, ACK state, escape prefix,
hangup, DTR drop, connection event or timer/log event is manufactured. The
component does not echo its bytes or mutate the configured command.

`terminal_manual_init_needs_resync` reports a physically emitted unterminated
line when the owner retires. An accepted CR clears the debt; empty begin or
cancel before sending does not clear existing debt. LF alone does not terminate
a partial command. This flag inserts no recovery bytes. Caller integration
must reconcile it with the existing command retry/resynchronization policy.

## Evidence and remaining gates

The [receipt](validation/manual-init-owner.json) binds117 test inputs executing
the actual linked owner, native expander, UART/IRQ and receive parser. Cases
cover idle and confirmed online sends, control/FF/NUL/pause behavior, exact wire
bytes, private-copy ownership, caller/stack/register preservation, invalid
extents, busy refusals, all three flow stalls and withheld grants, absolute
deadlines, low-word and midnight wrap, cancellation/loss/exit notifications,
partial-line debt, ordinary RX/CPR queueing, and subsequent dial/loss/redial.
UART, BIOS/DOS and filesystem boundaries are models. The harness explicitly
withholds ordinary TX while granting the component output; this is not proof
that the production dispatcher already enforces that exclusion.

A Git-free tree containing only538 declared source files reproduces the
executable exactly. All22 elapsed-view linked regressions pass against it.
These results do not establish actual DOS timing, BBS/SIP/analog compatibility
or physical acceptance for manual Init.

Before enabling Alt-J, integrate guarded key/menu admission after view
restoration, exclusive output scheduling with ordinary RX/CPR still serviced,
typed cancellation/carrier-loss/exit cleanup and partial-line reconciliation.
Then repeat the actual DOS, Enigma/Synchronet, source and package gates. The
15 unavailable original entries and all other feature-parity work remain open.
The hardware-test package remains ZIP04b6ce69/candidate340cb4ba; installed
9f2a37e7 and active selection93a9db94 remain unchanged.

```sh
./tools/dev --command python standalone/check_manual_init_owner_live.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-manual-init-check
./tools/dev --command python standalone/prove_terminal_manifest.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-source-proof
```
