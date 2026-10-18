# Recovered BIOS cursor shape and visibility

Four actual PCPlus 2.01 resident routines now assemble exactly to **120 original
bytes** and link into source-only `build/cursor-shape/CURSOR.EXE`. This closes the
BIOS cursor service dependency used by CSI mode 25. There are no unresolved
callbacks in this module: it invokes real INT 10h/AH=01h through the recovered
helper, with BP protected around the BIOS call.

| Original CS range, exclusive end | Export | Bytes | REA assembly Evidence |
| --- | --- | ---: | --- |
| `2f78..2fb8` | `modes_cursor_shape` | 64 | `ev_f380f92cab70637bdee46ef1adb1c9e982d1676e95b79c7b9f36a4c811103a6e` |
| `6dca..6ddd` | `cursor_shape_show` | 19 | `ev_3199e8f2bcb62ef528f8faca949641f3c6de62610a8d1903c942d92da6bceb54` |
| `6e5a..6e66` | `cursor_shape_hide` | 12 | `ev_cdb63f3a18dae162386a6147b76290e018ab9c109d05c5d919872b12acd47f3b` |
| `7e58..7e71` | `cursor_shape_bios` | 25 | `ev_0311d0f14fadc8b6c7522791a0b84593e92eec3d8a147d88629ff3cd9b0449c4` |

Baseline SHA-256:
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Original file offsets add `0x1200` to these resident offsets. The source provenance
file records ranges, hashes and symbolic state. Saved REA resident exports were
reused; no duplicate native session was opened. The explicit analyst-only
`recover.py` rejects undecoded code, verifies each encoding and validates the
complete assembled ranges. Normal builds do not read originals or generated
analysis databases. Names and interpretations are analyst annotations.

## Integration ABI and state

Assemble all four source files with `-DCURSOR_SHAPE_OMF` and the existing UART
encoding-macro include directory. `modes_cursor_shape` takes one word at SS:SP+2;
**the caller removes the argument**. It returns near and preserves BP/SI.
AX/BX/CX/DX and flags may be clobbered. Use the project's DS=SS convention.
Show/hide helpers take no arguments. The internal BIOS entry expects BL=0 for
show or BL=1 for hide, and combines that selection with the configured scanlines.

| Original DS offset | Required linked symbol | Observed role |
| --- | --- | --- |
| `7a88` | `cursor_shape_start_scanline` | Start scanline word; low byte used by BIOS output |
| `7a8a` | `cursor_shape_end_scanline` | End scanline word; low byte used by BIOS output |
| `7a6c` | `cursor_shape_visibility_state` | Show gate/status word: hide sets 0; permitted show sets 1; signed values greater than 1 suppress the show call |

The input flags use masks **04h** for visible, **02h** for half-height and **01h**
for underline. If visibility is clear, the routine invokes hide without changing
the start scanline. If visible, half-height takes priority over underline and
computes signed-truncated end/2 plus one; underline uses end minus one; neither
style bit selects start zero. The routine updates the configured start even if
the show gate then suppresses BIOS output. Those are recovered original semantics,
not newly selected cursor rules or a complete interpretation of higher gate
states.

BIOS output loads CH from the start scanline, ORs mask 20h into CH when hidden,
loads CL from the end scanline, and issues AH=01h. Valid configured font/adapter
scanlines are a caller requirement; this scalar helper does not validate a video
mode or clamp malformed configuration words. The diagnostic supplies bounded
representative scanlines and does not reconstruct adapter/font initialization.
Original arbitrary negative/oversized settings must not be treated as validated
configuration simply because they assemble or reach BIOS.

## Build and checks

```sh
./tools/dev --command python3 standalone/build_cursor_shape.py
./tools/dev --command python3 standalone/check_cursor_shape.py
./tools/dev --command python3 standalone/test_cursor_shape_dos.py
```

Four linked CPU regression groups pass: visibility/style priority; representative
font scanline calculations; signed show gating and unconditional hide; repeated
transitions with BP/SI preservation. The BIOS-boundary hook deliberately clobbers
BP, verifying that the actual recovered wrapper restores it rather than assuming
the hook preserves registers.

The DOSBox-X self-check independently sets and queries actual BIOS cursor shapes:
full block, hidden, half-height and underline. It restores the cursor shape saved
after selecting text mode 3 and returns to DOS. All checks pass; this is not
physical adapter validation. Exact binary identity and scopes are retained in
`build/cursor-shape/{manifest,checks}.json` and
`build/cursor-shape-dos/result.json`.

An optional original-required audit, separate from normal builds, verifies all
120 flat bytes:

```sh
./tools/dev --command python3 standalone/check_cursor_shape_flat.py
```

The combined CSI diagnostic also passes actual parser-driven mode-25 set/reset
with BIOS shape readback. Full startup/font/video configuration and physical display
validation remain separate requirements.
