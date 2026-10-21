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
  --download-pressure-preparation build/bbs-lab/audio-pressure-download-preparation-02.json \
  --output build/bbs-lab/current-enigma-pressure-download-audio-01
```

Actual audio acceptance requires the complete producer, independent full-stream/
hardware audit, serial ownership audit, independent caller waveform, passive
source/CRC/control/finish/file/accounting audit and post-helper input return.
Measure retransmissions and queued timing separately; a completed file alone
cannot establish transfer acceptance or efficiency. This is one larger-file
campaign, not arbitrary-duration pressure, other directions/protocols/profiles,
physical Boca/SPA2102 or full-application completion.
