# Transfer UART integration boundary

The transfer routines already exist in `reconstruction/uart/core.asm`. This
module reuses that source rather than copying the timed reader, byte getter,
bulk transmitter or software-ring flush. `reconstruction/transfer_uart/` adds
their exact DOS-clock dependency, a relocatable form of the already-recovered
BIOS header timeout, source-owned link aliases and a separate extent guard.
It does not yet connect a complete live upload/download session.

The selected original SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
`provenance.json` records byte ranges, hashes and saved REA evidence for DOS
seconds3323, time extractor778c and BIOS timeout5ca0. Flat assembly matches
11+33+46 original bytes. No new REA session or analysis-image execution was
needed; the existing saved exports and SHA-verified original replay were used.
The reused UART core retains its documented OMF-only ISR overflow/flow safeguards;
those are separate from the unchanged entries described here.

## Original contracts

Calls are near, DS=SS. AX/BX/CX/DX/ES and flags are volatile unless specified.

| Existing entry | Original CS | Inputs and result | Cleanup |
| --- | --- | --- | --- |
| `uart_receive_byte` | aa65 | AXbyte0..255 or ffff when the ring is empty | No arguments |
| `uart_available` | aad9 | One timeout word; consumes a byte, returns AXbyte/ffff; preserves SI/DI | Callee2 |
| `uart_transmit_byte` | ab0b | One word, low byte transmitted literally | Callee2 |
| `uart_transmit_buffer` | ab92 | Count word first, near buffer pointer second; preserves SI/DI | Callee4 |
| `uart_clear_receive_buffer` | abca | Resets software count and read/write pointers | No arguments |
| `transfer_uart_header_byte` | 5ca0 | AXbyte/ffff, waits at most36 observed BIOS tick changes | No arguments |

The immediate getter reads the software ring, not the hardware RBR directly.
The flush similarly does not drain the physical UART or send anything to a peer.
It executes CLI then STI, so it does not preserve an initially-cleared IF.
The IRQ remains responsible for newly arriving hardware bytes.

`uart_available` checks the ring before calling its clock provider. If a byte is
already queued, it returns it without a DOS time call. When initially empty it
calls the clock even for timeout0; zero then performs an immediate getter.
A positive timeout decrements once whenever the seconds value changes, ignoring
how large the change was. Repeated identical clock samples do not count. The
59-to0 transition counts once. This is not a full elapsed-seconds calculation,
and the next transition may happen shortly after entry. No keyboard, carrier,
flow poll or foreground application callback executes during that wait.

The exact `pcplus_seconds` calls `transfer_dos_time(sample)` and returns the
fourth word of its sample. The time extractor calls INT21h/AH2Ch and stores
four words: hundredths, hour, minute, second. Its near pointer argument is
callee-cleanup2. It clobbers BX/CX/DX as well as AX. The eight-byte
`transfer_dos_clock_sample` is caller/host-owned state and makes this clock
nonreentrant. A host must not call this DOS service from its UART ISR or another
DOS-reentrant context. Existing maintained terminal clock services can remain
separate providers; do not link two definitions of `pcplus_seconds`.

The BIOS header timeout instead uses low BDA046ch tick observations. It enables
interrupts, samples up to36 changes, and reads the ring immediately if it becomes
nonempty. It does not use DOS seconds or service keyboard/carrier/flow callbacks.
It clobbers ES. Counting observations rather than full elapsed ticks means this
is the preserved original policy, not a maintained full32-bit day deadline.

## Blocking transmit behavior and safe extents

Bulk transmit sends bytes literally, including00 andff; it has no KBD ff-to-NUL
or TEXT caret/pause expansion. It invokes the original flow-aware byte writer
for every byte. Its loop reads the first byte before decrementing the count:
**count0 transmits65536 bytes and wraps through DS**. Pointer/count extents are
unchecked. The diagnostic proves that behavior separately from the guard.

Original byte transmission can block indefinitely on THRE. HARD mode polls CTS
and the local Escape service; Escape bypasses CTS and continues transmitting
rather than returning a cancellation status. A paused software transmitter
presents its external wait UI, polls Escape and counts20 DOS-second transitions,
then clears its paused flag and proceeds. These legacy policies cannot supply
a responsive live transfer controller by merely renaming entry points.

`transfer_uart_send_bounded(count, pointer)` is a maintained near C caller-cleanup4
adapter. It accepts count1..1024, a nonzero near pointer and a nonwrapping extent;
an extent ending exactly at10000h is valid. AX1 rejects before port IO; AX0 means
the raw blocking call completed. BP/SI/DI are preserved. It does not validate
buffer ownership, add flow/cancel deadlines or turn the call asynchronous.
It is not stack-compatible with the raw callee-cleanup4 entry without a bridge.

A live maintained transfer scheduler should use the existing nonblocking
`uart_try_write`/`uart_poll_flow` and foreground input/controller service with
explicit deadlines and accepted-byte accounting. Keeping the exact native
callbacks available is useful for bounded diagnostics and comparison, but does
not remove the above integration requirements.

## Link aliases

`bindings.asm` provides tail aliases preserving the raw ABI:

| Transfer names | Reused service |
| --- | --- |
| `send_timed_byte`, `receive_timed_byte` | `uart_available` |
| `send_transmit_byte`, `receive_transmit_byte` | `uart_transmit_byte` |
| `send_transmit_buffer` | `uart_transmit_buffer` |
| `send_flush_input`, `receive_flush_input` | `uart_clear_receive_buffer` |
| `send_receive_byte` | `uart_receive_byte` |
| `send_header_byte`, `receive_header_byte` | `transfer_uart_header_byte` |

Assemble the clock/header with `TRANSFER_UART_OMF`, UART core with `UART_OMF`,
and provide the normal UART state plus eight-byte clock sample. Existing
`layout.inc` lists required application flow UI/Escape/screen services. The
diagnostic supplies explicit UI fixtures with no display and a configurable
Escape result; they are not proposed production no-op implementations. A full
application must link real services or use the maintained scheduling boundary.
Do not link these aliases alongside another adapter exporting the same names.

## Verification

```sh
./tools/dev --command python standalone/build_transfer_uart.py
./tools/dev --command python standalone/check_transfer_uart.py
./tools/dev --command python standalone/test_transfer_uart_dos.py
# Optional SHA-verified resident-code comparison; original is never DOS-launched:
./tools/dev --command python standalone/check_transfer_uart.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

TUART.EXE SHA256 is
`b976f8a928dc052b7cfc4c2adf3b34f7e869e1b4748ba2d6f30d2652a90db28b`.
55 linked inputs equal55 genuine-original replays. They cover timeout0/1/2/3/10,
repeated seconds and minute wrap, queued binary bytes,128/1024-byte raw writes,
CTS-ready operation, ring flush leaving RBR untouched, BIOS header timeout and
exact time sample layout. Fifteen additional source-linked cases cover invalid/
edge extents, the legacy zero-count wrap, CTS/THRE blocking, Escape's CTS bypass,
software pause expiry/escape, and timed-read absence of local cancellation.
Only DOS/BIOS/port boundaries are modeled; no tested product callback is skipped.

The isolated actual DOS8086 diagnostic installs the recovered IRQ, receives a
synchronization byte with the timed reader, transmits1024 binary bytes containing
all256 values four times through the real bulk/byte writer, receives its peer's
acknowledgement, checks an empty ring and restores UART/vector hardware state.
Its loopback peer sees exactly the expected bytes. NONE flow is intentional for
this diagnostic. It does not establish physical CTS/DCD timing, cable/modem
behavior, full transfer negotiation or a complete PCPlus session.
Evidence remains under ignored `build/transfer-uart/` and
`build/transfer-uart-dos/`. Normal builds/tests have no original or REA database
input; only the explicit optional comparison reads the original executable.
