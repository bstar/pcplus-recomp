# Loadable Chat screen and cursor lifecycle

The optional `--presentation` module adds physical screen ownership to the
native-audited Chat session. Its code stays in the separately loaded module;
the parent frontend and Alt-O binding remain open. This checkpoint does not
change the selected or installed connection package.

The variant is API `0101`, with the existing 50-byte request and a 362-byte
caller-owned session. A separate 16-byte far presentation context holds saved
geometry, cursor and backup identity. Operation6 opens physical presentation;
operation7 refreshes the local cursor. Open uses the request's `user` as the
presentation context, `value=16`, and `frame`/`capacity` as the caller's backup
and its cell capacity. Other session operations retain their existing meanings;
their callback `user` may subsequently differ from the presentation context.

The 5,120-byte MZ file contains a 5,072-byte image and two self-relocations:
`f0e91e2b1aff29e466d68bbe7d1a267c57382126dce21b2c6759aff6ce31850f`.
It has no private DGROUP, heap, frame, stack or CRT. Callers must reserve an
8,192-byte module window and keep state, context and backup outside that window
and mutually disjoint. Existing 4KB loader fixtures cannot host this variant.
Default API0100/state358 remains a separate, byte-identical module `77270fb6`;
the existing parent builder continues to select that default.

## Behavior and admission

Open admits color text mode3, page0, 80 columns and 25/28/43/50 rows. It checks
bounded conventional memory and overlap before saving all visible cells and the
BIOS cursor position/shape. Chat paints the physical frame and keeps the cursor
at the local insertion point, preserving hidden cursor state. Cached position
avoids redundant BIOS cursor writes. This is maintained lifecycle code around
the recovered renderer, not a claim of identical intermediate BIOS timing.

Close or abort restores every saved cell and the original cursor. If geometry
changes, key/RX processing refuses before painting. Abort can stop the session,
but retirement refuses to restore into a different mode/page/geometry and keeps
the module active. The caller must restore the admitted geometry and retry
abort before unloading or releasing borrowed storage. This explicit refusal
does not itself switch the user's display back. It is not a guarantee against
arbitrary caller memory corruption or asynchronous changes inside callbacks.

## Verification

Actual normal DOS8086 execution loads the variant through DOS4B03 at two bases,
with all remaining DOS paragraphs reserved. Eight presentations cover all four
row geometries and visible/hidden cursor shapes. They check local and CP437 RX
painting, ordered history/log callbacks, active-unload refusal, exact full-screen
and cursor restoration, four changed-page retirement refusals and nine invalid
open controls. Rejected key/RX operations leave local cursor state and pending
RX unchanged. Guard bytes, PSP, JFT and largest-free-block checks pass. The
fixture links the recovered source-built row helper, not Chat implementation.

A fresh 38-file declared public source export repeats the test and reproduces
the module, generated identity header, host executable and result exactly.
The current API0100 regression still matches 568 complete native-reference
frames and 1,071 ordered effects, including 1,024 RX effects while TX is refused.
A fresh parent build remains exactly `75c84373`, and its loader objects remain
bound to that current DOS-tested default module. See the
[checkpoint receipt](validation/chat-presentation.json).

```sh
./tools/dev --command python standalone/test_chat_presentation_dos.py \
  --output build/NEW-chat-presentation
```

Foreground entry/pre-dequeue, real UART/RX/TX/history/log adapters, Help/direct
TEXT, notice/trap policy, parent memory admission and final BBS/package/physical
gates remain open. The prior intermittent Enigma redial miss remains unresolved.
No physical DOS PC or production SynthModem/Enigma service was changed.
