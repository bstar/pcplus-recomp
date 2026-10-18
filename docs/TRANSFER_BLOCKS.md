# Transfer selection and first recovered block primitives

`reconstruction/transfer_blocks` contains93 exact original CRC instructions,
an independently generated512-byte polynomial table verified against the
original, and maintained bounded CRC/block encoders. The source-only
`BLOCKS.EXE` diagnostic builds and runs in DOS. This is a concrete first transfer
module; it is not a complete upload/download implementation or a live terminal
transfer command.

Provenance binds PCPlus2.01 original SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904` to exact
resident file offsets, flat hashes and saved REA IDs. Normal builds need no
original executable, install files, databases or private configuration.

## Actual protocol selection paths

The selected protocol is DS3996. The selector548c computes a six-byte table row,
copies its protocol ID from DS4ddc+6*index to3996, and calls the handler at
DS4dda+6*index. Thus the following callbacks are actual function pointers, not
guesses from protocol labels. The first word of each row is not interpreted by
this recovery. Protocol-ID labels are independently read through DS2d82.

| ID / protocol | Selected handler | Observed downstream route |
| --- | --- | --- |
|4 XMODEM |5647 |5561 then resident stub bbb3 ->overlay21:d0d0, flags0/1 |
|2 1K-XMODEM |5596 | Same shared entry, flags2/3 |
|9 WXMODEM |5631 | Same shared entry, flags8/9 |
|10 1K-XMODEM-G |55ac | Same shared entry, flags0eh/0fh |
|12 IMODEM |561b | Same shared entry, flags14h/15h |
|1 MODEM7 |54fa | Shared5561 with base flag6 plus direction |
|3 TELINK |5532 | Stub bbd7 ->overlay21:ec48, base flag4 plus direction |
|13 SEALINK |550d | Send bbe3 ->overlay21:d394; receive bbb3 ->d0d0 flag17h |
|5 YMODEM /11 YMODEM-G |5545 | Send bbe3 ->overlay21:d394; receive bbef ->overlay21:d55c |
|17 ZMODEM |565b | Stub bb83 ->overlay28:d0d0, explicit direction argument |
|7 ASCII /18 RAW ASCII |55f6 /5608 | Shared55c2 with ordinary/raw selector0/1; further engine unresolved here |
|6 KERMIT |54d5 |4124 ->414c, actual filename argument `kermit.rte` |
|8 COMPUSERVE B+ |54cc |413d ->414c, actual filename argument `cisb.rte` |
|14/15/16 EXT1/2/3 |cb5b/cb97/cbf7 | Overlay18:e950/e962/e975 ->e932 with external slot0/1/2 |

Resident explicit send/receive routers596c/5a54 corroborate the XMODEM-family
flags and different batch/streaming entry paths. In shared controller d0d0,
the even/upload direction reaches transmitterde58 at d2b8; odd/download reaches
receiverd6a4 at d2ee. This maps entry points and argument propagation. It does
not prove every protocol's framing, option semantics or feature completeness.

The external slot wrappers reach separate direction-dependent services3c63/
3ca1. The Kermit/B+ wrapper414c constructs a command containing ` PCPLUS ` and
passes it through path resolver353d and external execution433d. Exact complete
helper command grammar, memory/IRQ handoff, exit handling and source-built
replacements remain F09 work; these filenames alone are not an implemented
plugin interface.

## Framing and negotiation observed in overlay21

Transmitterde58 initializes payload size128 and start byte1. Its1K paths choose
size1024/start2 when sufficient file data is available. Negotiation at df76..e034
selects additive checksum for NAK15h, CRC for `C`43h or `G`47h, and has separate
`S`/`W` branches whose complete semantics are not recovered here. The ordinary
transmit span e12c..e1b6 performs:

1. Send start byte, block number low byte and one's complement low byte.
2. Send the full128/1024-byte payload through UART bulk senderab92.
3. In checksum mode, sum payload bytes modulo256 and send one byte.
4. In CRC mode, call resident5c77 and send its high byte then low byte.

Before file reads, the original fills its10,240-byte work buffer with1ah at
e0be..e0cc. Short final blocks therefore inherit that padding. The maintained
encoder below accepts a complete supplied payload and does not invent file
length, padding or EOF behavior. ACK/retry/EOT, cancellations, duplicate blocks,
batch names/metadata, flow, disk errors and progress UI remain outside it.

Receiverd6a4 reads bytes with timeout serviceaad9, tracks block/counter state,
updates CRC through5c42 or accumulates checksum, then calls5c5c for CRC
finalization at d9ab. Its d8ee comparison uses the low-byte next-block counter.
The caller also contains batch/duplicate/file-write branches; their complete
retry/cancel/commit semantics are not claimed from this bounded trace.

## Exact CRC unit

| Range | Export | Original ABI |
| --- | --- | --- |
|5c42..5c5c,26 bytes |`transfer_crc_update_original` | Near `(crc,input_word)`, callee cleanup4 |
|5c5c..5c77,27 bytes |`transfer_crc_finish_original` | Near `(crc)`, caller cleanup2 |
|5c77..5c9f,40 bytes |`_transfer_crc_buffer_original` | Near `(source,count)`, caller cleanup4 |

The update computes `(crc_low<<8) XOR table[crc_high] XOR input_word`. The
buffer routine starts at0, supplies zero-extended input bytes and finalizes by
updating twice with zero. This augmented formulation yields CRC16/XMODEM:
`123456789` gives31c3. There is no reflection or final XOR in the recovered
path. The little-endian256-word table at DS39fc exactly matches a table
generated from polynomial1021h; source regenerates it mathematically rather
than embedding extracted data.

Original buffer count uses decrement/JNS: counts0..32768 process that many bytes;
32769..65535 skip processing rather than provide a general unsigned length API.
Original routines have no pointer/span validation. They preserve BP/SI where
used; AX/BX/flags are scratch. DS=SS is required. OMF builds use
`TRANSFER_BLOCKS_OMF` and named table/functions; flat builds retain original
addresses and instruction encodings.

## Maintained near-C interfaces

```c
unsigned __cdecl transfer_crc16(const unsigned char *source,
    unsigned count, unsigned *result);
unsigned __cdecl transfer_block_encode(const unsigned char *source,
    unsigned count, unsigned block, unsigned crc,
    unsigned char *destination, unsigned capacity);
```

Both use16-bit DOS small-model near pointers and fullAX status; callers own
buffers in DS=SS. `transfer_crc16` accepts count0..32768, permits a null source
only for count0, validates the result word and spans, computes through actual
recovered CRC, then writes the result. Status0 succeeds,1 rejects an extent,
2 rejects count. Output can overlap input because calculation completes first.

`transfer_block_encode` requires count128 or1024, block0..255 and crc0 checksum/
1 CRC. It emits132/133 or1028/1029 bytes respectively. It validates source and
the declared destination capacity, builds the entire frame in a local stage,
then commits. Overlapping source/destination is supported. Status0 succeeds,
1 rejects an extent,2 rejects size/mode/block,3 rejects insufficient capacity.
Failure leaves destination untouched; success preserves its unused tail. It
calls the real recovered CRC, not a test callback. These pure APIs do not send
UART bytes, touch files, wait for ACKs or maintain a connection state machine.

## Reproducible checks and next recovery

```sh
./tools/dev --command python3 standalone/build_transfer_blocks.py
./tools/dev --command python3 standalone/check_transfer_blocks.py
./tools/dev --command python3 standalone/test_transfer_blocks_dos.py
# Optional explicit original, synthetic payloads and memory-only UART recording:
./tools/dev --command python3 standalone/check_transfer_blocks.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

Source-only checks cover105 cases:70 CRC vectors including empty,31c3,binary,
random and32768-byte boundary;20 frames spanning both sizes/modes and block
values0/1/127/128/255;four overlapping buffers;11 invalid-count/extent/capacity
cases. The independent oracle uses Python's CRC/checksum operations. Optional
replay adds70 executions of the actual original CRC and20 executions of the
actual overlay21 transmit fragment, with only UART byte/bulk output explicitly
recorded into memory. All195 cases pass. Actual DOS checks31c3 and a bounded
CRC frame header. No public BBS uploads or installed/private files participate.

The packet receive/validate and session boundaries have since been recovered;
see [TRANSFER_RECEIVE.md](TRANSFER_RECEIVE.md),
[TRANSFER_SESSION.md](TRANSFER_SESSION.md) and [TRANSFER_SEND.md](TRANSFER_SEND.md).
Maintained real-DOS storage is composed separately in
[DOWNLOAD_STORAGE.md](DOWNLOAD_STORAGE.md). Their exact scopes distinguish
continuous native state from per-block fixtures, real file IO from controlled
UART input, and legacy baseline defects from maintained safeguards. Full F08/F09
still requires terminal UI/live UART integration, owned peer transfers, every
advertised protocol and physical modem evidence.
