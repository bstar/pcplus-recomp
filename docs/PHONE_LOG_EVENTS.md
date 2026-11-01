# Session call-log events

The optional `--phone-log-events` terminal now calls the
[banked producer](PHONE_LOG_LIFECYCLE_BANK.md) at actual session boundaries.
It implies lifecycle/startup/claims. This is an experimental RAM-event build:
there is no live disk scheduler, and it deliberately reports unsaved records
at shutdown. It is separate from the published BBS package and card.

## Application boundaries

Four zero-argument far cdecl entries run in PHONE_LOG_CODE. Seven relocated
call sites are checked against the actual MZ/map:

- One admission call in `terminal_connection_start_impl`, before clearing
  transmit state or initiating another modem/DIRECT attempt.
- Two START sites: successful response classification and logical DIRECT start,
  before the directory callback can schedule a script.
- Three END sites: observed MODEM carrier loss, admitted modem retirement and
  DIRECT hangup. A failed pre-CONNECT attempt creates no call records.
- One finalizer in common shutdown, after restoring UART/IRQ/PIC ownership and
  before remaining file-owner cleanup. It can end an outstanding logical call
  and preserves a preexisting errorlevel.

Admission first services a retained END in RAM, then requires room for another
call pair. Refusal leaves the transport idle and shows `Call log blocked`.
Disabled logging bypasses event timestamp reads and records no generation.
Repeated events are delegated to the producer's generation/retention policy.
No log-file append runs in these callbacks.

The existing failed-hangup branch that retains state 6 on high DCD precedes
modem retirement, so that branch has no END hook. This is the intended source
placement; the selected native cases below do not yet prove failed-hangup or
physical-DCD behavior. Likewise, child entry/return does not create a new
START. Exact child-owned carrier observation and clock handling remain open.

A successful START captures the accepted directory name and actual live dial
target. Non-directory modem calls use the bounded label `MODEM`. DIRECT
selection uses its directory name and an empty live dial target, because it
sends no dial command. This does not infer an Internet BBS hostname from a
telephone number or from a hostname entered later in the Linux bridge.

Dates/times come from the existing bounded DOS date/time/date provider.
A clock failure is visible and remains a fault for shutdown reporting; no
fabricated time replaces it. A valid but refused END remains retained by the
producer, with its original timestamp and redial gate.

## Unsaved records remain explicit

Until the scheduler exists, queued records are RAM-only. Common shutdown
reports `Call log pending; records were not saved.` and sets errorlevel 12
when no earlier error exists. `PLE_UNSAVED` (512) is distinct from queue-full
and the producer's pending-END result. An empty or disabled queue exits through
its ordinary status. This checkpoint is not durable telephone logging.

The current image is `build/terminal-phone-log-bank-2fbc7bc87592/TERMINAL.EXE`,
SHA256 `0074fa9e872cf6544572295285c2e883beace58f7e75ed0501cdc3ff6d24fc0a`.
It uses 64,672 near data/stack bytes (864 spare), a 9,807-byte logger bank and
18 resident-code bytes spare. The existing histories, stack, queue and
compiler/VM limits are unchanged. The optional native-reset bank still remains
a separate feature combination from the published directory-adoption package.

## Native evidence

Eight actual 8086 DOS cases pass in `events-final-01`:

1. CONNECT and ordinary exit: one START/END generation.
2. Configured hangup before exit: exactly one pair, without a duplicate END.
3. BUSY: no successful call or queued record.
4. Dial timeout: no successful call or queued record.
5. Failed first attempt followed by redial: the successful call is generation 1.
6. Logging disabled: normal serial/rendering behavior and no records.
7. DIRECT call: one pair, selected name and empty dial target.
8. Two DIRECT calls followed by another attempt: four retained records, no third
   generation, visible capacity refusal and the correct directory accounting.

The tests use the normal terminal, synthetic serial peer and real BIOS keys.
They require actual CPR/DA replies, retained initial banner, unchanged settings,
expected directory accounting and restored hardware. Python independently
validates record kinds/generations, name/target layout, native calendar text and
elapsed time; the final producer and queue state must agree. No `.FON` is
created because no log append is yet scheduled. Expected unsaved shutdowns
must return exactly errorlevel 12 and display the notice; this is not accepted
as normal durable success.

A passive test TSR derives the load base from the installed UART vector.
Its timer samples live state without DOS/UART/keyboard activity or application
RAM writes. Its INT21/4C handler takes the final witness only when caller CS and
SS match the parent, before DOS deallocates it. The collector restores and
checks both original INT21 and INT1C vectors before writing the witness.
Timer observations may coalesce transitions; acceptance uses the complete final
record sequence, not an assumption that every timer sample saw every event.
The product receives no diagnostic flag or memory patch.

The [receipt](validation/phone-log-events.json) binds a clean export of 1,735
committed public files from `a4b605b`. It reproduces the exact event-enabled
terminal and repeats all eight event cases. Another 46 native regressions pass:
21 producer cases/1,041 assertions, 15 queue-claim cases and ten startup/capture
cases. The last ten run on the independently compared event-off lifecycle
control, not on the event-enabled executable.

Both the event-off lifecycle control (`a3ad2cca...`) and the bank-only control
(`3fbb1acf...`) remain byte-exact against `ca37434`. No original executable,
install, old object or Git metadata is copied into the export.

```sh
./tools/dev --command python3 standalone/test_phone_log_events_terminal.py \
  --terminal build/terminal-phone-log-bank-2fbc7bc87592 --label YOUR-EVENTS
./tools/dev --command python3 standalone/prove_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-2fbc7bc87592 \
  --output build/YOUR-EVENT-PROOF --commit a4b605b --baseline-commit ca37434
```

Use fresh labels/output directories. Earlier compile, oracle and status-model
attempts remain outside acceptance; the receipt identifies the final native run
and public replay explicitly.

Next implement UART-aware foreground disk scheduling and checked shutdown
draining, then visible retry/recovery controls. Extend native coverage for
failed-hangup continuity, real carrier edges, exceptional exits, child ownership,
clock failures and sustained traffic. Whole F07/F10, full application/feature
composition, BBS rendering/protocol acceptance, physical Boca/SPA2102 and card
deployment remain open. No live BBS, installed bridge, ATA, host network,
published package or removable card changed.
