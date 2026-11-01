# Guarded call-log writes

The later [call-log controls checkpoint](PHONE_LOG_CONTROLS.md) adds confirmed
retry and application-level uncertain-close refusal. This page retains the
original disk-only image and its 13-case validation boundary.

The optional `--phone-log-disk` terminal now schedules the checked append
backend from its main loop and drains retained records after UART restoration
at shutdown. It implies the existing event/lifecycle/startup/claim options.
This is application file-write integration, not complete F07/F10 or deployment
acceptance; retry/recovery controls and wider transport testing remain open.

## Scheduling and serial ownership

One far main-loop entry appends at most one queued event per eligible call.
It never runs from parser, keyboard, ISR, connection or child callbacks.
An explicit owner guard rejects reentry. It defers while a parser, child or
pending PROGRAM, transfer, macro, modal view, controller, monitor, break or
queued RX/TX data owns the foreground. It also requires interrupts enabled
and the application's UART still acquired.

For a live connection with receive flow enabled, the scheduler temporarily
lowers RTS and/or sends XOFF after checking physical TX completion. It waits
at most two BIOS ticks, with a finite iteration bound. An incoming RX byte
cancels that opportunity so the main loop can process it. Receive interrupts
remain enabled during the DOS append/commit/close.

The temporary pause does not borrow the driver's watermark flags. On release,
a short IRQ-protected update raises only the RTS it owns and queues XON only
if driver watermark ownership has not intervened. The ordinary UART poll and
existing shutdown flow cleanup send that queued control byte. A known lost
MODEM carrier suppresses XON; idle MODEM file writes send no new XOFF into
command mode. These are application policies; the synthetic tests do not
prove physical flow timing or unbounded DOS/disk latency tolerance.

Online NONE-flow connections retain events in RAM. Idle/offline opportunities
and shutdown can drain them. The idle path still relies on the existing UART
ring and interrupt service if an unflowed peer resumes unexpectedly; no
unlimited buffering or arbitrary-latency protection is claimed.

The checked backend still owns absolute identity, short-write rollback,
commit/close, retry and ambiguous-close recovery. Any scheduler error latches
until explicit recovery is implemented; neither later polls nor shutdown
blindly retry it. The terminal can continue the existing serial session and
hang up. Admission of another logged call is blocked while that error remains.
Warnings distinguish retry/recovery and are shown once per unchanged class.

## Shutdown and PROGRAM handoff

Common shutdown first finalizes any remaining logical call, then invokes a
bounded drain after UART/IRQ/PIC restoration. It preserves the original event
stamps, services a retained END before/among queue drains, and stops immediately
at retry/recovery or another error. Healthy complete calls return normally.
Unsaved or faulty records still produce the notice and errorlevel 12 without
replacing a preexisting application error.

PROGRAM admission now checks the logger's checked file owner before delegating
to the original capture/printer/file gate. Open, uncertain or recovery-latched
log handles cannot be inherited by a new child. The small far wrapper preserves
the original gate's return values, including printer-drain deferral. The native
case below exercises healthy generic PROGRAM handoff; uncertain-close rejection
in the complete application remains a separate validation requirement.

## Current image and native tests

The image is `build/terminal-phone-log-bank-a0204da7f636/TERMINAL.EXE`, SHA256
`e9d0c4987a2faa3505b909ba0c6f7299c3c7769ee9815b0c8835e9b80a1350af`.
It retains 64,752 near data/stack bytes (784 spare), a 10,852-byte logger bank
and 65,530 resident code bytes (six spare). Existing histories, application
stack, queue capacity and compiler/VM limits are unchanged. This remains the
optional native-reset bank combination, separate from the published BBS package.

Thirteen actual 8086 DOS cases pass in `disk-final-01`:

- Successful MODEM, configured hangup, failed dialing, timeout and redial.
- Disabled logging and a selected DIRECT connection.
- Three consecutive DIRECT calls, with all six records saved.
- SOFT, BOTH and NONE flow settings alongside the default HARD cases.
- A namespace failure after startup but before CONNECT: one append attempt,
  retained START/END, a retry notice, balanced XOFF/XON and errorlevel 12.
- Generic PROGRAM execution while online: the child takes and changes UART,
  IRQ and video state, returns to the same generation, and leaves one exact
  call pair with normal key delivery and final hardware restoration.

Normal cases compare exact heading, record count, name/number layout, calendar
text, elapsed time and final queue/generation/commit counters independently.
Timer snapshots prove a START was committed while the call was still active
in the flow-enabled cases. NONE-flow snapshots prove online commits deferred.
Each saved record requires exactly one queue poll. The failure case proves
only one poll occurred and its externally created directory/marker survived.
That namespace change is an explicit owned test action, not a product patch.

The passive observer retains the original parent-before-deallocation witness,
checks both restored vectors, and additionally reads disk attempt/status words.
A separate timer video latch proves the retry warning was displayed even when
a later hangup notice replaced it. SOFT/BOTH/failure cases require real emitted
XOFF/XON to balance. No synthetic terminal replies or application RAM writes
are used by the observer.

The [receipt](validation/phone-log-disk.json) binds a clean export of 1,739
committed public files from `89586fe`. It reproduces the exact new executable
and repeats all 13 disk cases. Another 54 regressions pass: eight on the
RAM-only event control, ten startup/capture cases on the lifecycle control,
21 producer cases/1,041 assertions and 15 queue-claim cases. These scopes are
separate; the older startup/capture tests do not claim disk-enabled coverage.

The RAM-only event, lifecycle-only and bank-only executables each match
`42e94e9` byte-for-byte. Their hashes remain `0074fa9e...`, `a3ad2cca...` and
`3fbb1acf...`. Original binaries/installs, previous objects and Git metadata do
not enter the export. Object inspection also proves the scheduler's eight
private/status bytes have complete initialized DATA and no nonempty BSS.

```sh
./tools/dev --command python3 standalone/test_phone_log_events_terminal.py \
  --terminal build/terminal-phone-log-bank-a0204da7f636 --label disk-check-01
./tools/dev --command python3 standalone/prove_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-a0204da7f636 \
  --output build/phone-log-disk-public-repeat-01 \
  --commit 89586fe --baseline-commit 42e94e9
```

Use fresh labels/output directories. Earlier link and warning-oracle attempts
remain outside acceptance; the receipt names `disk-final-01` and its committed
public replay explicitly.

Next supply explicit retry/recovery controls and add sustained data/protocol,
slow/error-I/O, physical flow/DCD, failed-hangup, child/ASPECT and exceptional
exit acceptance. Existing-file append and uncertain-handle rejection also need
full-application coverage beyond their component tests. Whole F01–F16 behavior,
feature composition, BBS rendering/protocol acceptance, physical Boca/SPA2102
and card deployment remain open. No live BBS, installed bridge, ATA, network,
published package or card changed.
