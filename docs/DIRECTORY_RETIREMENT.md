# Retire pending calls before the next selection

The opt-in `--directory-retirement` build saves pending directory statistics
after disconnect through PROGRAM kind 7. It uses the existing UART drain,
RTS/IRQ/vector handoff and shared directory-storage transaction, then returns
to the terminal without a return-key prompt. This is a prerequisite for live
selection changes, not an implementation of selected-entry adoption/dialing.

```sh
./tools/dev --command python3 standalone/package_special_edition.py --build \
  --custom-irq --directory-retirement --output build/retirement-package
```

The flag implies the resource-owner variant and retains the LoC.6 splash.
The older ordinary, LoC.6, CLI-only and resource-owner binaries remain exact.
No card deployment is included.

## One attempt per connected event

The existing connected-event handler arms retirement while retaining its
pending flag, calendar and modular count. Foreground polling waits for logical
disconnect and idle parser, RX/TX, transfer, controller, monitor, process and
popup owners. PROGRAM admission precedes the actual write. Startup cookie
initialization preserves an event already armed before the first poll.

The worker checks the actual handed-off UART, empty queues and PROGRAM owner
before IO. The old canonical directory path and expected record remain with
the shared storage owner. Canceling a queued attempt consumes no statistics;
pending counts remain for shutdown. A new connected event may arm a later
attempt. There is no repeated automatic retry of the same failed attempt and
no forced reset of uncertain file/recovery ownership.

Before writing, the worker computes the exact expected accounting patch and
checks the frozen setup context. A confirmed installation consumes the pending
count and refreshes only the eleven date/count bytes in the logical record and
the setup owner's cached context. This also happens when installation succeeds
but backup cleanup fails. An uninstalled failure leaves the count and logical
record intact. Unexpected post-write inconsistency requests controlled exit.
Actual save failures display the bounded `Log save error` status notice.

Kind 7 executes no child, so it bypasses the PROGRAM capture-close step. An
independent capture remains open with its handle, enabled sink and owner state
unchanged. Shared file reservations continue to reject conflicting aliases;
real child operations retain their existing capture-close behavior.

The pure setup reconciliation API accepts differences only in those eleven
bytes and refuses a pending setup or outstanding offer. It preserves source
baud/clipboard baselines and other setup state; it does not rebind or reread a
file merely to refresh statistics.

## Settings after a child changes folders

Testing retirement exposed a separate application gap: settings scheduling
accepted only a leaf PRM name and executed a relative `PRMEDIT.EXE`. After an
ASPECT child changed CWD, settings could not open reliably.

This variant now stages a bounded explicit tail from the setup owner's frozen
canonical PRM name and locates PRMEDIT beside the parent's executable through
the checked PSP/environment helper. Both outputs publish only after PROGRAM
admission. The setup transaction retains that frozen namespace through begin
and finish, while still requiring the same lexical request and logical context.
No shell command or CWD-based fallback is used. Supported canonical PRM names
remain DOS83 paths of at most 63 bytes.

## Validation and limits

The [receipt](validation/directory-retirement.json) binds the application,
package and evidence. Five actual DOS8086 COM3/IRQ5 workflows cover successful
save followed by PRMEDIT reuse, a counter wrapping to zero, preserving an open
capture, an existing backup that prevents installation, and one explicitly
injected backup-delete failure after installation. Each runs a source-built
ASPECT child that changes CWD.

The passive DOS/timer observer requires DS=SS, closed popups, disconnected
state, IRQ masked, IER disabled, RTS lowered and the original vector at every
retirement DOS boundary. It records the exact active-state changes, installed
and pending flags, visible failure notice and subsequent PRMEDIT EXEC. The
cleanup-failure variant separately injects its declared DOS error; the normal
observer does not alter application state or kernel results. Source/decoy,
PRM/script preservation, recovery artifacts, exactly-once installation and
final hardware restoration are checked independently.

Thirty-five linked CPU cases cover admission refusals, connected-event arming,
queue/cancel/rearm, context reconciliation, immutable PRM namespace and settings
publication failures. BIOS time/calendar and DOS canonicalization are modeled.
Six damaged linkage controls are inspected, never executed. Packaged nested
ASPECT compilation and later redisplay, and a stock ENiGMA login/editor/preview
run through the actual proxy, pass. The ENiGMA check uses250 ms key framing and
no artificial input-byte delay; its historical `exact_screen` predicate checks
final markers/frame size, not a complete character/attribute oracle.

An isolated export of all 772 declared source files from commit `a580fc7`
reproduces all ten package files exactly with the pinned Nix toolchain. The
export cannot discover ancestor Git metadata and includes no original binary
input. Uncommitted telephone-log work is excluded from that reproduction.

The candidate retains both63000-byte history allocations, the8192-byte stack
and the existing63504-byte frozen-memory loan. Near storage is65136 bytes,
resident CS has246 spare bytes and minimum module retention is411904 bytes.

Selected-entry commit, translation/script staging, same-entry refresh during
an adoption transaction, and dialing from the preview remain open. The complete
F01–F16 scope, physical Boca/SPA2102 and card acceptance remain open.
