# Composed serviced Chat session

`src/chat/session.c` now combines the
[send owner](CHAT_SERVICED_OWNER.md) and [pane renderer](CHAT_SCREEN.md).
The caller supplies358 bytes of far state and an existing checked frame.
The three production objects contain3047 code bytes in CHAT_GROUP and zero
DGROUP data. They are not linked into the selected parent or installed package.

## Effects and ownership

Accepted ordinary keys paint the local pane once, then use the recovered send
owner's TX/log/history ordering. A pending send or incoming effect refuses the
next key without consuming it. Help and KEY records return explicit actions to
the frontend; this component does not execute them or claim their modal UI.
Escape and these action handoffs also wait for an explicit transport-idle grant.
Queue acceptance alone is not evidence that the parent has finished transmitting.

Received input is translated, suppresses translated NUL, and paints the remote
pane once before history then logging, matching E921/E928/E92C. One pending
received word retains its effect phase. A second receive is refused until that
phase retires; the eventual UART adapter must retain that byte or stop dequeuing.
It must not drop a byte after observing this refusal.

The foreground step alternates ready RX/TX work, attempts at most32 sink calls,
and yields on a refusal. A stack-local far callback adapter records refusal;
it is never retained after the call. This prevents repeated attempts at a blocked
TX from starving incoming history/log work. Sinks must be bounded, all-or-refuse,
and must not reenter or mutate this context. Per-stream native ordering is
preserved; servicing RX while native TX would have blocked intentionally changes
interleaving and does not claim original blocking timing.

Confirmed disconnect/abort retires both directions without changing the borrowed
frame. Reopening the same storage clears previous ownership. Bad local display
state causes an explicit failure and retirement before key output; the parent
must handle frame restoration/fatal policy. An invalid open leaves the current
valid context unchanged. There is still no raw-DCD classification, live UART
queue/drain implementation, application frame owner or hardware cursor binding.

## DOS and source evidence

Eight actual DOS8086 far-bank workflows exercise all eight buffered/duplex/LF
combinations, with geometries distributed across25/28/43/50 rows. They keep transmission refused while64 translated incoming
bytes per case render and complete history/log operations. All1024 incoming
effects complete while TX is pending. Repeated pending-key and receive refusals,
zero-budget turns, transport-busy action/close refusal,12 abort/reopen progress
points, old-session exclusion and invalid-screen retirement pass.

The568 complete frame/cursor snapshots match the662-byte native renderer/cursor
CPU reference with its declared BIOS/scroll boundaries. The1071 accepted effects
match the760-byte native controller's outgoing trace and native received-byte
history/log ordering, separately per direction. The combined reference executes
1422 recovered bytes, not a second maintained Chat implementation. It still
models UI/help/KEY/TX/logger/history callees; those actual application services
remain unverified in this integration.

The controller fixture now explicitly initializes DS334A to rows-2, matching
the Chat local-pane bottom, and can record keyboard-read boundaries. The optional
markers do not alter its ordinary returned trace. Fresh1089 native CPU cases,
342 send-owner DOS cases/119312 effects and4837 screen frames also pass on the
current source. Earlier receipts retain their historical source identities.

A separate23-file source export, excluding originals, existing objects, private
settings and Git metadata, reproduces the DOS executable exactly and repeats the
composition tests. Exact reports and fixture identity are bound in
[the receipt](validation/chat-session.json). This is component DOS/CPU evidence,
not a physical serial, Enigma or Synchronet session.

## Parent integration and memory

The current receive loop dequeues UART data before connection, monitor,
controller, transfer and autostart filters. Chat will need both a hold before
dequeue and a filter after connection classification, plus an idle service turn.
The main frontend must acquire the existing guarded screen owner, save/restore
the proper frame/cursor, dispatch help/KEY actions and compose deferred notices.
None of those hooks is enabled by this checkpoint.

A separate retained code bank addresses segment pressure but consumes conventional
memory. The current parent retains478272 bytes, and the accepted Enigma ASPECT
fixture previously exposed tight child admission. Adding3047 permanent bytes
would require fresh memory/admission evidence; a successful standalone bank is
not that evidence. Borrowing an existing snapshot area can avoid another358-byte
reservation but does not eliminate code retention.

The next implementation should investigate a source-built on-demand DOS overlay
loaded into checked existing far storage, then bind the foreground hooks. DOS
overlay loading, relocation/entry bounds, exact module identity, DS=SS, nested
callbacks, retirement and memory behavior must be proved before relying on it.
This is a proposed next mechanism, not an implemented loader or accepted package.
Repeat full Enigma/Synchronet connection and memory gates on the resulting parent
before reversible deployment and physical Boca/SPA2102 testing. Preserve existing
stacks, stream capacities, configuration and call history.

```sh
./tools/dev --command python standalone/test_chat_session_dos.py \
  --output build/NEW-chat-session
```
