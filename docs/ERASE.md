# Recovered erase and rectangle services

Twelve recovered routines now provide the actual PCPlus 2.01 line/display erase,
rectangle clear/scroll, video/shadow-memory and small attribute-plane helpers.
Flat assembly reproduces **1,456 original bytes**. OMF assembly links source-only
into `build/erase/ERASE.EXE`; normal builds/tests never read the original install,
executable, proprietary resource, or REA database.

These services are suitable for continued CSI J/K/X integration. They are not the
complete screen subsystem: complex protected erase and attribute repair remain
explicit external services, and not all wide-screen/video configurations have
been validated.

## Recovery evidence

The baseline SHA-256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resident offsets add `0x1200` for original file offsets. The three overlay routines
come from overlay 12, loaded at CS-relative `0xd0d0`, with original code file
offset 89,472 (`0x15d80`). Overlay bytes must be mapped through that context rather
than treated as resident data or sourced from a synthetic analysis executable.

| Source unit | Original CS-relative range, end exclusive | Bytes | Export/interface |
| --- | --- | ---: | --- |
| `line_before.asm` | `d844..d85e` | 26 | `csi_service_d844` |
| `display_before.asm` | `d85e..d8b5` | 87 | `csi_service_d85e` |
| `display_after.asm` | `d8b6..da11` | 347 | `csi_service_d8b6` |
| `rectangle.asm` | `2530..27e9` | 697 | `csi_service_2530` |
| `scroll_up.asm` | `6edc..6ef5` | 25 | `erase_scroll_up` |
| `scroll_down.asm` | `6ec2..6edb` | 25 | `erase_scroll_down` |
| `far_fill.asm` | `63fa..6412` | 24 | `erase_far_fill` |
| `far_move.asm` | `6412..644b` | 57 | `erase_far_move` |
| `move_bytes.asm` | `85b4..85fc` | 72 | `erase_move_bytes` |
| `default_attribute.asm` | `2d38..2d4c` | 20 | `erase_default_attribute` |
| `previous_attribute.asm` | `2d4c..2d6c` | 32 | `erase_previous_attribute` |
| `scan_attributes.asm` | `2d6c..2d98` | 44 | `erase_scan_attributes` |

`reconstruction/erase/provenance.json` records original file ranges, instruction
counts, region hashes and the DS/service symbol map. The assembly exports and
REA Evidence IDs used for corroboration are indexed under
[docs/evidence/erase](evidence/erase). No duplicate REA session was opened; this
pass reused saved resident and overlay-12 assembly evidence. Analyst-selected
routine names, boundaries and interpretations remain distinguished from original
source. The explicit `recover.py` analysis tool verifies the baseline identity,
rejects undecoded instructions, reassembles every instruction and verifies each
complete region. It is not a normal build dependency.

## Integration ABI

Assemble the twelve files with `-DERASE_OMF` and the UART encoding-macro include
path. Use near calls in real mode with **DS=SS**, DF clear on entry, valid screen
geometry and appropriately sized backing buffers. Callees may clobber
AX/BX/CX/DX/ES and arithmetic flags. The large rectangle and display-after
services preserve BP/SI/DI. The line-before helper has no such general register
preservation contract. Preserve live parser registers as its original callers do.

| Function | Inputs and cleanup | Recovered behavior |
| --- | --- | --- |
| `csi_service_d844` | None | Clear pending-wrap state and erase row start through cursor inclusive using configured normal attribute. |
| `csi_service_d85e` | None | Erase all rows before cursor, clear affected line flags when enabled, then call d844. |
| `csi_service_d8b6` | Word flag at SS:SP+2, `RET 2` | Erase cursor through line end; nonzero flag also erases following rows through the relevant bottom limit. Monochrome/current attribute and wrap/attribute modes affect attribute selection and metadata. |
| `csi_service_2530` | SS:SP+2 attribute, +4 packed bottom/right, +6 packed top/left, +8 signed scroll count; `RET 8` | Zero count clears inclusive rectangle; positive count scrolls up; negative count scrolls down. Packed positions use row in high byte, column in low byte. |
| `erase_scroll_up`, `erase_scroll_down` | Same four-word stack layout as rectangle; `RET 8` | Real INT 10h/AH=06h or 07h with count in AL, attribute BH, corners CX/DX; protect BP around BIOS call. |
| `erase_far_fill` | Count, packed attribute/character, destination offset, destination segment; `RET 8` | Swap AL/AH then actual REP STOSW to far memory. |
| `erase_far_move` | Word count, source offset, source segment, destination offset, destination segment; `RET 10` | Actual overlap-safe far REP MOVSW with backward-copy handling and CLD restoration. |
| `erase_move_bytes` | Destination offset, source offset, byte count; caller cleanup | Actual overlap-safe near move, preserving SI/DI; uses aligned word copies or backward bytes. |
| `erase_default_attribute` | None; returns AL | Select first cell's attribute when its protection flag bit 80 is set; otherwise configured fallback. |
| `erase_previous_attribute` | Cell offset; `RET 2`; returns AL | Obtain preceding cell attribute, or call default helper for zero offset. |
| `erase_scan_attributes` | Count, near flag-buffer pointer; `RET 4`; returns AX | Scan bit 80 over the supplied range; requires valid positive count. |

This layer does not sanitize arbitrary coordinates/counts. Recover caller
invariants or add explicit maintained guards before feeding untrusted values
directly. In particular, line-flag shifting in rectangle mode moves one row when
scroll count is nonzero; multi-row flag semantics are not proven. The scan helper
inspects at least one byte even for a zero count, so callers must provide the
expected positive range or deliberately fix the maintained path.

## Shared data and remaining services

Existing `screen_*` symbols from [SCREEN.md](SCREEN.md), `attributes_*` from
[ATTRIBUTES.md](ATTRIBUTES.md), and `csi_wrap_pending`/`csi_last_row`/
`csi_erase_attribute` from the dispatcher are reused. These additional DS names
are required; the diagnostic supplies synthetic data, never user configuration:

| Original DS offset | Symbol | Observed meaning |
| --- | --- | --- |
| `3260` | `erase_lineflags_enabled` | Enables per-row line flag clearing/shifting |
| `3736` | `erase_protection_mode` | Chooses metadata value written during certain erase paths |
| `325c` | `erase_cell_count` | End of attribute-plane cell range |
| `39c2` | `erase_attribute_values_base` | Near pointer to per-cell attribute values, paired with `screen_attributes_base` flag plane |
| `5dea`, `5dec` | `erase_shadow_offset`, `erase_shadow_segment` | Far pointer to backing/shadow character/attribute words |

When horizontal viewport mode is enabled, rectangle code can fill or move actual
shadow memory and decide which visible subrectangle also needs BIOS output.
The recovered code includes both memory operations and BIOS calls; it does not
replace the viewport with an empty callback. Wider geometry and adapter variants
still need runtime fixtures.

Two services remain unresolved:

- `erase_complex_protected`, original call at `d05f`: one word argument, caller
  removes two bytes. Selected by wrap mode plus the attribute-check flag.
- `erase_repair_attributes`, original `2d98`: one word selector, callee removes
  two bytes. Recomputes display/attribute state after some metadata erasures;
  its larger call chain is not reconstructed here.

The diagnostic deliberately traps if either is invoked. These traps make missing
behavior visible and must be replaced by recovered services for application
integration. They are not implementations or accepted compatibility substitutes.

## Verification

```sh
./tools/dev --command python3 standalone/build_erase.py
./tools/dev --command python3 standalone/check_erase.py
./tools/dev --command python3 standalone/test_erase_dos.py
```

Seven linked-instruction regression groups pass: inclusive rectangle bounds and
outside preservation; positive/negative scroll counts; before-cursor line/display
erase; after-cursor erase and monochrome attributes; overlapping line-flag moves;
invisible viewport shadow fill without visible writes; and attribute-plane updates
with an explicit unresolved protected-path check. The CPU harness models INT 10h
text-video operations and records actual register arguments from the recovered
BIOS wrappers. It is a declared model, not proof of a real video adapter.

The independent DOSBox-X self-check uses the actual BIOS: fill video memory with a
pattern, clear a rectangle through the recovered routine, verify erased cells
and unchanged neighboring cells in B800 memory, then return to DOS. It passes.
`build/erase/{manifest,checks}.json` and `build/erase-dos/result.json` identify the
exact tested executable and scope. This does not validate all CPU-test cases in
DOSBox or physical display hardware.

An optional baseline audit reads the ignored original separately:

```sh
./tools/dev --command python3 standalone/check_erase_flat.py
```

All 1,456 flat bytes match. The combined CSI diagnostic also checks parser-driven
J/K/X display updates, including a real DOSBox BIOS clear of all 2,000 cells.
Remaining work includes complete protected attribute repair, caller bounds and
invariants, wide-screen/adapter behavior and DOS hardware verification.
