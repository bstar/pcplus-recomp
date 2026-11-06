# Chat effects through the actual parent

`--chat-adapters` adds the FAR cdecl `terminal_chat_sink(kind,value,user)`
callback. It requires the presentation build. Original Alt-O/reference entry,
keyboard ownership and main-loop receive/poll hooks remain unbound.

The callback requires the parent's DS=SS and exclusive Chat storage owner2;
it refuses while quitting or executing ASPECT. Unknown effect kinds refuse.
No private queue, polling, key read or direct UART access is introduced.
TX checks the existing 1,024-byte queue before calling its user-origin enqueue
path. Full-queue refusal leaves bytes and provenance bits unchanged, allowing
the Chat session to retain the pending effect. Values above255 refuse as TX.

LOG and HISTORY pass the full original word argument to the recovered native
services. History retains RET2; logging retains caller cleanup, CR/LF settings,
printer/capture routing and native filters. Literal00FF/007F logging is filtered,
while promotedFFFF/FF7F reaches the native writer. The bridge does not normalize
these to the same byte before native dispatch. If printing is enabled, LOG
reserves two printer slots before any effect; native CR plus optional LF cannot
half-fill a full queue. Refusals have no product-data effect. Accepted native
logging still uses the existing checked-file error/notice policy; general DOS
I/O failure and foreground notice handling are not newly proved here.

The adapter object has17 resident code bytes and110 far-bank code bytes, no
private data. Parent `c1b3faf8` uses478240 minimum module bytes, near65488 and
resident CS65504. Its minimum grows128 bytes over the preceding presentation
parent; alignment means resident extent grows16 rather than17. Capacities and
stacks are unchanged. Six buffered ASPECT streams across three DOS children,
including missing-file recovery, still pass normal-main admission.

## Actual DOS composition

The dedicated DOS8086 host loads the real parent and module as DOS overlays.
It invokes parent APIs using their actual DS=SS and declared stack. The loaded
Chat module calls the actual parent sink; no Chat, sink or native-service
implementation is statically linked into the host.

At two module load addresses the test queues a buffered line, refuses TX while
its queue is full, checks all1,024 bytes and128 provenance bytes unchanged,
then verifies wrapped admission and user-origin bits. Printer backpressure
refuses the pending LOG before history changes; a later step completes the
ordered line effects. Duplex's recovered LF behavior is preserved even with
the independent newline option off. CP437 RX history/log effects and signed
native-word filters pass. With exactly two printer slots left, native CR/LF
fills both; the next LOG refuses without duplicating capture output.

Two actual checked capture files have the exact expected ten bytes. Ownership,
quit/child and malformed requests refuse; canaries, PSP, JFT and largest free
block remain correct. These are queue-admission and real DOS log/history checks,
not observed UART delivery or a connected Chat workflow. Parent main is tested
separately by ASPECT admission, not executed by this composition host.

A clean637-file public source export reproduces parent/module/header, host,
result and both logs exactly without originals, private inputs, prior objects
or ancestor Git. All54 linked storage cases/16cycles still pass. Disabling only
the adapter option rebuilds preceding parent `75fdb753` byte for byte.
See the [checkpoint receipt](validation/chat-parent-sink.json).

```sh
./tools/dev --command python standalone/test_chat_parent_sink_dos.py \
  --terminal build/PARENT/TERMINAL.EXE --output build/NEW-sink-composition
```

Next bind terminal entry, pre-dequeue hold, translated RX, bounded idle service,
direct TEXT/Help and notice/trap/disconnect retirement. Recheck full frontend
memory and Enigma/Synchronet after those hooks. The preceding presentation
parent's BBS results are not acceptance of this new image. The older unexplained
redial miss remains open. Selected package, physical DOS PC and production
SynthModem/Enigma are unchanged; no full parity or physical acceptance claim.
