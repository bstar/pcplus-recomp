# ZMODEM upload dates

The preceding [upload checkpoint](enigma-upload.md) saved exact bytes but
exposed an invalid future filesystem date on the empty upload. A focused test
against the same actual SEXYZ executable reproduces bad dates on both empty
and nonempty files when the optional timestamp field is absent. The companion
Synchronet source assigns an uninitialized `tmptime` after a partial `sscanf()`;
the executable test establishes the missing-field behavior independently.

The maintained ZMODEM sender now includes an explicit zero timestamp, meaning
unknown for this receiver. Its current source callback ABI supplies a filename
and length, without a source timestamp. The receiver consequently leaves the
new file's creation date in place. This fixes invented dates; preserving the
original DOS source date still needs an ABI/filesystem extension. The shared
minimal YMODEM header codec and recovered native baselines remain unchanged.

`standalone/check_zmodem_timestamp.py` uses the actual selected receiver over
stdio and generated binary/empty batches in both orders. It compares absent
time, explicitly unknown time and unchanged engine output. Only the first two
variants replace offer metadata and recompute its CRC; protocol replies and
file data come from the actual engine/receiver. All six cases require exact
bytes and successful peer exits. The four unknown-time cases additionally
require current filesystem creation dates. The absent-field failures remain
recorded rather than becoming acceptance results.

```sh
./tools/dev --command python3 standalone/check_zmodem_timestamp.py \
  --sexyz build/bbs-lab/OWNED/candidate/helpers/sexyz \
  --label UNIQUE_PEER --engine
```

The actual DOS upload test now requires explicit unknown-time metadata in every
ZFILE offer and creation dates inside its recorded test interval. A fresh owned
ENiGMA fixture receives a 65,539-byte binary and empty file, accepts their
details, persists exact data/catalog records, then returns through search/index
to NFO input. Its fixture also freezes the selected transfer-helper executable.
A retained first attempt completed its transfer but the fixed Tab count did not
accept both forms. The current harness uses a bounded timer observer around the
unchanged DOS program. It first acknowledges the visible scan-completion pause,
requiring both the checker heading and the pause text so login pauses are ignored. It recognizes only the two generated filenames, the
visible detail-form/Continue text and stable BIOS cursor positions. It inserts
ordinary BIOS Tab/Enter keys, records every insertion, stops after the scan acknowledgement and both Continue
keys and fails closed after twelve keys. No product variables, UART registers,
DOS interrupt calls inside the timer or server methods are used. The sampler
removes the observer before checking original hardware/vector restoration.
Acceptance requires the recorded per-file field sequence, exact outgoing keys,
actual installed files and subsequent NFO input.

The passive audit checks the received dates again and rejects a valid-CRC offer
with an invented nonzero time, in addition to its earlier thirteen corruptions.

Use the [upload fixture commands](enigma-upload.md) with fresh candidate/result
labels, then run `check_enigma_upload_audit.py` for that capture. The
[acceptance record](../../docs/validation/enigma-upload-time.json) binds these
results to the current DOS binaries, host/linked/DOS regressions, a fresh
31-product source rebuild and both staged DOS packages. Earlier captures keep
their original bytes, timestamps and producer identities.

Live decoder deployment, physical RS-232 Wi-Fi modem behavior, upload
interruption and the wider application requirements remain open. This work
does not change the running board or establish source-date preservation.
