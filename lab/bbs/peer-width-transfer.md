# File transfers with a wide logical screen

The source-built experimental terminal now has separate transfer composition
evidence at logical132 columns on its physical80-column display. Width changes
arrive through the real UART/parser before protocol selection and after manual
keyboard recovery. No ANSI width command is inserted into binary protocol data.

Six [X/YMODEM workflows](../../docs/validation/peer-width-transfer.json) pass
strict remote filename selection, exact file data and final protocol handshakes:
XMODEM Single download/upload, YMODEM Tagged download/All upload, plus stale-name
and canceled-filename-prompt recovery. Payloads include binary data, an empty
batch member and a partial final block. The independent audit rechecks frame
complements, CRC16, sequence, padding, batch metadata/empty terminator, exact
file trees, source identities and before/after hardware bytes. Its receipt
binds134 artifacts.

Six separately audited [ZMODEM workflows](peer-width-zmodem.md) also pass against
independent pinned `lrzsz`, including CRC16/CRC32, escaped upload, files over64KiB
and automatic conservative-credit downloads. The two receipts retain separate
protocol coverage and limitations.

The existing BIOS observers must also see clipboard hotkeys in the filename
prompt and during an active protocol. A clipboard cannot open over the active
protocol; nested Alt-R cannot escape a clipboard owner. Successful transfers
must permit clipboard reuse and ordinary keyboard input afterward. Actual
cursor replies prove132 before selection and after protocol completion, then80
after manual input and narrowing. The full42-byte UART/PIC/vector snapshot
restores exactly. Cases use8086, COM1/38400/8N1/HARD and fresh synthetic media.

The initial pilot transferred all12KiB correctly but failed the old final-video
oracle: native width commits clear the screen. The corrected peer repaints its
menu after narrowing, preserving the final-video requirement with an appropriate
expectation. The failed pilot is retained locally and is excluded from the
accepted receipt. The original harness sources and previous results are unchanged.

For a fresh X/YMODEM case:

```sh
./tools/dev --command python3 lab/bbs/peer_width_transfer_dos.py \
  --terminal build/SELECTED-SOURCE-PRODUCT/TERMINAL.EXE \
  --case xmodem-rx-single --output build/YOUR-FRESH-WIDE-TRANSFER
```

Other case names are `xmodem-tx-single`, `ymodem-rx-tagged`, `ymodem-tx-all`,
`xmodem-rx-stale`, `xmodem-rx-prompt-cancel`. The accepted paths are
`build/peer-width-transfer-final-CASE-01`. Supply all six directories to
`record_peer_width_transfer.py` as repeated `--case` arguments with `--output`.

This is actual DOS UI/UART/file execution against independent protocol peers,
not a stock BBS login, software-audio or physical modem test. Arbitrary width
changes during transfers, other terminal profiles, all remaining protocol and
application families, physical acceptance and card deployment remain open.
Application source and product binaries are unchanged from the SUB checkpoint.
