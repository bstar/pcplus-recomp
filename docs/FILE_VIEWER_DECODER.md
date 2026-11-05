# Incremental internal viewer decoder

The [decoder](../src/filesystem/viewer_decode.c) implements the recovered
[original text contract](FILE_VIEWER_RECOVERY.md) as a bounded source component.
The [validation receipt](validation/viewer-decode.json) binds actual DOS,
linked-code, original-character comparisons and an original-free source rebuild.
This does not yet enable the maintained viewer or change the DOS installation.

## Ownership and scheduling

The decoder has no persistent globals, DOS/BIOS calls, CRT calls or file handle.
It compiles into1314 bytes of FILE_CODE with zero bytes in other object segments.
The caller supplies a26-byte state and a flat character page, both through far
pointers. No new persistent DGROUP storage is required. The future modal owner
can keep state in its bank and borrow its page from existing foreground storage.

Initialization clears exactly `width*rows` character bytes to spaces. Widths
1–132 and heights1–49 are supported by this component. Each feed consumes at
most256 input bytes, stops at a complete page, and reports the exact count
consumed. Read-ahead remains the caller's responsibility; unused bytes must
not be discarded when the decoder stops at a page boundary.

The26-byte state records raw position as32 bits. Position overflow latches a
distinct error without consuming the unrepresentable byte. Reinitialization
starts another page at a supplied raw offset. This component does not implement
or silently introduce the original controller's inferred100-page limit.

As recovered, chunks end at LF or133 consumed bytes; displayed text is clipped
to width, NUL ends display only, trailing unsigned bytes at most32 are removed,
and all remaining bytes are literal screen characters. There is no ANSI
interpretation, tab expansion or display-width wrapping. Trimming uses explicit
length bounds, avoiding the original's static zero-length underflow concern.

`VIEWER_MORE` requests another bounded feed. `VIEWER_PAGE` means the content page
filled, without implying EOF. The owner supplies real EOF through `finish`;
it flushes a partial final chunk and returns `VIEWER_EOF`. Finishing an already
full page leaves `VIEWER_PAGE`, allowing the owner's next-page read to discover
an exact-boundary EOF as the original does. Terminal phases are stable until
reinitialization.

Argument errors preserve all caller storage. Passed spans must be valid caller
allocations, fit16-bit offsets, remain below1MB and not overlap state/page/input/
count output. Checks compare linear addresses so paragraph aliases cannot
bypass ownership. These arithmetic checks cannot establish whether an arbitrary
address is actually allocated; callers remain responsible for memory ownership.

## Verification

- 175 generated vectors pass45,745 checks in DOSBox with8086/FPU-off execution,
  using both ordinary DGROUP and banked FILE_CODE state. They cover eight
  original content oracles at eight feed sizes, widths1–132/heights1–49,
  deterministic binary input, empty/NUL/control-only chunks, input beyond a
  page boundary, partial EOF and32-bit position boundaries. The diagnostic
  checks exact pages, consumed bytes, positions, phases, memory guards,
  argument-error preservation and stable terminal phases.
- 66 additional cases execute the actual linked Watcom code with page/state/
  input/count in separate far segments. All non-stack DGROUP bytes remain
  unchanged. DS=SS, BP/SI/DI and cdecl stack return are checked; every interrupt
  fails. Paragraph aliases, segment/address wraps and malformed states are
  rejected without changing buffers.
- Eight accepted original VGA captures match all15,360 content character
  bytes used by the corresponding decoder vectors. This comparison excludes
  attributes, footer and cursor, which belong to the future UI owner.
- A fresh export containing only the five declared source/header/Python build
  inputs reproduces `DECODE.EXE` byte-for-byte. No original executable,
  configuration, REA database or previous object was copied into that export.

Reproduce with fresh output paths in the pinned environment:

```sh
./tools/dev --command python standalone/build_viewer_decode.py \
  --output build/viewer-decoder-new
./tools/dev --command python standalone/test_viewer_decode_dos.py \
  --program build/viewer-decoder-new/DECODE.EXE \
  --output build/viewer-decoder-dos-new
./tools/dev --command python standalone/check_viewer_decode_linked.py \
  --program build/viewer-decoder-new/DECODE.EXE \
  --output build/viewer-decoder-linked-new
```

## Remaining viewer work

The decoder is not a file viewer by itself. A [read-only DOS owner](FILE_VIEWER_OWNER.md)
now passes its component checks, and their [paging controller](FILE_VIEWER_SESSION.md)
passes composition checks with retained read-ahead and checkpoints. The
[serviced foreground UI](FILE_VIEWER_UI.md) now passes initial terminal/serial
checks and enables opt-in Alt-V. Stock-editor, capture/HOLD/printing and
disconnect/reconnect/transfer pressure composition remain open.
Configured external-viewer binding, hardware acceptance and
all remaining ASPECT/emulation/protocol/Host parity remain separate requirements.
