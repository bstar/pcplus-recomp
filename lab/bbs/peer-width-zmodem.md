# ZMODEM in the wide logical view

This campaign composes the source-built DOS terminal's logical132-column view
with independent pinned Nixpkgs `lrzsz`. The physical display remains80 columns.
Manual CRC32/CRC16 downloads, ordinary/escaped uploads and automatic CRC32/CRC16
downloads each transfer an empty file, a one-byte file and65797 binary bytes.
Automatic cases use the saved autodownload preference and `/Z:256`; manual
downloads preserve the default8192-byte offer.

All six final cases pass. The [independent receipt](../../docs/validation/peer-width-zmodem.json)
binds122 artifacts and the complete selected matrix. Accepted paths are
`build/peer-width-zmodem-final-CASE-manual-02` for the four manual cases and
`build/peer-width-zmodem-final-CASE-auto256-02` for the two automatic cases.
The `-01` matrix is retained separately and is not accepted.
Each accepted upload includes one repeated file offer and two byte-verified
data replays. These recovered transfers are not claimed to be retry-free.

Actual cursor replies prove width132 before the protocol starts and after the
independent peer finishes. A single DSR then checks ordinary terminal ownership,
followed by actual manually typed `ready`, a peer-requested narrow mode and an
80-column cursor reply. Width changes clear the native view, so the remote peer
repaints its menu afterward. The final physical screen and the independent
42-byte UART/PIC/vector snapshot must match their defined expectations.

The passive [wire audit](audit_zmodem.py) uses Python CRC16/CRC32 and quoted-byte
decoding rather than the maintained C codec. It verifies all file metadata,
payloads including replayed ranges, lengths/EOF, ZFIN and literal OO. The
opposite stream must contain real ZRPOS and ZFIN responses. Download ZRINIT
flags/credit are checked, including removal of overlap at256 bytes. Both actual
source/destination trees must match all three synthetic files; `lrzsz` must exit0
and its Nix-store binary hash must remain unchanged. These checks do not claim
the separate response-timing audit based on TCP chunk timestamps.

The first matrix retained three failed fixtures. Automatic cases stopped before
terminal startup because the generic PRM generator left mouse scales at zero;
the current mouse-enabled build requires1..999. The final adapter supplies8/4
and the selected parent's existing custom IRQ settings. One manual upload had
all file bytes and hardware restoration correct but its peer discarded a
partially received status reply after repeated polling. The final peer consumes
one complete DSR and the exact keyboard bytes, preserving partial replies.
Earlier pilot preparation failures and the first matrix remain local, outside
accepted evidence. No application instruction, protocol response or native
width behavior was patched.

For a fresh case:

```sh
./tools/dev --command python3 lab/bbs/peer_width_zmodem_dos.py \
  --terminal build/SELECTED-SOURCE-PRODUCT/TERMINAL.EXE \
  --case rx-default --automatic --output build/YOUR-FRESH-WIDE-ZMODEM
```

Manual cases omit `--automatic` and use `rx-default`, `rx-crc16`, `tx-default`
or `tx-escape`. Automatic cases use the two receive names. All cases use8086,
COM1/38400/8N1/HARD and fresh owned synthetic media. Startup Enter dismisses
the edition splash; automatic cases use no transfer hotkeys. Supply all six
directories to `record_peer_width_zmodem.py` as repeated `--case` arguments,
with `--output` selecting the public receipt.

This is actual DOS/UART/file execution against independent `lrzsz`, not a stock
BBS login, SIP/audio or physical modem result. No width command is inserted
into binary transfer data. Arbitrary width changes during transfer, other
profiles/protocols, broader F01–F16 and card deployment remain open. Application
and compiler/interpreter binaries are unchanged from the SUB checkpoint.
