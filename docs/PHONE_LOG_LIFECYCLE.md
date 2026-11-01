# Retained connection events

`src/directory/phone_log_lifecycle.c` now supplies the foreground producer
needed by the [connection integration plan](PHONE_LOG_LIFECYCLE_PLAN.md).
It is a component, not yet linked into the terminal's logger bank or called by
connection transitions. It performs no filesystem or clock operations.

## Admission and event lifetime

`ready` requires an enabled queue, no active/pending producer event, no retry
or recovery latch and two available queue slots. This reserves room logically
for START and END under the single-producer contract. It is not a lock against
another raw queue producer. The controller must check admission before
initiating a new logged connection and check START acceptance at the actual
successful transition; those terminal hooks remain to be implemented.

`begin` passes the captured name, target and timestamp to the existing queue.
Only acceptance advances the process's nonzero 32-bit generation. Invalid
input, disabled logging, full queues and retries do not advance it. A repeated
begin while active is a duplicate; a pending END refuses another begin.
Generation arithmetic skips zero on wrap, but wrap is not yet exercised by
this native diagnostic.

`end` first validates the captured timestamp against the original START. An
invalid or backwards time is rejected, with the session still active. If the
queue accepts END, the producer becomes idle. If the queue refuses it, the
producer retains the original validated timestamp and returns `PLL_PENDING`.
This means accepted by the producer, pending admission to the queue; the
snapshot preserves the underlying queue status. Repeated END cannot replace
that timestamp, and readiness/begin stay blocked.

`service` retries only RAM enqueue using the retained timestamp. It never
rereads the clock, writes a file or acknowledges a disk retry. A queue recovery
latch therefore leaves the event pending. Explicit disk retry and ambiguous
close recovery remain governed by the checked backend. There is no reset API
that could discard an active or pending event.

The initialized near owner is 38 bytes; the public snapshot is 10 bytes.
Compile-time assertions bind these layouts in the DOS compiler. Entry points
use near cdecl with DS=SS. Caller timestamps/snapshot outputs are checked for
nonwrapping near spans and aliases into the private owner. The four-record,
666-byte near/far queue is unchanged.

## Actual DOS evidence

The [receipt](validation/phone-log-lifecycle.json) binds six workflows in each
of two queue-storage builds: 12 actual 8086 DOS cases with 550 assertions.

1. Successful call, repeated START/END, invalid/backwards timestamps, exact
   final state and exact native text output.
2. Two calls fill all four queue records. Another call is refused without
   advancing its generation; one drain is still insufficient, two permit it.
3. An explicit END-refusal wrapper retains the original timestamp. A repeated
   END with a different hour cannot replace it; begin is blocked until service
   enqueues that first END. The resulting row is checked independently.
4. An actual short-prefix DOS write is rolled back. New admission refuses the
   retry latch without further writes; explicit retry permits one exact row.
5. A diagnostic ambiguous-close result after a real DOS close leaves END
   pending, refuses redial/service recovery and performs no blind append.
6. Disabled logging neither admits a call nor creates the log file.

The tests compare exact file bytes independently in Python, compare the final
queue/producer states in DOS, check JFT restoration, actual DS=SS and unchanged
42-byte kernel/hardware snapshots. END refusal and close ambiguity are declared
boundary models; the saturation and short-write/rollback paths use the real
queue and DOS backend. No application executable is patched.

An export of 18 committed public source files from `aa6969e` rebuilds both
executables byte-for-byte and repeats all 12 cases/550 assertions. The export
copies no original executable/install, old object or Git metadata.

```sh
./tools/build test-phone-log-lifecycle
```

Use fresh output directories for direct runner invocations. The failed initial
link and stdout-newline attempts remain outside acceptance; the receipt names
the successful run and its public-source repeat explicitly.

Next bank the producer, add transition/admission hooks, resolve child-owned
carrier observations and clock ownership, and schedule UART-aware disk polls
with visible full/retry/recovery handling. The current component tests do not
prove those application paths, generation wrap, complete feature composition,
physical Boca/SPA2102 behavior, sustained transfers or card deployment.
The published BBS package and card have not been changed.
