# Upload cancellation and retry

This workflow keeps one source-built DOS terminal running while it sends a
generated 65,539-byte binary. An independent timer observer reads the actual
`Sending ZMODEM` footer and inserts one BIOS Escape only after confirmed KiB
progress is visible. The wire must contain valid source data and a real peer
ACK before the cancel burst, without an earlier EOF.

The client leaves the protocol selector through the normal UI, searches for a
generated game and opens its NFO. At that response, the test snapshots the
official FileEntry API, installed storage, private server temporary files and
unchanged DOS sources. It then returns through the real menu stack, retries a
binary/empty batch and reopens the NFO in the same connection. The second
Alt-S uses the already-selected ZMODEM protocol. `escape` is the DOSBox key
name; the retained first recipe used unsupported `esc` and never transmitted
its later commands.

The retry uses the existing visible scan-pause and detail-form observer. It
requires recorded BIOS keys, matching bytes at the server, exact installed
files/catalog fields, current creation dates, source-file preservation and
original hardware/vector restoration. No application variable, peer reply or
product callback is replaced.

The unmodified upload core passes the client recovery checks but retains its
canceled temporary data. The separate [scoped ownership experiment](patches/enigma-upload-temp/README.md)
addresses that server behavior; its differences are explicit in fixture
metadata. It is not installed on the live board.

```sh
./tools/dev --command python3 lab/bbs/enigma_upload_dos.py \
  --candidate build/bbs-lab/NEW/candidate \
  --label UNIQUE_CANCEL --upload-bytes 65539 --cancel-first
./tools/dev --command python3 lab/bbs/check_enigma_upload_audit.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_CANCEL
```

Start the isolated server with `--private-tmp` so the test can verify temporary
data ownership without examining other applications' temporary directories.
Use a fresh fixture after any installed files or retained partials; no previous
data is overwritten or removed to make a rerun pass. Ordinary successful upload
tests remain available without `--cancel-first`.

The [validation record](../../docs/validation/enigma-upload-cancel.json)
separates the invalid keyboard recipe, original-core cleanup failure, staged
component/server tests and unchanged DOS products. Physical modem and live-board
acceptance, upload carrier loss, source-date preservation and full application
requirements remain open.
