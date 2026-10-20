# External-program UART ownership

The [validation record](validation/process-serial.json) binds41 linked modeled
cases, eight actual DOS cases/448 assertions, two mixed-variant link rejections
and108 ordinary serial regressions. A fresh normal ASPECT build remains
byte-identical. This is a gated component: no RUN/DOS/SHELL handler or full
PROGRAM controller is published.

`src/aspect/process_serial.c/.asm` supplies a synchronous pause/resume owner
around an external child. It uses the existing compiler flow bracket to send
an introduced XOFF/lower RTS and wait for actual TEMT while the UART IRQ is
still live. The detach step revalidates the lease, line state, known disabled
FIFO and actual installed ISR before masking its IRQ, disabling IER and restoring
the original baseline vector. Active phase2 prevents ordinary byte, carrier,
poll, reopen, close and compiler-release operations from using the child's
port. Read/unread rejection preserves the existing rollback token and ring.
Closed pause/resume calls are idempotent no-ops.

All serial objects in this variant use `ASPECT_EXTERNAL_PROCESS`. Separate C
and assembly capability symbols make mixing an ordinary serial object into the
new owner fail at link time. The ordinary production build omits these guards
and remains unchanged. The component's local assembly data has explicit DGROUP
fixups: the first attempt caught a missing group frame that wrote private state
outside the C data group. That failed DOS capture and its exact source snapshot
remain retained; later passes do not relabel it as successful.

## Return from the child

Resume masks/quietens the child's UART and retires its vector before polling.
It restores the saved divisor, framing, IER, post-pause MCR and parent ISR, then
restores only the owned PIC bit. Other PIC bits keep the child's current values.
It installs the cached ISR directly instead of calling the native installer,
which would overwrite the shutdown baseline with the child's vector. The final
ordinary serial close therefore still restores the original hardware/vector.

The code never resets the raw ring or calls the UART enable helper that reads
and discards RBR. Compiler flow release happens after the original line format
and IRQ owner are restored; only introduced pauses retire, and a high queue
retains the required soft/hard pause until normal consumption reaches low water.
The full ASIOv3 wrapped/full ring is still published exactly on final close.

The restore loop requires IF1 and an unmasked IRQ0 for the BIOS deadline. A
masked IRQ0 causes immediate bounded port recovery with STATE4, leaving that
unrelated PIC bit to its owner. A stalled child transmitter has a36-tick bound;
after timeout the port is reclaimed with PENDING7. Overrun returns OVERFLOW5,
increments the saturated drop counter and still restores ownership. A child
dropping DTR or enabling FIFO reports LINE8; the known FIFO-disabled policy is
restored. Pending FIFO bytes are not promised after that unsupported change.
An IF0 retry retains the detached owner until the caller resumes with IF1.
The full controller still needs to decide how these fatal conditions unwind
the application/session and any unrelated global state.

## Evidence and reproduction

The linked tests execute the real bounded serial C API, new ownership code,
native UART ISR and native vector save/restore. Only DOS vector services,
UART/PIC and BIOS clock boundaries are modeled. They cover all four standard
ports and N/S/H/B policies,128/3072/4096-byte pressure, unread rejection/rollback,
pending RBR retention, wrapped/full ASIOv3 handback, BREAK/foreign vector/FIFO
admission, IF0 retry, missing IRQ0, overrun/DTR/FIFO faults and timeout recovery.

Actual8086 DOSBox-X runs cover COM1/COM2 with all four flow policies. An independent
loopback peer supplies binary `00 1A 80 FF` before suspension and `NEXT` after
return. A separately built child checks that RTS is low and IER is disabled,
then changes the divisor, LCR/DLAB, MCR, IRQ vector and an unrelated PIC bit.
The parent verifies restored hardware/vector, retained unread bytes and token,
new input through its resumed IRQ, exact outgoing flow bytes and final baseline
restoration. The actual child writes its port marker and returns37. These are
modeled serial devices with a cooperative peer, not physical modem acceptance.

```sh
./tools/build test-process-serial
# Explicit capture labels and publication:
./tools/dev --command python3 standalone/test_process_serial_dos.py --label NEW
./tools/dev --command python3 standalone/record_process_serial.py --label NEW
```

Use fresh labels. The test runner retains manifest-listed source snapshots,
executables and captures, and
refuses to reuse a run directory. The optional recorder `--failed-label` binds
the initial DGROUP failure separately. Ordinary build/test targets need neither
original binaries nor REA databases.

Production shared VM/CRT state, ASIOv4 resident-renderer leases, full interpreter
stream/setting/error continuation, known FIFO-policy tracking for broader adapter
admission, mode/font/cursor/WAIT/NOCLEAR ownership and
final opcode publication remain in the [external controller plan](ASPECT_EXTERNAL.md).
Physical RS-232 Wi-Fi modem pressure/reconnect tests and the full application
gates remain open.
