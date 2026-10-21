# Larger stock ENiGMA download over software audio

The [preparation receipt](../../docs/validation/current-enigma-pressure-download-preparation.json)
binds a fresh65797-byte `PCPRESS.BIN`, crossing the64KiB file-position boundary.
The deterministic payload exercises all256 byte values. It is registered through
the existing stock scan CLI and FileEntry API, preserving prior physical fixture
bytes/inodes/sizes/mtimes and selected metadata. Source/config/menus/helper remain
fixed. The old11.5KiB fixture is kept intact.

The real pinned `lrzsz` TCP reference passes nine gates: exact source/received
file, full CRC/EOF/ZFIN/OO and opposite controls, helper exit/accounting and actual
post-helper Search/List. The first attempt lacked `rz` in the modem shell and
stopped before connecting; its source/stderr remain under ignored storage. The
corrected reference uses the existing default Nix shell, which includes lrzsz.

The actual8086 BIOS helper passes six checks, including a wrong-filename screen
that must not release Alt-X. Its default binary is identical to the accepted
normal download helper. Replacing only the gold binary's marker,13 search-key
words and watchdog reproduces the pressure binary exactly. The pressure watchdog
is54000 BIOS ticks; the outer process bound is3020 seconds. Four default-helper
checks and15 legacy download-audit gates pass. The alternate legacy audit output
keeps all captured files and prior receipts unchanged.

```sh
./tools/modem-dev --command python3 lab/bbs/prepare_audio_pressure_download.py \
  --output build/bbs-lab/pressure-fixture-new
./tools/dev --command python3 lab/bbs/reference_audio_pressure_download.py \
  --fixture build/bbs-lab/pressure-fixture-new/result.json \
  --output build/bbs-lab/pressure-reference-new
./tools/modem-dev --command python3 lab/bbs/check_audio_download_keys.py \
  --pressure --output build/bbs-lab/pressure-keys-new
./tools/modem-dev --command python3 lab/bbs/audio_pressure_download.py \
  --fixture build/bbs-lab/pressure-fixture-new/result.json \
  --reference build/bbs-lab/pressure-reference-new/result.json \
  --keys build/bbs-lab/pressure-keys-new/result.json \
  --output build/bbs-lab/pressure-preparation-new.json
```

Fixture creation requires a fresh filename and refuses to replace an existing
PCPRESS.BIN. Reuse the existing validated fixture receipt after preparation;
do not remove prior files to rerun setup. All output paths must be fresh.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --route download \
  --runtime build/bbs-lab/synthmodem-buffered-runtime-01/runtime \
  --buffered-runtime-proof build/bbs-lab/synthmodem-buffered-runtime-01/result.json \
  --download-pressure-preparation build/bbs-lab/audio-pressure-download-preparation-03.json \
  --output build/bbs-lab/current-enigma-pressure-download-audio-new
```

Actual audio acceptance requires the complete producer, independent full-stream/
hardware audit, serial ownership audit, independent caller waveform, passive
source/CRC/control/finish/file/accounting audit and post-helper input return.
Measure retransmissions and queued timing separately; a completed file alone
cannot establish transfer acceptance or efficiency. This is one larger-file
campaign, not arbitrary-duration pressure, other directions/protocols/profiles,
physical Boca/SPA2102 or full-application completion.

## Damaged-evidence controls

The [nine protocol controls](../../docs/validation/audio-pressure-download-protocol-controls.json)
reproduce the real65797-byte reference protocol and opposite controls exactly,
then reject copied evidence with a corrupt packet CRC, wrong source byte above
64KiB, CRC-valid EOF position wrapped to16 bits, missing finish, missing literal
OO, ACK substituted for receiver ZFIN, premature data ACK, premature receiver
ZFIN, or completion ZRINIT before EOF. Original reference captures stay exact.
These are verifier tests; the live DOS/audio campaign remains separate.

The first checker expected the truncated stream's error at an inner parser gate.
The parser correctly rejected it at its final missing-ZFIN/OO gate. That source
is retained; only the expected diagnostic changed in the passing checker.

```sh
./tools/modem-dev --command python3 lab/bbs/check_pressure_download_protocol.py \
  --reference build/bbs-lab/audio-pressure-download-reference-02/result.json \
  --output build/bbs-lab/pressure-protocol-controls-new.json
```

## First actual audio failure

The [retained actual run](../../docs/validation/current-enigma-pressure-download-failure-01.json)
fails before64KiB, at verified source extent15360. The receiver ACKs1024 and15360,
then requests position15360 nine times while old data at1024 is replayed. All
observed packets have valid CRCs and exact source bytes. The sender emits no EOF,
begins closing with an incomplete file and its stock helper exits255. No installed
file or download-count advancement follows. This is a failure, not a larger-file
acceptance result or evidence of a64KiB arithmetic defect.

All394 online bytes match the independent caller waveform decode. The decoded
84648 display bytes are an exact prefix of89316 emitted bytes; the remaining4668
bytes are not delivered before DOS closes. The normal full-stream auditor rejects
this mismatch, and the download auditor stops at that same identity prerequisite.
The separate failure diagnostic validates the clipped prefix explicitly without
allowing it to satisfy the full-stream gate.

The product's32 IRQ-vector bytes and six UART/PIC bytes restore exactly; only
the test helper's four INT1C bytes differ. The helper had not reached its guarded
post-transfer exit. DOS reports `RX file error`, but the adapter maps multiple
protocol failures to that text: it does not prove a DOS storage failure. The
engine explicitly rejects ZFIN while an incomplete receive is owned. Sender
queuing/checkpoints and active-file stale-frame handling need controlled tests;
no exclusive timing cause or correction is claimed here.

The [stock credit experiment and isolated sender candidate](sexyz-send-credit.md)
now measure the packet/group gap directly. The [EOF response auditor correction](zmodem-response-end.md)
preserves mandatory-byte timing while allowing a reply before optional flow.
A fresh stock TCP reference03 and nine protocol counterexamples pass with that
auditor; preparation03 replaces02 for future launches. Earlier proof/source
snapshots and the failed audio run are retained. No new audio pass is implied.
