# Startup-owned telephone-log identity

The optional `--phone-log-startup` terminal now combines the accepted PRM
setting, bounded current/PCPLUS path selection and retained queue with the
[fixed canonical file claim](CAPTURE_FIXED_RESERVATION.md). It implies
`--phone-log-reservations` and `--phone-log-bank` and requires the existing
baseline-enabled application options. It does not yet generate connection
events or run log-file disk polls.

The full terminal refuses processed capture to its claimed log, leaves an
existing file byte-exact, and still captures to an unrelated file. Disabling
logging leaves that filename available for ordinary capture. The claim is for
one canonical DOS identity within the managed file owners; it is not a disk
lock against external processes or a changing drive namespace.

## Ownership lifetime

`PHONE_LOG_QUEUE_RESERVATION` and `CAPTURE_FIXED_RESERVATION` bind the existing
666-byte near/far queue to the second reservation slot. The existing near
file-result snapshot is the stable opaque owner token; no queue/stack/buffer
size is enlarged. The recorder keeps its independent dynamic reservation.

- Enable acquires the claim before publishing the path. Idle retarget checks
  conflicts before transferring it; refusal retains the previous identity.
- Active/pending records prohibit disable or retarget. Idempotent enabled/path
  requests refresh under the queue guard; callbacks cannot reenter the queue.
- Poll refreshes before append. A conflicting replacement returns `PLQ_BUSY`
  without file calls, event consumption or retry-state changes.
- Safe failures retain records and the claim until explicit retry. Close
  ambiguity retains recovery ownership and refuses blind reopening/retry.
- Draining keeps the configured claim. An admitted idle disable releases it;
  only an admitted idle retarget transfers it.

Capture, snapshot, monitor and history use their existing checked owners. Both
queue acquisition/release calls are actual relocated far calls into CONFIG_CODE;
the memory inspector verifies them alongside the established logger ABI.

## Native and source evidence

The [receipt](validation/phone-log-reservation.json) binds 25 original DOS cases
and their 25 public-source repeats:

- Fifteen queue/claim/recorder cases across near/far storage and the real bank,
  with 606 assertions. They cover pending/retry/recovery retention, recorder
  coexistence/reentry, conflicting owners and refresh refusal/reacquisition.
  Close ambiguity and removed-claim faults are explicit diagnostic models.
- Seven actual terminal startup/direct/modem cases. A passive observer reads
  the live queue and 74-byte reservation via the real installed UART vector,
  checking the token, identity, idle guard and disabled state. Bad paths stop
  before UART ownership with the correct notice.
- Three actual capture-UI cases: new/existing claimed paths are denied, while
  disabled logging permits capture there. Each case also captures exact data
  to a different file. A separate passive video observer proves a filename
  prompt preceded the denial and observes denial/open/close order; normal
  DOS exit alone cannot accept a case. Actual ANSI replies and all hardware,
  settings and fixture-preservation checks remain required.

A clean export of 1,723 committed public files reproduces the exact full
terminal and repeats all 25 cases, with no pending-source differences. It
copies no original executable/install, old objects or Git metadata. The
feature-disabled full bank terminal matches the prior public commit exactly
at `3fbb1acf887cb03d243dca35c758c79d05007e09a121ec602e94db9de888be15`.

The combined product is `build/terminal-phone-log-bank-d3b6a7ea3e53/TERMINAL.EXE`,
SHA256 `8b8847783d95a4e1e1892187995d44f8161d81d86108c77d9ee62ead38830522`.
It retains 64,560 near data/stack bytes (976 spare), 22 resident-code bytes
spare, the 666-byte far queue and an 8,493-byte logger bank. Both 63,000-byte
histories and the existing 8KiB stack remain intact. This is the full native-reset
bank variant, separate from the published directory-adoption BBS package.

```sh
./tools/build test-phone-log-reservation
./tools/dev --command python3 standalone/test_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-d3b6a7ea3e53 --label YOUR-STARTUP
./tools/dev --command python3 standalone/test_phone_log_claim_terminal.py \
  --terminal build/terminal-phone-log-bank-d3b6a7ea3e53 --label YOUR-CAPTURE
./tools/dev --command python3 standalone/prove_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-d3b6a7ea3e53 \
  --output build/YOUR-PUBLIC-PROOF --commit c04fd2f --baseline-commit 61fe381
```

Use fresh result labels/directories. Earlier queue-only measurements and their
draft receipt remain archived locally; this receipt records the combined,
committed-source boundary. The prior startup-only and ordinary BBS package
receipts retain their historical scopes.

Next connect complete modem/direct/ASPECT connection lifetimes, schedule disk
polls with UART service, and provide visible full/retry/recovery handling.
No live call records are generated yet. Full F07/F10, all feature combinations,
physical Boca/SPA2102, sustained transfers and card/deployment gates remain
open. No published BBS package, removable card, live BBS, installed bridge,
ATA or host networking was changed.
