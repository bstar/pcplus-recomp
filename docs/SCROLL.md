# Recovered scrolling, linefeed and index

Five actual PCPlus 2.01 routines now assemble exactly to **491 original bytes**
and link with the recovered cursor/erase modules into source-only
`build/scroll/SCROLL.EXE`. The independent executable never reads an original
installation or REA database. It scrolls actual video memory through recovered
rectangle services and BIOS calls; wrapping and cursor movement use the real
recovered cursor code.

| Original CS-relative range | Export | Bytes |
| --- | --- | ---: |
| `12c8..12d1` | `screen_wrap_forward` | 9 |
| `1d88..1e0c` | `screen_linefeed` | 132 |
| `1fc4..20a3` | `scroll_up` | 223 |
| `da46..da84` | `scroll_index` | 62 |
| `da84..dac5` | `scroll_reverse_index` | 65 |

The first three ranges are resident; original file offsets add `0x1200`.
Index/reverse-index belong to overlay 12, whose source bytes begin at file
89,472 and CS-relative `d0d0`. `provenance.json` records file ranges and hashes.
The verified source executable SHA-256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The explicit analyst-only `recover.py` decodes each instruction and verifies exact
complete-unit assembly, with no undecoded-code fallback. It is not a normal build
step.

Saved REA assembly Evidence:

- Wrap: `ev_55612f601d77a839f92890d19e838d8e2a739b42c456fb3a23e86aea410395d0`.
- Linefeed: `ev_e574bf63a901163f987c1cc050ff64f41f0f23d0a6b3d9d765973677c2a85086`.
- Scroll: `ev_b48bd720c4333b6eab57e3d717cf42132b05f46481ef95b0b02f241ad5d86173`.
- Reverse index: `ev_4f2fe6ba4d4a21abd3207e0dc32b64ef0cdc868c4aac86307a9b4371bac90846`.

Index at da46 was decoded directly from the verified original overlay because
there is no separate saved REA export at that entry. Names/roles are analyst
annotations; static exports do not themselves establish runtime behavior.

## Integration

Use `-DSCROLL_OMF`, the UART encoding macros, and the existing screen/erase objects.
All five exports take no arguments and return near. DS must equal SS, DF must be
clear, and callers must supply valid geometry and initialized cursor/attribute
buffers. Volatile registers include AX/BX/CX/DX/ES and flags. Scroll-up preserves
BP/SI/DI; linefeed preserves SI and uses the cursor services' preservation rules.
Index/reverse-index do not generally preserve volatile registers.

Wrap-forward zeroes the current column then jumps into linefeed. Linefeed consumes
a one-shot suppression flag, advances a row, performs configured bottom scrolling
or terminal wrapping, adjusts double-width coordinates, updates hardware cursor,
and optionally invokes attribute-boundary correction. Scroll-up clears pending
wrap, chooses the fill attribute, scrolls the active rectangle up one line and,
in its alternate mode, shifts the flag/value planes and clears/fills their final
row. Its plane movement covers the configured whole cell buffer, so nonzero
scroll-region interactions with that mode need further validation.

Index advances or scrolls at the bottom margin. Reverse-index decrements or
scrolls down at the top margin. Both use the configured erase attribute and retain
the column. Unlike linefeed's configured-scroll switch, these original ANSI
entrypoints invoke rectangle scrolling directly at their respective boundaries.

New state aliases are `scroll_enabled` (DS `1d22`),
`scroll_suppress_next_linefeed` (`3340`), and `scroll_skip_attribute_scan` (`904c`).
The latter is the **same original word** as `csi_report_private_prefix`; combined
hosts must alias both names rather than allocate two independent variables.
Existing `screen_*`, `erase_*`, `csi_wrap_pending` and `csi_last_row` state is
shared with the documented cursor/erase modules.

Dependencies are actual `screen_set_cursor`, `screen_width_transition`,
`csi_service_2530`, `erase_previous_attribute`, `erase_scan_attributes` and
`erase_move_bytes`. Optional `screen_adjust_attribute_boundary`, viewport helpers,
and `erase_repair_attributes` remain unresolved. The diagnostic traps at these
boundaries; they are not no-op implementations. The original routines assume
valid caller row/column/margin invariants and do not generally clamp malformed
positions. Suppressing linefeed after wrap-forward can change the column without
running cursor-offset synchronization; preserve/understand original caller state
rather than treating arbitrary combinations as a valid API.

## Verification

```sh
./tools/dev --command python3 standalone/build_scroll.py
./tools/dev --command python3 standalone/check_scroll.py
./tools/dev --command python3 standalone/test_scroll_dos.py
```

Seven linked CPU groups pass: linefeed/wrap/suppression; bottom-scroll enable and
wrap modes; index/reverse-index regions and outside preservation; fill attributes;
actual overlapping flag/value-plane moves and final-row fill; explicit required
attribute-repair failure; and double-width transitions/ABI. CPU tests use a stated
BIOS text-video model. The DOSBox-X self-check independently verifies actual BIOS
video-memory scrolling, reverse-index, wrapping and DOS return. It does not cover
all CPU replay cases or physical adapters.

`build/scroll/{manifest,checks}.json` and `build/scroll-dos/result.json` retain exact
binary identities/scopes. Optional `standalone/check_scroll_flat.py` verifies all
491 baseline bytes separately and requires the ignored original. Remaining work
is full renderer/parser integration, protected-attribute/viewport services,
caller bounds/invariants, additional video modes and DOS hardware validation.
