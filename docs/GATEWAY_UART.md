# Live Gateway UART owner

The optional `--gateway-uart` parent adds a retained IRQ owner around a DOS
Gateway child. It keeps RX and flow service live, following the original
Gateway's live-ISR contract rather than PROGRAM's detach policy. It composes
with the file transaction but does not bind Alt-F4 or implement the normal
foreground/display lifecycle.

## Receive and flow policy

BEGIN requires the real parent DS=SS, IF1/DF0, kind9/active1/pending0, acquired
hardware/vector ownership, drained TX/control output, an unmasked supported IRQ
and the actual parent UART vector. It validates standard COM bases, IRQ3/4/5/7,
DLAB/BREAK, IER, OUT2/loopback, FIFO-disabled policy and transmitter readiness.
It snapshots the actual framing/divisor, modem-control value and parent vector.
The 22-byte initialized lease and all new IRQ code live in retained FILE_CODE;
kind9 is excluded from the existing child-memory loan.

During the child, a small wrapper dispatches RDA/timeout to the existing native
RX handler through an interrupt frame. The native ring/control-byte behavior
and PIC EOI remain active. The wrapper adds bounded work around that handler's
existing receive-drain loop; it never calls DOS/BIOS or spins waiting for TX.
It preserves a foreign child's DS/SS/registers and direction flag.

The maintained native ISR queues XON/XOFF for foreground transmission. A DOS
child suspends that foreground, so the wrapper sends ready control output or
enables a temporary THRE interrupt to finish it later. THRE never enters the RX
handler and never reads RBR. Hardware flow lowers RTS at the high watermark,
including combined S/H mode. A guarded foreground poll releases the marked RTS
hold at the low watermark: native software dequeue otherwise returns before
reaching its hardware-release branch. XON and RTS therefore both resume after
return and queue drain. DTR/OUT2 and unrelated PIC bits are preserved.

Modem-status IRQs record DCD deltas/falls without treating a single edge as a
new fatal line error or publishing connection UI status. Their eventual
connection-state integration is still required. The receive ring remains 4096
bytes; a peer ignoring flow can exceed it. Overflow is reported rather than
silently overwriting unread data.

## Return boundary

Raw EXEC calls the kind9 return owner with IF0 after restoring parent DS/SS/SP,
before trap resume or interrupt enable. The owner masks its IRQ, retires a
child vector, repairs framing/divisor and the known FIFO-disabled policy, and
restores the live wrapper without rewriting the native shutdown baseline.
It does not reset the ring or read RBR. END restores the original parent ISR
and IER. An invalid lease invokes PROGRAM's existing masked/IER0 fallback;
the foreground must quarantine an unresolved owner before further use.

Observed overflow, unsupported line/FIFO changes and busy child TX remain
explicit errors even when the hardware is repaired. Reasserting saved DTR
cannot undo a hangup, and a transient DTR change that was already restored is
not observable by this boundary. This is not an arbitrary-memory child sandbox
or a promise that a second serial application can share the port.

## Evidence

The receipt is [gateway-uart.json](validation/gateway-uart.json).

- 54 linked CPU cases execute the wrapper, native RX, poll and IF0 return code
  with modeled UART/PIC/IVT endpoints. COM1–4 and N/S/H/B flow, custom IRQ5/7,
  3200-byte pressure, foreign child DS/SS/DF, deferred THRE XOFF without RBR,
  combined low-water recovery, DCD observation, admission refusals, corruption
  fallback, and UART/vector/FIFO/overflow faults pass. Parent startup snapshots
  and unrelated PIC bits remain unchanged.
- Nine actual DOS8086/FPU-off workflows pass 189 checks. COM1/2 each run N/S/H/B;
  another COM1/S child replaces its vector and changes IER, framing, divisor,
  MCR and FIFO before exit. The child waits with foreign DS while 3200 binary
  bytes arrive. Exact raw queue bytes, XOFF during the child, marked RTS hold,
  XON/RTS after actual dequeue, real child wait/vector/format, four application
  files continuing AB with the same descriptors, retained file transaction,
  and final hardware/vector restoration are checked. The mutation case reports
  fault8 while preserving data and repairing the hardware.
- The file transaction's 40 cases, private handles' 56 cases, direct resolver's
  33 cases and ordinary HOOK28 plus 14 boundary cases pass with the new parent.
- Fresh source trees reproduce the normal and diagnostic parents exactly from
  588 and 590 public inputs. Disabling this option reproduces a3fb5c2b and the
  ordinary ASPECT control remains 23caac93. No original executable is a build
  input and the recovered flat UART source bytes are unchanged.

An initial COM2 fixture was rejected before acquisition because it changed the
selected port without filling that port's synthetic PRM address/IRQ. The final
matrix uses corrected fixtures. Earlier pre-resume matrices are superseded by
the final dequeue/XON/RTS checks.

Normal parent: `build/gateway-uart-resume-20261104/TERMINAL.EXE`, SHA256
`076ea49b44a29f0c8eeaf555bf8fa9d7eef6f7b3326360f026bdc974be3d45a3`.
Near data/stack stays 65,488 bytes (48 spare); resident code is 65,358 bytes,
FILE_CODE 7,287 bytes, retained floor 28,861 paragraphs including PSP.

The diagnostic `--gateway-uart-probe` runs after actual UART acquisition, opens
the four application files, declares kind9, brackets direct COMSPEC, dumps the
raw receive ring, drains it through the real driver/poll, then exits. Its
136-byte report and near-call helpers are diagnostic-only. This is not a normal
frontend or deployment selection.

## Remaining application integration

The optional [normal frontend](GATEWAY_FRONTEND.md) now supplies the scheduler,
keyboard/menu route, foreground revalidation, printer drain, display/mouse
ownership, no-return-key behavior, serial/file error quarantine and foreground
connection poll. Its separate receipt covers the composed application. Active
BBS interactions, sustained traffic, disconnect/reconnect, transfers and physical
Boca/SPA2102/SynthModem acceptance remain open.

The DOS peer intentionally delivers in-flight bytes after flow requests; it
does not prove a physical peer honors RTS or emulate SIP/audio/carrier. No
hardware performance benchmark or perfect BBS-rendering claim follows from
these tests. Physical files, deployment selector, network, boot, ATA and services
are unchanged.
