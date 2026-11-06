# Original Chat echo cursor context

The next echo integration now has a verified cursor service and a regression
for an original cursor-cache hazard. **The echo sink and ten foreground TEXT
shortcuts remain unbound.** This checkpoint does not change executable bytes or
claim that Chat echo is finished.

Original Chat's pre-key path writes logical row399C/column399E and calls6E66.
That helper packs the coordinates and calls BIOS cursor output. The0610 echo
dispatcher then reaches the ordinary renderer, which also uses cached video
offset3344, attribute offset3346, previous row39A2, visible column39A0 and previous
column3348. A BIOS cursor move alone does not synchronize those caches.

The CPU regression explicitly applies those logical writes and the actual6E66
instructions, then enters0610. Across144 vectors/4608 character operations,
72 raw-coordinate cases place the first echoed A at the previous cached position.
The tested prior positions are0:0,2:7,18:79,24:79; local targets20:0,21:10,23:79;
profiles4/6 use ordinary color text. Printable/high bytes, TAB/CR/LF/BS/NUL/DEL
and wrapping streams execute recovered input/render/cursor/history code.
The entire recovered760-byte Chat controller is assembled and hash-checked;
the analyst run also matches those bytes to the genuine file. Its controller
instructions are not executed by this cursor-setup fixture.

An analyst run also executes the unmodified genuine2.01 resident instructions,
SHA6401ccfd…7196904. After every byte, original and source-linked paths agree on
all4000 video bytes, logical/cached/deferred cursor state, history state/bytes
and modeled BIOS calls. This is a controlled Chat-style pre-key setup, not full
original Chat entry/exit, startup or overlay execution. ESC and overlay emulations
are excluded from this resident comparison and still need integration evidence.

Calling the existing1BBE cursor helper before echo instead synchronizes the
caches and places the first character at the intended local position. Original
and source handlers still match after that repair. **This is an intentional
coherent-cursor adaptation, not a claim that original Chat performs the repair.**
Moving the cursor back alone also leaves deferred-wrap state set. The eventual
echo owner must preserve/restore the full required context, not only row/column.
History/log effects require their own ordered/backpressure handling, and escape
continuations must not consume unowned input.

## Parent service without growth

`terminal_key_position_far` aliases the already serialized CALL
`screen_set_cursor`/RETF pair inside `terminal_key_cursor_far`. It takes AX=row,
DX=column with parent DS=SS; BP/SI/DI/DS/SS and the caller frame are preserved,
other registers are scratch. The caller owns geometry and admission. There are
no new resident/near bytes. All2000 physical80x25 positions pass through the
actual parent instructions, cache arithmetic and modeled BIOS cursor call,
without a key read or UART byte.

The rebuilt parent remains byte-identical
`5ecf87743f55c97e83a334c3a5ef9e049dc4de1558ec4d482a529cf215092846`.
Its module remains5b6892e7…d45622. Existing Enigma/Synchronet results for those
exact executable bytes are reused; no new BBS run is represented by this cursor
checkpoint. Selected/deployed packages and the physical PC are unchanged.

The input diagnostic builder now accepts an isolated output directory and
records its builder/provenance inputs. A fresh673-file public-source export repeats
the source-only echo vectors and parent position checks and reproduces the
input EXE/parent/module/header exactly. That export has no original/analysis
directory, private configuration, prior objects or discoverable ancestor Git.
The genuine-original comparison is separate and never an application build input.

Fresh REA static assembly confirms0610's render/history/log and escape dispatch
(`ev_f365c88f83c443797063f3655ae754a0e43fd62fb975d0b030f373c2ab3b4c7e`),
1BBE's cache updates
(`ev_fda29d5a24cbef5ea8196a77a9fa0d5e557ba29da3255127e608c4d2aef6f5c4`)
and6E66's packing/call-only behavior
(`ev_87fb0d4004131a25f656f3654a82585096a747f7d15552f2d58d7d300edeebee`).
These static results do not observe runtime behavior. The provider did not
recognize3FB0 as a procedure; nearby3F9C was not substituted for it. Full records
remain in ignored analysis storage and the REA session is closed.

Next implement the echo context owner and serviced parser continuation, then
bind all ten direct-TEXT keys with pre-read/RX fairness. Help/Alt-Z/send-mode UI,
broader Chat faults/geometry/sustained traffic and final package/hardware/full
parity gates remain open. See the [receipt](validation/chat-echo-context.json)
and [timing checkpoint](CHAT_TEXT_TIMING.md).
