# v86 DOS door input candidate

The owned BRE image uses a non-FIFO UART input path. In the pinned v86 runtime,
`serial0_send()` enqueues a whole string without guest execution between bytes.
The actual baseline trace records the complete `LoC Lab` plus CR burst arriving,
one guest read of `L`, seven pending bytes and receive interrupt identification
4. A later CR finds the same pending bytes while the instruction counter has
advanced. This is a server-side guest UART stall, separate from PCPlus's
outgoing key encoding.

The staged worker uses an authored byte queue. It injects one byte, then checks
the pinned UART's `input.length` before injecting another. The guest can clear
its receive interrupt between characters. Scheduling polls at 1ms; it is not a
baud-accurate serial-wire model or a throughput guarantee. The 64KiB host ring
owns its data and rejects an oversized chunk atomically rather than silently
truncating a command. Closing cancels its timer and discards pending input.

The component checks cover all 256 byte values, ordering across chunks and ring
wrap, caller mutation, a busy UART, capacity, cancellation, callback failures
and reentrant enqueue/close. Actual reference acceptance sends the name in one
burst and requires confirmation, the real game menu and a normal return to
Doors and Main. Both traced and untraced fixtures run that route. Trace output
must show at most one byte in the guest UART and every injected byte consumed.
Actual DOS checks use a separate uninstrumented fixture and unchanged source
terminal; reference acceptance alone is not a DOS-client claim.

After preparing a fresh stopped fixture with `enigma_v86_fixture.py`:

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-v86-input/stage.py \
  --candidate build/bbs-lab/NEW/candidate
./tools/bbs-dev --command node lab/bbs/patches/enigma-v86-input/check_serial_input.js
```

The stage refuses an already modified worker or a running candidate. An
optional `enigma_v86_input_trace.py` stage must follow the bridge stage; it
explicitly changes the worker identity and is diagnostic only. Keep all image,
database, trace and game-output artifacts under ignored `build/`. No live board
source or image is patched by these tools.

Remaining work includes physical modem behavior, guest binary protocols,
throughput, saved-realm persistence, concurrent operations and integrated
overflow/error shutdown persistence. Component error handling does not prove
that the existing door/isolated-worker error path saves every guest write.
Deployment remains separate from this candidate experiment.
