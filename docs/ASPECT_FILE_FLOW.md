# File-backed ASPECT calls, frames and operand reads

Recovered control-flow routines now execute against actual stdio-backed DOS
files through a maintained adapter. The linked diagnostic reads targets across
64KiB, makes two nested framed calls, reserves locals and returns through the
native value stack. Short operand reads and failed positioning unwind through
real native abort/setjmp/longjmp instructions.

This advances the interpreter's file/control layer. The diagnostic invokes
native entries directly; it has no opcode loop, expression evaluator, complete
loader owner or script compiler, and the maintained terminal still cannot run
ASPECT scripts.

## Build and evidence

```sh
./tools/build aspect-flow aspect-file
./tools/build test-aspect-flow test-aspect-file
# Optional private original comparison of native flow/stack/copy bytes:
./tools/build test-aspect-flow-compat
```

| Output | SHA256 | Checks |
| --- | --- | --- |
| `build/aspect-flow/FLOW.EXE` |181160210ffb6e15b60b8d67d5a287b09a8cce7136f180591b9426f820edcc27 |457 CPU scenarios;631 linked8086 DOS assertions |
| `build/aspect-file/FILE.EXE` |c3786f890c44ad898a16e716888c8b0bc791bcbb061ad5f7da2442795b5770b7 |113 host API checks;218 linked8086 DOS assertions |

The optional native comparison matches330 new flow bytes plus the reused197-byte
value stack and72-byte copy routine, and repeats457 paired CPU scenarios.
Ordinary builds/checks use no original executable, installation or REA database.
Both DOS outputs join the71-output fresh original-free rebuild. The interactive
terminal remains731418bd…; these changes introduce no live terminal behavior.

`standalone/record_aspect_file.py` verifies current source hashes, both diagnostic
reports, optional comparison and retained REA records. Sanitized evidence is in
`validation/aspect-file.json`. The real-file fixtures are source-owned72,016-byte
binary files; host and DOS copies match SHA256
`53d5f77fc5300e3f3a28e74d744ada8683b6bffbc9c05c0e8d2eb524c5c60875`.
They are generated only in owned test directories. DOS execution uses DOSBox-X's
mounted filesystem, not the physical CF card or target386.

## Exact native recovery

`src/aspect/control_flow.asm` supplies14 entries in four exact flat ranges:

| Native range, exclusive end | Source file offset | Bytes | Operations |
| --- | --- | --- | --- |
| D1F2..D20D |109474 |27 | Reserve local bytes from word operand |
| D27D..D2A0 |109613 |35 | Wait-gate decrement/increment; DWORD seek |
| D2D6..D372 |109702 |156 | Call, frames, operand calls, return, jump, local-record cleanup |
| E129..E199 |113369 |112 | Buffered word read; DWORD fread wrapper |

Near ABI requires DS=SS. Seek and direct call consume low/high argument words
with RET4. Other entries return normally. Word reads return AX, DWORD reads
DX:AX. CRT hooks use cdecl. OMF builds use linker symbols; flat units retain the
original coordinates for private exact-byte comparison. Retained static Evidence
IDs and the synthetic carrier's source mapping are frozen in the report; the
carrier is never executed.

The isolated flow tests execute actual typed-stack and memory-copy instructions.
They explicitly retain native hazards: ignored seek/tell failure, short DWORD
reads exposing previous local-stack bytes, unchecked gate/depth/frame arithmetic,
local reservation changing the pointer before checking105, and local cleanup
that scans all three records and may decrement its count again on repetition.
Word EOF refill results are combined without validating them as bytes. These
observations do not establish malformed-input safety or a production resource
owner.

## Maintained file bridge

`src/aspect/file_io.{c,h}` owns a read-only stdio stream and256-byte native read
window. Its small-model prefix provides cursor/count and the EOF flag at byte6;
DOS pointer/count/flag offsets are compile-time checked. The prefix is maintained
state, not an imported original CRT FILE object. The same C API runs against
actual host files and actual DOS stdio.

Logical tell subtracts unread window bytes from stdio's current position. SET
and CUR seeks calculate checked signed32-bit targets, discard the window on
success and clear owned EOF state. Targets are0..7FFFFFFFh; unsupported END
origin and invalid ranges preserve logical position. This is the adapter contract
needed by the recovered calls, not a complete replacement C stdio library.

Read validates size multiplication, DOS near span, destination overlap with its
owner and window consistency. It returns complete elements while preserving
ordinary partial-element consumption; status distinguishes EOF and truncation.
The caller must provide sufficient valid destination storage. Owners require
explicit initialization before open and must not be reinitialized while active.
Refill is called only after native count falls from0 to-1.

The linked adapters in `standalone/aspect_file_fixture.asm` abort short required
operand reads and failed seek/tell calls **before** native readers can publish
unchecked results. They execute the real recovered abort/longjmp; failure codes
in this fixture are maintained adapter categories, not invented original ASPECT
error numbers. These adapters are currently exercised by the diagnostic and are
not integrated into the terminal.

## Observed real-file behavior

The common host/DOS API checks verify missing/open/duplicate-owner handling,
buffer-aware position, SET/CUR behavior, EOF, partial elements, rejected ranges,
destination overlap, corrupted-window rejection/recovery and close state. Host
checks additionally reject offsets outside32-bit range.

DOS then runs the actual native entries. A word read starts with one byte left
in the native window and refills for its high byte. A DWORD read crosses file
positionFFFFh. A framed operand call reads target10680h from file offset20h and
saves return24h. It reserves four local bytes, reads another target10690h from
10682h and makes a second framed call, saving return10686h. The second reserves
eight bytes. Native framed returns restore10686h and24h, both previous frames,
the value-stack pointer and call depth. Top-level return signals the exit hook;
jump and direct seek exercise DWORD positioning independently.

Truncated word and DWORD operands trigger real nonlocal aborts. A failed negative
seek during native call also aborts and leaves logical file position unchanged.
The native call had already incremented depth and pushed a return address; those
changes remain observable. Failed tell likewise leaves increased depth. The
fixture explicitly resets native state between such cases and closes its actual
file. It does not pretend abort rolls back native state or automatically owns
all loader resources.

## Remaining integration

The next work is typed expression/operand evaluation, conditional handlers and
a full checked script owner: initialization, file/global-string/value-stack
lifetimes, failure cleanup, scheduling and all invocation paths. Opcode dispatch
must be connected to real handlers, with missing commands kept explicit rather
than silently skipped. Complete compiler grammar/passes, recorder, FLOAT.RTE,
terminal integration and physical validation remain open. All F01–F16
whole-application gates remain open.
