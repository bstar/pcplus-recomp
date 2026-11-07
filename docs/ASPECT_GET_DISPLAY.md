# Parent-owned GET display controller

The new [controller](../src/terminal/script_field.asm) and
[parent adapters](../src/terminal/script_field_adapters.asm) supply the persistent
video/cursor half of a field behind `ASPECT_GET_DISPLAY`. They remain components: no renderer capability,
RPC opcode, maintained compiler command or application package enables them yet.
The [keyboard/service lease](ASPECT_GET_SERVICE.md) and recovered
[typed GET owner](ASPECT_GET.md) still need to be composed with this controller.

The recovered original `ui_write_string` at6BF0 writes character/attribute words
directly to video and does not restore a saved popup frame. This controller
therefore leaves entered text visible on normal close and ordinary error
retirement. Staging remains invisible until a complete field is presented.
No snapshot, UART operation, keyboard read, parser entry, DOS IO or child pointer
is part of this module. Its81-byte staging buffer and state live in a private
code segment, adding no DGROUP storage to the nearly full parent data segment.
Without that macro both assembly files emit no code/data segments; the build
checks their OMF records. This keeps the ordinary terminal assembly glob from
silently incorporating these not-yet-integrated owners.

## Scalar interface

Far entry `terminal_script_field` takes operationAX/valueBX, returns a typed
result in AX and preserves the other registers and FLAGS. Active operations
require DS=SS and enabled interrupts; disabled-IF admission is rejected before
calling parent policy. These are maintained interfaces, not original PCPlus
function signatures.

| Operation | Value | Effect |
| --- | --- | --- |
|0 begin|packed physical row/column, orFFFF for the native visible cursor|Capture physical geometry, logical row limit, viewport origin, current attribute and raw BIOS cursor shape. |
|1 configure|attribute byte high, width low|Validate width1..81 and complete span; start an invisible frame. |
|2 stage|index high, nonzero byte low|Accept the next ordered cell; reject gaps, zero and excess cells. |
|3 present|insert flag high, cursor index low|Require a complete frame, draw it, position/show the physical cursor. |
|4 info|byte selector0..10|ReturnF000 OR byte, distinct from typed errors. |
|5 end|0 normal,1 error retirement|Normal close adopts the cursor through the recovered parent cursor code; retirement does not adopt field state. |

Info bytes are start column/row, initial attribute, saved shape low/high,
physical columns, logical rows, viewport origin low/high, and most recently
presented physical column/row. Before presentation the last pair is the start.
Typed failures include3 unsupported,7 operand and10 state, plus errors returned
by the parent admission callback. Invalid requests preserve the previous usable
frame; a partially staged replacement cannot be presented.

Drawing checks mode/page, native/BIOS column agreement, video stride/segment,
physical row count, logical CSI row limit and viewport backing. A field cannot
write past the logical terminal plane into a reserved status row. Direct video
output has a BIOS character-write fallback when BIOS output or CGA synchronization
is selected. Bytes are glyph indexes with their supplied attributes; they are
not interpreted as terminal control characters.

Presentation changes the physical cursor while native cursor offsets remain
untouched, matching the original field/editor separation. Normal close adds the
captured viewport offset and uses the actual recovered `screen_set_cursor`,
`screen_cursor_pack` and `screen_cursor_output` code. It restores the original
raw cursor shape, including hidden state. Fields crossing a row normalize the
physical coordinate instead of issuing an invalid BIOS column; this is a
maintained safety behavior, not a claim of exact original overflowing behavior.

Every operation rechecks parent admission and view identity. Existing script
windows, abort confirmation and external PROGRAM ownership reject access. A
normal close rejected by a changed owner/view retains ownership for an explicit
retry. Error retirement clears only this module's ownership; if the context is
invalid, it returns that error without changing the foreign view/cursor. With a
valid context, it restores the cursor to the current parent logical position and
restores shape, leaving received text and field pixels in place.

## Accepted component evidence

The actual DOS8086/FPU-off diagnostic passes103 authored cases and805,133
checks. It reads the complete4000-byte video frame, tests color and monochrome
text modes, direct/BIOS drawing and CGA-flag fallback routing, hidden/visible
cursors, insert shape, native BIOS/direct cursor backends, narrow geometry and
the retained52-column viewport origin. All255 nonzero CP437 byte values appear
in successfully verified presentations. Staging/rejection is invisible; normal
close retains pixels and updates native logical/video/attribute offsets only at
the adoption boundary. Reserved status-row writes are refused. ABI checks cover
registers, FLAGS, DS=SS, disabled IF and nonzero DF.

Parent admission is modeled; the actual admission adapter and original recovered
cursor instructions execute. Test adapters use explicit segment/class aliases
`ASPECT_CODE=_TEXT`, `FARCODE=CODE` to share the C admission stub's code bank.
Linker-map checks enforce this near-call placement and a separate controller
bank. An initial wrong-class test link failed; it is not accepted evidence.
A nine-input clean public-source export reproduces the exact EXE and complete
report without original executables, private data, previous objects or ancestor
Git metadata. [The receipt](validation/aspect-get-display.json) binds identities.

This does not verify the full parent admission function, authenticated RPC,
child/runtime/serial composition, live parser repaint, native abort lifetime,
physical hardware or application memory/package gates. Actual video tests are
80x25; additional physical geometries and left-side wide-view behavior still
need application-level coverage. Mode7 and BIOS/CGA fallback checks are component
tests, not changes to the parent renderer's existing mode admission policy or
proof on physical CGA hardware.

```sh
./tools/dev --command python standalone/build_script_field.py \
  --output build/my-script-field
./tools/dev --command python standalone/prove_script_field.py \
  --build build/my-script-field --output build/my-script-field-source
```

Next is versioned parent/child RPC publication with PSP/DS/lease checks,
symmetric rejection of competing operations, proper field retirement on END,
real receive/repaint composition and native GET abort checkpoints. Floating
runtime, both compiler grammars/opcode49 and connected script/memory/package
acceptance remain open. Installed files and deployment selection are unchanged.
