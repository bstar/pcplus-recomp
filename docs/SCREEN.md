# Screen cursor recovery

The later [viewport pane component](VIEWPORT_PANES.md) recovers the external
enter/leave services and joins them to these actual cursor instructions in an
optional reset diagnostic. Live width/allocator/renderer admission remains open;
the original cursor-only diagnostic below retains its explicit boundaries.

Eight resident routines are recovered as editable assembly in
`reconstruction/screen`. Their flat builds reproduce **662 bytes** of the selected
PCPlus 2.01 executable exactly. Symbolic OMF builds link into an independent DOS
cursor diagnostic without reading an original executable, install, REA export or
database. Names are analyst annotations, not original source symbols.

This is actual cursor state/output logic, including BIOS and direct CRTC paths.
It does not yet implement a complete screen renderer, scrolling, erase, wide-screen
viewport management, or attribute-boundary correction.

## Provenance

Baseline SHA-256:
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The resident file offset equals the CS-relative offset plus the 4,608-byte MZ
header. There are no data blobs copied from the original into the source build.
Register-direction encoding macros preserve original instruction encodings in
flat mode; symbolic references provide normal OMF relocations in linked mode.

| Routine | CS-relative range, exclusive end | Bytes | REA assembly Evidence |
| --- | --- | ---: | --- |
| `screen_set_cursor` | `1bbe..1c66` | 168 | `ev_aaf0a7b601d063e49c83675634b1c652248984c52cb0bf936b9c00ea6b3441dc` |
| `screen_cursor_down` | `1e0c..1e2f` | 35 | `ev_36bcdcb66a1f6c1f42c50bf203bad7d8b7c5dc8b94308777a7f1e0c5f6f524e6` |
| `screen_cursor_left` | `1e30..1e9f` | 111 | `ev_31486d857089dd1db369ef58b76d07aa297197e5317d002a29b44db1e402399f` |
| `screen_cursor_right` | `1ea0..1efc` | 92 | `ev_32c27faac667dd9d501121217a85874bfce66dcc80d96d8a9c643a2db97f7fe3` |
| `screen_cursor_up` | `1efc..1f55` | 89 | `ev_53f8a040f197a83d7b88f457f5b9fff0f9eb71da1bf31ab883bcd4da7ce127ea` |
| `screen_width_transition` | `2a90..2adc` | 76 | `ev_6f5ae57785d56c66d9dfabb99d6e79cb3ddf183af82b45c136eb23c680daaec0` |
| `screen_cursor_pack` | `6e66..6e77` | 17 | `ev_ccca30728799396078bbdb4e145ac477ebcc51ebb7f663b2742895607ef582a4` |
| `screen_cursor_output` | `6e78..6ec2` | 74 | `ev_ccfc95f44a132e4a754ba00110f40de185308bc9ca2192e4365298347c2871af` |

The original resident exports are local ignored artifacts under
`analysis/pcplus-main/functions`. `reconstruction/screen/provenance.json` records
unit hashes and the full original-address-to-symbol map. The explicit recovery
script reads only the verified baseline and rejects undecoded instructions or
nonmatching assembly; it is an analysis tool, never a normal build dependency.

## Calling convention and state

Use near calls in 16-bit real mode, with **DS=SS**. `screen_set_cursor` takes AX=row,
DX=column and preserves SI/DI. It updates state and invokes the recovered hardware
cursor service. The four direction entrypoints take no arguments. Their return AX
is not a documented result; AX/BX/CX/DX/ES and arithmetic flags may be clobbered.
Do not assume these services preserve machine flags or video registers.

`screen_cursor_pack` takes column at SS:SP+2 and row at SS:SP+4 and removes both
words (`RET 4`). It packs their low bytes into DX through AX and calls
`screen_cursor_output`, which takes the packed word at SS:SP+2 and removes it
(`RET 2`). `screen_width_transition` takes signed row displacement at SS:SP+2,
removing that word. Callers must maintain valid row/column bounds and initialized
screen geometry; `screen_set_cursor` does not clamp arbitrary inputs.

| Original DS offset | Linked symbol | Observed role |
| --- | --- | --- |
| `399c`, `399e` | `screen_cursor_row`, `screen_cursor_column` | Current row and column |
| `39a0`, `39a2`, `3348` | `screen_visible_column`, `screen_previous_row`, `screen_previous_column` | Previous positions used to update buffer offsets |
| `3344`, `3346` | `screen_video_offset`, `screen_attribute_offset` | Incremental video/attribute-plane offsets |
| `7a7a`, `325a` | `screen_video_row_bytes`, `screen_attribute_row_bytes` | Row strides |
| `ceb0`, `cee4` | `screen_top_margin`, `screen_bottom_margin` | Single-step up/down boundaries |
| `ce0e`, `ce3a`, `3258` | `screen_first_row`, `screen_last_row`, `screen_last_column` | Reverse-wrap and right-edge bounds |
| `cf86` | `screen_line_flags` | Per-row byte flags, bit `40` changes horizontal step/width transitions |
| `d122` | `screen_doublewidth_enabled` | Enables row-width adjustment during vertical movement |
| `900c`, `9038` | `screen_cursor_wrap`, `screen_reverse_wrap_blocked` | Wrap control and reverse-wrap inhibition |
| `cdfa`, `3256`, `39a4` | `screen_viewport_enabled`, `screen_viewport_active`, `screen_viewport_offset` | Horizontal viewport state |
| `ce2e`, `7a7e` | `screen_viewport_left`, `screen_viewport_right` | Viewport thresholds |
| `3734`, `9018`, `39c4` | `screen_attribute_checks`, `screen_vertical_attribute_check`, `screen_attributes_base` | Optional attribute-cell boundary checks and near buffer pointer |
| `7a66`, `7a72` | `screen_use_bios_cursor`, `screen_columns` | BIOS/direct-output selection and columns (read as a byte for hardware-position multiplication) |

BIOS output uses INT 10h/AH=02h with page zero. Direct output stores DX at BIOS
Data Area `0040:0050`, derives character position using `screen_columns` and BDA
`0040:004e`, then writes CRTC registers 0Eh/0Fh through the port in `0040:0063`.
The tests verify these exact accesses; this is not physical adapter validation.

## Unresolved service boundaries

The OMF objects intentionally leave these as external symbols:

| Symbol | Original call | Required behavior/ABI |
| --- | --- | --- |
| `screen_viewport_enter` | `482a` | No stack arguments; called before activating the left viewport. Full behavior not recovered here. |
| `screen_viewport_leave` | `4850` | No stack arguments; called before restoring viewport offset. Full behavior not recovered here. |
| `screen_viewport_refresh` | `2fb8` | No stack arguments; refresh after viewport transition. Full behavior not recovered here. |
| `screen_adjust_attribute_boundary` | `2adc` | First stack argument is attribute-plane offset, second direction/selection flag; removes four argument bytes. Called for tested cell bits `81`. The standalone screen diagnostic retains an explicit callback boundary; the application now uses the recovered [attribute-boundary scanner](ATTRIBUTE_BOUNDARY.md) through checked far bridges. |
| `screen_wrap_forward` | `12c8` | No arguments; original sets column zero and branches into line-advance logic at `1d88`, including scrolling dependencies. |

The diagnostic links **fail-fast trap boundaries** for those five services. They
are not screen implementations, and integration must replace them with real
recovered services. Tests prove optional dependency paths remain visible rather
than silently succeeding. The ordinary 80-column bounded cursor cases do not
invoke them. No caller should enable a feature whose required service is absent.

An inherited edge case is now characterized: in a row with line-flag bit 40 set,
left movement from odd column 1 subtracts two and stores `ffff`. The original
routine assumes an alignment invariant or lacks a guard. This pass preserves the
baseline exactly and records the underflow; it has not established the original
caller invariant or implemented a maintained fix. The caller/parser must resolve
that issue before arbitrary untrusted coordinates reach this path.

## Build and validation

```bash
./tools/dev --command python3 standalone/build_screen.py
./tools/dev --command python3 standalone/check_screen.py
./tools/dev --command python3 standalone/test_screen_dos.py
```

Output is `build/screen/SCREEN.EXE`, a DOS diagnostic. Build inputs are recovered
assembly, encoding macros, the diagnostic host, NASM and the Nix-managed linker.
The seven linked CPU regression groups cover absolute buffer offsets and BIOS
positions; all four directions and margins; double-width row steps/transitions;
the inherited odd-column underflow; reverse-wrap plus explicit forward-wrap
dependency; explicit viewport dependency; and direct CRTC/BDA output. The small
DOSBox-X self-check independently exercises cursor positioning, right/down
movement and DOS exit. It does not cover every CPU-replay scenario in DOSBox.

An optional baseline audit requires the ignored original, separately from the
source-only build:

```bash
./tools/dev --command python3 standalone/check_screen_flat.py
```

Local `build/screen/{manifest,checks}.json` and `build/screen-dos/result.json`
identify exact tested binaries and scopes. The current 662-byte flat audit,
seven CPU groups, and DOSBox-X smoke all pass. Remaining work is real viewport,
attribute-boundary, wrap/scroll services, screen rendering, and maintained bounds
checks informed by original caller invariants; then full ANSI integration and
DOS/hardware display validation.
