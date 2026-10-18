# Recovered character editing and tab stops

This module recovers **1,095 exact original instruction bytes** from the verified
PCPlus2.01 executable SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
It is recovered assembly with analyst names, not the vendor's source. Normal
builds use maintained source and public hashes only, without originals, install
files, private settings or a REA database.

| Original CS range, exclusive end | Bytes | Export | Actual operation |
|---|---:|---|---|
| d270..d440 | 464 | `csi_insert_character` | Insert one blank cell, shifting following cells right |
| d440..d668 | 552 | `csi_delete_character` | Delete one cell, shifting following cells left |
| dac6..daf2 | 44 | `terminal_set_tab` | Set tab stop using the original30-byte table algorithm |
| 77ae..77bd | 15 | `character_cga_restore` | Restore CGA display control when status port configured |
| 77be..77d2 | 20 | `character_cga_disable` | Wait vertical retrace and disable CGA display during movement |

The original CSI dispatcher maps **@** to d270 and **P** to d440, clears deferred
wrap before either, and repeats the helper using its signed16-bit parameter
loop. Helpers themselves do not interpret counts or scrolling margins. They
edit only the current row from the cursor to the effective right boundary,
without moving the cursor. Existing ESC dispatch calls dac6 for **ESC H** and
C1 **HTS88**. The recovered SETTAB routine is separate from character shifting.
No live application boundaries or dispatcher source are changed by this module.

## Original behavior and limits

Normal insertion preserves the attribute already at the cursor while blanking
its character byte; whole following character/attribute cells shift right.
Deletion shifts whole cells left and fills the last cell with a space and the
configured normal attribute. At the last column, insertion simply blanks it
and deletion fills it. The d440 helper itself clears deferred-wrap state;
d270 relies on its dispatcher caller for that reset.

Row flag `screen_line_flags[row] & 0x40` changes video movement to **two cells**.
Valid doublewidth cursor positions are even and end at physical column78 on an
80-column screen. The exact original helper does not validate malformed odd or
out-of-range cursor/width state. The tests exercise valid0/16/78 positions.

When `screen_attribute_checks` is nonzero, the helpers scan the metadata plane
for the next flag with bits`0x81`. A protected current cell produces no change;
a later protected cell bounds the editable span and is preserved. This is
actual selective behavior, not a blanket no-op for all protected mode.

With `screen_cursor_wrap` nonzero and protection checking off, both helpers also
shift the parallel flag and attribute-value planes. Their metadata movement is
one byte per step even in doublewidth video mode; bit0 is cleared at the newly
blank logical position. Delete preserves the original current flag's bit`0x80`
and calls **erase_repair_attributes2d98** if it was set. That complex repair
remains an explicit external dependency and diagnostic trap. Character edits
can already have occurred when it is reached; this exact module does not claim
transactional failure. The live caller must decide which unsupported attribute
states it accepts before calling it. Neither helper directly calls d05f.

Active viewports use the actual far shadow buffer and visible video memory.
The source-only tests cover a132-column logical row with80 visible columns,
including moving the boundary cell between video and the right shadow area.
They do not recover viewport selection/UI or validate arbitrary corrupt layouts.
The helpers invoke the actual overlap-safe far word mover and near byte mover;
no copy service is replaced with a test no-op.

Configured CGA status port0 bypasses CGA I/O. At3da, the actual helper waits for
retrace, writes25 to3d8 before moving cells, then2d afterward. Character-byte
writes use the already recovered text writer and its actual CGA synchronization.
The CPU oracle models status-bit transitions and observes those output ports.
This is not physical CGA timing validation.

SETTAB searches30 byte slots using the low byte of the cursor column. Existing
equal stops do nothing. Otherwise it **replaces the first larger stop**, rather
than shifting later stops to insert a new array element. If that slot is29, it
writes slot28. If all30 stops are smaller, it does nothing. The existing FE
sentinel and this historical replacement behavior are preserved; the helper
must not be described as an improved or standards-normalized tab editor.

## ABI and integration

Assemble with `CHARACTER_EDIT_OMF` for named near services/data; without it each
file assembles at its original address and must match its public byte hash.
Use DS=SS for recovered stack argument access. The entry helpers take no stack
arguments. BP/SI/DI are preserved; AX/BX/CX/DX/flags and **ES may change**. A live
wrapper needing ES preservation must save it explicitly. State uses existing
canonical names and addresses:

| Original DS | Canonical symbol |
|---|---|
| 3342 | csi_wrap_pending |
| 3344 /3346 | screen_video_offset /screen_attribute_offset |
| 399c /399e | screen_cursor_row /screen_cursor_column |
| 3258 | screen_last_column |
| cf86 | screen_line_flags |
| 3734 /900c | screen_attribute_checks /screen_cursor_wrap |
| 39c4 /39c2 | screen_attributes_base /erase_attribute_values_base |
| 3256 /7a7e /7a72 | screen_viewport_active /screen_viewport_right /screen_columns |
| 5dea /5dec | erase_shadow_offset /erase_shadow_segment |
| 7a78 /7a8e | text_video_segment /text_cga_status_port |
| 1d32 | attributes_normal_value |
| ce10 | terminal_tab_stops |

Real external services are `erase_far_move`6412, `erase_move_bytes`85b4,
`text_write_char`6c84 and the explicit `erase_repair_attributes`2d98 dependency.
Reuse existing state storage for these aliases; they must not be duplicated.

## Evidence and verification

`reconstruction/character_edit/provenance.json` records original file offsets,
unit hashes, exact-byte checks and retained REA evidence IDs. d270/d440 and CGA
helpers use saved REA exports. Default Ghidra analysis had not decoded tiny
dac6, so a focused static analysis container changed only MZ CS:IP to0:dac6;
its code bytes stayed unchanged and were independently checked against the
verified original. This analysis container was **never executed**. REA evidence
`ev_32fb43d0a78a295d9dbeb716ca6b10c37bbcfecd663d7595fc72b6ba20bad5d7`
confirms the44-byte helper; containers and raw exports stay ignored.

```sh
./tools/dev --command python3 standalone/build_character_edit.py
./tools/dev --command python3 standalone/check_character_edit.py
./tools/dev --command python3 standalone/test_character_edit_dos.py
# Explicit analyst check using the ignored verified original and overlay map:
./tools/dev --command python3 standalone/check_character_edit.py --original
```

Seven CPU groups contain **43 cases**, each matched against actual original
instructions when `--original` is selected: row/border cells, valid doublewidth,
protected current/neighbor cells, both metadata planes including doublewidth,
132-column right shadow transfer, CGA port paths and tab edge cases. A separate
explicit trap verifies the unresolved attribute repair is not hidden. Only
BIOS/CGA hardware is modeled. Public default tests do not read original bytes.

Actual DOSBox-X8086 self-checks verify insertion/deletion video cells and SETTAB.
Diagnostic `CHAREDIT.EXE` SHA256:
`ff8c65cea099092ba50908d0b6b4e5bb1901509b9303b744ee0191f7bcaa82f6`.
This module does not claim full terminal compatibility, UI, corrupt-state safety,
physical hardware behavior or a complete PCPlus application rebuild.

## Maintained live integration

`src/terminal/character_edit.asm` supplies the actual application services for
d270/d440/dac6 using the recovered helpers. The live renderer currently uses a
fixed80x25 direct video plane; the wrapper validates row/column bounds, strides,
video and metadata offsets, the video segment and zero viewport offset before
editing. Unsupported viewport geometry is a bounded no-op. Valid doublewidth
edits require even cursor positions and a complete final two-cell pair. These
checks are maintained application policy; the flat recovered bytes stay exact.

The wrapper bounds the existing dispatcher's repetition count to the remaining
physical cells (or complete doublewidth pairs). Omitted, zero and signed
high-bit parameters retain the existing one-operation behavior. An invalid
layout also normalizes the parser count to1, preventing a32767-iteration no-op
loop. Character editing remains independent of vertical scrolling margins.

Known metadata planes are allowed, including the actual protected-cell scan.
The wrapper checks that their near bases name the application's allocated
buffers. Before an unprotected attribute-plane deletion, it conservatively
checks **the entire remaining row span** for bit80, rejecting it through the
explicit2d98 boundary before moving any cells or metadata. Scanning only the
first deleted byte would allow a later repeated helper to fail after partial
mutation. This preflight also rejects flagged tail bytes beyond the requested
count; it is intentionally conservative until2d98 is recovered. Insert does
not invoke that repair. Protected-mode deletion uses its actual bounded scan
and skips repair exactly as the recovered helper does.

All three live wrappers preserve BP/SI/DI and the caller's arbitrary ES value.
SETTAB retains the native replacement algorithm after validating the live
column geometry. Both CSI bindings and ESC H are linked through actual
application dispatch; no boundary returns a pretend success instead of calling
its helper.

```sh
./tools/dev --command python3 standalone/check_character_edit_live.py
```

On terminal SHA256
`36b14af2281a4921c0da210cfb3ceed22c3c33d82c9b40f2877850bea169d5f4`,
**nine linked CPU groups pass** using real UART IRQ/input/CSI/ESC, wrappers,
native character operations and video/move helpers. Only BIOS video/keyboard,
UART registers and ticks are modeled. Tests cover both profile gates, borders,
large counts, doublewidth pairs, vertical-margin independence, invalid geometry,
metadata shifts, preflight failures at current/middle/tail positions with no
partial mutation, protected boundaries, HTS and arbitrary ES4321 restoration.
Evidence is `build/terminal/character-edit-live-checks.json`. This is CPU-linked
integration evidence; actual BBS/editor and physical hardware validation are
separate scopes.
