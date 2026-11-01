# Logger and driver flow-control ownership

The optional call-log controls image now has three larger-burst workflows that
cross the UART driver's high watermark during a delayed log write. The image
is unchanged. This extends selected serial/logging evidence; full BBS,
protocol, rendering and physical acceptance remain open.

## Driver ownership during and after the write

Each case delays the first real log append for 72 BIOS ticks while IRQs remain
enabled. A bounded 3,576-byte burst reaches the receive ring: above 3,072 bytes
but below its 4,096-byte capacity. The same three-frame/48-query workload and
final 1,920 glyph/attribute checks as the earlier delayed-write matrix remain.
All call records, the old file prefix, keyboard input and hardware restoration
must still be exact, with zero receive drops and no retry acknowledgements.

The optional fixture extension reads driver flags during the hold and installs
a passive timer observer. After the logger publishes completion, that observer
requires samples while RX remains above 128 bytes and the driver still owns
flow. It also records release after the ring drains. ISR/vector checks restrict
reads to the actual live UART owner, avoiding freed parent memory; both fixture
vectors are restored and checked before collection finishes.

- **SOFT:** the driver latches its XOFF-sent flag and queues XOFF while the
  logger's pause is already active. After the write, a repeated XOFF remains a
  pause; a single later XON resumes the peer. Equal XOFF/XON counts are not
  required because repeating XOFF is idempotent.
- **BOTH:** the native receive dispatcher gives software flow priority, so this
  follows the same queued-XOFF ownership path. The logger's temporary RTS pause
  is separate from a driver-owned RTS hold.
- **HARD:** the driver sets its RTS-lowered flag. The peer sends a bounded timed
  burst rather than following physical RTS. Post-logger timer samples require
  RTS to remain low while the driver owns it; later samples require the driver
  to release after draining. This proves selected MCR behavior in the emulator,
  not physical propagation to a modem.

All scheduled peer sends are checked against observed XOFF/XON intervals.
Software cases allow one explicit in-flight burst after the initial XOFF;
HARD sends its bounded burst during the hold and schedules the remaining rows
afterward. Every actual cursor reply and the final screen must remain exact.
Timer samples are discrete observations, not a claim about every instruction
or every possible hardware race.

## Negative control

A separate ignored source copy removes exactly the `!uart_rts_lowered` guard
from the logger's RTS-release condition. It is rebuilt from public source and
run through the actual HARD watermark test. The test must reject that build
solely for `no_sampled_RTS_override`, with positive bad-RTS and post-logger
sample counts. Ordinary terminal, file, screen, query and restoration checks
must still pass. Production source and its executable must remain unchanged.

This deliberately faulty executable is never installed, packaged or written
to a card. It is a source mutation in isolated build storage, not a patch to
product variables or a production binary. The source-copy helper accepts only
files matching the named public commit and excludes generated Python caches.
The initial copy/probe runs are outside final acceptance.

## Reproduction and limits

The [receipt](validation/phone-log-watermark.json) binds three final native
workflows and a clean public-source replay of 42 workflows, including the 39
previous cases. The negative control has a separate orchestration revision and
records its unchanged public input commit and exact one-file mutation. The
non-watermark delay helpers remain byte-exact against the previous checkpoint.
The negative-control orchestration is committed as `2acd36f`; its application
and test inputs remain the same public `08c42dc` snapshot. The later helper fix
only excludes generated Python cache directories from that copy.

Image: `build/terminal-phone-log-bank-3d164fda0202/TERMINAL.EXE`.
SHA256: `2c5f5fc4dd4b9948b897db6499e920f694f30fbbbcdf3d1fb0596cbc921027f7`.

```sh
./tools/dev --command python3 standalone/test_phone_log_slow_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --label watermark-check-01 --watermark
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --output build/phone-log-watermark-public-repeat-01 \
  --commit 08c42dc --extended --permissions --slow --watermark
./tools/dev --command python3 standalone/prove_phone_log_watermark_mutant.py \
  --source build/phone-log-watermark-public-repeat-01/source \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --output build/phone-log-watermark-mutant-repeat-01 --commit 08c42dc
```

Use fresh lowercase labels/output directories and the corrected committed
source-copy helper for the final command. The hold remains an IRQ-friendly
fixture before a real DOS write. Overflow beyond capacity, arbitrary physical
disk behavior, carrier/child/ASPECT/exception composition, long transfers,
stock-BBS response deadlines, every rendered frame/profile and full F01–F16
acceptance remain open. No published package, card, live BBS, installed bridge,
ATA or host network setting changed.
