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

## Second actual run

[Upload02](../../docs/validation/synthmodem-audio-upload-02.json) completes the
exact11521-byte upload, official metadata/details workflow, fresh search/list
and normal DOS/hardware/timer return. All25 producer,26 independent byte/cleanup
and12 ownership checks pass. Twelve exact data packets and all required
opposite controls/FIN/OO pass with no retransmitted packet. All12330 online DOS
bytes and66879 BBS display bytes survive the software modem exactly.

The full upload audit remains false:18 of19 transfer gates pass, but literal OO
reaches the relay about319ms after stock SEXYZ has exited. Its final reply
itself reaches the DOS frontend after that exit, so this is not a sender that
waited too long after receiving it. The
[receiver diagnosis and isolated counterexample](sexyz-receive-finish.md) bind
that timing and reproduce stock early retirement against a reference receiver.
No gate is removed and no stock audio upload acceptance is claimed.

The timing verifier now supports either transfer direction. For upload02,
`--protocol-only` tests its validated protocol while explicitly retaining the
failed overall transfer result. Both premature-ACK and premature-ZFIN timestamp
mutants are rejected; this verifier result grants no transfer acceptance.
The original accepted download03 artifacts remain byte-identical, including its
old verifier receipt. New verifier results use fresh filenames and cannot
overwrite retained evidence.

## Completed candidate audio run

[Upload03](../../docs/validation/synthmodem-audio-upload-03.json) passes all82
producer and independent gates on the explicitly isolated ENiGMA board with the
pinned Nix receiver-finish candidate. The DOS binary, software modem runtime,
38400 DTE and full11521-byte source are unchanged. Twelve data packets have no
replay; official storage matches the source SHA256. All12331 online DOS bytes
and66887 display bytes survive exactly. The frontend completes67096 bytes with
zero skipped, failed or pending bytes.

The final OO is observed at the relay before normal helper retirement (about
0.813ms, with maximum clock-anchor sampling interval2.214us). Frontend OO
submission precedes retirement by63ms. These are transport timestamps; they do
not measure DOS application consumption. The timing verifier runs with the full
transfer audit passing and rejects both premature-control mutants. Actual
post-transfer details/search/list and normal DOS, UART/PIC/IRQ/timer cleanup
pass. The original source/stat and stock server/helper/official upload remain
preserved. The sealed receipt binds raw captures, frozen inputs and all audits.

Acceptance covers this modified-helper workflow. Stock upload02 remains failed
at closing ownership; pressure, cancellation/loss, arbitrary peers, physical
Boca/SPA2102 and F01-F16 whole-application acceptance remain open.


## Audio cancellation experiment

The isolated cancellation recipe uses the original11521-byte source and same
DOS binary, fixed DTE and V22/1200 runtime. `--upload-cancel` requires an explicit
fresh fixture. The observer waits for the actual confirmed KiB footer before
BIOS Escape, observes TX canceled and then tries the remote cancel and PCXTEST
search/list. Normal full-upload gates retain their meaning and reject this mode.
The separate `audio_upload_cancel.py` auditor checks valid source/ACK before
CAN, absence of EOF before cancel, source/stat, no official installed file,
helper retirement and real postcancel input, in addition to complete stream and
hardware/ownership audits. No successful file upload is expected or claimed.

The [preparation receipt](../../docs/validation/audio-upload-cancel-preparation.json)
accepts only the observer and isolated-board prerequisites. The
[completed cancellation01](../../docs/validation/synthmodem-audio-upload-cancel-01.json)
passes all75 producer/byte/ownership/client-cancellation gates and four control-
time negative mutants. Exact1976 DOS online bytes and56270 display bytes survive;
source/stat, real postcancel search/list and normal hardware/timer restoration
pass. All56479 frontend bytes complete with zero skipped/failed/pending bytes.

Overall cancellation acceptance remains false. The helper exits1/signal0 and
leaves an exact1024-byte source prefix in its logged receive temporary path.
The observation and exclusive ignored backup preserve it without deleting the
original. No official file is installed. The recorder verifies the original
stock source/helper/upload, complete offline decode and frozen inputs/captures.
Retry and temporary cleanup remain separate open requirements.

```sh
./tools/dev --command python3 lab/bbs/check_audio_upload_keys.py \
  --output build/bbs-lab/audio-upload-cancel-keys-01
# Prepare/start a fresh receiver candidate and run navigation/isolation above.
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --key-framing --route upload --upload-cancel \
  --upload-key-checks build/bbs-lab/audio-upload-cancel-keys-01/result.json \
  --fixture-lab build/bbs-lab/enigma-audio-cancel-candidate-01 \
  --runtime build/bbs-lab/synthmodem-key-framing-runtime-01/runtime \
  --output build/bbs-lab/synthmodem-audio-upload-cancel-NEW
# After natural producer exit: run independent byte/cleanup and ownership
# audits, then audio_upload_cancel.py on that same fresh cohort.
```


After the producer exits naturally, run the independent audits on its cohort:

```sh
./tools/modem-dev --command python3 lab/bbs/audit_synthmodem_audio_dos.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py COHORT
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js RUNTIME COHORT
./tools/modem-dev --command python3 lab/bbs/audio_upload_cancel.py COHORT
./tools/dev --command python3 lab/bbs/check_audio_upload_cancel_timing.py COHORT
./tools/dev --command python3 lab/bbs/record_audio_upload_cancel.py COHORT \
  --output docs/validation/synthmodem-audio-upload-cancel-NEW.json
```

The timing verifier checks metadata/ZRPOS/data/ACK/CAN/search causality on one
actual frontend timeline. Premature ZRPOS, premature ACK, ACK after cancellation
and cancellation before valid data must all fail when only copied times change.
The recorder additionally requires the retained-temp observation/backup made
from the exact session-log path after helper exit. Its zero exit means this
mixed result is consistent; the canonical receipt keeps `passed: false`.


## Cancel and retry on the same call

The [retry observer receipt](../../docs/validation/audio-upload-retry-keys.json)
adds a fourth actual DOS probe: cancel after confirmed KiB, leave the remote
protocol selector, navigate another upload, reuse retained ZMODEM, complete
forms and search for AUDIOUP.BIN. All12 observer checks pass. These synthetic
screen probes verify the BIOS observer; they do not prove a real transfer.

The [fresh-board prerequisites](../../docs/validation/audio-upload-retry-preparation.json)
pass seven navigation and thirteen isolation checks. The
[completed retry01](../../docs/validation/synthmodem-audio-upload-retry-01.json)
passes its client transfer/recovery workflow, with exact14459 online DOS bytes,
78868 display bytes,12 unreplayed retry data packets, exact official11521-byte
file, source/stat preservation, real postretry search/list and normal native
cleanup. All79077 frontend bytes complete without skipped/failed/pending bytes.
The original strict-count auditor report remains preserved: there are two
metadata announcements within the single retry. The separate v2 auditor uses
the existing CRC/control parser to validate both and still requires exactly two
actual helper executions (cancel1 then success0).

Overall acceptance stays false:5999ms misses the unchanged6000ms hold minimum.
Independent protocol-only negatives reject premature ACK/FIN, and actual relay
OO precedes final helper retirement. Previous partial/receipt evidence remains
unchanged. Timer correction and receiver cleanup remain open.

```sh
./tools/dev --command python3 lab/bbs/check_audio_upload_keys.py \
  --output build/bbs-lab/audio-upload-retry-keys-NEW
# Prepare/start a fresh isolated board and its navigation/isolation checks.
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --key-framing --route upload --upload-cancel-retry \
  --upload-key-checks build/bbs-lab/audio-upload-retry-keys-NEW/result.json \
  --fixture-lab build/bbs-lab/enigma-audio-retry-candidate-NEW \
  --runtime build/bbs-lab/synthmodem-key-framing-runtime-01/runtime \
  --output build/bbs-lab/synthmodem-audio-upload-retry-NEW
# After natural exit and the independent byte/cleanup and ownership audits:
./tools/modem-dev --command python3 lab/bbs/audit_audio_upload_retry.py COHORT
```

The observer prerequisite is explicit through `--upload-key-checks`; its source
hashes must match before the producer starts. Full-upload and cancellation-only
workflows keep their distinct gates. The retry auditor requires exactly two
helper executions, cancellation1 then success0, valid first data/ACK/CAN and
complete second source/control/finish/storage/resume validation. Receiver
partial cleanup, faults during retry and physical tests remain open.


Retry01 logs a5999ms minimum hold, below the unchanged6000ms gate. The
[actual-method counterexample](../../docs/validation/posttrain-minimum-counterexample.json)
reproduces attachment when a modeled timer callback arrives at5999ms;6000ms is
its successful control. It replaces only timer/clock and DSP/Telnet boundaries,
starts no VM and changes no running runtime. This demonstrates missing elapsed-
time validation in the minimum callback, without claiming the precision of the
actual logged interval. Preserve the audio run and retain its strict gate;
correction requires a separately staged and validated runtime.

```sh
./tools/modem-dev --command node lab/bbs/check_posttrain_minimum.js \
  build/bbs-lab/synthmodem-key-framing-runtime-01/runtime \
  build/bbs-lab/posttrain-minimum-counterexample-NEW
```

The counterexample command exits zero when the defect is reproduced; its
receipt keeps `passed: false`.


The isolated [minimum-hold candidate](../../docs/validation/synthmodem-posttrain-runtime.json)
now passes15 actual-method checks, including a real default6000ms Node timer.
Only CallSession changes in the separately staged runtime. See
[minimum-hold repair](synthmodem-posttrain.md); no new audio acceptance follows.


## Accepted candidate cancel/retry

[Retry02](../../docs/validation/synthmodem-audio-upload-retry-02.json) passes all81
producer/byte/ownership/retry gates on the explicitly isolated receiver and
monotonic minimum-hold runtime. Hold6002ms, exact14361 online DOS bytes and78322
display bytes, full11521-byte official file,12 unreplayed retry packets, source/
stat preservation, normal hardware/timer cleanup and actual search/list all
validate. Both timing negatives reject without protocol-only mode, and required
OO reaches the actual relay before final helper retirement. Original stock
source/helper/upload and previous captures remain preserved. The old5999ms
retry01 failure stays unchanged.

The new recorder seals only this modified-runtime/helper workflow:

```sh
./tools/dev --command python3 lab/bbs/record_candidate_audio_retry.py COHORT \
  --output docs/validation/synthmodem-audio-upload-retry-NEW.json
```

Unmodified-stock closing, receiver temporary cleanup, sustained pressure/loss,
other peers, physical Boca/SPA2102 and full application requirements remain open.
