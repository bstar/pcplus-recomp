# Window display snapshots

The original resident save/restore path is recovered and independently builds
as `build/ui-windows/WINDOWS.EXE`. The snapshot routines contribute 158 exact original bytes; the original flow-message
service and five small dependencies add 231 bytes, for **389 exact original bytes**
in this module, with existing recovered text stores as the output dependency. A separate
maintained wrapper adds bounded rectangular transfers. No original executable,
analysis database or vendor install is read by the default build or tests.

## Original evidence and behavior

The original is PCPlus 2.01, SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
`reconstruction/ui_windows/provenance.json` records each source range, file
offset, byte digest and REA/Ghidra evidence ID. Flat NASM builds are checked
against those digests before linking the relocatable OMF build.

| Original CS | Recovered symbol | Bytes | Behavior |
| --- | --- | ---: | --- |
| `6fa0..6fcf` | `ui_read_byte` | 47 | Video byte read, including the original optional CGA status wait |
| `6fd0..6feb` | `ui_read_packed` | 27 | Reads character and attribute as a packed word |
| `765c..7682` | `pcplus_screen_save` | 38 | Saves a contiguous count of text cells to DS buffer |
| `7682..76b0` | `pcplus_screen_restore` | 46 | Restores those cells through actual `text_write_packed` |

Ranges are end-exclusive. The single alignment byte between read helpers is
not claimed as recovered instructions. Saved REA exports are under ignored
`analysis/pcplus-main/functions/`; the checked-in provenance retains their IDs.

Current REA caller evidence for save is
`ev_8c52162e841ddde4985edc5d1639c8d8d99d4532ea0555034020f489d5943a37`
and restore is
`ev_6fa85bbb1c99e891948a77e89afc9d784476a79e6cbbd8f923a5a97549d91e96`.
Both resolve the resident callers `CS:31bb`, `4647` and `ac0e`:

- `31bb` saves 15 cells into a stack buffer, paints and writes a short overlay,
  optionally waits, then restores the saved cells.
- `4647` saves a configured contiguous region, presents a prompt, polls keys
  and restores it before returning a selection value.
- `ac0e` is the already recovered UART flow-status caller, using its small
  screen-save buffer around status display changes.

Those are observations from resident call references and saved instructions;
they do not establish all modal-menu callers in appended overlays or unresolved
indirect calls. No general original window manager or border renderer is claimed.

## ABI and shared state

The two original transfer functions use near stack arguments in this order:
`count, video_byte_offset, buffer_offset`; they return with `RET 6`. A caller
pushes buffer first, then video offset, then count. `BP`, `SI` and `DI` survive;
`AX/BX/CX/DX/ES` and flags are scratch. Both require **DS=SS and DF clear**.
The original routines do not bound count, screen extent, buffer allocation or
segment wrap. A zero count transfers no cells.

The buffer contains **attribute byte, character byte** for each cell, whereas
video memory contains character, attribute. This is the existing packed-word
ABI; direct `rep movsw` from such a buffer to video would reverse the bytes.

`ui_read_packed(offset)` and `ui_read_byte(offset)` each return AX and `RET 2`.
Their internal register preservation follows the recovered source. Applications
should normally call the transfer functions rather than rely on scratch flags
or individual read-helper registers.

| Original DS | Canonical shared symbol | Role |
| --- | --- | --- |
| `7a78` | `text_video_segment` | Configured text-video segment, host default `b800` |
| `7a8e` | `text_cga_status_port` | Zero for direct access; nonzero selects original CGA synchronization |

The restore dependency is the existing recovered `text_write_packed` at
`CS:6cb4`, including its real `text_cga_word` dependency. There are no callback
fixtures or no-op writer implementations in the runtime executable. The CGA
waits retain original unbounded hardware polling; a future timeout belongs in
a separately identified maintained change.

## Maintained rectangle API and ownership

`bounded.asm` is deliberately distinct from exact recovery. `ui_window_save`
and `ui_window_restore` take near stack arguments
`top,left,height,width,buffer,capacity_bytes`, then `RET 12`. Coordinates are
zero-based. They return AX=0 for success or AX=1 for rejected arguments, preserve
BP/SI/DI/BX and use AX/CX/DX/ES/flags as scratch. DS=SS and DF clear remain required.

The wrapper rejects empty rectangles, arithmetic overflow, screen crossings,
insufficient declared capacity and buffers whose end wraps the data segment.
It validates geometry before I/O, then invokes the real original helper once
per row, advancing the video offset by `2*screen_columns`. It uses shared
`screen_columns` and a host-supplied `ui_window_rows` word. Current supported
geometry is 1..255 columns and 1..127 rows, which keeps byte offsets in range.
The standalone host supplies 80x25. The wrapper uses only the necessary
`2*width*height` bytes of the buffer.

The caller must supply a real allocation of at least the declared capacity,
keep it separate from live stack/state and pass identical rectangle metadata
to restore. Different allocations support nested windows; restoration is LIFO.
There is no allocator, global saved-screen slot or hidden window stack.

These helpers own **display cells only**. They preserve both character and
attribute bytes, but neither reads nor saves the BIOS cursor, cursor shape,
logical terminal cursor, current renderer attribute, charset, scroll margins
or parser state. They do not change those states while copying, which the DOS
test confirms for BIOS position. If menu painting moves the cursor or changes
logical attributes, the application must save and restore that context separately.
The already recovered CSI cursor-save state uses global slots, so those slots
must not be borrowed as a nested UI context stack or overwrite a remote BBS's
saved cursor. A future modal UI needs caller-owned context per nesting level.
Incoming terminal rendering must also be paused or staged while a modal screen
is active to prevent restoring a stale snapshot over new remote output.

## Verification

```sh
./tools/dev --command python3 standalone/build_ui_windows.py
./tools/dev --command python3 standalone/check_ui_windows.py
./tools/dev --command python3 standalone/test_ui_windows_dos.py
```

The CPU checks execute actual linked instructions. Four groups cover a random
2000-cell save/restore with packed-order assertions, zero count, nested rectangles
and buffer canaries, bottom/right edges, invalid geometry/capacity/segment wrap,
and actual recovered CGA branches. The CGA input port is an explicit alternating
low/high test fixture, not a physical adapter observation. All four passed.

The DOS executable initializes real B800 text memory, nests two windows with
different character/attribute pairs, restores each in order and checks the
unchanged BIOS cursor through INT10. DOSBox-X's actual DOS run passed with
binary SHA256 `fbf6cabd1539075134062d99e4477c7eb7a229325e6fa50791adc11867420671`.
The expanded host also checks persistent FLOW text and a timed WAIT overlay
restoring FLOW through actual BIOS timer progress.
This does not exercise a full application menu or physical CGA timing.

An optional comparison explicitly requires the ignored original:

```sh
./tools/dev --command python3 standalone/check_ui_windows_original.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

All **28 original/source runtime comparisons passed**, including direct and CGA
paths, zero/small/full-screen counts and edge offsets. Both sides run actual
resident instructions; video, buffer, stack cleanup, preserved registers and
CGA fixture read counts are compared. The original is SHA-pinned before loading.
No synthetic analysis executable is executed. Comparison is optional and cannot
be a build input. Results are local under `build/ui-windows/` and
`build/ui-windows-dos/`.

Next integration is to link these sources with `-DUI_WINDOWS_OMF -DTEXT_OMF`,
reuse the existing video segment/status symbols and `screen_columns`, supply
the row word and caller-owned snapshot/context allocations, and call the bounded
API around actual menu painting. Root build/terminal files are unchanged.


## Original flow-message service

`pcplus_flow_message` now recovers the complete original `CS:31bb..3226` body
(107 bytes), not a renderer fixture. It links the existing real snapshot and
`text_fill_cells` helpers and these additional original routines:

| Original CS | Symbol | Bytes | Behavior |
| --- | --- | ---: | --- |
| `6b98..6bb6` | `ui_tick_delay` | 30 | Waits for changes in BIOS tick lowword at physical 046c |
| `6bf0..6c1f` | `ui_write_string` | 47 | Writes a NUL-terminated DS string with attribute at packed coordinates |
| `7e02..7e0e` | `ui_coordinate_offset` | 12 | Converts DH=row,DL=column to video byte offset using screen_columns lowbyte |
| `77be..77d2` | `ui_cga_blank` | 20 | Optional CGA vertical-retrace wait and mode-control output 25h |
| `77ae..77bd` | `ui_cga_unblank` | 15 | Optional CGA mode-control output 2dh |

The service is **cdecl**, near arguments `message_offset,duration`; caller
removes 4 bytes. It preserves BP/SI/DI and uses scratch AX/BX/CX/DX/ES/flags.
The string helper has callee cleanup `RET 6` with arguments
`string_offset,attribute,packed_coordinate`. The delay helper has `RET 2`.
Original DS=SS/DF-clear requirements remain.

| Original DS | Canonical symbol | Meaning |
| --- | --- | --- |
| `3250` | `ui_flow_region_cells` | Original region value; service subtracts 80 before calculating display location |
| `7a82` | `ui_flow_video_base` | Added to the resulting video byte offset |
| `7a84` | `ui_flow_coordinate_base` | ORed with the shifted location to produce packed row/column |
| `1d46` | `ui_flow_suppressed` | Nonzero skips all screen and delay I/O |
| `1f6e` | `ui_flow_attribute` | Lowbyte is string attribute; highbyte is ORed with20h for fill character |

It saves 15 cells into its own 30-byte stack buffer, fills them, and writes the
message starting one column later. **Duration zero leaves the message painted**;
the local snapshot is then discarded. Nonzero duration waits and restores the
15 saved cells. Suppression bypasses both rendering and waiting. The delay
increments its 16-bit duration then waits that many observed tick transitions;
`ffff` wraps to zero and still waits one transition because of the original
loop structure. Its lowword change comparison naturally tolerates tick wrap.
It enables interrupts and does not pump keyboard/UART callbacks while waiting.
These legacy behaviors are preserved, not silently corrected.

For the currently recovered 80x25 UART caller, which separately saves 15 cells at
video offset 0f00h, coherent host values are region_cells=80, video_base=0f00h,
coordinate_base=1800h, suppressed=0 and attribute=001eh (or another lowbyte color).
This paints bottom-row text at column 1 while matching the UART's independently
saved cells at column 0. Other geometry needs an explicit application choice;
the original subtracts 80 rather than adapting that constant to columns.

The original service is not the bounded rectangle API. It trusts its state and
NUL-terminated string; messages longer than 14 visible bytes extend past its
saved 15-cell region, and malformed pointers/coordinates can write beyond the
intended area. Current caller strings must fit. A maintained clipping/time-budget
adapter can be added separately if application requirements demand it. Cursor,
logical attributes and nested UI context still belong to the caller; this code
does not consume global CSI cursor-save slots.

Additional verification:

```sh
./tools/dev --command python3 standalone/check_ui_flow.py
./tools/dev --command python3 standalone/check_ui_flow_original.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

All five linked CPU groups passed persistent/timed/suppressed branches,
maximum-fitting bottom-row text, legacy delay boundaries and actual CGA blank
and unblank instructions. The explicit clock fixture advances every three reads
and crosses ffff->0; the port fixture alternates 0/9 to supply retrace bits.
All **32 full-call-chain original/source comparisons passed**, comparing actual
video, ABI/preserved registers, timer read counts and CGA IN/OUT sequences for
all branches at top and bottom rows. Neither side substitutes text or timing
callbacks for the original code: only hardware clock/port values are fixtures.
The actual DOS self-check additionally uses live BIOS tick progress and verifies
that the persistent message survives the timed overlay and BIOS cursor stays
unchanged. New records are `flow-checks.json` and `flow-original-comparison.json`
under ignored `build/ui-windows/`.

For terminal integration, replace the three fail-fast service definitions with
these real exports, link all module sources and existing `text_fill_cells`,
`text_write_packed`/`text_cga_word`, and provide the five state words above.
The source module is complete for this original service. No shared terminal
files or root Makefile were edited in this recovery scope.
