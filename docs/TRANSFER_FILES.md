# Native receiver file writing and close

`reconstruction/transfer_files/` recovers 1,657 exact instruction bytes from the
original receiver and its CRT file-writing stack. The source-only diagnostic
executes the actual recovered `fwrite`, `fflush`, `fclose`, DOS write/close and
buffer-copy code. It writes owned files in DOSBox-X, reopens them and verifies
binary/text bytes and EOF. It is separate from the maintained transaction
backend and does not establish a complete UART-to-file transfer session.

## Provenance and recovered ranges

The selected original SHA-256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
`provenance.json` records exact file offsets, byte hashes, symbolic state and
retained REA evidence IDs. The receiver evidence is
`ev_5627e54d9f87691801201530328b3cd53d294b87c896a38d9c5b1d3c1e62851b`;
the supporting exports include resident `0x186ac`, `0x18318`, `0x18c54`,
`0x1a368`, `0x1868c`, `0x191a6` and `0x1a000`. These saved exports were reused;
no private configuration or original installed resources were read.

| Original CS range, end exclusive | Bytes | Service |
| --- | ---: | --- |
| `86ac..87ad` | 257 | CRT `fwrite` |
| `8c54..8cc6` | 114 | CRT `fflush` |
| `8318..83c6` | 174 | CRT `fclose` |
| `a368..a4a6` | 318 | Binary/text handle write, optional append seek |
| `868c..86ac` | 32 | DOS close and handle flag cleanup |
| `a000..a02a` | 42 | Allocated FILE buffer release |
| `91a6..9286` | 224 | Buffered/unbuffered character write |
| `a22e..a2a8` | 122 | DOS seek wrapper |
| `9420..9428`, `9435..9442` | 21 | Shared CRT return/error-frame epilogues |
| `a8d4..a8e6` | 18 | Available stack calculation |
| `4735..4748`, `85b4..85fc` | 91 | Overlap-safe near memory copy |
| overlay21 `db2a..dbbc` | 146 | Periodic receiver flush and failure close |
| overlay21 `ddf6..de58` | 98 | Final receiver write, close and success tail |

The existing PROGRAM error mapper/table is linked from its source module rather
than counted again here. Some shared CRT ranges overlap earlier recoveries; this
is a module byte count, not an increase in unique application bytes. The explicit
analyst-only `recover.py` requires the verified original; ordinary builds do not.
Every flat unit matches its recorded original hash. OMF objects use linker
symbols; OMF-only fallthrough jumps expose receiver checkpoints.

## Actual receiver semantics

The receiver's push order is important: its file calls are
`fwrite(buffer, used_bytes, 1, stream)`, **one full-sized element**. The result
is an element count, not a byte count.

At `db2a`, a known expected length can defer a flush when the received total
has reached/exceeded that length, retaining the final buffer for trimming.
Otherwise the periodic path writes the used buffer and requires `AX >= 1`.
A short DOS write yields an incomplete element and `fwrite` returns zero; the
receiver reports status 3, closes the stream, and returns failure. Successful
periodic writing resets `cd34` buffer usage to zero and resumes receive.
Explicit source/original regressions cover positive one-byte short writes,
zero-byte writes and DOS errors. No periodic short-write acceptance defect is
claimed.

The final tail is different. Both the `ddf6` and `de20` full-buffer routes call
`fwrite`, call `fclose`, and continue to the success return **without checking
either result**. Tests reproduce success after a short write, DOS write error
or close error, including comparison against the actual original instructions.
This historical behavior is preserved in the exact baseline; a maintained
receiver must explicitly require complete writing and successful close.

The preceding known-length branch (`dd0d..dd4a`, not part of this module)
computes the expected-size remainder and supplies a shortened final element
through `de02`. The source exposes that continuation, but the complete length
calculation/session owner has not been reconstructed here. Final timestamp
application on the `ddf6` route calls resident `3af8`; that remains a named
external contract in this module. The ordinary `de20` route is what the
receiver-tail diagnostic executes.

The flow gate at DS `1d1e` surrounds file IO with calls to `abfa(0)`/`abfa(1)`.
This module does not invent the complete serial-flow/scheduler policy behind
that service. Error/success continuations likewise return to the original
receiver owner, whose nonlocal cancellation is separate reconstruction work.

## CRT layout and near ABI

All functions are near, DS=SS. Stack arguments listed below follow the return
address; the caller removes them. These are recovered internal routines and
**do not validate arbitrary pointers or extents**.

| Export | Arguments / result |
| --- | --- |
| `files_fwrite` | source, element size, element count, FILE pointer; caller8; AX completed elements |
| `files_fflush` | FILE pointer; caller2; AX 0 or `ffff` |
| `files_fclose` | FILE pointer; caller2; AX 0 or `ffff` |
| `files_write` | DOS handle, source, byte count; caller6; AX bytes or `ffff` |
| `files_close` | DOS handle; caller2; AX 0 or `ffff` |
| `files_putc` | character word, FILE pointer; caller4; AX character or `ffff` |
| `files_seek` | handle, offset low, offset high, origin; caller8; DX:AX position or error |

`fwrite`/`fflush`/`fclose` preserve BP/SI/DI through their frames; working
registers, ES and flags are not generally preserved. The shared error epilogues
require their original BP frames and are not ordinary callable APIs.

Original FILE records occupy eight bytes at DS `7b6a`: current pointer at0,
remaining capacity at2, buffer base at4, flags at6 and DOS handle byte at7.
A parallel eight-byte record at `7c0a` holds buffer ownership/selection bit0,
capacity at2 and a temporary-file cleanup selector at4. Source names relocate
both arrays together, including the standard-stream aliases used by `putc`.
The DOS handle flag table begins `7b2b`, with its limit at `7b29`.

The recovered write routine preserves binary bytes when handle flag80h is
clear. In text mode it inserts CR before every LF and returns the number of
input bytes, excluding inserted CR bytes. Flag20h enables append seeking.
Zero-length binary writes return zero without issuing DOS40, avoiding its
truncate-at-current-position meaning. `fwrite` uses a 16-bit multiplication
without an overflow guard; a 256×256 request becomes zero. The diagnostic
explicitly tests that baseline behavior rather than offering it as a safe API.

Flush compares the actual written byte count with the buffered count. On a
short/error result it sets FILE flag20h and returns `ffff`; it still resets the
buffer pointer and remaining count. Close attempts flush, buffer release and
DOS close, and clears the FILE flags even when one fails. An allocated buffer
requires the unrecovered heap free service; a temporary-file selector activates
additional filename/deletion helpers. Those paths remain traps in the standalone
link rather than successful no-ops.

## Bounded diagnostic and verification

The standalone host offers only a trusted synthetic FILE setup:
`files_initialize(handle, borrowed_buffer, text_mode)`, near caller6, AX0/1,
DS=SS, preserving BP/BX/SI/DI/ES. It validates handle0..19 and boolean modes
before changing its tables, uses fixed512-byte owned storage as a borrowed
buffer, and performs no IO. It does not open an original FILE or provide a
production file API. Receiver probes enter the actual periodic/tail fragments
with a bounded synthetic buffer and stop at named owner continuations.

```sh
./tools/dev --command python3 standalone/build_transfer_files.py
./tools/dev --command python3 standalone/check_transfer_files.py
./tools/dev --command python3 standalone/test_transfer_files_dos.py
# Explicit optional bounded original-instruction replay:
./tools/dev --command python3 standalone/check_transfer_files.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

The source CPU suite passes 65 cases: 62 native IO/receiver scenarios and three
invalid synthetic-initialization checks. Optional SHA-verified original replay
adds 62 genuine comparisons, totaling127. It checks lengths0..4096, binary/text,
borrowed/unbuffered paths, element sizes, multiplication overflow, short/zero
writes, write/close errors, receiver periodic failure and unchecked final-tail
success. DOS kernel calls are an explicit byte-recording/fault boundary; source
CRT logic is executed, not replaced with callbacks.

Four actual DOSBox-X8086 cases pass: borrowed-buffer binary600 bytes, unbuffered
binary600, text600 input/603 output bytes, and a deliberately closed DOS handle.
The diagnostic runs real DOS40/3e and reopen/read/EOF checks; the runner separately
verifies complete resulting files. All files are synthetic under ignored
`build/transfer-files-dos/`. Results, maps and digests are recorded there and
under `build/transfer-files/`.

Unresolved services are allocator/free, flush-all, temporary-file helpers,
stack-failure handling, timestamp, flow control and broader receiver lifecycle.
Unknown paths trap. Full UART peer transfer, atomic install/no-overwrite policy,
file transaction recovery, batch names/metadata, retry timing and the complete
session remain separate gates; this native recovery does not replace the
maintained DOS transfer-file transaction backend.
