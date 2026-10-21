# Stock ENiGMA upload over the software modem

This extends the accepted [audio download](audio-download.md) in the opposite
direction. It uses the same normal V.22/1200 SIP/RTP/DSP runtime, fixed38400 DTE,
explicit250ms bridge key framing, source-built DOS terminal/ASPECT and unchanged
stock local ENiGMA/full artwork. No upload acceptance is established yet.

The first fixture is `AUDIOUP.BIN`,11521 bytes containing every octet value.
`audio_upload.py` checks absence through the official FileEntry API and the
owned storage directory before creating `SEND/AUDIOUP.BIN` in the isolated DOS
test mount. It refuses existing targets and does not remove or overwrite uploads.
Source content, inode, size and modification time are recorded before the call.

## Navigation and input prerequisites

The [navigation receipt](../../docs/validation/audio-upload-navigation.json)
passes seven checks on the same server through the independent fast TCP
reference: Main/File Base/upload options/protocol selection, no receive helper
started, no installed upload, unchanged configuration, compiled ASPECT route and
the all-octet fixture. The reference stops before starting the actual receiver.

The ASPECT child selects the default blind upload, follows the stock form's
three-Tab Continue path and selects the configured ZedZap helper. It then exits,
releasing its receive lease before the parent terminal's modal upload owner.
The test-only `audio_upload_keys.asm` observes the real helper banner, enters
Alt-S, F2/F2 and the DOS source path through BIOS input, and waits for Sending
ZMODEM before proceeding. It does not read product variables or UART bytes.

After reception/scanning, the helper acknowledges the visible upload checker,
uses actual visible form text and BIOS cursor positions to reach Continue, then
performs a fresh filename search and exits through Alt-X. It also has a bounded
visible TX-timeout/cancel exit and an overall watchdog. It never calls DOS from
the timer or manufactures protocol replies or pass markers.

The [actual DOS helper receipt](../../docs/validation/audio-upload-keys.json)
passes both synthetic-screen cases:45 exact BIOS words for the success phases,
24 for the failure exit, and timer restoration in both. Shortened test-only
delays exercise the observer; this proves no real upload or native transfer.

## Full-run requirements

The first actual call is `synthmodem-audio-upload-01`. Its source, helper,
executable/map, fixture, prerequisite receipts, server modules/assets and runtime
are frozen while it runs. Do not restart because an observation times out.

After the producer is terminal, run the byte/cleanup and ownership audits first:

```sh
./tools/modem-dev --command python3 lab/bbs/audit_synthmodem_audio_dos.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_audio_upload.py COHORT
```

The upload auditor independently requires every observed data CRC and payload,
offset/EOF, opposite-direction controls and ZFIN/OO. It binds timing to complete
decoded frontend manifests. The final file must exist at the exact owned path
with matching official name, area, storage, size, hash and uploader; timestamps
must remain within the actual run. Source data/stat must be preserved. One real
receive helper must exit successfully, no protocol tail may reach the BBS after
it retires, and actual post-form input must reach a new search/list. Full byte
identity, unchanged inputs, no gateway error and DOS/UART/IRQ/timer cleanup stay
mandatory. Preliminary producer storage/helper checks alone cannot accept it.

## First actual failure

The [upload01 receipt](../../docs/validation/synthmodem-audio-upload-01.json)
records failure, not acceptance. All21 positive producer checks and native
cleanup hold, but the exact installed file, successful helper exit, resumed
search/list and final filename gates fail. The independent full-stream audit
also fails:21775 native online bytes were submitted, while the offline caller
decoder, actual guest DATA_RX and target-plus-BBS input retain6085,6082 and6080
bytes respectively. Each is an exact prefix of the native stream. This is
truncation with pending modem data when the client ends; it is not evidence of
midstream insertion or corruption. All downstream display bytes survive.

The first1024-byte packet's CRC reached the modem frontend at438.260493 seconds.
Replay began at441.375959, but the valid ACK reached the DOS frontend only at
447.791871: a3.115467-second retry versus a9.531379-second actual response.
Native ZDATA offsets are0 three times followed by1024 ten times, queuing more
source bytes before earlier data has crossed the carrier. These are transport
observations, not application-consumption timestamps.

The producer captured no successful helper exit. Separate preserved late rows
show the stock receiver retiring naturally at04:28:21.609Z with exit255 and
signal0; no kill was sent. Its temporary AUDIOUP.BIN contains the exact first1024
source bytes. A separate ignored copy preserves that partial without deleting
or overwriting the server's file. The official FileEntry API still reports no
entry and the intended storage target is absent. Original capture files and
hashes remain unchanged.

`standalone/check_zmodem_upload_response.py` executes the unchanged linked DOS
engine, adapter, watchdog, file owner and UART ISR with modeled hardware/kernel
boundaries. An immediate response completes and preserves the source/application
tail. With the ACK delayed182 BIOS ticks, native replay begins after57 ticks,
before that ACK is delivered. The test stops at the premature wire output; it
makes no cleanup claim for that interrupted counterexample. The
[receipt](../../docs/validation/zmodem-upload-response-counterexample.json)
retains this failing policy separately from passing transfer checkpoints.

Reproduce the failed-run evidence and linked counterexample in pinned Nix:

```sh
./tools/dev --command python3 standalone/check_zmodem_upload_response.py
./tools/dev --command python3 lab/bbs/audit_audio_upload_failure.py
```

The failure recorder verifies original capture hashes, exact prefix identity,
source bytes/stat, current official absence, late helper error and preserved
partial. Its zero exit means the failure evidence is consistent; its receipt
has `passed: false`. It requires the original ignored local cohort and receiver
temporary file; it is not a portable acceptance test.

The [native response fix](../../docs/ZMODEM_MODEM_RESPONSE.md) now calculates
the allowance from unacknowledged payload and quoted framing at a300-bps carrier
floor; the DTE divisor stays fixed. Its
[receipt](../../docs/validation/zmodem-upload-response-fixed.json) verifies14
linked timing cases,11 host API/policy cases and the broader protocol/ABI/DOS
regressions. The same timing checker retains a predecessor failure. Independent
accepted-progress, cancellation and loss bounds remain active. The next step is
the original owned audio upload, with the same fixture, DTE, receiver and full
acceptance gates. Native checks do not establish actual audio upload acceptance.

Physical Boca/SPA2102, cancellation/loss, other peers and full-application gates
remain separate.
