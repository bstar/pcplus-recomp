# Owned ENiGMA upload acceptance

`enigma_upload_dos.py` drives the actual file menu's U action, upload options,
custom protocol selector, ZMODEM receive process and post-transfer detail forms.
It sends a nonempty binary plus `EMPTY.BIN` in one batch, accepts their details,
then uses the normal search/index/game route to open an NFO. A successful
protocol process alone does not pass the test.

The fixture copies the owned upload menus, five upload ANSI assets and selected
theme settings. Relevant tracked upload/FileEntry code must match the source
board. Only one synthetic area is writable by `loclab`; real board configuration,
catalogs, users and storage are not copied. Each successful run retains its own
fixture and files. There is no automatic overwrite or cleanup of earlier uploads.

Both files must match the transmitted size, SHA-256 and exact bytes without
XMODEM padding. The official ENiGMA `FileEntry` API must return exactly one entry
for each name, in the owned area/storage with the correct uploader. The capture
replay additionally checks that the prefilled descriptions were preserved.
Source-file inode/size/mtime/hash remain unchanged. The captures at this
checkpoint have invalid empty-file dates and omitted optional mtime metadata.
The later [date compatibility fix](enigma-upload-time.md) makes the sender
advertise unknown time explicitly and adds received-date checks; original
source-date preservation remains open. Actual DOS compiler output,
ASPECT login trace, directory accounting and original device restoration remain
canonical harness checks. No keyboard credentials or invented protocol replies
are used; only the isolated synthetic account's existing login script is compiled.

The small batch uses 1,501 binary bytes plus an empty file. A fresh second fixture
uses 65,539 bytes, crossing both several protocol windows and the 64 KiB file-size
boundary, plus another empty file. Its keyboard schedule allows the larger send
to finish before submitting details. Wire CRCs, source identity, final receiver
ZFIN before sender `OO`, installed bytes/metadata and subsequent NFO input must
all pass. The separate adversarial replay damages data, the empty offer/EOF,
finish responses/timing, NFO response and catalog fields; every change must reject.

The first DOS attempt completed its protocol but did not install the batch.
Its three-Tab recipe did not accept both detail forms. A small batch passed
with two paced Tabs per form. The first larger batch also transferred exactly,
but its form keys arrived before the queued processing/detail screens finished
arriving. That attempt did not install the files or reach the NFO page.
That checkpoint added time for those screens and the transition between
forms. The later [date workflow](enigma-upload-time.md) replaces fixed Tab
counts with visible scan-pause and focus-driven BIOS keys. Acceptance depends on stored bytes, descriptions,
metadata and subsequent NFO input; elapsed time or protocol exit alone cannot
pass it. These failed captures remain separate from successful evidence.
A still earlier attempt used the BBS-only shell, which lacks NASM; that is an
environment failure before DOS execution, not a client failure.

The later [date follow-up](enigma-upload-time.md) reproduces missing-field
behavior against the actual selected helper and tests explicit unknown time.
Its companion source assigns an uninitialized temporary after a partial time
parse; that source observation is separate from the executable evidence. The
historical captures here retain their original invalid filesystem dates.
The newer sender and acceptance tests are documented in that follow-up.

After exporting a fresh checked candidate, prepare and run it using the pinned
Nix environments:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_search_fixture.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs --uploads
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate
./tools/dev --command python3 lab/bbs/enigma_upload_dos.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_LABEL --upload-bytes 65539
./tools/dev --command python3 lab/bbs/check_enigma_upload_audit.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_LABEL
```

Use the default development shell for the DOS test; it supplies Node, NASM,
DOSBox-X and the compiler. Use a fresh candidate after successful installation,
and preserve captures under unique labels. See the
[validation record](../../docs/validation/enigma-upload.json). This tests the
staged decoder and synthetic upload storage with the modeled 19200/HARD modem.
Live-board installation, physical Wi-Fi modem uploads, upload cancellation/link
loss and the wider application requirements remain open.
