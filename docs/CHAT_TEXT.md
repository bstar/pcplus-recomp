# Serviced direct TEXT for Chat

Original Chat's Alt1..Alt0 branches call48CC with the selected52-byte text
field at3758 +54*index. They do not call47B6's general action dispatcher or
inspect the preceding kind word. The maintained sender and optional module
ABI0102 now preserve this direct-TEXT path at explicit service boundaries.
The foreground still selects API0101 and refuses these shortcuts; live binding
and its echo/delay/transport services remain unfinished.

## Sender contract

`src/chat/text.c` uses68 caller-owned far bytes and880 code bytes, no private
DGROUP, heap, UART/BIOS polling or frame. Open accepts a disjoint conventional
far field with capacity1..52 including NUL. It copies/expands once before
starting; later changes to the source cannot change the pending send. Invalid
input, overlap, wrap, busy reopen or an unterminated field refuses without
changing the state or emitting an effect. A trailing caret, even after an
encoded NUL, is deliberately refused instead of reproducing the original
unbounded decoder's overread.

The recovered [TEXT grammar](META_KEYS.md) is retained: `^@` storesFF for
wireNUL, three carets produce one literal caret, two carets produce1E, and other
caret operands use their low five bits. An encoded00 terminates transmission
while decoding still validates the remainder of the field. Pause comparison
precedes FF handling: a pause markerFF consumes `^@` as a pause instead of
transmitting NUL.

Each ordinary nonzero byte requests optional echo, transmission, then calibrated
pacing in that order. FF requests only wire00, with no echo/pacing. A pause
requests the original BIOS-delay argument9, whose helper counts ten tick
transitions. Zero pacing still reaches its service boundary. Delay arguments
are not silently reinterpreted as milliseconds.

Step attempts at most32 sink calls. A refusing sink has no external effect;
the current effect remains pending. Echo, native-UART transmit completion,
BIOS-wait completion and calibrated-pacing completion are separate boundaries.
Queue admission alone must not advance the native transmit/pacing sequence.
Abort discards pending work; subsequent steps cannot repeat it. Callbacks are
bounded, foreground-only, and cannot mutate/reenter the owner.

## Optional loadable ABI

`build_chat_module.py --text` implies presentation and produces API0102 with
the existing50-byte request and430-byte session, including the68-byte TEXT
owner. The file is6176 bytes/image6128, SHA
`5ee67785e2efa4f630c6d17b391a99226fce9569af69070130cd5b53c87c0b72`.
It remains inside the existing8192-byte module window, with no private data,
stack, CRT or extra allocation. It is not a drop-in module for an API0101
parent; the matching loader identity/ABI is required.

Operation8 opens TEXT: `user` is the far text pointer, `value` its capacity,
`bar` the pause byte, `duplex` the echo flag, `budget` the pacing word, and
`transport_idle` must be nonzero. Chat must be active with no pending normal
send/RX effect. An unfinished buffered local line may remain and is preserved.
Operation9 steps TEXT using `budget`, `sink` and callback `user`. Ordinary
receive/session-step remain available so incoming Chat data can progress while
TEXT transmission refuses. The caller must schedule those services fairly.
Keys/open/unload cannot silently replace a pending TEXT send. Whole-session
abort clears it before module retirement; loader lifetime includes TEXT activity.

## Evidence and limits

The component fixture runs the production far code in actual DOS8086 and
compares1834 vectors/8471 ordered accepted effects against the exact recovered
48CC/4934 instruction bytes. These191 bytes were also compared with genuine
original2.01 SHA6401ccfd…7196904. Cases cover every nonzero caret operand and raw
byte, pause/FF/NUL precedence, triple carets, embedded NUL, echo flags0/1/FFFF,
pacing0/7/FFFF, maximum legal text, source kinds0..3, bounded synthetic refusal,
12 abort points/reopen, canaries and10 invalid-open controls including far alias
overlap. Native echo/UART/time services are CPU recorders, not rendered or timed
original callees.

The runtime module fixture loads API0102 through DOS4B03 at two addresses with
all remaining DOS paragraphs reserved. It compares88 ordered TEXT effects,
changes the original field after expansion, preserves unfinished local input,
rejects stale file/API and busy key/open/unload/reentrant operations, verifies
abort, image CRC, canaries and unchanged PSP/JFT/free memory. IncomingF0 renders
and produces history/log effects while TEXT TX is refused. Chat/TEXT code is
absent from the host link map and only executes from the loaded module.

A clean29-file public source export repeats both fixtures without originals,
private settings, prior objects or ancestor Git. Module/header, both host EXEs,
results and effect files match exactly. Default API0100's568 full frames and1071
session effects and API0101's eight presentation lifetimes still pass. A fresh
current-source foreground build remains byte-identical `5875536a`.
The [checkpoint receipt](validation/chat-text.json) binds the results.

Fresh REA inspection of original cursor/window helpers is retained in ignored
analysis storage. In particular,6E78 updates BIOS/hardware cursor state; this
does not establish equivalence with the maintained parser's cursor state.
The original TEXT echo calls0610's terminal dispatcher. The fixture does not
replace that rendering proof with ordinary pane painting or claim that its
effects inside the echo boundary are recovered here. Static Evidence
`ev_2e2bd86bed53d6481b1dd65744c3bb732b13180ee17e1a19c6c4e0d854098da2`
supports that cursor distinction; no original runtime was observed by REA.

```sh
./tools/dev --command python standalone/test_chat_text_dos.py \
  --output build/NEW-TEXT-owner
./tools/dev --command python standalone/test_chat_text_module_dos.py \
  --output build/NEW-TEXT-module
```

Next implement and verify live transmit acceptance, original echo context and
bounded delay completion; bind the ten foreground shortcuts without generic
KEY actions and preserve pre-read/RX ownership. Original Help, Alt-Z/config/UI,
broader failure/geometry/mouse coverage and final BBS/package/physical gates
remain open. No foreground shortcut, selected package, physical PC or production
bridge/server was changed by this component checkpoint.
