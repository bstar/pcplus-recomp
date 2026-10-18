# Read-only DOS upload sources

`src/transfer/upload_file.c` owns one read-only source for one foreground
transfer. It has no write, create, rename or delete operation. Explicit ASCII
DOS8.3 paths are normalized and bounded to63 bytes; devices, wildcard components,
directory and volume entries are rejected. Startup initialization is explicit
because the assembly host does not assume C BSS is zeroed.

Preflight queries attributes, opens once read-only, seeks to end for a32-bit
length, then rewinds. The recovered sender's initial `r` open receives logical
token1; its discovery close does not close the physical source. Its subsequent
`rb` open receives token2 over that same preflight handle, avoiding a close/reopen
race. Tokens belong to this foreground session, not arbitrary stale callers.

Native reads use element size1 and at most10240 bytes. They preserve every byte,
including00h/1Ah/11h/13h/FFh. Only bytes up to the length snapshot are supplied.
Early EOF, positive short reads, invalid count/near spans, DOS errors and ownership
violations poison completion. Near spans cannot wrap or overwrite ownership
state. Byte counts remain full32-bit values; diagnostic call counts saturate.

The binary close physically closes exactly once. Repeated native cleanup cannot
close a recycled handle. Closing before consuming the snapshot latches incomplete
input. A failed DOS close is ambiguous: ownership becomes uncertain, further
close/reset is refused, and the live application reports recovery. Completion
requires the full snapshot, a clean error latch and a successful close.

The92-byte result layout is checked with compile-time offsets/word sizes. It
contains state/error/ownership words, DWORD size and consumed counts, and the
normalized path. `terminal_upload.c` separately gates native success and latches
source errors into the live owner. Its native signed-size boundary is stricter
than this general backend: sources above7ffffbffh are refused before negotiation
so padded totals fit the recovered signed32-bit calculations.

```sh
./tools/build upload-file test-upload-file
```

`UPLOAD.EXE` uses actual DOS open/seek/read/close to check70013 binary bytes,
empty/missing/directory cases and source immutability. `UPFAULT.EXE` exercises
filesystem errors, short/early reads, near-buffer bounds/aliasing, invalid paths,
full DWORD accounting and ambiguous close without repeated close. Captured
results and hashes are in `docs/validation/upload-source*.json`.

This is an initial length snapshot, not concurrent-writer exclusion or a
content hash. Same-length changes by another writer are not detected. Appended
bytes beyond the snapshot are not sent. The fixed tokens are not generation-tagged
across sessions. Physical modem and BBS transfers require separate evidence.
