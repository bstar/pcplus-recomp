# Native screen snapshot recovery

`reconstruction/snapshot` recovers381 exact PCPlus2.01 instruction bytes in six
flat/OMF units. A source-only8086 DOS diagnostic links the actual row selector,
character-copy helper, CGA video brackets, original snapshot writer and keyboard
wrapper. Its FILE/UI services are declared memory fixtures, not a live file
owner. The maintained application can reuse the row helpers with its separate
checked file policy; that does not make the unchecked native writer safe.

```sh
./tools/dev --command python3 standalone/build_snapshot.py
./tools/dev --command python3 standalone/check_snapshot.py
./tools/dev --command python3 standalone/test_snapshot_dos.py
# Explicit analyst-only optional original instruction comparisons:
./tools/dev --command python3 standalone/check_snapshot.py --original
```

The normal build/check/DOS commands do not read an original executable,
installation, private configuration or analysis database. `recover.py` is an
explicit analyst regeneration tool requiring the digest-bound original and
retained exports; it is never invoked by the build.

## Units, ABI and integration

Build with `-DSNAPSHOT_OMF`, including `reconstruction/uart/encodings.inc`.
Flat assembly preserves original offsets and exact bytes. OMF uses symbolic
state/services and actual instruction labels; no binary extraction occurs in
the build. Provenance records per-unit EXE file offsets, hashes and REA IDs.

| File | Original span, end exclusive | Bytes | Public entry |
| --- | --- | --- | --- |
|writer.asm|3496..353d|167|snapshot_write_original|
|row.asm|3446..3496|80|snapshot_row_original|
|copy.asm|64b8..64fd|69|snapshot_copy_original|
|keyboard.asm|1310..132e|30|snapshot_keyboard_original|
|video_begin.asm|77be..77d2|20|snapshot_video_begin|
|video_end.asm|77ae..77bd|15|snapshot_video_end|

`row.asm`, `copy.asm`, `video_begin.asm`, `video_end.asm` form the independently
linkable source subset for a checked maintained writer. They do not depend on
the diagnostic host, unchecked writer or keyboard/UI entry.

- `snapshot_row_original(row,destination)`: near caller-clean four-byte stack
  arguments (`[BP+4]` row, `[BP+6]` near destination), returns AX trimmed length.
  BP/SI are preserved; working registers and ES are not general preserved state.
- `snapshot_copy_original`: near **callee-clean RET8**. At entry SP+2=cell count,
  SP+4=far source offset, SP+6=far source segment, SP+8=near destination. Push
  destination, source segment, source offset and count before CALL. It returns
  AX trimmed length and restores DS/SI/DI. ES remains the caller's DS; DF is
  explicitly cleared on return. DS=SS is required because it obtains argument
  addresses through BX=SP and reads via DS:BX. This is not a normal caller-clean
  C function despite its four-word input layout.
- `snapshot_video_begin`/`snapshot_video_end`: near no-argument services.
  Nonzero CGA status port executes actual port IO; the begin routine has an
  unbounded retrace-bit wait. Neither is a generic saved-mode restore API.
- `snapshot_write_original(interactive)`: near caller-clean word argument,
  preserves BP/SI/DI. AX is not a stable success/error result; unchecked FILE/UI
  return values can become its final value. DS=SS and DF-clear entry are needed.
- `snapshot_keyboard_original`: no arguments. Calls0dae(1), writer(1),0dae(0)
  and returns. It preserves the original route, not a new configurable hotkey.

The host's `_snapshot_copy_c`, `_snapshot_row_c`, `_snapshot_writer_c` and
`_snapshot_keyboard_c` are explicit diagnostic C adapters preserving BX/ES
around these raw routines. They are not attributed to the original.

## Original state and geometry

| Original DS | Module symbol | Existing application alias suitable for integration |
| --- | --- | --- |
|cdfa|snapshot_shadow_enabled|screen_viewport_enabled|
|325a|snapshot_shadow_columns|screen_attribute_row_bytes|
|5dea/5dec|snapshot_shadow_offset/segment|erase_shadow_offset/segment|
|3250|snapshot_video_columns|ui_flow_region_cells|
|7a7a|snapshot_video_stride|screen_video_row_bytes|
|7a78|snapshot_video_segment|text_video_segment|
|7a8e|snapshot_cga_status_port|text_cga_status_port|
|7a74|snapshot_rows|Physical screen row count |
|334c|snapshot_special_row|First status row, or physical row count when hidden |

Despite the inherited alias name `screen_attribute_row_bytes`,325a is used by
this selector as a **cell count**, then multiplied by2 to locate character/
attribute pairs. Shadow row address is low16(2*325a*row)+5dea in segment5dec.
The native routine does not propagate offset overflow into that segment.

With cdfa=0, the selector brackets copying with77be/77ae, uses source segment
7a78 and byte offset low16(7a7a*row), and copies3250 character/attribute cells.
It does not silently choose the active BIOS page instead of the original
configured video-memory state. Both multiplication paths are unbounded native
arithmetic; live callers must validate row/width/source extents themselves.

The copy helper walks the source words backwards. It discards each attribute,
converts NUL characters to spaces and stores exactly `count` character bytes,
followed by NUL at destination[count]. AX excludes trailing spaces, but those
spaces remain in the buffer until the caller overwrites them with CRLF. Leading
and interior spaces remain. Count0 writes just the destination NUL and returns0;
DS/SI/DI are restored and DF is cleared even on that path.

For CGA port0 the video brackets are real conditional-return paths. For a
nonzero port, begin repeatedly reads until bit08h is set, then changes DL to
d8h and writes25h; end writes2dh to that control port. Source-only CPU checks
execute those instructions with only IN/OUT modeled, proving port3d8 writes
25h then2dh. A maintained live policy rejecting a nonzero CGA status port is
separate from this exact original and avoids inheriting its unbounded wait.

## Snapshot writer, text length and the special row

The native writer opens `PCPLUS.SCR` in append-binary mode `ab`, obtains screen
rows0..7a74-1, writes literal CRLF at destination+trimmed_length using the real
resident8268 **strcpy**, and invokes8e88 on each terminated string. It closes
once and, in interactive mode, displays status, waits for a key and refreshes.
Open failure invokes the explicit BX-message boundary427f. Row-write and close
failures are ignored. The diagnostic deliberately tests those original gaps;
it does not reinterpret them as checked success.

The138-byte local allocation also contains the FILE pointer at BP-2. There is
no native width/row validation. A live writer must not pass arbitrary geometry
into this frame or its near row buffer; the checked application writer owns
its own bounded buffer and IO instead.

After CRLF insertion, if row==334c, the writer checks the byte three positions
before the string end and changes1Ah to space. This is the last displayed
nonblank byte before CRLF, not an instruction to strip every1Ah or truncate the
file at DOS EOF. Original widths/empty rows do not supply a separate guard for
the preceding pointer calculation.

The special row's ordinal is proved from two additional retained functions:
resident6d1a reads BDA0484's last-row byte (normally24), stores it at7a80, then
increments it into physical row count7a74 (normally25). Resident46ba toggles
1d46: nonzero assigns334c=7a74 and334a=7a74-1; zero assigns334c=7a80 and
334a=7a80-1. Therefore a25-row display with the status line present uses
special row24. When status is hidden it uses25, which the0..24 writer loop
never visits. Treating334c unconditionally as25 would lose the native status
row patch. The row's exact UI rationale is not inferred beyond this evidence.

This file is a character-only appended text snapshot. Packed RAM UI-window
snapshots are a different subsystem; no original `.DMP` format is established.

## Verification and explicit boundaries

The linked checker passes24 cases, with24 optional comparisons against the
same digest-verified original instructions and identical synthetic inputs.
Cases cover counts0/1/5/80/132, attribute stripping, NUL-to-space, all-blank and
mixed rows, destination canaries, DS/SI/DI/DF, real shadow/video selection,
native CGA IN/OUT brackets, interactive/noninteractive snapshots, failed open,
unreported write/close failure and both special-row ordinals. It reuses actual
original CRT strcpy/strlen modules; string formatting is not a successful
no-op callback.

The actual8086 DOS diagnostic also passes row extraction, empty rows,
complete CRLF output, status-row1Ah conversion, repeated append, keyboard
wrapper/UI calls and open failure. SHA256 of the tested executable:
`fdcc00355ace42b426cc320d779dc51c0b3ae8a0d47abf3a7bac3973417f69c9`.
JSON evidence is `build/snapshot/checks.json` and `build/snapshot-dos/result.json`.
These are component diagnostics with memory-FILE/UI fixtures; they neither
write a production snapshot file nor prove complete native file ownership/UI.

Only explicit `--original` reads the original EXE. It maps original code and
supplies synthetic state plus documented FILE/UI boundary models; it never
executes an analysis executable or uses a private capture/configuration file.

## Evidence identities

Original EXE SHA256:
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resident offsets map to EXE1200h+offset. Per-unit hashes and offsets are in
`reconstruction/snapshot/provenance.json`.

| Retained REA assembly export | Evidence ID |
| --- | --- |
|13496 writer| `ev_68337647c17ff53945a61bc81e6e08247d7b411b28e586de927f3c7e7d559fa1` |
|13446 row selector| `ev_3e80115b63239dd2e9e663e183f115b211778ed0e7eec02a76c7b9c1ec6c7a9b` |
|164b8 character copy| `ev_073a04b35f90a84a7ea7dfa10db55bca00d442e74f9adfe4deee25ece4413bab` |
|0x177be| `ev_c43082a7dc48a9b3f0ae81f668650d020422ffdb6633b93dd20ecaa1aaef3a06` |
|0x177ae| `ev_ba097dc8042b5fdd581c14b780e0f3f2e177bfd405a026654fd88b209d83e7af` |
|0x146ba| `ev_6e176171671c861500f5bed692dae31976c63dc08cb85e82d04c617bf844009d` |
|0x16d1a| `ev_b69c16de3a282945866264390ca70dc20baf95e61a5d5edf2ff0fd3bee666688` |

The1310 keyboard wrapper has no matching saved function export. Its bytes were
recovered from the SHA-verified original, and its scan22h pointer is already
verified in the recovered keyboard table. No new REA session was opened.
