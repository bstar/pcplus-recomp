# Maintained ZMODEM framing

`src/transfer/zmodem_wire.c` is an independently maintained, bounded C89 codec
for standard ZMODEM headers and data subpackets. It builds for DOS 8086 through
the pinned Nix/Watcom toolchain. It is linked into TERMINAL.EXE through the
separate [session engine](ZMODEM_SESSION.md) and [live adapter](LIVE_ZMODEM.md).
This document's diagnostic remains framing-only; prior terminal/XMODEM/YMODEM
reports retain their explicitly recorded historical binary identities.

The implementation follows [Forsberg's 1988 protocol specification](https://gallium.inria.fr/~doligez/zmodem/zmodem.txt),
sections 7–11. [Native evidence](ZMODEM_NATIVE.md) separately records retained
REA observations of the original common framing and send/receive overlays,
with image identities, Evidence IDs and static-analysis limitations. No original
executable, overlay bytes or generated analysis database is a codec build input.

## Interface and ownership

`zw_init` binds caller-owned state to a disjoint 1–1024-byte payload buffer.
There is no allocation or global state. DOS calls use near cdecl pointers and
DS=SS; span/overlap checks reject wrapped near buffers. Nothing is added to the
terminal's constrained near-data segment at this checkpoint.

`zw_feed` consumes one wire byte and returns an event. It searches for binary16,
hex or binary32 headers, accepts extra padding and hex parity-marked LF, and
verifies the header CRC. Hex completion consumes LF before reporting the header,
so its CR/LF cannot become a subsequent data payload. Optional XON remains
out-of-band. Following an accepted header the session owner calls `zw_data` to
begin a data subpacket using that header's CRC width.

Payload bytes are tentative until `ZW_DATA`. Only that event authorizes the
session owner to append bytes to a file. It retains count and terminator until
the next meaningful byte. CRCG/CRCQ continue data; CRCE/CRCW return to header
search. CRC, malformed escape and overflow events require the owner to recover
from its last committed file offset. Overflow consumes/checks the remainder of
the packet while preserving the buffer bound. A timeout is supplied by the
future session owner, which can explicitly return to header search. Repeated
input does not impose its own elapsed-time policy.

Five consecutive raw CAN bytes cancel globally and remain canceled until
reinitialization. Quoted CAN payload is ordinary data. Raw XON/XOFF, including
high-bit counterparts, is ignored even between ZDLE and its suffix. Negotiated
ESCCTL also filters unsolicited unescaped control bytes. ZRUB0/1 decode to
7f/ff. Encoders protect IAC using ZRUB1, escape mandatory controls and conditional
CR/8d after @/c0, and conservatively escape an initial data CR/8d because a prior
packet's CRC could end in @. This last choice avoids hidden cross-packet state.

CRC16 uses direct CCITT update with initial zero; it does not append augmented
zero bytes. CRC32 uses reflected IEEE update, initial ffffffff, final complement
and low-byte-first transmission. Each data CRC covers payload plus terminator.
The small bitwise implementation makes no hardware throughput claim.

Encoders count before writing and return zero without changing output on invalid
arguments or short capacity. Header and data output must be disjoint from input.
A 24-byte header span and 2059-byte data span cover the worst quoted standard
packet. All storage belongs to the caller; the future terminal integration can
use its exclusive transfer arena rather than allocate another resident buffer.

## Verified checkpoint

Run `./tools/build test-zmodem-wire`.

The independent Python oracle uses `binascii.crc_hqx`/`zlib.crc32`, not the C CRC
implementation. It supplies exact encoded headers/data and checks bytewise C
decoding, all four endings, both CRC widths, ESCCTL, all byte values, random
payloads, empty/1/1023/1024-byte packets, quoting, short outputs, corruption,
truncation, capacity overflow, continued subpackets, header recovery, parity LF,
flow injection and cancellation. The host run passes 5,027 assertions. Watcom's
source-built 8086 executable passes 822 independent wire vectors and 55
fault/continuation streams: 7,309 checks, zero failures. It also checks near-span
wraps and state/buffer aliases on the actual 16-bit target.

A separate directory containing only the codec C/header and diagnostic C source
produces a byte-identical DOS executable. The report records Nix compiler and
DOSBox-X paths, source hashes, input corpus hashes and diagnostic executable
hash. See [validation/zmodem-wire.json](validation/zmodem-wire.json).

These results establish wire framing only. The separate
[maintained session engine](ZMODEM_SESSION.md) now adds negotiation, metadata,
verified-position recovery, checked receive commits, sender seeking and bounded
completion, with independent peer and actual DOS component checks. Live terminal
adaptation, far placement and UART/UI ownership now have separate evidence in
`LIVE_ZMODEM.md`. Stock Synchronet/ENiGMA BBS sessions and physical modem tests
remain open.
All full-application gates, including F08, remain open.
