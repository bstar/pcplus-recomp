# Recovered CSI mode handlers

`reconstruction/modes/core.asm` recovers the actual PCPlus 2.01 overlay-12 set
and reset routines at CS:de98..df7d and df7e..e083: **492 exact original bytes**,
including two 25-entry jump tables and nine alignment NOPs omitted from the
function Listing. Each flat region is checked against its stored SHA-256.
`provenance.json` retains original identity, offsets, REA Evidence IDs, table
entries and state/service mappings. Names are analyst annotations.

OMF builds replace both CS table displacements, every jump-table word and all
DS references with relocatable linker symbols. Independent code/data padding
regressions verify this rather than relying on the original address layout.
Normal builds read no original executable or analysis database.

## Integration ABI and dependencies

Assemble with `-DMODES_OMF` and the UART include directory. Exports
`csi_set_modes()` and `csi_reset_modes()` are near, no-argument entries. They
preserve SI/DI and rely on the small-model DS=SS invariant and ordinary BP-preserving
callee conventions. AX/BX/CX/DX/ES and flags may be clobbered by their services.
The caller supplies the validated `ansi_parameters` word array and signed
`ansi_parameter_count`; the original loop has no independent capacity bound.
The maintained parser currently limits this array to sixteen entries.

| External service | Original CS | ABI and recovery boundary |
| --- | --- | --- |
| `screen_set_cursor` | 1bbe | AX=row, DX=column; actual recovered screen code is linked in this diagnostic. |
| `modes_keyboard_map` | 0b4e | One word, caller cleanup; mode1 passes 4fh on set, 5bh on reset. Keyboard-map mutation remains external to this unit. |
| `modes_screen_width` | 2a6e | One word, **callee cleanup RET2**; private mode3 passes 1/0. Full reset/geometry side effects remain external. |
| `csi_reset_terminal` | 20a4 | One word, caller cleanup; private mode2 reset passes 1 after changing terminal IDs. |
| `screen_viewport_refresh` | 2fb8 | No arguments; invoked by mode12 branches. Full refresh behavior remains external. |
| `modes_cursor_shape` | 2f78 | One word, caller cleanup; passes the updated cursor-flags word after changing low-byte bit04h. |

The source-only host **traps unresolved effects**, records their call address and
argument, and never silently returns success. Existing optional screen viewport,
attribute-boundary and wrap dependencies also trap if reached. Integration must
replace these boundaries with real recovered or maintained implementations.

## Observed mode behavior

A nonzero `csi_report_private_prefix` at original DS:904c disables both entire
handlers. Nonpositive signed parameter counts return immediately. Otherwise each
parameter is processed in order. Unknown values are ignored.

| Mode | Set | Reset |
| --- | --- | --- |
| 1 | Keyboard-map helper with 4fh | Keyboard-map helper with 5bh |
| 2 | Ignored | With private flag: saves terminal ID, sets ID1, invokes terminal reset(1) |
| 3 | With private flag: screen-width helper(1) | With private flag: screen-width helper(0) |
| 4 | With private flag clear: DS372c=1 | With private flag clear: DS372c=0 |
| 6 | Sets origin mode/margins and homes at scroll-top,column0 | Clears origin mode, uses full last row, homes at row0,column0 |
| 7 | DS1d20=1 | DS1d20=0 and wrap-pending=0 |
| 12 | DS1d1a=0 then refresh | With private flag clear: DS1d1a=1 then refresh |
| 18 | DS3980=1 | DS3980=0 |
| 19 | DS3982=0 | DS3982=1 |
| 25 | Sets low-byte bit04h of DS333e, invokes cursor-shape helper | Clears that bit, invokes same helper |

Mode6 is not locally gated by the private flag. Mode12's asymmetric private
check is preserved. Mode4's shared DS372c also affects the renderer and follows
the keyboard-map storage region; its complete semantics are unresolved. The
neutral `terminal_mode_372c` alias avoids claiming a complete insertion or capture
implementation from this branch alone.

Canonical state mapping:

| Original DS | Symbol |
| --- | --- |
| 904c | `csi_report_private_prefix` |
| cb3c, cb5c, ceac | `ansi_parameters`, `ansi_parameter_count`, `ansi_private` |
| ce0e, ce3a | `csi_scroll_top`, `csi_scroll_bottom` (screen first/last row aliases) |
| ceb0, cee4 | `csi_origin_row`, `csi_origin_bottom` (screen top/bottom margin aliases) |
| cdd2, 334a, 3342 | `csi_origin_mode`, `csi_last_row`, `csi_wrap_pending` |
| 1d18, 321e | `csi_terminal_id`, `csi_previous_terminal_id` |
| 1d20 | `cursor_state_value_1d20`, retaining the existing cursor-state alias |
| 372c | `terminal_mode_372c` |
| 1d1a, 3980, 3982 | `modes_value_1d1a`, `modes_value_3980`, `modes_value_3982` |
| 333e | `modes_cursor_flags` (word, with low-byte bit operations) |

## Verification

```sh
./tools/dev --command python3 standalone/build_modes.py
./tools/dev --command python3 standalone/check_modes.py
./tools/dev --command python3 standalone/check_modes_relocation.py
./tools/dev --command python3 standalone/test_modes_dos.py
```

Four linked CPU regression groups cover direct states and private gates, actual
mode6 cursor/margin updates, signed count/processing gates and sixteen-entry
iteration, and every unresolved mode-effect boundary with original arguments.
Three relocation cases independently shift code/data by (0,0), (137h,251h) and
(2137h,1234h), exercising both tables, immediate parameter pointers, state writes,
real screen calls and an explicit dependency trap.

`MODES.EXE` runs under DOS and checks mode7 set/reset and mode6 set/reset. It
queries the actual BIOS cursor with INT10h/AH03h to verify row4 then row0, both
column0, rather than checking only internal variables. DOSBox-X passes this
self-check. This does not establish physical hardware or full terminal behavior.

Optional original comparison:

```sh
./tools/dev --command python3 standalone/check_modes_original.py \
  --original /path/to/PCPLUS-main-2.01.EXE
```

**136 original/source comparisons pass** for modes0..27 and ffffh, both private
states, both handlers, mixed/sixteen-item/empty lists, negative count and the
DS904c processing gate. The test compares actual original/source state changes
and BIOS cursor calls; at unresolved effects it compares the call boundary and
argument and **stops before executing that external service**. It therefore proves
the handler's routing and preceding state, not completion of those side effects.
This optional comparison uses ignored local original/overlay artifacts. Build
and test results retain exact executable hashes under `build/modes/`,
`build/modes-relocation/` and `build/modes-dos/`.

The combined CSI diagnostic now links these handlers and shared DS aliases.
Its `modes_keyboard_map` interface tail-jumps to the real recovered
`terminal_keyboard_mode`, preserving caller cleanup. Persistent parser-driven
DECCKM tests verify four arrow bindings and the final key slot change between
ESC `[` and ESC `O`, while custom/longer bindings and the adjacent DS372c word
remain unchanged. Tests also verify the keyboard-enable gate, private mode state,
mode6 origin/homing and explicit failures at remaining mode-effect boundaries.

The combined DOS self-check parses private mode1 set/reset and checks its real
arrow-table mutation; it also parses mode7 and mode6 set/reset, reading the
actual BIOS cursor at origin row4 then row0. The existing terminal-services and
combined code/data relocation regressions pass after this integration.

Mode25 is also closed in the combined diagnostic: `modes_cursor_shape` links the
actual recovered 120-byte cursor-shape module, with shared start/end scanline and
visibility words. Persistent parser tests verify block, half-height and underline
shapes, hide/show transitions, preserved high flag bits and the signed show gate
through BIOS AH01h. The BIOS test model deliberately clobbers BP to verify the
original wrapper protects it. The combined DOS executable independently reads
back actual BIOS block/hidden/half/underline scanline settings with AH03h. The
standalone MODES executable still intentionally traps this external dependency;
the separate cursor-shape diagnostic and combined build execute its real code.
Full geometry/reset/refresh service closure, outbound key selection, ordinary
text rendering and physical modem validation remain separate work.
