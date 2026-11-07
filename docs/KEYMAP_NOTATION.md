# Keyboard editor notation recovery

The matching `PCKEYMAP.EXE` was found in the immutable CF baseline image at
`UTILS\PCPLUS`, extracted without mounting or writing the image. Its 23117 bytes
have SHA256 `f079418fca6392cde318e2eb657874a1f5ee10db83616c83054d191441fb6244`.
The original and the 48-record REA export stay under ignored analysis storage.
No installed KBD, PRM, dialing data or factory defaults were imported.

`src/key_mapping/keymap_text.c` reconstructs the notation conversion used by
that helper. Storage control bytes use caret notation, literal caret becomes
`^^`, and CP437 `AE … AF` markers represent record separator (`^`), delete
(`D`) and the stored-FF/serial-NUL sentinel (`0`). Lowercase control letters
are accepted, as in the original. The terminal emitter still handles binary
storage directly; notation conversion belongs only at the editor boundary.

REA identifies the original converters at CS:0D4C and CS:0DC4, the editor at
CS:0A3F, load at CS:0714, save at CS:0970, and the outer edit operation at
CS:08A2. The helper addresses 33 profiles of 79 twelve-byte slots, matching the
already-recovered main-program file layout. Save converts all slots back to
storage before writing, then returns the working table to display notation.
These file/UI paths have static evidence only in this milestone.

The original field shows ten columns. A valid eleven-byte storage binding can
expand to 33 notation bytes; the original whole-table conversion uses a
12-byte stack temporary. The maintained converter requires explicit lengths
and capacity, never truncates expanded strings and leaves the destination
untouched on failure. Future UI admission must address bindings exceeding ten
columns without rewriting or clipping them.

Literal CP437 `AE` (`«`) collides with the original marker prefix. Executing
the original converters confirms that stored `AE 44 AF` displays unchanged but
saves as the single byte `7F`. The maintained encoder refuses literal `AE`;
the decoder requires complete, recognized markers and refuses malformed caret
sequences, embedded terminators and overlong storage. These are intentional
safety differences. An editor must preserve an unrepresentable original slot
and explain refusal; this component never rewrites a file.

[Validation](validation/keymap-notation.json) records 800 isolated original CPU
comparisons, 386 host round-trip vectors with 789 transactional boundary
checks, 772 source-built DOS8086 conversion cases and thirteen malformed-input
DOS checks. Original CPU tests use the actual converters and their actual CRT
copy routine, with generous synthetic buffers and DS=SS. They do not execute
the original entry point or establish original whole-application safety.
A separate three-file source export reproduces the DOS executable byte for
byte without access to original inputs. Public provenance contains addresses,
range hashes and REA Evidence IDs, not original executable bytes.

```sh
./tools/dev --command python standalone/test_keymap_text.py \
  --output build/keymap-notation
```

Optional `--original /path/to/PCKEYMAP.EXE` enables the SHA-pinned CPU comparison;
it is never a source-build input. The full editor screen, field-state machine,
transactional KBD save, factory-default recovery, Alt-F8 foreground admission
and post-return reload remain open. The installed connection-test package and
physical machine have not changed.
