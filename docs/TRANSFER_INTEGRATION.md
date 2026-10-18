# Remaining live transfer integration

The native owner/file/UART components and actual DOS storage composition are
verified separately. The interactive terminal still has no live transfer command.
This audit identifies the next required work; it is a design plan, not completed
runtime evidence. The terminal checkpoint remains `7b9ca14b`, with DGROUP/SS
59,408 bytes and separate BBS validation.

## Preserve memory rather than discard application state

A11264-byte near receive arena cannot simply be added to the current DGROUP.
Its native pointer is near/DS-relative, as are the maintained storage callback
buffers; moving the receive arena far would break those ABIs.

The8192-byte erase shadow already uses the segment:offset fields
`erase_shadow_segment/offset`. Recovered rectangle paths272b/2785, ICHd30a and
DCHd51c/d520 load that far address. The4096-byte history ring likewise already
uses LES through `terminal_history_pointer`; its bounds are offsets. They can
move together into a separate ungrouped FAR_STORAGE segment, retaining all
history/metadata. This would leave58,384 DGROUP bytes after adding the11264-byte
receive arena, before further adapter/control state (7,152 bytes of headroom).
No such relocation has been made in this checkpoint.

The live direct near shadow clears in `src/terminal/main.asm` and
`terminal_reset.asm` must become ES:DI clears of the actual shadow segment.
Preserve ES around them. History pointer/bound initialization must retain proper
linker OFFSET/SEG relocations; it has no other live direct near accesses.
Keep a far end marker covering both arrays.

PROGRAM's current resize floor derives from DS and the stack end. Once there
is storage outside DGROUP, it must retain the maximum of the stack end and far
storage end, expressed in paragraphs relative to PSP. Set both process keep and
minimum floors. Never assume Wlink orders the far segment before STACK. Verify
map/MZ memory extents and use a child memory-pressure/far-canary regression so
DOS EXEC cannot overwrite released application state.

## One owner, actual shared state

Compose the native receiver once per transfer with one live BP frame and
setjmp context; keep it active until return. Use the actual UART ring/count
aliases rather than duplicate diagnostic words. Protocol ID4 means XMODEM and
is independent of terminal profile4/6. The native baud table index is not the
actual baud word; supply bounded initialization or an explicit source-owned
rate table. Preserve all near-C/callee-cleanup differences documented in the
individual modules.

The standalone IO adapters are controlled fixtures. Replace their UART/time,
carrier, keyboard, UI and file callbacks explicitly; do not turn fixture defaults
into production success stubs. Connect the real DOS bridge using prepared stage
names, empty/bounded native prefix and the independent completion/error gate.

## Serviced waits and binary flow

The raw original timed reader/header helpers and transmitter have blocking or
unbounded waits, and do not service the maintained foreground. Use independent
full-clock deadlines and service transfer cancellation/Alt-X, UART RX/TX and
flow while waiting. Do not call the ordinary `terminal_poll_io` wholesale:
it also runs macros, PROGRAM, bindings, redial/hangup and parser ownership paths.
Suspend those producers while the transfer owns the transport. Drain prior TX
before starting C/NAK negotiation. Treat RX overflow as transfer failure and
preserve bytes queued after completion instead of blindly flushing the ring.

The UART SOFT ISR consumes incoming11h/13h before storing binary payload. An
ordinary binary transfer under that mode would lose valid file bytes. Initially
reject SOFT (including simultaneous SOFT+HARD) before file/stage acquisition,
unless an explicit end-to-end binary flow policy is implemented. HARD/NONE
preserve byte values; their stall/overflow and modem compatibility still need
actual owned-peer and physical validation. The separate TUART test uses NONE.

Native double-CAN/local/carrier cancellation uses the foreground nonlocal
context, never an ISR/DOS-interrupt longjmp. Timeout exhaustion can leave the
native FILE open, so the maintained owner must always abort/close on failure.
A successful native close only seals a stage; only the independent maintained
success/error checks authorize installation.

## EOT and validation

The exact owner ACKs EOT before final file IO and ignores final write/close
results. Current actual-DOS composition prevents failed installation, but cannot
retract an ACK already sent. Define and test the live EOT policy explicitly;
never claim wire success implies installed data. Preserve exact baseline tests
and distinguish intentional safe maintained behavior.

After these changes, test the combined terminal, real UART and real file backend
against an independent owned peer: binary CRC/checksum,128/1024 and mixed blocks,
sequence rollover, duplicate/retry/corruption, flow stalls, cancellation,
carrier loss, timeout, disk/close/install failures and exact target bytes.
Recheck BBS navigation and PROGRAM restoration on the new terminal hash. Batch,
window/streaming protocols, uploads, all advertised protocol families and complete
transfer/settings UI remain part of the full application goal.
