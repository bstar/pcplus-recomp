# Chat echo cursor-context exchange

The next implementation piece is `src/chat/echo_cursor.asm`: a76-byte8086
far service that exchanges eleven native cursor/cache/deferred words with
caller-owned storage. It uses the existing position service to move the BIOS
cursor, preserves general/segment registers and the caller frame, and adds no
private state or UART/keyboard operation. The primitive is linked into an
isolated diagnostic; **it is not linked into the live parent or Chat module.**

The caller supplies DS=SS, DF clear and ES:DI pointing to22 writable bytes,
disjoint from native state/stack and without segment wrap. The words are:

| Offset | Native field |
| --- | --- |
| 0 | screen_cursor_row |
| 2 | screen_cursor_column |
| 4 | screen_visible_column |
| 6 | screen_previous_row |
| 8 | screen_previous_column |
| 10 | screen_video_offset |
| 12 | screen_attribute_offset |
| 14 | csi_wrap_pending |
| 16 | render_deferred_row |
| 18 | render_deferred_column |
| 20 | scroll_suppress_next_linefeed |

Both contexts must already be coherent plain80-column contexts with the
viewport disabled and admitted geometry. This low-level service does not
validate those preconditions, perform entry admission or prevent reentry.
The future echo owner must hold the entire parser operation and exchange back
on completion, timeout or cancellation before another renderer can run.
Attributes, modes, parser state, history and logging remain shared; this is
cursor-context ownership, not a complete terminal-state snapshot. It is an
intentional maintained adaptation to the [native cursor hazard](CHAT_ECHO_CONTEXT.md).

`standalone/build_input_dispatch.py --chat-echo-cursor --output build/NAME`
links the actual service plus a diagnostic adapter matching the parent's
existing position ABI. Ordinary builds remain byte-identical7bcb9d54…13ea.
The optional diagnostic isae448266ddc8fead88b96f717e20d55a6a2755fff69d40d4a4080af3794b68de.

The CPU test executes160 exchanges around80 local native parser invocations,
across16 combinations of profiles4/6, autowrap on/off and four stream families.
Independent native local/remote instances verify both screen regions and all
eleven cursor words. A third native instance verifies shared history in actual
interleaved byte order. Cases include pending right-margin wrap, TAB/CR/LF/BS,
NUL/DEL/high bytes, embedded-control CSI and incomplete CSI ending in the
fixture's memory-provider timeout. Caller registers, stack, IF and storage
canaries pass. These continuations are supplied by the diagnostic memory
provider; **they do not establish serviced live input ownership.**

A fresh3641-file public-source export with analysis/docs excluded, no original
or private input, no prior objects and no discoverable ancestor Git repeats
the exact diagnostic and all160 exchanges under the pinned Nix environment.
An initial export assertion caught public analysis files; the next attempt
was refused by Nix's enclosing-repository detection. The final run excludes
analysis and uses an explicit path flake. Neither failure changed application
code or weakened the successful source-only check.

The live parent/module and selected/deployed package are unchanged. No new BBS
or physical test is claimed. Next integrate the cursor owner with admission,
serviced escape continuations, abort handling and the foreground TEXT scheduler,
while retaining the nested-ASPECT memory budget. Then bind/test all ten keys.
See the [receipt](validation/chat-echo-cursor-swap.json).
