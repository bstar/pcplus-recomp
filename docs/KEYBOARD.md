# Recovered keyboard unit

The source-only `KEYBOARD.EXE` links nine recovered PCPlus 2.01 resident routines
and a small maintained DOS host. It exercises the local keyboard acquisition and
key-word normalization layer. Terminal-emulation-specific outbound escape
sequences, key maps, macros, and the full application event loop remain separate
reconstruction work.

Build and verify with the pinned toolchain:

```sh
./tools/dev --command python3 standalone/build_keyboard.py
./tools/dev --command python3 standalone/check_keyboard.py
./tools/dev --command python3 standalone/test_keyboard_dos.py
```

`build/keyboard/KEYBOARD.EXE` runs under DOS and expects the keys `k`, Up, Right,
Alt-X, in that order. It returns DOS errorlevel zero when all four values match,
one otherwise. This is a diagnostic rather than an interactive terminal.
The DOSBox test schedules those actual emulated key events and checks the DOS
exit status. The CPU tests execute the linked MZ instructions and model BIOS
INT 16h; they are complementary evidence, not physical keyboard testing.

## Source and baseline identity

`reconstruction/keyboard/core.asm` contains recovered instructions. Normal builds
read no original executable or analysis database. Four flat-mode regions are
assembled and compared to stored SHA-256 values in `provenance.json`: resident
CS-relative `[64fe,6553)`, `[77d2,77fd)`, `[7836,7880)`, `[7fe2,7fff)`, totaling
231 bytes including two original alignment bytes. OMF mode replaces absolute
references with linker symbols. Register-direction macros in the shared
`encodings.inc` preserve original instruction encodings for baseline checks.

The identity of the source image and the REA assembly Evidence IDs are retained
in `reconstruction/keyboard/provenance.json`. The original executable and raw
analysis exports stay outside the public repository. Names and interface
annotations are analyst interpretations; they are not recovered source names.

## Interface and observations

Calls are near calls in a shared code segment. **DS must equal SS**: the original
normalizers use `DS:BX` to access stack arguments. AX returns the key word; BX and
flags are volatile. The original read/poll paths preserve SI, and `keyboard_read`
also preserves BP. The maintained wrappers in `src/keyboard/api.asm` expose
caller-cleanup word arguments for the two original `RET 2` normalizers.

| Export | Observed behavior |
| --- | --- |
| `keyboard_bios_peek` | INT 16h AH=1 or 11h; returns zero when BIOS ZF indicates empty; maps an occupied zero key word to 0100h. |
| `keyboard_bios_read` | INT 16h AH=0 or 10h, then original BIOS key normalization. |
| `keyboard_peek` | Peeks the application queue when count is nonzero, otherwise BIOS. |
| `keyboard_queue_read` | Decrements queue count, clears active flag, reads current index; enables interrupts before returning, including empty calls. |
| `keyboard_poll` | Peeks; consumes key 2c00h and invokes a callback when signed debug gate is nonnegative. |
| `keyboard_read` | Waits until poll returns nonzero; prefers queued data, falling back to BIOS read. |
| `keyboard_read_extended` | Applies the second normalization after `keyboard_read`; E0h extended markers become AL=0. |

`keyboard_bios_mode` is a byte, 0 for standard functions or 10h for enhanced
functions. The normalizer retains special Backspace, scan-only and selected
extended words while reducing most ordinary characters to their low byte. Its
comparison with 372ah is **signed**, and this behavior is preserved.

The original queue peek base is DS:5df4h, while dequeue uses DS:5e00h, twelve
bytes later. Neither read routine advances the queue index; the producer has
not been reconstructed. The host preserves the separation and tests it rather
than assuming a conventional ring buffer. The host's debug callback only counts
invocations; the original callback at 57aeh creates a diagnostic display and
requires application UI services outside this unit.

## Next integration

Supply real application queue state and recover its producer before exposing a
queue injection API. Recover key-to-terminal-byte translation and configurable
maps before connecting keyboard output to the UART. Integrate the unit into the
application event loop with the ANSI work, and repeat on physical DOS hardware.
