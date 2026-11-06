# Experimental native Chat echo input scope

The later [native-wait follow-up](CHAT_BUSY_KEYS.md) replenishes the read
allowance on BIOS clock progress and verifies real busy-key cancellation.
The global4096-attempt limit and unverified foreground guards below describe
this earlier checkpoint, rather than the current native-echo build.

`--chat-echo` now links the cursor exchange and a native echo scope into an
experimental parent. It requires the existing timing, physical-TX adapter and
foreground-core flags. **The TEXT scheduler and ten shortcuts remain unbound;
this image fails the nested-ASPECT memory gate and is not a connection candidate.**

The far-cdecl `_terminal_chat_text_echo_sink(kind,value,user)` accepts only
ECHO4 and byte0..255 with the exact22-byte cursor context at frozen+14500.
It requires Chat storage owner2, a coherent local cursor, plain80-column
geometry/page0, no viewport, no parser/wait/ASPECT owner, no pending program,
macro or deferred keys, no quit and connection phase0/6. Both the pane/context
initialization and full frontend scheduling are still caller responsibilities.

Once admitted, the scope exchanges the local/native cursor contexts, marks
parser/wait ownership, invokes the actual native terminal dispatcher, and
exchanges back before returning. Wait/cancel state and the outer cursor are
restored. Attributes, modes, history and logging retain native shared behavior.
Acceptance means the echo was invoked exactly once, including partial rendering
followed by timeout/cancellation; it must never be retried as an untouched refusal.
`terminal_chat_echo_error_far` reports the last admitted scope's outcome:
0 completed,1 tick deadline,2 cancellation/quit,3 changed modem phase,
4 operation budget,5 invalid unread. Rejected admission does not clear that result.

Three checked, relocated resident hooks route ANSI next-byte/unread and nested
controller reads to this owner only while active. Inactive calls retain their
ordinary provider. Reads use actual UART IRQ-ring bytes and continue polling
the live modem/flow/TX/keyboard paths. A one-byte parser undo slot never rewinds
the ordinary UART ring; it is primed with the initial echo byte for native C1
dispatch, which unreads before its first continuation read.

The entire echo has36 BIOS ticks and4096 read attempts. This whole-operation
budget is an intentional maintained adaptation to native blocking behavior.
It also ends a stopped-clock/no-input wait. The nested original CSI-M discard
controller already polls before reading, so its nonblocking provider avoids a
second poll. The tested exhausted nested wait performs4098 total polls including
entry/exit edges and then returns through ordinary cleanup.

While a module call is busy, the optional frontend guard holds ordinary BIOS
typeahead and permits Escape/Alt-X/Alt-H to reach the parent cancellation paths;
other events cannot reenter or unload that module. The CPU scope tests inject
external cancellation/modem-phase state after a real poll. **They do not prove
the busy-key branch or foreground TEXT cancellation with actual BIOS keys.**

## Evidence and limits

Parent SHA977d1f552fb214a464e79f640eff43f14eae02d0c10dede41d5b09d47969f70c
passes six CPU groups executing real parser/renderer, transport and IRQ code:
plain echo/deferred wrap with remote interleaving; CSI and C1 undo leaving the
next byte for main; tick/stopped-clock expiry with restoration and retry;
external cancellation/quit/modem revocation; nested original CSI-M wait; and
owner/pointer/byte/geometry/cursor admission refusals. Registers, stack and
cursor-context canaries are checked. BIOS/DOS/UART hardware remain modeled;
Chat owner2 and initial local cursor are explicitly supplied preconditions.

Actual DOS8086 main passes ordinary Alt-O entry, BIOS typing, RX ownership,
Escape return and held-prefix/ordinary-CPR recovery with this image. Echo and
TEXT remain inactive during that main test. A fresh3643-file public-source
export without analysis/original/private/prior-object inputs or ancestor Git
reproduces the exact parent/module/header and repeats all six CPU groups.
The module remains API0103/SHA5b6892e7…d45622. Echo disabled rebuilds the exact
previous5ecf8774…092846 parent.

The new bank is895 bytes including cursor service/alignment/scope state; the
three resident hooks add24 bytes. Near DS=SS remains65504 and resident CS65464.
Minimum allocation is480368,976 bytes above the preceding timing image and
960 above the earlier foreground baseline. Stacks, streams and capacities are
unchanged. Actual DOS8086 nested-ASPECT testing with the unchanged cbdee194
interpreter fails child/six-stream/file/viewport checks; missing-file recovery,
hangup, hardware restoration and the fixture PRM preservation checks pass.
These observations establish a failed gate, not a complete causal diagnosis.

The initial linked-image verifier rejected the changed line-read bridge; the
updated verifier now checks its actual relocated owner hook and untouched raw
UART thunk. Early nested-wait testing caught double polling, corrected by the
nonblocking provider. The final scope results and failing ASPECT result are
retained separately; failures have not been reclassified as passes.

Next recover the memory budget without reducing capacities, verify actual busy
key/cancel behavior, initialize/synchronize the local cursor and presentation
state, compose echo/TX/timing in the foreground scheduler, and bind all ten TEXT
keys. Geometry changes/fault recovery, broad Chat/BBS, packaging/deployment,
physical acceptance and full original parity remain open. No selected package,
physical PC or production network/bridge configuration changed.

See the [receipt](validation/chat-echo-owner.json) and
[cursor primitive](CHAT_ECHO_CURSOR_SWAP.md).

The subsequent [partial memory recovery](CHAT_ECHO_SIZE.md) saves480 allocated
bytes while preserving capacities. Its nested-ASPECT gate still fails; it does
not enable TEXT or change the selected package.
