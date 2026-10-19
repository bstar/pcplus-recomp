# Shared renderer: call boundary and remaining integration

ASPECT must invoke the actual terminal renderer while a script runs. A separate
query responder cannot reproduce native parser consumption, cursor reports,
profile state, scrolling, history or MESSAGE output. The automatic Synchronet
failure in [directory scripts](DIRECTORY_SCRIPTS.md) remains the acceptance test.
Neither of the mechanical bridge components described here publishes a renderer
capability or closes that test.

## Isolated DOS evidence

`resident_service.asm` is an isolated source-owned experiment. A parent COM
program EXECs a child COM program. The child far-calls parent code, which
switches to a guarded parent stack, reads the current DOS PSP, invokes a child
callback and returns. The callback switches to a separate child stack and reads
the emulated COM1 line-status register. A nested service request is rejected.

The actual 8086 DOS run passes 32 calls, 32 callbacks, 32 nested refusals and 96
controlled INT60 injections. Sixteen actual child timer-handler entries occur
while SS is the parent segment. The current DOS PSP remains the child. Caller
registers, FLAGS including IF/DF/CF, stack position and both redzones survive.
An independent CPU checker covers 16 scenarios and interrupt-visible stack
transitions. These are software-interrupt and timer proofs; they do not prove
physical UART IRQ behavior or arbitrary renderer call depth. The tiny body
touches 30 bytes of its 1,024-byte slice.

```sh
./tools/dev --command python3 standalone/build_aspect_resident_service.py
./tools/dev --command python3 standalone/check_aspect_resident_service.py
./tools/dev --command python3 standalone/test_aspect_resident_service_dos.py
```

## Reusable bridge contract

`resident_bridge.asm` is a separate OMF library for parent code whose CS differs
from DS. Mutable bridge anchors live in CS, preserving the terminal's near-data
budget. Initialization selects an existing unused DS=SS stack slice with 16-byte
redzones. It checks alignment, a minimum 512-byte slice, address bounds and a
512-byte separation from the current live stack. A production owner must also
check separation at its final EXEC safe point and measure the actual renderer's
maximum usage. The application owns DOS allocation/MCB checks, descriptor and
callback identity, lease generation, operation admission and byte/time budgets.

The far call takes AX=request and BX=value. It returns a typed AX result and
preserves other caller registers and FLAGS. It masks interrupts while switching
SS:SP and DS, restores the caller's IF only after DS=SS is valid, and clears DF
for the body. The body must preserve parent DS/SS; other general registers may
change. The callback is a separately validated far trampoline that restores the
parent context after running on its declared child stack. External reentry is
rejected before changing the saved owner context.

The body can return normally or call the synchronous typed-abort entry, which
discards only this service's frames. It cannot jump to the parent's ordinary
shutdown or reset the suspended EXEC stack. Stack guards are checked before and
after the body. This detects a guard violation; it is not a general memory-safety
guarantee for arbitrary native instructions or unbounded interrupt nesting.

The library is not linked into the terminal or advertised through ASIO yet.
Its independent OMF DOS proof and renderer integration are separate requirements.

The OMF proof now passes 40 actual DOS cases and 40 independent CPU scenarios.
It checks normal return, deep typed abort, low/high guard corruption, rejection
before body entry, invalid reinitialization preserving a valid lease, and disable.
Eight nested callbacks/refusals, 48 controlled interrupts and four actual timer
entries exercise both contexts. The corrected fixture also verifies its outer
EXEC stack restore. It touches 136 bytes of its 2,048-byte slice in this body;
that is an observed footprint, not the complete renderer's maximum stack use.
Earlier fixture attempts with incorrect initial/return stack handling remain
retained and explicitly invalidated in the DOS report's history.

```sh
./tools/build test-aspect-resident-bridge
./tools/build test-aspect-resident-bridge-dos
./tools/build test-aspect-serial-unread-dos
./tools/dev --command python3 standalone/record_resident_service.py
```

The frozen terminal has 80 bytes free in DGROUP and 844 bytes free in resident
`_TEXT`. Production placement must therefore keep the bridge/body in far code,
with only small resident renderer/transport adapters and bounded state. The
service stack must reuse checked free space in the existing 8 KiB stack during
the EXEC lease. Adding a new near stack or assuming that a diagnostic's tiny
stack usage applies to the complete parser would violate these constraints.

## Raw continuation rollback

`aspect_serial_unread()` provides the checked one-shot rollback needed by the
real ANSI parser. It is valid only after a successful API read. Another read,
including an empty read, replaces or invalidates that permission. It restores
the original raw ring cell, so seven-bit dequeue masking and XLT do not replace
the retained byte. A second unread returns STATE. The operation preserves IF
instead of using native ABDE's unconditional STI.

If an IRQ filled the freed slot before rollback, unread returns fatal OVERFLOW
and leaves the full queue intact. Its future parser callback must turn every
nonzero result into a typed service failure; native callers assume a void
unread and cannot simply ignore this checked result. CPU tests include actual
ISR filling, wraparound, IF0/1 and raw-byte preservation. Four actual DOS cases
exercise preload and live IRQ reads on COM1/COM2, including a full wrapped FIFO.

## Required application boundaries

The source audit identifies these integration requirements:

- Call real `terminal_receive_character` directly for a mapped lead byte.
  `terminal_receive_input` would apply translation again. Parser continuations
  use child raw reads/unread and never reach WAITFOR's matcher.
- Route report byte/string output synchronously through the child's serviced
  UART. Parent TX queues and parent UART polling are stale during EXEC.
- Replace parent foreground polling with a narrow child transport/cancel path.
  Audit direct UART reads in `terminal_wait_control_n` as well as the normal
  parser continuation callback.
- Reject CSI media-copy at entry before any parameter or handle mutation.
  Its current `terminal_program_pending` guard is false during child execution;
  private `5i` could otherwise open PRN under the child's DOS identity.
- Check actual closed/uncertain file-owner state at admission. Preserve truthful
  disabled capture/printer paths and reject reopening before mutation.
- Intercept unsupported renderer aborts before global parent stack reset.
  Preflight unsupported mode lists and control policies before earlier parameters
  mutate state. Local bounded parser errors keep their ordinary return path.
- Latch screen adoption at successful service admission, including later script
  failure. Skip all old PROGRAM video-mode, screenshot, cursor and shape restore.
  Preserve the real shared cursor, margins, tabs, attributes, keymap and history.
- Route MESSAGE through the renderer. Runner errors currently print after serial
  close and need a defined lifetime or a parent diagnostic handoff. BIOS/DOS
  teletype after admission would diverge from the renderer's cursor state.

Only after these boundaries, stack usage, callback error paths and full parser
replays pass should the capability be advertised and native WAITFOR/RGET display
enabled. COMGETC's normal post-open suppression must remain intact. The strict
automatic Synchronet editor test and ENiGMA workflows then require actual reruns.
