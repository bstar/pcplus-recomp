# Foreground COM ownership handoff

`terminal_port_handoff` is a maintained, linked prerequisite for live COM
selection. **Alt-F10 does not call it yet:** COM changes still require restart.
The settings transaction must next stage an explicit COM choice, preserve its
coupled profile/serial proposal, prepare future modem commands, call this owner,
and reconcile the target's flow policy before normal PROGRAM restoration. An
unsuccessful preflight must retain the old settings and any independent changes.
Actual DOS multiport and physical UART validation also remain open.

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
It independently checks pointer extent, standard COM1–4/base/IRQ agreement,
and an exact BIOS port-table match before probing target hardware. The caller
must be the active successful setup-child owner. Its old IRQ must be masked,
DLAB clear, IER zero, RTS low, and its old-format XON/TEMT handoff completed.
The connection controller must be idle; both software queues must be empty;
neither old nor target hardware may have pending input, overrun, an incomplete
transmit, or asserted carrier. This entry does not hang up a live connection.

Rejection precedes all hardware writes, port-global changes, and snapshot/vector
replacement. LSR reads acknowledge hardware overrun; observed loss on either
port increments the existing saturating dropped-byte counter before rejection.
MSR reads have the ordinary UART delta-status acknowledgment behavior. No RBR
byte is read during acquisition. The native disable routine leaves the target
masked, DLAB clear, IER zero and MCR zero, with its original interrupt vector
installed. This can lower an already asserted target DTR; its modem policy
must be addressed during settings integration. The caller must then install its
desired baud/line/flow policy and run `terminal_program_restore_uart`. The entry
sets the target's eventual MCR policy to DTR/RTS/OUT2 and clears old flow state;
it sends no bytes, clears no receive buffer, and does not dial automatically.

`./tools/dev --command python3 standalone/check_port_handoff.py` executes 61
linked cases with four independent UART register banks and distinct IRQ3/IRQ4
vectors. It uses the actual native snapshot/vector routines, maintained handoff,
PROGRAM restoration, receive ISR, checked transmit helper and final shutdown.
The cases cover all directed port pairs, repeated switches, original DLAB and
divisor restoration, binary traffic routed only to the target, busy/rejected
owners, pending hardware and queued data, carrier, unreleased XOFF, overruns
with saturation, invalid layouts/pointers and absent or mismatched BIOS ports.
Only DOS/BIOS/hardware boundaries are modeled. This evidence does not establish
working settings UI integration, actual DOS multiport behavior, or physical
modem compatibility.

The hash-bound checkpoint is [validation/port-handoff.json](validation/port-handoff.json).
The complete terminal regression also runs this check; its separate actual DOS
settings tests still exercise same-port serial and profile changes.
