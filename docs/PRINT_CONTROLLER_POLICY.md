# Maintained dedicated-print policy

This records the maintained serviced owner replacing native12:D0D0, implemented
in `src/terminal/print_controller.asm`. It distinguishes deliberate safety changes
from the exact native recovery in
[PRINT_CONTROLLER_NATIVE.md](PRINT_CONTROLLER_NATIVE.md). It is not itself a
test result; linked and actual DOS validation records establish the tested scope.
Physical printer behavior remains separate. No native reconstruction bytes are
changed by this policy.

## Admission and ownership

Unprefixed `CSI5i` requests dedicated raw printing; it must not silently become
private`CSI?5i` processed stream copying. Admission happens at the parser's
foreground boundary with valid geometry/state and no monitor, transfer,
snapshot, screen-print, macro, PROGRAM or unrelated wait owner.
Denied admission leaves RX, existing printer ownership and caller state intact.
The current implementation uses a serviced modal wrapper inside the existing
CSI call: bounded service/filter callbacks run without invoking another ANSI
parser. It returns only after dedicated ownership resolves, preserving the
order of remaining parameters in a compound CSI command. Admission may wait
for a previously requested printer close to finish.

The owner uses the maintained checked PRN backend. A healthy preexisting PRN
handle is borrowed, retaining its prior stream-copy flag and responsibility for
closing it. Dedicated RX bypasses the processed logger, ordinary ANSI parsing,
processed capture and printer-copy formatting. A newly acquired PRN belongs to
this controller until its accepted queue drains and checked close resolves.
No unconditional open may overwrite a borrowed handle, and no close may be
performed twice after an uncertain outcome. Entry/open denial is distinguishable
from a sticky failure after acquisition.

Alt-B remains a recognized blocked local action; it does not transmit a fake
BREAK byte or invoke an unproved calibrated duration. See
[BREAK_NATIVE.md](BREAK_NATIVE.md) for the exact native operation and F03 gap.

While active, ordinary keys and network key bindings may transmit through the
real foreground queue. Nested macro, PROGRAM, monitor, capture/transfer and
screen operations must not enter another modal consumer. Alt-X/Alt-H remain
responsive through an explicit orderly exit/cancel path. UART IRQ/flow/carrier,
printer output and clock checks continue at bounded foreground service points.
A backend DOS call may itself block inside a device driver; an application tick
deadline cannot interrupt that call, and documentation must retain that limit.

## Grammar and intentional changes

The native body is the source for accepted byte classes and profile gates:
NUL/DEL outside or inside a prefix are ignored; ESC starts buffering;
DEC-family`[` marks a CSI-like prefix, any digit4 marks stop, other digits and
semicolon continue; final`i` with both markers stops, with`[` only discards the
prefix, otherwise keeps waiting. Consequently`ESC[14i` and`ESC[4;5i` stop as in
the native routine. ProfileID1 accepts`ESC X`; other-family9004 accepts`ESC a`
(lowercase61h). A nestedESC is an unknown byte, replaying the current buffer;
it is not a restart. These native quirks must not be mistaken for strict ECMA
parameter parsing or a backslash terminator.

The maintained changes are explicit:

- Outside a buffered prefix, received14h exits without output for native
  profile1Fh; for other profiles it is printed **once**. Native's duplicate output is a recovered fallthrough bug.
- Prefix capacity is32 bytes **including the initialESC**, preventing native
  unchecked stack-buffer growth. On an over-capacity incoming byte, replay the
  stored prefix and the current byte literally once, then reset prefix state.
  This33-byte replay uses reserved queue capacity and does not interpret that
  overflow byte as a newESC; only a later byte can start another prefix.
- A36-tick deadline starts at the firstESC and uses a full32-bit BIOS-day tick
  difference with midnight correction. Digits, semicolons and ignored NUL/DEL
  do not refresh it. On expiry replay the actual stored bytes and reset prefix
  state. Never synthesizeFFh from an absent-byte/FFFFh sentinel.
- Keyboard Escape normalization compares ASCII AL=1Bh, accepting actual BIOS
  key words with a scan code as well as normalized001Bh. Two consecutive
  keyboard Escapes end the owner; the first is transmitted once. Other keys
  reset this keyboard sequence; RX does not. This broadens native's exact-word
  comparison deliberately and must be independently tested.

Printing raw bytes uses the checked raw printer queue, not09B6 or the optional
CR-adds-LF path. Native36FC flushes each byte; the maintained backend may batch
foreground progress while preserving ordered bytes and explicit accepted counts.
No synthetic EOF, timestamp, formfeed or final newline is added by this owner.

## Termination, partial prefixes and failures

A recognized wire terminator is consumed as protocol control and not printed.
No subsequent byte may be dequeued until ownership returns to ordinary input.
In particular, the first banner/menu byte following`ESC[4i` stays in the genuine
UART RX ring; it must not be read into an unrelated private queue or discarded.
Stopping enters a drain state serviced by the modal wrapper without recursively
invoking the parser. Buffered printing finishes while RX remains untouched,
with UART service and bounded cancellation still active.

An explicit local exit or carrier loss is not proof that a partial buffered
escape is a terminator. If the device is healthy, replay the actual prefix once,
then drain the accepted printer queue and release ownership. Never feed it back
into the ordinary ANSI parser, where its interpretation could affect the UI or
consume a following byte. Alt-X's global shutdown may perform its existing
bounded printer drain rather than start another nested synchronous owner.
Carrier loss must not trigger further reads to complete a prefix. The owner
retains whether connection state was online at admission: a later transition
away from online cancels even if connection polling observed the falling DCD
before the controller sampled it. Stable DIRECT/idle sessions with DCD never
observed high remain usable; the independent high-to-low latch still applies.

On driver/write failure, acceptance is no longer trustworthy for pending bytes.
Latch the first error, retain the backend's partial accepted count, explicitly
abandon unaccepted queued/prefix bytes, and restore the terminal without retrying
a possibly partly accepted write. A failed borrowed PRN cannot resume prior
stream copying as though healthy: disable copying and expose the sticky error.
On successful exit with a healthy borrowed PRN, restore the prior copy flag and
leave the same handle open; do not take a second open/close cycle. A privately
acquired handle closes once after drain. Checked close failure remains visible,
and an ambiguous close prevents reuse rather than retrying the physical close.

RX overflow remains the application's explicit overflow error, rather than a
successful dedicated-print completion. Cleanup must not overwrite an earlier
exit/error with success. A partial prefix may be replayed during bounded cleanup
only when device health and queue capacity permit; otherwise report its loss
as part of the failure. No bytes which were never accepted by the backend may
be counted as printed. The exact order of cleanup/UI notices must preserve the
primary error even if restoring a borrowed state or closing PRN also fails.

## Review and validation boundaries

Independent implementation review should check admission/pending/active/drain
transitions, one backing word per shared native state, caller/callee cleanup,
flags/register preservation, prefix bounds, first-byte day-tick expiry, raw-byte
queue accounting and exactly-once close. It should also check simultaneous
ordinary-copy and dedicated-print ownership, failed private admission, and
explicit application shutdown while a prefix or PRN wait is outstanding.

Meaningful regressions need actual linked UART ISR/foreground and checked DOS
PRN code with hardware/kernel-only models, followed by source-built DOS virtual
printer runs. Cover binary bytes, native grammar/profile differences, bytes
following the terminator, prefix overflow/timeout across midnight, cancellation,
carrier, driver/write/close failure and borrowed-handle preservation. Memory
fixtures for native recovery prove native instructions; they are not evidence
that the maintained owner or a physical printer passed these scenarios. Keep
physical driver blocking, hardware latency and full-application gates explicit.
