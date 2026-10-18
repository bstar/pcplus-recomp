# Recovered character-cell output backend

The original character path at resident `0730` ultimately invokes `6c5e` to
write a character and attribute, `6c84` for character-only writes and `6cb4`
for a packed cell. These backends and their fill/BIOS/CGA dependencies are now
independently linked from recovered source. The module contains 201 original
bytes in six units, each checked against a recorded original-region SHA-256.
Two zero alignment bytes at `6c83` and `6cb3` are deliberately excluded from
instruction recovery. No original executable is needed by the build or tests.

```sh
./tools/dev --command python3 standalone/build_text.py
./tools/dev --command python3 standalone/check_text.py
./tools/dev --command python3 standalone/test_text_dos.py
```

The resulting `build/text/TEXT.EXE` runs in DOS. Its self-test performs actual
text-video-memory writes and invokes the recovered BIOS-output branch, then
checks video memory and returns a DOS errorlevel. The linked Unicorn regression
checks all 256 character/attribute byte pairs, packed-cell ordering,
character-only attribute preservation, zero/multiple fills with canaries, and
the actual CGA polling instruction paths using a synthetic alternating status
port. This does not establish physical CGA timing behavior.

## Original ABI and maintained adapters

All low-level recovered functions return near and clean their stack arguments.
Arguments shown below run from nearest the return address outward. DS must
equal SS because the original code accesses stack arguments through DS:BX.
The direction flag must be clear. Routines clobber AX/BX/CX/DX/ES and flags;
DI is restored, but CGA paths explicitly enable interrupts after the write.
Original names are analyst annotations.

| Resident entry | Export | Stack words |
| --- | --- | --- |
| `6c20` | `text_fill_cells` | count, byte offset, packed cell |
| `6c4a` | `text_write_bios` | attribute/page, character |
| `6c5e` | `text_write_cell` | byte offset, attribute, character |
| `6c84` | `text_write_char` | byte offset, character |
| `6cb4` | `text_write_packed` | byte offset, packed cell |
| `7e20` | `text_cga_word` | internal register service: AX cell, ES:DI target, DX port |

Original packed form places the character in the **high byte** and attribute
in the low byte. The implementation swaps these before `STOSW`.
`src/text/api.asm` provides ordinary near-return adapters usable without
constructing stack arguments:

| Adapter | Registers |
| --- | --- |
| `text_put_cell` | AX offset, DX attribute, CX character |
| `text_put_char` | AX offset, CX character |
| `text_put_packed` | AX offset, CX packed cell |
| `text_fill` | AX offset, DX count, CX packed cell |
| `text_put_bios` | CX character, DX attribute/page |

Build recovered files with `-DTEXT_OMF`. Supply these DS words:

| Original offset | Symbol | Meaning |
| --- | --- | --- |
| `7a78` | `text_video_segment` | video segment, normally B800 for color text |
| `7a92` | `text_bios_output` | nonzero selects BIOS in `text_write_cell` |
| `7a8e` | `text_cga_status_port` | zero for direct write, otherwise CGA status port |

The BIOS branch uses INT 10h AH=09, one character, at the existing BIOS cursor;
it does not use the byte offset argument to move that cursor. Attribute high
byte becomes BH (BIOS page). Cursor integration must keep BIOS state current.
The direct single-cell writer does not consult the CGA status port; packed,
character-only and fill paths do.

## Remaining high-level path

The 646-byte original character routine at `0730..09b5` still needs recovery
and integration. Its normal path performs deferred wrap, glyph mapping,
attribute-map checks, writes the cell and advances the cursor. Its dependencies
are not replaced by no-op services in this module:

| Target | Role observed or inferred from calls |
| --- | --- |
| `1bbe` | recovered cursor-position service |
| `1fc4` | scrolling at bottom margin |
| `b9f7` | capture/logging overlay boundary; exact behavior not reconstructed |
| `2adc`, `2d98`, `2d4c` | attribute-map/character transformation services |
| `bb53` | alternate mapped/font output overlay boundary |

The low-level source is actual rendering code, but this diagnostic is not a
complete terminal renderer. It does not implement remote control parsing,
scrolling, logging, font selection, configuration loading or the application's
high-level cursor bookkeeping. Startup helper `1c66` resets cursor bookkeeping
and invokes the separately recovered cursor-output routine at `6e78`; it is
outside this module.

## Evidence

Original target SHA-256:
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resident addresses add `1200` hex for original file offsets and `10000` hex
for REA linear addresses. `docs/evidence/text/rea-index.json` identifies the
retained Ghidra assembly evidence reused here. `reconstruction/text/recover.py`
is an explicit analyst step that reads the verified original, disassembles each
known function range and validates every encoding and complete flat output.
It is not a build dependency. Recorded test results include executable hashes;
local binaries and original artifacts remain ignored.
