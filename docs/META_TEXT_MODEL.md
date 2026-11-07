# Serviced Meta Keys text field

The new memory-only field model reproduces the Meta Keys use of the original
shared editor without its blocking keyboard loop. It is a building block for
Alt-M, not a complete editor or a change to the interactive terminal. The
installed release and its pending physical acceptance are unchanged.

The subsequent [dialog component](META_DIALOG.md) composes this field with the
native row/navigation rules and tests an actual source-built VGA popup. It keeps
file ownership and application integration separate.

## Native authority

REA/Ghidra pseudocode for resident `79d4` is
`ev_8c003c884636ef6c380b8805a8406868f097d76ba0b450d3bfe38dbd8cf4a278`;
assembly is
`ev_73072fd86c4a6e98f7a51d423da8324aa3e9fa89067e3e591af97211665f47e2`.
Static analysis uses the identified overlay-3 image, never executed. A separate
explicit analyst replay executes the original `7880` wrapper, `79d4` editor,
overlay-3 `e261` callback and original CRT instructions from SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.

That replay supplies only synthetic 52-byte text records. Keyboard, cursor,
display, visibility and bell services are modeled. It records every pre-key
50-byte field, cursor, shape and bell count, then the exact destination bytes
and return code. No installed KEY, PRM, private macros, BIOS, DOS or UART are
inputs. The pooled [frozen trace corpus](../standalone/fixtures/meta_text_native.json)
contains 554 cases and 8,418 key states, with range hashes and explicit authority.
All 256 byte-valued keys, all 50 cursor positions for five edit operations,
full-latch transitions and initial lengths 0, 1, 49, 50 and 51 are represented.
These are instruction/service-boundary observations, not original VGA captures.

## Behavior established here

The working field starts space-padded, in overwrite mode at column zero.
Typing stages changes independently of the destination. Enter trims trailing
spaces and copies through the new NUL, preserving subsequent opaque record bytes.
Escape cancels without copying anything back. Tab and Shift-Tab accept while
returning their original codes; Enter returns zero. A stored 51-byte definition
survives cancellation; acceptance produces at most 50 content bytes, as in the
original replay. The model's working display buffer is always bounded to 50.

Backspace at a fully occupied last cell clears that cell first without moving
left. Delete, Home, End, Left, Backspace, Ctrl-End and whole-field clearing reset
the full latch. Right and Insert retain it. Alt-C and the extended clear code
clear the field and return the cursor to the start. Insert mode shifts the fixed
field, dropping its final cell, and uses the saved end-scanline formula for its
cursor shape. Accept/cancel restore the saved shape. Unsupported keys ring the
modeled bell; byte `ff` is consumed by the Meta callback. Other unassigned byte
controls remain raw field content rather than being silently filtered.

The full-cell Backspace rule also merits a separate 62-cell path-dialog
regression: its existing source decrements before shifting. The generic native
branch is shared, but this Meta replay does not claim actual path-window pixels
or close that follow-up.

## Source interface and tests

[meta_text.h](../src/key_mapping/meta_text.h) defines a caller-owned 64-byte state
and explicit far begin/key/commit/shape functions. They perform no allocation,
file IO, keyboard wait, BIOS calls or UART operation. A future live owner can
feed one key at a time while the foreground continues servicing traffic.
It must supply canonical native keys, render the state, and adopt accepted
record changes through the separate row/file/action owners.

The source model checks cookie, phase, cursor/full consistency, terminated
record input, nonwrapping far spans and physical overlap, including segment
aliases. Rejected arguments leave the state/output unchanged. These checks are
maintained guards around the original valid-input semantics, not recovered
original validation. The caller still owns allocation and lifetime.

```sh
./tools/dev --command python standalone/build_meta_text.py \
  --output build/NEW-meta-text
```

The source-only diagnostic executes in DOS8086 against all frozen states and
complete 52-byte outputs, plus twelve guard cases. A diagnostic-only 64-KiB pad
forces the model and caller into different CS values; DS=SS is checked as well.
The pad is not application residency or a proposed runtime dependency. A six-file
isolated source export reproduces the exact EXE and complete replay report,
without originals, private data, prior objects or ancestor Git. The outer Nix
environment supplies the toolchain. The [receipt](validation/meta-text.json)
binds these finite observations.

Remaining work includes the Alt-M window and navigation, original VGA/cursor
comparisons, checked load/save, resource identity, live action-table adoption,
foreground ownership and application memory/capacity gates. No full F02/F05/F06,
physical runtime or whole shared-editor parity claim follows from this model.
