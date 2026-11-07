# Keyboard editor field recovery

The source field at `src/key_mapping/keymap_field.c` now follows the original
PCKEYMAP2.01 CS:0A3F editor. [Validation](validation/keymap-field.json) covers
363 original-instruction cases and1246 pre-key states, replayed against the
source in both the host and actual DOS8086. A seven-file isolated export
reproduces the DOS executable byte for byte without any original input.
This is the field/commit component, not the complete Alt-F8 helper.

The recovered behavior differs from the Meta Keys editor: Tab clears the field;
Enter accepts; Escape cancels. Insert toggles insertion, otherwise characters
overwrite. The last column can be overwritten repeatedly. Home, End, arrows,
Delete, extended Backspace and Ctrl-End retain their original behavior.
Ctrl-^, Ctrl-2 and extended DEL insert the original three-byte display markers.
Invalid keys ring the bell. The editor keeps ten columns and restores the
saved cursor shape after accepting or cancelling.

`standalone/capture_keymap_field.py` is an explicit optional SHA-pinned original
CPU oracle. It runs the actual field and CRT helpers with synthetic initial
strings. Keyboard, drawing, cursor and bell boundaries are modeled and declared;
the fixture is not a VGA capture. Original bytes remain outside public Git.
The source-only fixture records fields, cursor positions, shape starts, bell
counts, cancellation and return values. Final commit checks use the separately
recovered bounded notation converter; malformed notation leaves output unchanged.

End on a full field, or a marker ending in the last column, can leave the
original cursor one column beyond the field. That position is preserved.
The maintained model refuses typing, Delete and marker insertion there, rather
than adopting the original unsafe writes/count underflow. Backspace and cursor
navigation remain usable. Original three-byte insertion can also shift bytes
beyond its local field; the maintained shift stops at the field boundary.
Four explicit safety guards pass on both host and DOS, including oversized
initial-input refusal without changing state. These are deliberate differences,
separate from the1246 matching original states.

The real helper was also run in DOSBox8086 at1000 cycles on an all-empty,
31284-byte synthetic `SYN.KBD`, profile6 (ANSI). A passive INT1C VGA observer
waited for the ready `PgUp/Dn:Terminals` footer, captured all4000 character/
attribute bytes and restored the previous interrupt vector. The synthetic file
remained unchanged after Escape. [Screen receipt](validation/keymap-screen.json)
records frame hashes and attribute counts. An earlier capture of the transient
`READING DATA...` footer was excluded; it is not the accepted ready screen.
This observation establishes the original layout/colors, not a matching source
screen. No private KBD, physical machine, serial modem or live BBS was accessed.

```sh
./tools/dev --command python standalone/test_keymap_field.py \
  --output build/keymap-field
```

Optional evidence regeneration uses `capture_keymap_field.py` or
`capture_keymap_screen.py` with explicit `--original` and a fresh `--output`.
The former emits a fixture; the latter executes only the SHA-pinned original
helper in isolated DOSBox media. Neither is an application build input.

Next integration gates remain: source screen/navigation for all79 slots and
33 profiles; preserve uneditable bindings longer than ten notation columns;
transactional KBD loading/saving without changing opaque or unselected slots;
recover factory defaults separately; foreground helper admission, screen return
and strict post-return keyboard reload. The installed build remains RA608E10,
with physical acceptance pending.

Subsequent integration: [foreground helper](KEYMAP_HELPER.md) now joins these
components and verifies standalone persistence plus an existing PROGRAM return.
Dedicated Alt-F8/reload and the remaining native parity gates are still open.
