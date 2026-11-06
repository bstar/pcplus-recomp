# Foreground Chat text shortcuts

The [queued-key follow-up](CHAT_QUEUED_KEYS.md) now uses the existing deferred
FIFO while TEXT/native echo cannot accept ordinary input. Earlier descriptions
of holding that input in BIOS apply to this initial foreground checkpoint.

The opt-in `--chat-foreground-text` build connects Alt-1 through Alt-0 to the
ten imported KEY text fields in ordinary DOS8086 main. It passes direct text,
native local echo, pause/RX, queued typing, cancellation and nested-ASPECT
tests. This is a development checkpoint; it does not replace the installed
connection package or establish full Chat parity.

Parent SHA256 is
`e03c6e410018d93857509392e8c1d41d0fe04a6c93547be2ff66e1298c647674`.
The matching module is API0104, with a476-byte caller-owned session and the
unchanged50-byte request. Its identity is pinned by the parent loader's generated
file and relocated-image CRCs. Earlier module versions remain separately
buildable; disabling this flag reproduces the prior457ebb17 parent exactly.

## Routing and ownership

The recovered Chat controller skips the kind word of each54-byte KEY record
and calls its52-byte text field directly. This build retains that behavior for
all kinds0..3; PROGRAM and ASPECT are not substituted for Chat TEXT. The text
owner copies and validates the field before emitting effects. Configured pause,
duplex and pacing are sampled when a shortcut starts. Literal wire NUL,
caret escapes and native pacing use the previously tested text and timing
owners.

The module now owns shortcut selection, cursor initialization and fair bounded
service of text and pending normal RX/send effects. Ordinary incoming Chat
text remains raw pane text rather than becoming terminal ANSI commands. A
refused physical TX remains pending; an accepted echo is never repeated.
Native echo faults abort the session after the current callback returns. An
echo admission refusal is also a fault, avoiding an infinite retry loop.

An immutable24-byte binding supplies four explicitly DS-relative read-only
configuration pointers, three far callbacks and the far22-byte cursor context.
The parent and module require DS=SS. The module validates extents and cursor
overlaps, then copies the descriptor into the session. Callback lifetime and
code remain the trusted parent's responsibility. Operation10 binds an active
unbound presentation; ordinary foreground construction supplies the descriptor
through operation6. After construction the request's table returns to its RX
translation role. Generic operations8/9 cannot bypass initialization of a bound
foreground session.

The code window grows from8192 to12288 bytes inside the already retained63000
bytes of frozen storage. State begins at12288, presentation at13000, request
at13200, translation at14000 and native echo cursor at14500. No new allocation,
private DGROUP, module stack or CRT is introduced. The independent native echo
cursor persists between bytes. After each accepted native echo, presentation
cursor selection is invalidated so the unchanged packed local-pane cursor is
restored. Retaining that packed cursor follows the recovered controller's
behavior after48CC; this is not a new execution of the full original controller.

Normal BIOS typing is held during a pending text send and resumes afterward;
Escape may cancel it. The existing native-parser-busy guard still prevents
module reentry/unload. The DOS tests below exercise ordinary text pauses, not
BIOS key cancellation from inside a native parser continuation.

## Memory gate

The first linked parent retained479488 bytes and failed the nested-script gate.
DS-relative bindings and module-side construction reduced it to479456, which
still failed. Those negative reports are retained. Sharing the six identical
foreground assembly bridge bodies then removed144 allocated bytes, yielding
479312 bytes:96 fewer than the previous passing echo parent. The bridge still
preserves registers and converts the C event result to carry for each entry.
The optional flag selects sharing; older builds retain their exact bridges.

The final DOS8086 test passes26 checks, including three NOCLEAR DOS children
with all six stream buffers held, missing-file recovery and exact viewport
return. The interpreter remains byte-identical cbdee194. Application stack8192,
interpreter heap growth512, near DS=SS65504, resident CS65368, all stream
buffers and history/display/workspace capacities are unchanged.

## Validation and remaining work

`standalone/test_chat_live_keys_dos.py` runs the actual main loop, BIOS keys,
module and synthetic physical UART. It exercises all ten imported records
across kinds0..3, wire NUL, triple carets, configured pause, nonzero pacing,
preservation of unfinished local input, incoming raw Chat text, Escape return
and ordinary terminal CPR after return.

`standalone/test_chat_live_echo_dos.py` enables native local echo through Alt-E.
A passive timer observer reads VGA/BDA without writing product state, UART or
keyboard data. Captured frames show AB with incoming RXD during the configured
pause, then ABC with no locally echoed wire NUL and the restored local-pane
cursor. It also checks queued X/Enter through a pause, Escape cancellation and
ordinary terminal return. Its observer uses conventional memory; it is separate
from the unobserved ASPECT capacity test. The initial cancellation test pressed
Escape before the full prefix was sent; the corrected test allows the prefix
to complete before cancelling during the pause. That fixture failure is retained.

`standalone/test_chat_live_module_dos.py` separately loads the exact API0104
image through DOS4B03 at two addresses while all other DOS paragraphs are
reserved. It checks null KEY and cursor aliases into state/code/backup,
rebind/generic-operation refusal, stale API/file identity, copied KEY text,
ten-tick pause with RX/history/log progress, TX refusal without duplicate echo,
unfinished local input and cursor initialization, callback reentry/unload
protection, constructor binding, accepted echo faults and admission refusal.
Both failure types restore the frame and retire without TX or retry. Image CRC,
canaries, PSP/JFT and free memory remain intact. These callbacks record TX/echo;
the native-echo and physical-UART tests are separate. An initial fixture expected
column0 despite having typed L; correcting its expectation to column1 required
no application change.

The [validation receipt](validation/chat-foreground-text.json) binds exact
identities and report hashes, including source-only reproduction and separate
BBS regressions. CPU echo tests retain their modeled-hardware and supplied-owner
scope. Enigma/Synchronet regressions exercise ordinary terminal workflows with
Chat inactive; they do not establish interactive Chat inside those BBSes.

Still required: broader binding alias and lifetime failure coverage;
actual native-parser-busy key and cancellation tests; flow-control stalls and
printer/logging failure coverage; broader geometry and mouse tests; original
Chat Help, Alt-Z/configuration integration; final package and physical
acceptance. Shared native attributes/modes/history/log behavior and bounded
parser waits retain their documented limitations. No claim of perfect BBS
rendering, full original Chat execution, SIP/audio or analog-modem acceptance
follows from this checkpoint.
