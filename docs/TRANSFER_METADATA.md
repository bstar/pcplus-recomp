# Batch metadata: native baseline and maintained codec

The source-only `METADATA.EXE` diagnostic now links 1,140 newly recovered
original bytes, plus existing CRC/decimal/string/input-drain modules. A separate
`HEADER.EXE` exercises a bounded maintained metadata codec. Neither executable
is a complete batch transfer engine. The interactive terminal remains frozen
at `036a80922c783887249224122f1f44b856d0ff8ae22a106ffe843cb5c9f1cdad`;
these modules are not yet linked into its Alt-R/Alt-S paths.

## Native recovery

`reconstruction/transfer_metadata/provenance.json` binds every flat byte range,
file offset and hash to the verified PCPlus 2.01 original and saved REA Evidence.
`recover.py` is an explicit analyst regeneration tool; normal builds never run
it or read original binaries, installed files or REA databases. NASM flat output
must match its recorded hash before the same instructions are linked as OMF.

| Unit | Original CS range, end exclusive | Bytes |
| --- | --- | ---: |
| TELINK metadata parser | e4c2..e529 | 103 |
| YMODEM metadata parser | e52a..e5d9 | 175 |
| TELINK metadata sender | e5da..e762 | 392 |
| YMODEM metadata sender | e762..e878 | 278 |
| Empty YMODEM batch header | efcc..f01b | 79 |
| Signed decimal-format entry | 9ae8..9af2 | 10 |
| DOS basename helper | 3ea4..3ed9 | 53 |
| Zero-byte transmitter | 40aa..40b1 | 7 |
| Bounded NUL-padding string copy | 9888..98b0 | 40 |
| Decimal-parser thunk | 9b32..9b35 | 3 |

Existing source supplies the decimal core, permissive signed decimal parser,
reverse string search, CRC and native drain loop. They are reused rather than
copied into this module. In particular, 9888 is `strncpy`-style zero padding,
not arbitrary binary memcpy. The 16-byte sender identifier is explicitly
represented in source. The original near ABI requires DS=SS; routines may set
ES=DS and do not promise to restore ES. Detailed orchestration/dependency
ledgers remain in [batch send](TRANSFER_BATCH_SEND.md) and
[batch receive](TRANSFER_BATCH_RECEIVE.md).

The diagnostic UART, file-stat, timing, UI, carrier and cancellation interfaces
are declared fixtures. Native CRC, basename, string copy, signed conversion,
header/parser and drain instructions execute. Nonlocal unwind is an explicitly
observed boundary here; the full receiver/sender context has separate tests.
This diagnostic does not stat real files or use a live UART.

127 linked CPU cases pass independent byte/CRC/field assertions; the same 127
synthetic cases match executions of the verified original instructions. Tests
cover ordinary and streaming header branches, three header attempts, local
cancel/carrier loss, mixed-case DOS paths, binary TELINK fields, absent/zero
length, signed/wrapping conversions and the defective empty-header retry.
The actual 8086 DOS self-check verifies a complete 133-byte metadata frame,
its independently expected CRC, native parsing, the empty header and batch-end
detection.

## Defects preserved in the baseline

- The empty-header function ignores its initial readiness byte. After a missing
  ACK, its apparent retry compares unchanged DI+1 (131) against 3, so it sends
  only one header. The original batch owner does not check a success result.
- The sender calls the signed long formatter. Lengths at or above 80000000h
  become negative decimal strings. The current live upload backend already
  restricts sizes below this range; this is not a new live regression.
- The original parser accepts signed decimal prefixes and wraps arithmetic;
  absent size and explicit zero have no separate validity bit. The surrounding
  owner clears size first, so omitted length is unknown zero there.
- Filename copies, path prefixing and some native drain loops lack the bounded
  checks required for a maintained remote-file owner. A successful header CRC
  does not make its filename safe. Native final-tail write/close failures and
  exact-length completion still require the existing maintained storage gate.

These behaviors remain executable comparison cases. They must not be silently
fixed in the exact source or exposed as trusted production validation.

## Maintained metadata codec

`src/transfer/batch_header.c` supplies pure near-cdecl functions to encode a
128-byte filename/size header or empty header, and decode 128/1024-byte headers.
Its fixed 36-byte result contains a basename, file/end kind, presence flags,
DWORD length/date/mode/serial values, and an offset/length for opaque future
metadata in the original input. The caller must retain that input to inspect
the opaque extension. The code performs no I/O, CRC, timestamp application or
protocol handshakes.

The [Forsberg 1988 reference](https://android.googlesource.com/platform/external/syslinux/+/refs/heads/oreo-m6-s2-release/com32/libupload/ymodem.txt)
defines optional consecutive metadata: decimal length, then octal modification
time, mode and serial number. Further fields may extend the format. The codec
preserves absent length separately from known zero and retains bounded printable
extensions without assigning them invented meanings. Encoding defaults to the
original sender's size-only layout, using checked unsigned DWORD formatting.

The local-platform filename policy accepts case-preserved DOS8.3 basenames and
rejects device names, paths, traversal and long names explicitly. Strings must
terminate within the supplied block, numeric fields must fit a DWORD, and unused
padding must be zero. Malformed separators, signs, control bytes, overlapping
buffers and wrapping near spans reject before changing output. No header text
can select an arbitrary local drive or directory through this codec.

An independent Python oracle checks 1,611 host cases. The source-built 8086 DOS
diagnostic passes 221 checks, including 200 oracle-generated vectors and actual
near-pointer wrapping/overlap guards. These tests cover a metadata codec, not
file-transfer interoperability.

## Reproduce and continue

```sh
./tools/build test-transfer-metadata test-batch-header
# Explicit optional original comparison; synthetic inputs only:
./tools/dev --command python3 standalone/check_transfer_metadata.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

[Validation summary](validation/transfer-metadata.json) records executable/source
identities and separates exact recovery from maintained behavior. Both
diagnostics participate in the fresh source-only application-component proof:
39 outputs reproduce byte for byte with original/installed/REA inputs absent.
The terminal's binary and near data/stack extent (60,432 bytes) remain unchanged.

Next, reconstruct the batch owner and DOS enumeration/path state, then connect
metadata validation to checked per-file source/destination ownership. A maintained
owner must validate readiness and the final empty-header ACK, distinguish missing
length from zero, discard only declared padding, handle repeated headers/EOTs,
preserve exclusive target installation and propagate write/close/rename failures.
Only actual multi-file transfers, retries, cancellation and disk/carrier failures
can establish live YMODEM support. Other protocol families, the full application
and physical modem validation remain open.
