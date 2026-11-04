# Cancel and retry through the size-probed proxy

The current source-built parent now passes an actual stock Enigma ZMODEM
cancellation and retry in one DOS process and one authenticated proxy connection.
The [receipt](validation/proxy-cancel-retry.json) binds the successful capture,
independent replay, BIOS helper checks and corrupted-copy controls.

This extends [successful proxy transfers](PROXY_SIZE_TRANSFERS.md). It uses the
same unchanged application,
SHA256 `a2fd6a3fcdcc30138426d747d8cde400d9fc6eb9ca5fca84d1656aeaf17caa77`.
All 569 declared public inputs still match the existing exact source-only proof.
No installed application, private configuration or live service is changed.

## Actual workflow

The route is DOS 8086 COM3/3E8h/IRQ5,19200/HARD → synthetic guarded Hayes →
actual staged SynthModem size-probe proxy → owned stock loopback Enigma →
its real SE/X/Y/Z helper. The saved startup selects 25 physical rows with a
visible status row; the wire carries actual 80x24 NAWS. Sequence framing is
250ms, with no artificial per-byte delay. No SIP or DSP runs in this fixture.

The test enables the existing automatic ZMODEM receiver in its synthetic PRM.
After login and a full-name file search, the unchanged DOS application starts
receiving the stored 65,539-byte binary fixture. A timer observer reads only
VGA cells and injects BIOS Escape once the displayed count is at least 8KiB.
It never edits PCPlus memory, supplies protocol responses or truncates the peer.

The passive audit confirms a source-matching CRC-valid ZFILE/data packet before
the actual CAN sequence, with no completed ZEOF before cancellation. The host
observer records a nonempty 4,096-byte DOS stage matching the source prefix,
then an empty receive directory after cancellation and before the retry command.
Those observations are ordered against the serial trace's monotonic clock.

The same parent searches for the target and displays its full name before
requesting another download. The retry completes all 65,539 bytes, verifies
data CRCs, ZEOF, ZFIN/OO and opposite-direction controls, and searches for the
target again afterward. Only the expected exact file remains; no `PCRX.$$$`
survives. The stock server logs show one login and two ordered helper processes:
the canceled helper returns 255 and the successful retry returns 0.

Raw Telnet decoding must reproduce every online application byte after the one
owned `loc`/size-reply prefix. The full serial command capture must additionally
contain exactly the declared initialization/dial prefix and guarded hangup suffix.
The 215 size-reply lookalikes and every byte value in the file remain data.
Normal exit, unchanged PRM/sources, actual BIOS geometry, an 8000-byte screen
capture and restoration of the 42-byte hardware snapshot are required.

## Test keyboard and observer evidence

A source-built, paced BIOS helper replaces the long DOS `ADDKEY` command.
It uses the normal BIOS key insertion service, retries a full queue and removes
its own INT1C hook after the final key. The callback calls no DOS and accesses
no product state or serial port. Its independent DOS 8086 check fills the BIOS
queue to 15 entries, then verifies all 32 literal key words in order and exact
timer-vector restoration. The BBS auditor rebuilds the actual helper and sampler
from their captured public source and requires byte-identical COM files.

The cancellation observer checks the five-digit field, rather than just its
units digit. Its separate DOS test rejects 7KiB and a wrongly colored 15KiB,
accepts a jump to 15KiB and injects no second key at 23KiB. It restores its
hardware state. These are test-only TSRs in the emulator, not physical installs.

Nine copied-capture controls accept the unchanged evidence and reject altered
partial hashes, impossible partial/cancel chronology, uncleared staging, a
missing BIOS Escape witness, wrong NAWS, changed hardware, an extra authenticated
session and damaged retry data. The data mutation changes the same payload byte
in the serial/proxy/raw TCP captures, preserving their equality and Telnet
decoding; the independent packet auditor rejects it with `Data CRC mismatch`.
Controls change ignored copies only, and do not execute DOS or write BBS data.

## Retained failures and scope

The first preflight completed the retry but expected the final unfiltered list
to select the target. It selected another file, so the strict gate rejected it.
That preflight's partial observer could also see a write from the retry rather
than proving a write before cancellation. The accepted recorder requires the
partial observation before CAN, with independently checked clock ordering.

The next probe's units-digit-only threshold waited until a later progress update,
and navigation arrived while cancellation still owned keyboard input. The retry
never started. The accepted observer handles multi-digit jumps, and the paced
recipe gives cancellation a longer return interval before searching. Failed
captures remain failed; no successful storage or normal exit overrides them.
Assembly/import/input-path setup failures before DOS are excluded as well.

This proves one local-cancel/data/retry route at 25-visible startup geometry.
It does not establish real DCD loss, same-process redial, all layouts/protocols,
unframed transport, slow physical throughput or full original feature parity.
The synthetic modem holds CTS ready. Boca/SPA2102/SIP/DSP/analog acceptance,
the physical BUSY report and verified deployment remain separate work. The
500ms synthetic hangup guard is not a Boca S12 measurement.

```sh
./tools/dev --command python lab/bbs/test_proxy_cancel_retry_dos.py \
  --runtime build/STAGED_PROXY/candidate \
  --terminal build/SELECTED/TERMINAL.EXE --file PABCDEF.BIN --label NEW_LABEL
./tools/dev --command python lab/bbs/audit_proxy_cancel_retry.py \
  --capture build/bbs-lab/results/enigma/NEW_LABEL \
  --bridge build/bbs-lab/NEW_LABEL-proxy --output build/NEW_LABEL-audit
./tools/dev --command python lab/bbs/check_proxy_cancel_controls.py \
  --capture build/bbs-lab/results/enigma/NEW_LABEL \
  --bridge build/bbs-lab/NEW_LABEL-proxy --output build/NEW_LABEL-controls
```

Use the uppercase name of an existing owned 65,539-byte file from the transfer
matrix; the driver does not create, overwrite or remove a catalog fixture.
