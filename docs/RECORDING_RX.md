# Received prompts and parser lookahead

The [RX checkpoint](validation/recording-rx.json) connects normal input and native
ANSI parser continuation reads to the recorder. A combined query/prompt/user
test now records the prompt before user output while excluding the terminal's
query reply. Record menu controls and complete transition guards remain open;
this is not yet foreground UI recording or full F01–F16 acceptance.

Normal input is observed after modem, monitor, controller, transfer and invitation
filtering, before the XLT table. Continuation bytes are observed after successful
`ansi_next_byte` reads. These are bytes dequeued with the configured UART mask;
the hook does not recover high bits deliberately removed by a seven-bit mask.
Local echo and ASPECT's separate renderer/serial owner bypass these hooks.

Native lookahead can unreceive a byte and read it again. A replay flag and saved
post-read UART cursor suppress that reread, including a wrap at the end of the
physical RX ring. Equal bytes at different cursor positions remain distinct.
The helper consumes the replay flag once and records a different cursor normally.
Initialization clears deliberately dirty replay state; admitted begin, stop,
cancel and shutdown invalidate it at session boundaries. Busy rejected calls
preserve active replay state. Failed reads never record the FFFF timeout sentinel.

The two words add four bytes to the stable owner state, making396 explicit
owner/path/cookie/replay bytes. Actual linked alignment increases near use by16
bytes. The helper entries preserve registers and flags around the far one-word
recorder callback. The compiled source pins both state/claim field offsets used
by the assembly guards. Four resident bindings, the callback frame/target and
all required relocations are checked in both terminal variants.

Automatic transfer admission now refuses while the recorder owns active or
unresolved files. Ordinary input continues through the recognizer's existing
delivery path. Full activation still needs a boundary flush of any invitation
prefix held before recording starts, plus manual transfer/script/child/setup/
port/controller/monitor guards. This checkpoint does not claim those transitions.

| Evidence | Scope |
| --- | --- |
| Ten RX campaigns |Input before XLT, actual ANSI continuation parsing, lookahead rereads across both normal/continuation paths and physical ring wrap, repeated identical bytes, timeout, fresh-session replay state, automatic admission and native query/reply/user ordering. |
| Ten TX campaigns |Current user/report separation, full queue, stalls, cancellation, bindings, transfer draining, file errors and far-helper ABI. |
| Six owner cases |Current stable ownership and modeled file-error behavior. |
| Five autostart groups |Existing invitations, corrupt/truncated/ordinary data, deadlines, midnight and ownership refusal. |
|783 translation inputs |Loader/mappings, native parsing, capture, raw replies, RIS and monitor behavior. |
|78 ZMODEM workflows |Existing protocol/storage behavior against the current terminal, with modeled hardware/kernel boundaries. |
|594 ABI corruption cases |Adds three RX helper segments, two replay-state locations and five call targets/relocations to prior checks. |
|11 actual DOS capture scenarios |Current terminal with recorder idle; startup/shutdown, capture UI/UART/files and XMODEM coexistence. |

Linked campaigns execute product instructions without patching product callbacks;
hardware, BIOS and DOS kernel boundaries are modeled. The first RX fixture
combined automatic IRQ delivery with an explicit ISR call and manufactured an
extra empty read. The corrected fixture uses the existing automatic hardware
delivery model once. The initial failed receipt remains preserved.

The keyboard binary is
`3d3cdee802913a1518d1f0e1e38b29f6f52fe0702c4cc3ec393d111368062435`,
with96 near-data bytes and414 resident-code bytes free. The mouse build is
`ef199b4b42a5e6f2c3dda0ee864f955d5623a4fd4efc136f7ec4d370b9acf2b2`,
with48 near-data bytes and264 resident-code bytes free. Both pass static
memory/bank/state audits; runtime mouse acceptance remains separate.

Next expose Record/save/cancel/recovery controls and finish all byte-owner
exclusions and start/stop boundaries. Then test actual foreground DOS recording,
DOS compilation/UART replay and affected BBS/audio workflows using the resulting
binaries. Physical modem compatibility and all full application gates remain open.
