# Foreground COM ownership handoff

Alt-F10 now offers a COM move after saving and closing PRMEDIT. Disconnect the
modem first and let incoming data drain; Alt-H handles configured managed
connections. A raw session must disconnect through its modem commands or controls.
**Y** at the COM question accepts its
port/baud/line/flow proposal; any other key keeps the old link and defers that
serial/profile group. No automatic hangup or redial occurs. After a successful
move, Alt-D can start a configured MODEM/DIRECT target on the new port. Existing CLI category
overrides still take precedence.

Both ports must be idle, with no queued or pending incoming data and no carrier.
The profile question remains separate after COM preflight. If a byte or carrier
arrives during that question, the final acquisition check cancels the COM move
and coupled profile while retaining independent display/modem/BREAK edits.
An unavailable target keyboard can retain the old profile while allowing the
confirmed COM move. Failure leaves a visible result requiring acknowledgment.
The new port uses its saved baud instead of inheriting the old port's negotiated
autobaud, except when an explicit CLI baud override applies. The remembered
source-rate baseline advances only for a successful baud commit.

The recovered driver owns one hardware snapshot and one previous interrupt
vector. Replacing the port globals before releasing that snapshot would restore
the old interrupt vector into a different IRQ slot. The new entry restores the
old UART/PIC/vector first, changes port globals, captures the target snapshot,
and installs then immediately releases the native ISR while the target IRQ is
masked and IER is zero. This captures the target vector for PROGRAM's normal
restore sequence. Revisiting a port captures its restored original state, so
no permanent per-port snapshot table is needed. The recovered flat driver bytes
remain unchanged.

The near entry takes AX pointing to an already validated 40-byte serial plan in
DS=SS, and preserves BP/SI/DI/ES. Return AX is zero for transfer, one for an invalid
candidate or foreground owner, and two for an occupied or undrained line.
`terminal_port_check` performs the same preflight without acquiring resources.
The handoff repeats these gates at commit. It independently checks pointer extent, standard COM1–4/base/IRQ agreement,
and an exact BIOS port-table match before probing target hardware. The caller
must be the active successful setup-child owner. Its old IRQ must be masked,
DLAB clear, IER zero, RTS low, and its old-format XON/TEMT handoff completed.
The connection controller and parser must be idle; both software queues must be empty;
neither old nor target hardware may have pending input, overrun, an incomplete
transmit, or asserted carrier. This entry does not hang up a live connection.

Rejection precedes all hardware writes, port-global changes, and snapshot/vector
replacement. LSR reads acknowledge hardware overrun; observed loss on either
port increments the existing saturating dropped-byte counter before rejection.
MSR reads have the ordinary UART delta-status acknowledgment behavior. No RBR
byte is read during acquisition. The maintained target quiescence preserves DTR,
lowers RTS and leaves the target masked, DLAB clear and IER zero with its original
interrupt vector installed. The caller then installs its
desired baud/line/flow policy and run `terminal_program_restore_uart`. The entry
sets the target's eventual MCR policy to DTR/RTS/OUT2 and clears old flow state;
it sends no bytes, clears no receive buffer, and does not dial automatically.

`./tools/dev --command python3 standalone/check_port_handoff.py` executes 69
linked cases with four independent UART register banks and distinct IRQ3/IRQ4
vectors. It uses the actual native snapshot/vector routines, maintained handoff,
PROGRAM restoration, receive ISR, checked transmit helper and final shutdown.
The cases cover all directed port pairs, repeated switches, original DLAB and
divisor restoration, binary traffic routed only to the target, busy/rejected
owners, pending hardware and queued data, carrier, unreleased XOFF, overruns
with saturation, invalid layouts/pointers and absent or mismatched BIOS ports.
Only DOS/BIOS/hardware boundaries are modeled in this primitive suite.

`check_live_setup_port.py` adds33 complete foreground transaction cases through
the actual Alt-F10 scheduler, child handoff, policy, COM/profile choices and
rollback. All directed COM1–4 pairs, late byte/carrier, independent edits,
failed-move retry, keyboard failure, CLI override and old/new flow ownership
are exercised. Rejection after old XON reestablishes any buffered-RX pause.

`test_setup_port_dos.py` adds six actual DOS production-editor cases: COM1/2
both directions, COM1/3 with shared IRQ4, decline, absent BIOS COM4 and combined
COM/baud/profile acceptance. An independent INT1C sampler observes each UART's
enabled ticks, divisor and line format. Four separate UART/PIC/IRQ snapshots
match before and after. Late loopback peers establish carrier after the move
and verify fresh DSR/DA/CPR, ordinary keyboard bytes, resumed receive and actual
video. The test binds every copied terminal/editor to the frozen runtime hashes.
Physical UART/Wi-Fi firmware and stock BBS testing of this checkpoint remain open.

The hash-bound checkpoint is [validation/port-handoff.json](validation/port-handoff.json).
The complete58-command terminal regression runs all three COM suites alongside
the existing same-port serial and profile scenarios.
