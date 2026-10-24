# Call-log events, formatting and clock

This maintained component connects captured connection events to the
[checked append backend](PHONE_LOG_FILE.md). It preserves each accepted event's
bytes and timestamp until a successful committed append. It is tested in DOS
with the private queue in both near and far storage. It is **not wired into the
terminal** and does not change the deployed application.

The [validation receipt](validation/phone-log-queue.json) binds eighteen actual
8086 DOS workflows with 629 native assertions, a clean source rebuild of both executables and twelve
production objects, and 53,071 host formatter/calendar/preference inputs.
The native DS=SS convention and 8,192-byte diagnostic stack remain intact.

## Text and saved preference

`phone_log_format.c` uses the recovered telephone-log layout: an explicit CRLF
heading, name truncated/padded to 22 bytes, number right-aligned to at least
20 bytes, MM/DD/YY date, online/offline HH:MM:SS and elapsed hours/minutes/seconds.
Names and numbers accept up to 63 CP437 bytes; control characters and DEL are
rejected. The year is reduced modulo 100 for display. These are maintained
formatting policies, not a claim that the original controller had these bounds.

Calendar calculations cover 1980–2099 without printf, floating point or locale.
Elapsed time uses full dates, so midnight and intervals longer than 24 hours
work. A backwards wall clock rejects the end event without changing the queue.
This uses DOS wall time, not a monotonic elapsed clock. Output publication is
atomic on rejection; input/output spans must not wrap or alias.

`phone_log_clock.c` reads DOS date/time/date and the formatter retries a date
transition at most three times. It rejects unstable or malformed dates without
publishing a partial timestamp. No workstation/DOS clock is set by these tests.

The independently recovered saved flag is WORD offset `01E6` in the exact
1,264-byte PRM image: DS `1D6A` minus image base `1B84`. Any nonzero word enables
logging. Both the host PRM field table and the native decoder expose this
mapping. The decoder does not modify the image. Startup adoption remains open.

## Event ownership

`phone_log_queue.c` owns four bounded records in a 666-byte initialized store.
Defining `PHONE_LOG_QUEUE_FAR` places the entire store outside DGROUP, without
switching DS or SS. Callers pass ordinary near cdecl pointers. Physical-address
checks reject aliases into the private far store when reachable through DS.
The public 24-byte snapshot exposes counters/status, not names or numbers.

Configure an enabled queue with an already selected absolute DOS 8.3 path of
at most 63 bytes. The queue normalizes case and separators and validates the
path without DOS I/O. This keeps delayed events independent of later CWD
changes. It does not implement the native current-directory/PCPLUS-directory
resource search; the application must select the correct path first.

START/END accept captured timestamps and nonzero 32-bit connection generations.
Only one connection can be active. Duplicate generations are idempotent;
generation gaps and wrap are allowed under serial-number ordering with a
forward distance below 2^31. A full queue returns `PLQ_FULL` without accepting
the event or changing active/generation state. The caller must retain and
handle that event; this API alone does not guarantee arbitrary burst capacity.

Only `poll` appends data, one event per call. Successful backend commit removes
the event. A safe failure retains the exact bytes and latches explicit retry;
repeated polls do not repeatedly access the disk. `retry` acknowledges that
failure without appending. Failed rollback or ambiguous close permanently
requires recovery in that process. Neither initialization nor configuration
discards pending events or clears file ambiguity. Reentry during backend calls
returns BUSY and leaves the owner unchanged. These are foreground APIs, not ISR
entry points.

## Evidence

Each near/far DOS executable runs nine fresh-process cases:

1. Normal start/end, duplicates, midnight and an empty poll.
2. A real short-prefix write, rollback, retained end event, explicit retry and
   exactly one heading/row.
3. Four-record saturation, failed acceptance, draining and retrying each event.
4. Actual close followed by an injected ambiguous result; no reappend or end
   acceptance after recovery is required.
5. Generation wrap, stale generation rejection and a backwards end timestamp.
6. Maximum CP437 inputs and elapsed time across the supported calendar range.
7. Invalid pointers/paths, owner aliases, selected corrupt metadata and atomic
   invalid-input rejection.
8. Four raw PRM flag values, unchanged image, and disabled logging without a file.
9. Actual DOS clock reads and zero elapsed time.

The host independently compares every supported calendar day against Python
datetime, all 4,096 name/number length combinations, elapsed intervals and
modeled clock rollover/instability. DOS file bytes and final owner state are
checked independently. The diagnostics also check JFT restoration, nested-call
rejection, actual far placement, DS=SS and unchanged 42-byte kernel snapshots.
Failure injection is explicit test code, not an application binary patch.

Current witnesses are `build/phone-log-queue-near-dos-02`,
`build/phone-log-queue-far-dos-02` and `build/phone-log-queue-source-02`.
They repeat the prior accepted -01 cases after adding the optional external
storage declaration for the separate application code bank.
The source proof copies only sixteen declared files, with no original binary,
private settings, REA database or old object. OMF normalization changes only
THEADR filenames; every later instruction/symbol/fixup record remains identical.

```sh
./tools/build test-phone-log-queue
./tools/build test-phone-log-queue-source
```

`build/phone-log-queue/{near,far}/QUEUE.EXE` are diagnostics. They are not the
terminal or a replacement PCPlus application.

## Application work still required

Wire PRM startup/settings adoption and canonical native resource-path selection.
Capture every successful MODEM/DIRECT connection and all disconnect/redial,
carrier-loss, hangup, shutdown and ASPECT paths with a stable generation.
Handle queue saturation and visibly expose retry/recovery states. Reserve the
log's canonical identity against capture, scripts and other file writers.

The [dedicated code bank](PHONE_LOG_BANK.md) now links the code, explicit
bridges and retained far storage into an experimental terminal. It has only
38 resident-code bytes spare; live hooks remain absent. Do not shrink compiler/VM
stacks or limits to make them fit. Schedule filesystem polling safely with UART traffic and
test BBS sessions before physical modem and card acceptance. SynthModem/SPA2102
and Boca handshake compatibility remain separate unverified hardware work.
