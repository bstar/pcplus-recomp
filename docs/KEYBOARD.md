# Recovered keyboard unit

The source-only `KEYBOARD.EXE` links nine recovered PCPlus 2.01 resident routines
and a small maintained DOS host. It exercises the local keyboard acquisition and
key-word normalization layer. The live terminal now integrates its original raw
read path with a separate recovered79-slot classifier, strict explicit KBD import
and a bounded UART sender; see [LIVE_KEYBOARD.md](LIVE_KEYBOARD.md). Full KEY
macros and original application UI remain separate reconstruction work.

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

The recovered36-byte initialization helper7916 reads physical BDA0496 bit4 to
select mode0/10h when passed a nonzero AUTO argument. Startup calls it with1;
this is distinct from manually forcing enhanced services. The live `/B:AUTO`
default uses that helper, while `/B:STANDARD` and `/B:ENHANCED` are maintained
overrides. See [KEYBOARD_DETECTION.md](KEYBOARD_DETECTION.md).

The live terminal uses `keyboard_read`, retaining E0 keypad identities as the
original terminal dispatcher expects. It does not apply the second UI
normalizer before raw classification. Alternate low-E0 keypad words1ce0/35e0
map to e00d/e02f through explicit maintained aliases. The normalized API remains
available for callers that need the original UI convention.

The ASPECT child now links the same BIOS read/peek and normalizers through
`KEYBOARD_BIOS_ONLY`, with owned AUTO selection, capability5 parent-mode
inheritance and no private queue.
[ASPECT keyboard acquisition](ASPECT_KEYBOARD.md) documents exhaustive word
coverage and the remaining script-time dispatch boundary.

The original queue peek base is DS:5df4h, while dequeue uses DS:5e00h, twelve
bytes later. The later [mouse/keyboard composition](MOUSE_KEYBOARD.md) identifies
the native mouse producer: its event code is the index, its repetition count
is the queue count, and its button-pending word is the active flag. The six
original peek words differ from the read words for Enter/Escape. Neither read
routine advances the index because this is a repeated mouse event, not a ring.
The original keyboard-only host retains independent tables. Its debug callback only counts
invocations; the original callback at 57aeh creates a diagnostic display and
requires application UI services outside this unit.

## Integration and remaining scope

The live application still disables the private queue and uses one foreground BIOS
reader after a successful peek. Raw classification covers all79 slot identities;
maintained network defaults and explicit `/K` profile import provide their
contents. DECCKM updates matching arrow strings across the selected map, and
the bounded sender validates complete bindings before queuing wire bytes.
Detailed original table/consumer evidence is in
[KEYBOARD_MAPPING.md](KEYBOARD_MAPPING.md) and [KEY_MAPPING.md](KEY_MAPPING.md).

Ten actual DOS live-key cases pass for navigation, F11/F12 and Shift/Ctrl
variants, synthetic ANSI/VT220 KBD import, binary NUL and invalid-file rejection.
Original queue production, historical factory mapping tables, complete keymap
editing and KEY macro execution remain open. Physical keyboard/BIOS validation
is still required; DOSBox key delivery does not establish every XT/AT firmware
combination.
