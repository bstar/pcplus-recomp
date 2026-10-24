# Recovered high-level character renderer

The optional application parent now implements the historical `bb53` boundary
as [alternate field-cell output](ALTERNATE_OUTPUT.md), including bounded output
mapping and reset selection. It is a metadata/color operation. The unresolved
boundary list below describes this older standalone renderer checkpoint;
it does not establish font loading or the original font-resource format.

`reconstruction/render/character.asm` recovers the actual PCPlus resident
`0730..09b5` function: 646 bytes, with flat assembly checked against original
SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The routine now links with the recovered video writers, cursor services,
rectangle eraser and scrolling code in a source-only DOS executable.

```sh
./tools/dev --command python3 standalone/build_render.py
./tools/dev --command python3 standalone/check_render.py
./tools/dev --command python3 standalone/test_render_dos.py
```

The output `build/render/RENDER.EXE` writes actual text video memory, advances
the BIOS cursor, wraps at the last column and scrolls at the bottom margin.
Its DOSBox-X self-test checks the resulting video cells and cursor state.
The seven linked CPU regression groups additionally cover all 256 character
and attribute values, autowrap disabled, deferred/immediate wrapping, pound
and graphics-map selection, configurable translation, and two-cell lineflag
output through the real fill/packed writers. Unsupported features trap rather
than silently succeed. A separate source-only verification copied just source modules
and test harnesses into a temporary directory with no `analysis/` directory;
build, linked tests and the DOS self-test passed there as well.

For an optional analyst comparison using the ignored verified original:

```sh
./tools/dev --command python3 standalone/compare_render_original.py
```

This runs the original resident renderer, cursor, video and scrolling routines
against the linked source instructions with equivalent public host fixtures.
Ten scenarios (531 operations) compare the entire 4,000-byte screen, cursor/buffer/deferred-wrap
state and BIOS call records after every operation. No original executable is
read by the build or ordinary tests. Generated evidence is stored under
`build/render/`; a snapshot is recorded under `reconstruction/render/evidence/`.

## Entry ABI

Build the recovered source with `-DRENDER_OMF` and link export
`render_character`. It takes one word character argument at `[BP+4]`, returns
near, and **the caller cleans the argument**. It preserves BP/SI/DI, and may
clobber AX/BX/CX/DX/ES/flags. DS must equal SS for the recovered low-level
services' stack access through DS:BX; clear the direction flag before calling.
The test-only `render_test_character` wrapper reads `render_input_character`,
passes it to the original function, then cleans the stack.

The renderer intentionally preserves original behavior. In the color-mode
path a last-column write sets a deferred-wrap latch; the next character moves
or scrolls before being written. With autowrap off the next character replaces
the last cell. Other mode branches wrap immediately. The original lineflag
`40` path uses two cells; bit `02` selects two blank cells rather than a
character in the second cell. Glyph maps in tests are fixtures, not recovered
original font tables.

## DS symbols

All entries below are words except the translation mask and byte arrays.
Other existing `screen_*`, `attributes_*`, `ansi_charset_*` and erase/scroll
symbols retain their existing documented original addresses.

| Original DS offset | Symbol | Use observed in instructions |
| --- | --- | --- |
| `1d20` | `render_autowrap` | enables wrapping at last column |
| `1d22` | `scroll_enabled` | permits bottom-margin scrolling |
| `3340` | `scroll_suppress_next_linefeed` | one-shot linefeed state |
| `3342` | `csi_wrap_pending` | deferred wrap latch |
| `334a` | `csi_last_row` | physical last row bound |
| `372c` | `terminal_mode_372c` | nonzero invokes service `b9f7`; semantics unresolved |
| `372e` | `render_translation_enabled` | enables configured character lookup |
| `3736` | `erase_protection_mode` | selects alternate attribute/font path |
| `459b` | `render_graphics_map` | byte table base, indexed by character code |
| `9004` | `render_linefeed_suppression_enabled` | enables setting the linefeed suppression latch |
| `902d` | `render_translation_mask` | **byte** mask applied before lookup |
| `9036` | `render_translation_base` | near pointer to byte translation table |
| `9056` | `render_direct_output` | bypasses attribute-map rendering path |
| `cdfc` | `cursor_state_value_cdfc` | selects G0 mapping branches |
| `ce04` | `cursor_state_value_ce04` | selects G1 mapping branches |
| `d116` | `render_deferred_row` | row saved when deferred wrap was set |
| `d120` | `render_deferred_column` | column saved when deferred wrap was set |

`attributes_color_mode` and `screen_doublewidth_enabled` describe the same
original DS word at `d122` and must alias the same storage. The test host does
so explicitly. `terminal_mode_372c` must also alias any keyboard-mode symbol
for original DS `372c`; separate independent variables would be incorrect.

## Services and remaining gaps

These dependencies are actual recovered implementations in this diagnostic:

- `screen_set_cursor` (`1bbe`) and the real BIOS/direct cursor backend.
- `scroll_up` (`1fc4`) and its actual rectangle/attribute-plane operations.
- `text_write_cell` (`6c5e`), `text_write_char` (`6c84`),
  `text_write_packed` (`6cb4`) and `text_fill_cells` (`6c20`).
- `erase_previous_attribute` (`2d4c`) and its recovered dependencies.

The host deliberately traps these unresolved boundaries:

- `render_service_b9f7`: application overlay callback selected by DS `372c`;
  calling it is observed, but capture/insert semantics have not been proven.
- `render_font_output` (`bb53`): alternate output boundary; exact semantics
  remain unresolved beyond arguments and the selecting branch.
- `screen_adjust_attribute_boundary` (`2adc`),
  `erase_repair_attributes` (`2d98`) and complex protected erase (`d05f`).
- Viewport enter/leave/refresh (`482a`, `4850`, `2fb8`).

Configuration loading, original translation/font data, these specialized
branches and a complete terminal application remain unfinished. The renderer
diagnostic does not provide serial I/O or invoke the escape parser itself.

## Provenance

Retained REA/Ghidra assembly evidence:
`ev_9c6a5e39afa954b0ee6e1ccd4e0b1e9a0875c99f4ca252e5a1fa2e8cd62b53ec`.
Original file range is `1930..1bb5`; REA linear range is `10730..109b5`.
`provenance.json` records exact flat region hash, instruction count, named
state/services and limitations. Explicit analyst-only `recover.py` verifies
the original identity, disassembles the corroborated instruction range and
checks each encoding and the complete assembled result. It is never a normal
build dependency, and no new REA session was required for this saved evidence.
