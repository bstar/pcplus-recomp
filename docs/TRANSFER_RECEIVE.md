# Native block receiver recovery

The source now includes 886 exact instruction bytes from the original block
receiver and its ACK/NAK, drain and cancellation helpers. It validates actual
128/1024-byte frame payloads and their checksum or CRC, distinguishes duplicates
from unexpected numbers, advances accepted-block state, and exercises the
original EOT acknowledgement substate. This is a diagnostic component toward
F08; a complete downloadable file/session is still open.

## Evidence and source identity

The original PCPlus 2.01 executable SHA-256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The authoritative retained receiver export is
`analysis/pcplus-overlay-anchored-21/functions/0x1d6a4.asm`, REA Evidence
`ev_5627e54d9f87691801201530328b3cd53d294b87c896a38d9c5b1d3c1e62851b`.
`reconstruction/transfer_receive/provenance.json` records each original file
range/hash and the supporting drain, cancellation and header-reader evidence.
No original bytes are build inputs. The explicit analyst-only `recover.py`
regenerates reviewed assembly from the SHA-verified artifact; ordinary builds
only assemble maintained source and check its baseline hashes.

| Original CS range | Recovered responsibility |
| --- | --- |
| overlay21 `d8e8..da31` | Sequence gate; receive/store payload; checksum/CRC accumulation; trailer validation |
| overlay21 `daea..db2a` | ACK, accepted block/count/byte totals and buffer offset; disk-flush checkpoint |
| overlay21 `dbbc..dc28` | Integrity/sequence/complement failure, duplicate ACK, error/retry increments |
| overlay21 `dc6a..dcfd` | SOH/STX/SYN, complement and block-zero dispatch; EOT ACK checkpoint |
| overlay21 `dd4a..ddf6` | Initial EOT NAK, confirmation/timeout retry and cancellation check |
| resident `40b1..40c1` | Real ACK `06` / NAK `15` calls to original UART transmitter |
| overlay21 `f03e..f050` | Delay/flush until no queued input remains |
| overlay21 `f050..f070` | Two CAN bytes request event 7 via original event queue |

The range ends are exclusive. OMF-only jumps at fragment fallthroughs expose
checkpoints; flat builds retain the original bytes. CRC update/finalization and
the polynomial table come from the independently verified
[transfer block module](TRANSFER_BLOCKS.md).

## Established behavior

* SOH `01` and SYN `16` select 128 payload bytes; STX `02` selects 1024.
  The next two received words must sum to `00ff` in ordinary non-streaming mode.
* Expected number is `(low_byte(last_accepted) + 1) & 255`. A duplicate matches
  `low_byte(last_accepted)`, drains remaining input and ACKs without advancing
  payload/count totals. A different number requests status 8, NAK and retry.
  The stored accepted-block word increments modulo 65536, independently of
  the eight-bit wire number. Tests cross both byte and word rollover.
* CRC mode feeds every received byte through actual resident `5c42`, finalizes
  with `5c5c`, and reads high then low trailer bytes. Checksum mode sums modulo
  256 and reads one trailer byte. Failures request status 6 (CRC) or 5
  (checksum), drain input, NAK and increment retry/error counters.
* Invalid complement requests status 7. An early payload timeout requests
  status 2 and NAK. Original code **stores** the timeout word's low byte `ff`
  before checking its sign; a timeout on the final payload position counts as
  a full payload and proceeds to integrity rejection. This historical behavior
  is preserved, corroborated against the original and explicitly tested.
* Accepted data ACKs, increments accepted blocks and the stored last-block
  word, adds the payload length to buffer offset and two 32-bit byte totals,
  then calls progress UI. At buffer usage `2800h`, real file-flush work begins;
  the diagnostic stops before that boundary.
* For protocols 3/5/11, initial block zero routes through batch metadata logic.
  Source tests prove the gate and integrity check; applying metadata is an
  explicit checkpoint, with no invented file/filename implementation.
* Ordinary EOT first flushes input and sends NAK. A subsequent timeout can
  confirm EOT after the original delay/empty-input check, then ACK before file
  commit. The source also retains the second-observation branch. Diagnostic
  time callbacks record calls without waiting; real UART timing is unproved.
* The recovered cancellation helper recognizes two consecutive CAN bytes and
  posts event 7. The application loop consuming that event is outside these
  fragments; a posted event is not claimed as completed cancellation.

State ownership is explicit in the provenance ledger: DS `cc9a` last accepted,
`cc9c` received block, `cd32` complement, `cb5e` payload size, `39c0` buffer
pointer, `cd34` buffer usage, `cd80` accepted count, `cd8a` error count,
`8ffa/8ffc` and `cb2c/cb2e` byte totals. DI selects checksum/CRC; BP locals
include retry count at `-14h`, batch-metadata flag at `-0eh`, pending failure
at `-4`, previous/current start at `-2`/`-10h`. DS=SS is required.

## Bounded diagnostic ABI and boundaries

`standalone/transfer_receive_host.asm` exports near-C
`unsigned __cdecl transfer_receive_probe(const unsigned char *frame,
unsigned length, unsigned crc, unsigned previous_block)` (caller removes eight
bytes). DS=SS; BX/SI/DI/BP are preserved. It accepts the designated `receive_input` arena with a span of
1..1029 bytes, `crc` 0/1 and a full-word previous block. It rejects other pointers and wrapping
spans before touching diagnostic UART/state. The fixed payload arena is 2048
bytes and starts at offset zero for each probe. This API is a test fixture,
not a live transfer service or atomic file receiver.

| AX | Diagnostic checkpoint |
| --- | --- |
| 0 | Accepted data block |
| 1 | Duplicate ACK, no advancement |
| 2 / 3 | Unexpected block / invalid complement |
| 4 / 5 | Integrity failure / early payload timeout |
| 6 / 7 / 8 | EOT ACK before file commit / unsupported control / invalid arguments |
| 10 / 11 / 13 | Batch metadata / buffer flush / file commit boundary |
| 14 / 15 | Control-read timeout retry / double-CAN event posted |

The fixture implements bounded memory byte reads returning `ffff` at exhaustion;
records real ACK/NAK transmitter requests; models input flush, delay calls,
progress/status and cancellation-event posting. It does not call real UART,
DOS file APIs or UI. Flush intentionally discards already queued fixture bytes;
it does not model future asynchronous arrivals. Only non-streaming ordinary
receive and the stated batch gate are tested; YMODEM-G/SEAlink/WXMODEM session
semantics are not established by these tests.

## Reproduction and remaining work

```sh
./tools/dev --command python3 standalone/build_transfer_receive.py
./tools/dev --command python3 standalone/check_transfer_receive.py
./tools/dev --command python3 standalone/test_transfer_receive_dos.py
# Explicit optional bounded instruction replay; never runs the original app:
./tools/dev --command python3 standalone/check_transfer_receive.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

536 CPU cases pass with optional original comparison: 265 frame/state cases,
six bounds checks, and 265 independently loaded original-instruction replays.
The replay executes original instructions in a bounded CPU sandbox with the same
explicit UART/time/UI boundary model and compares wire, counters, payload,
status and cancellation request. It does not execute an original DOS process.
Vectors cover binary/random data, both block sizes and trailer types, duplicate
and wrong number, complement/trailer corruption, truncation, byte/word rollover,
SYN, metadata gate, EOT NAK/ACK and double CAN. Actual source-only DOSBox-X 8086
also passes eight self-check paths (accepted CRC, bad CRC, duplicate,
complement, sequence, truncation, EOT and double CAN).

Results live under ignored `build/transfer-receive/` and
`build/transfer-receive-dos/`. The next implementation boundary is buffered DOS
file writing/flush/close with failure handling, then a bounded session owner
connecting UART deadlines, retry limits, cancellation-event consumption and
handshake to these genuine validation paths. Batch metadata/file naming,
protocol-specific streaming/window behavior, full UI and F09 external protocol
execution remain open. No public BBS uploads or live peer transfer was performed.
