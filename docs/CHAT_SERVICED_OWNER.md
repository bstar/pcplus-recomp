# Serviced Chat send owner

`src/terminal/chat_owner.c` projects the keyboard/send branches of the
[recovered native controller](CHAT_NATIVE.md) into a yielding state machine.
It is a component for live integration, not an enabled application command.
The physical installation, selected parent, ASPECT and package recipe remain
unchanged.

## Storage, ABI and scheduling

The caller supplies a320-byte context through an explicit far pointer. The
298-byte input capacity remains; the299-byte array includes its terminator.
No second output queue, heap, global state, private screen frame, DOS call or
BIOS/UART polling loop is introduced. The compiled owner has no CONST, CONST2
or DATA bytes in DGROUP. Its optional CHAT_GROUP contains900 code bytes and
uses far cdecl entries with DS=SS, plus a far cdecl sink callback.

`chat_owner_open` starts a fresh owner with explicit buffered/duplex/LF settings.
`chat_owner_key` refuses without mutation while prior output effects are pending.
Its result tells the frontend whether to paint the accepted key, dispatch help
or a KEY record, or close. Local-control interpretation and painting therefore
do not happen twice on retries. Escape discards an unfinished buffered line.

`chat_owner_step` attempts at most32 sink operations per turn, regardless of a
larger requested budget. Zero budget performs no operation. A refusal returns
immediately; the same effect is retried later. The sink must return refusal
only when it has made no externally visible change. TX, logger and history are
separate effects, so refusal after an earlier accepted operation cannot repeat
that earlier operation. Buffered sends use the existing input array throughout
TX and echo; another key is not admitted until the whole event has retired.

The owner retains native ordering: paint ordinary keys; immediate TX then
optional log/history; buffered line TX then duplex log/history; optional LF TX
then duplex LF log/history. Full298-byte overflow flushes add no LF. Ctrl-Q/S
bypass buffered input without painting or echo. Native signed-byte promotion,
raw-word immediate echo, embedded-NUL truncation, backspace clamping, Enter
variants, ten KEY records and help are retained explicitly.

`chat_owner_abort` retires pending state on a confirmed logical disconnect.
It is not tied directly to a raw DCD edge. It cannot retract effects already
accepted by an external sink. The eventual UART adapter must distinguish queue
acceptance from wire completion, drain or retire its own queue correctly, and
finish that ownership before restoring normal terminal/command behavior.
Deadline, carrier classification and frame ownership remain parent services.

## Actual DOS checks

The same production component runs in DOS8086 with both ordinary near calls
and a distinct retained code group. A DOS-allocated block holds the guarded
context outside DGROUP, and the sink receives its own far context. Each run
checks342 vectors and119312 exact ordered effects against the recovered native
760-byte routine running under a CPU model with explicit service boundaries.
This compares the real instruction trace with the maintained C, not two copies
of the maintained state machine.

Vectors include both modes and noncanonical nonzero settings, line boundaries
through repeated overflow, backspace, ordinary/extended Enter, flow keys,
all ten KEY slots, help, high/raw BIOS values and embedded NUL. Alternate cases
refuse the first five sink attempts and every third later attempt. Zero-budget,
pending-key refusal,32-attempt limits and state guards are checked throughout.
Sixty-four permanent refusals yield without progress or state corruption;
forty-two additional abort progress points cover immediate, buffered and flow
effects, including TX/log/history/LF retirement. No effect escapes after abort.

The first banked test correctly rejected a same-CS layout: changing the C segment
name alone did not establish a distinct segment frame. The explicit aligned
CHAT_GROUP fixes that; the DOS fixture checks the far entry's segment differs
from its own CS before accepting the run. The failed attempt is retained locally.

A separate eight-file source export rebuilds the banked DOS executable exactly
and repeats all342 comparisons. It excludes originals, previous objects,
private configuration and Git metadata. See the
[receipt](validation/chat-serviced-owner.json) for report and executable hashes.
These checks use synthetic sinks and UI/keyboard boundaries. They do not prove
live UART/CTS handling, complete native callees, BBS rendering or hardware.

## Remaining integration

Bind Alt-O/reference/browser entry, borrow checked far storage while Chat owns
the foreground, implement the two panes and translated incoming-byte routing,
and compose real UART/log/history adapters with macro/help and deferred notices.
Entry must defer for parser, macro, child, transfer or other screen ownership.
Verify cursor/frame restoration, disconnect/exit, bounded backpressure and no
dropped input in actual DOS, followed by Enigma/Synchronet and physical tests.

The current parent's near code and data are tight, and its full Enigma ASPECT
startup has limited conventional-memory headroom. A separate code bank solves
segment addressing pressure but does not make conventional memory free. Account
for retained code/context and repeat the current full login/carrier/reconnect
admission gate before selecting a Chat-enabled package. Do not silently reserve
another320 bytes in DGROUP or reduce existing stack/stream capacities to fit.

```sh
./tools/dev --command python standalone/test_chat_owner_dos.py \
  --banked --output build/NEW-chat-owner
```
