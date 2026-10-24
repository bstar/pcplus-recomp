# Current IRQ downloads through framed ENiGMA

The current source-built terminal passes two DOS8086 workflows: discard an
unsaved ENiGMA editor session, download a file automatically with ZMODEM, then
search the file area again in the same connection. The isolated server uses the
[incremental decoder](FRAMED_IRQ_BBS.md); this does not establish equivalent
behavior against unmodified stock ENiGMA.

The [verified receipt](validation/irq-transfers.json) records:

| Case | IRQ | File | Bytes | Result |
| --- | --- | --- | ---: | --- |
| `irq7-framed-transfer-02` | 7 | PCXTEST.BIN | 11,521 | Passed |
| `irq5-framed-large-transfer-03` | 5 | IRQDATA.BIN | 65,539 | Passed |

Both use COM2, 19200 baud, hardware flow control and immediate forwarding.
The terminal SHA256 is
`31303aa66e1154848363e1b29a4353915e99b0a2bbb74444b03c0e0d288132db`.
There are no application binary changes in this checkpoint. Explicit product,
CPU, IRQ and mouse options now let the existing transfer harness exercise the
current build. The larger generated payload crosses 64 KiB and was indexed
using the server's official file APIs.

Independent capture replay verifies file headers, data CRCs, offsets, exact
stored bytes, ZEOF, the receiver's ZFIN and final OO. Actual subsequent menu
input receives the expected filename and size. Both runs restore all 42 sampled
hardware bytes, leave no transfer staging files and save no editor post.
Four read-only corruption checks reject a changed stored byte, damaged wire
CRC, invalid receiver ZFIN and a zero-byte decoded trace event.

## Retained failures and limits

Three earlier results remain failed and are included in the receipt:

- The first small run emitted three empty trace events for Telnet negotiation.
  The decoded-byte observer now omits events that own no application bytes;
  raw captures and transport bytes remain unchanged. A separate 269-partition
  check covers all 256 byte values, escaped IAC and negotiation boundaries.
- The first large run expected `64.00 KB`; ENiGMA displays `64 KB`. Its protocol
  completed, but its presentation assertion failed. The driver now follows the
  server's size formatting. Exact producer sources for both corrected pilots
  are retained against their original input hashes.
- The second large run completed the transfer, then a cumulative-download
  achievement popup consumed timed test inputs. The post-transfer search failed.
  The passing third run used the same account after it had earned that
  achievement; no achievement setting was disabled. Notification-aware test
  interaction remains open. This repeat does not prove popup handling.

Both temporary instances are stopped and loopback port 23234 was verified free.
Existing stock fixtures, the user's LAN board and the disconnected card were
not changed. Uploads with this exact composed build, repeated reconnects,
sustained saturation, arbitrary network latency and physical modem behavior
remain unverified. These two successful downloads do not close those gates or
the remaining native application work.

## Reproduction

Use the pinned Nix tools and fresh output paths. Export a checked decoder tree
as described in [the decoder workflow](FRAMED_IRQ_BBS.md#reproduction), then
prepare a fresh large-file instance instead of calling ordinary fixture setup:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_irq_transfer_fixture.py \
  --candidate build/bbs-lab/irq-transfer-next/candidate --bytes 65539
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/irq-transfer-next/candidate --private-tmp
./tools/dev --command python3 lab/bbs/enigma_irq_large_dos.py \
  --candidate build/bbs-lab/irq-transfer-next/candidate \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps-custom-irq/TERMINAL.EXE \
  --irq 5 --label irq-transfer-next
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/irq-transfer-next/candidate
```

The timed recipe can still encounter the documented notification limitation.
The receipt scripts replay the exact retained lab layout; they are evidence
verification tools rather than a claim that arbitrary board state is repeatable.
