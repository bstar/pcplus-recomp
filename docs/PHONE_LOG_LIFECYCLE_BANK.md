# Banked call-event producer

The later [session-event checkpoint](PHONE_LOG_EVENTS.md) adds selected actual
transition hooks to this banked producer. The placement-only measurements and
31-case evidence below retain their historical scope; durable logging is still
unfinished.

The optional `--phone-log-lifecycle` application now links the
[retained-event producer](PHONE_LOG_LIFECYCLE.md) into PHONE_LOG_CODE. It implies
startup settings/path selection, queue file claims and the logger bank. This
is code placement and ABI integration: actual session-transition hooks and
live disk polling are still absent, so it does not yet produce a call log.

## Entry and memory ownership

A separate `phone_log_lifecycle_abi.inc` declares five far cdecl entries:
ready (zero words), begin (three), end (one), service (zero) and inspect (one).
The assembly wrappers copy only those arguments into the near C frame, retain
DS=SS and restore the caller's stack with RETF. Assembly callers can enter the
bank directly; the full terminal gains no resident near-entry trampolines.
The existing ten queue/clock entries and eighteen DOS/CRT callbacks stay intact.

The initialized 38-byte producer store has a linker-visible symbol so the
memory inspector can check its actual segment, bounds and initial bytes. It
remains private implementation state, with no public reset API. The inspector
checks all five wrapper/implementation pairs and their copied argument words,
as well as the established queue, reservation and callback invariants.

The full image is `build/terminal-phone-log-bank-16a18a47571e/TERMINAL.EXE`,
SHA256 `a3ad2cca4c52fca731c8cff37b289d00807b690aaea7a6232dc5b948b0b2e305`.
It uses 64,592 near data/stack bytes (944 spare), a 9,358-byte logger bank and
65,514 resident code bytes (22 spare). The 666-byte far queue, both 63,000-byte
histories, existing 8KiB application stack and compiler/VM limits are unchanged.
The aggregate near allocation grows by 32 bytes after alignment changes;
the producer itself remains exactly 38 bytes.

This is the optional full native-reset bank variant. It is separate from the
published directory-adoption BBS package; their full feature composition is
still an open application requirement.

## Native evidence and public reproduction

The [receipt](validation/phone-log-lifecycle-bank.json) binds:

- Seven producer workflows in each near, far and real bank build: 21 DOS cases
  with 1,041 assertions. They cover normal/duplicate events, call-pair capacity,
  retained END time, retry, recovery, disabled logging and generation wrap.
- Seven full-terminal startup/direct/modem cases, with the existing passive
  queue/claim observer and pre-UART error checks.
- Three full-terminal capture-UI cases, preserving the enabled log identity,
  permitting the disabled filename and capturing correctly to another file.

The native context includes actual DS, SS, queue segment, producer segment,
38-byte owner and 10-byte snapshot sizes. Each case checks the near/far queue
placement and rejects snapshot aliases into the private producer. Exact log
bytes are independently compared in Python; final state, JFT restoration and
unchanged kernel/hardware snapshots remain required.

Generation wrap uses an explicit diagnostic idle-owner fixture at FFFFFFFE,
then exercises actual begin/end through FFFFFFFF and 1. No application binary
is patched. The declared END-refusal and ambiguous-close models remain distinct
from physical media failures.

The bank diagnostic adds only test-side near clients and an explicit cdecl
END-refusal callback. Its one imported END symbol is redirected through checked
near/stack/far adapters; the real END still executes in the bank when admitted.
The production object is retained alongside the diagnostic object, and the
manifest records both hashes and the one-name import change. These substitutes
are not linked into the full terminal.

A clean export of 1,730 committed public files from `de52850` reproduces the
full terminal exactly and repeats all 31 producer/startup/UI cases. It also
runs 15 queue-claim regressions. All three diagnostic executables reproduce
byte-for-byte. The feature-disabled full bank control remains exact against
commit `6762e9e`, SHA256
`3fbb1acf887cb03d243dca35c758c79d05007e09a121ec602e94db9de888be15`.
No original executable/install, old object or Git metadata enters the export.

```sh
./tools/build test-phone-log-lifecycle
./tools/dev --command python3 standalone/prove_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-16a18a47571e \
  --output build/YOUR-LIFECYCLE-PROOF --commit de52850 --baseline-commit 6762e9e
```

Use a fresh proof output directory. The original lifecycle-only and later
startup/claim receipts keep their historical scope and identities.

Next add the actual admission, CONNECT, observed-disconnect and exceptional
shutdown hooks. Preserve failed-hangup continuity, account for child UART
ownership and capture timestamps at accepted transitions. Then add a guarded
foreground disk scheduler with UART service and visible full/retry/recovery
handling. These tests do not close whole F07/F10, complete application behavior,
every feature combination, physical Boca/SPA2102, sustained transfers or card
deployment. The published package, removable card, live BBS, installed bridge,
ATA and host network are unchanged.
