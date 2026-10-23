# Live KEY PROGRAM actions

The source-built terminal supports kind1 PROGRAM records imported explicitly
with `/T:FILE.KEY`. Alt-1..Alt-9 select records0..8; Alt-0 selects record9.
Kind3 remains TEXT; ASPECT0 and HOOK2 remain unsupported, including empty
records. Directory KEY/SCRIPT/META bindings and the complete original application
are not implemented by this global import path.

PROGRAM executes a local DOS command, not serial text. Stored command bytes
are passed literally to COMSPEC using ` /c `; no TEXT caret or pause expansion
runs. Commands must contain 1..51 bytes, no CR/LF and a bounded terminator.
An empty PROGRAM definition is rejected. Imported definitions are not executed
at startup: the local Alt-digit event requests execution.

## Safe scheduling and child ownership

`terminal_program_start` stages a command and returns AX0 queued,1 invalid,
2 busy or3 connection engine owns RX. It accepts only passive state0 or online
state6. Foreground transport and ANSI parser callbacks never invoke DOS EXEC.
The main loop calls `terminal_program_poll` at its safe point, so requests made
while servicing terminal input remain pending until that boundary.

Existing ordinary output, including terminal replies, drains before launch.
Normal keys wait in the shared32-word FIFO. Escape cancels pending PROGRAM and
queued keys; Alt-X/H/D and observed carrier loss cancel it before exit, hangup
or redial. FIFO overflow is explicit errorlevel3. Cancellation cannot retract
bytes already accepted by the UART, and keyboard cancellation is unavailable
while DOS is running a child.

A pending launch requires physical THRE and TEMT. SOFT flow first sends XOFF,
then waits for TEMT again. Full32-bit BIOS day ticks bound a no-progress drain
to36 ticks, handling low-word wrap and midnight; continued TX progress renews
that allowance. Timeout cancels the request with lifecycle8 and a local notice.
Previously recorded RX loss stops with errorlevel6 instead of hiding lost data.

Only mode3, 80 columns, active page0 is accepted for this handoff. Unsupported
views are rejected before launching a child. The terminal saves all4000 text
screen bytes, BIOS cursor position and shape while preserving its separate
logical ANSI cursor/attribute context. It preserves DTR, lowers RTS, masks the
selected UART IRQ, clears IER and restores the startup IRQ vector before EXEC.
The parent UART ISR is not installed during child execution.

After EXEC returns, the port is quieted again and the baseline vector restored
**before** the BIOS return/error prompt or blocking key wait. A child may have
changed its UART enables, divisor, vector or display. After a local key, the
terminal recreates mode3, restores the saved text/cursor/shape, reinstalls its
UART ISR and selected baud/format, and restores its launch-time modem-control
state. This path does not read RBR or overwrite the immutable startup hardware
snapshot. LSR overrun is recorded as RX loss. It preserves pending hardware data
for the resumed real IRQ handler; it cannot recover bytes lost while the parent
was absent.

The maintained process backend shrinks the static parent allocation through
the higher of STACK and FAR_STORAGE ends and restores SS/SP/DS across EXEC.
An actual DOS child allocation checks shadow/history canaries after the shrink.
COMSPEC/PATH selection, exact
API limits, DOS result meanings and DOSBox command-processor behavior are in
[PROCESS.md](PROCESS.md). These maintained services are distinct from the3102
exact recovered bytes documented in [PROGRAM_EXEC.md](PROGRAM_EXEC.md).

## Status and flow cleanup

`terminal_program_status` is lifecycle state, separate from DOS/child results:

| Value | Meaning |
| --- | --- |
| 0 | Idle |
| 1 | Queued |
| 2 | Executing |
| 3 | Cancelled |
| 4 | Completed |
| 5 | Launch failed |
| 8 | Drain timeout |
| 9 | Unsupported display view |

`terminal_program_result` is eight bytes: four words for process status, DOS
error, child termination/exit AX, and retained paragraphs. A successful command
processor invocation can have a nonzero child status without lifecycle5.

On resume, PROGRAM releases only an XOFF it owns, and only when buffered input
is low enough; a preexisting driver watermark pause stays owned by the driver.
On terminal shutdown, cancellation happens before `terminal_release_flow` and
UART restoration. That cleanup sends an owed XON through the real flow sender,
even when quit is set, CTS is low or peer XOFF blocks ordinary output. If THRE
never becomes ready within36 BIOS ticks, cleanup records failure and uses
errorlevel11 when no earlier error exists; it preserves an earlier error.

RTS/XOFF are requests to a cooperating peer. NONE flow cannot guarantee remote
pause, and even HARD/SOFT cannot promise that a peer has stopped before a child
runs. The fixed RX ring and UART can overflow during a long child. Child changes
to unrelated PIC bits, timer/keyboard hardware, other interrupt vectors or DOS
state are outside this restoration contract. This is not a sandbox for arbitrary
programs and does not reproduce all vendor overlay/UI/vector services.

## Verification

```sh
./tools/dev --command python standalone/check_program_actions_live.py
./tools/dev --command python standalone/check_meta_actions_live.py
./tools/dev --command python standalone/test_program_actions_dos.py
```

On frozen terminal SHA256
`7b9ca14b22f7729107f9be9c9592372d1a6c1a1c3b038a77474c55bea7e6f57a`,
56 linked PROGRAM inputs and343 Meta/TEXT inputs pass. The PROGRAM checks execute
actual scheduler, C policy, process, transport, recovered UART/IRQ and keyboard
instructions. Only DOS-kernel, BIOS and hardware boundaries are modeled; no
product callback is skipped. They verify all ten BIOS selections, safe-point
execution, literal tails, child-clobbered context/UART/vector/video restoration,
no RBR discard, startup baseline preservation, FIFO/cancel/carrier paths,
flow ownership and bounded shutdown cleanup across tick wrap/midnight.

Four actual DOS cases cover COM1/HARD, COM2/HARD, COM1/SOFT and a missing nested
command. An owned source-built child records inherited vector/IER/DTR/RTS/format
and exact arguments, changes UART/vector/video, then returns so ordinary serial
keys and final hardware restoration can be checked. DOSBox nullmodem has CTS
ready: these checks do not establish physical modem timing or hardware stall
behavior. Evidence records remain under ignored `build/terminal/` and
`build/program-actions-dos/`, with hashes tying each result to its tested build.

## Optional ASPECT action build

The separate [ASPECT KEY terminal](LIVE_ASPECT_KEYS.md) now supports global
kind0 filename actions, including empty no-ops, through the existing Script
owner. The unsupported-ASPECT statements above describe the unchanged baseline
products. HOOK and directory KEY/META import remain open.
