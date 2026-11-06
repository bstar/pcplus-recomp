# Experimental physical TEXT transmit service

`--chat-text-transport` links an optional service for the recovered Chat TEXT
sender. **Keep it disabled for application use: nested ASPECT RUN regresses.**
It does not enable Alt-number shortcuts, select API0102, change the selected
connection package or update the physical PC.

The ordinary Chat sink accepts queue admission. The new
`terminal_chat_text_tx_sink` accepts only CHAT_TX after `uart_try_write` actually
emits its byte. It requires Chat owner2, no quit/ASPECT/native macro, an empty
ordinary TX queue, one physical grant and connection state0/6. On success it
consumes the grant, increments the progress epoch and records the user byte.
Refusal preserves those states. Echo/delay effects remain refused. No keyboard
or receive byte is consumed; no private queue or near data is added.

The final implementation reuses `connection_uart_write_resident`. Resident CS
remains65528/near65504; CHAT_ADAPTER_CODE grows110→224 bytes. Alignment raises
minimum allocation479408→479520 bytes. Stack8192, heap-growth quantum512, six
stream buffers and capacities are unchanged. Experimental parent SHA:
`0258248b621e2280cd02a0542d71dc86634ff248f5c7d32112793aac1d80fbfa`.
The presentation module remains API0101/SHAf0e91e2b…1850f.

Six linked CPU checks execute actual sink/UART/IRQ/queue/recorder instructions:
all256 bytes and exact recording, one byte per grant/epoch wrap, connected
state, atomic refusal, THRE/CTS/XOFF/BREAK hold, ordinary reply/native macro
priority, binary RX preservation, no keyboard read and register/stack ABI.
BIOS, filesystem and hardware are modeled; product routines are not patched.
Owner2 is a supplied precondition, not Chat-entry acceptance. Normal DOS8086
main separately passes buffered Chat entry/input/RX/return and the held-prefix
regression, using the existing foreground/ordinary sink. It does not prove
foreground TEXT scheduling or echo/delay integration.

A clean648-file source export repeats the exact parent/module/header and six
CPU checks. Its flag-disabled parent remains exact5875536a. Originals, private
configuration and prior objects are absent; a Git ceiling prevents ancestor
checkout discovery. Reproducibility does not override the failing ASPECT gate.

## Failing gate

Actual8086 DOS uses the unchanged cbdee194 interpreter, three nested NOCLEAR
children, six512-byte streams and missing-file recovery. Both0caaaefa (initial
extra resident thunk) and0258248b (reused thunk) fail RUN with error10/opcode9B;
missing-file recovery passes. The flag-disabled5875536a control passes all26
checks with the same interpreter/settings/scripts. Negative captures remain.

A separate386/UMB passive observer reproduces0258248b's failure. Each failed
child reports one external call, raw statusFFFF, error10, cleanup error0 and
retired scope/display/program/process owners. It records a successful38-para
allocation followed by a refused254-para request: DOS error8, largest offered
block67 paragraphs. These are observations, **not a complete diagnosis of the
error10 conversion or proof that112 extra parent bytes explain every effect**.
The observer adds memory and is separate from unobserved8086 capacity evidence.

The initial fixture manually invoked an ISR in a harness already injecting
IRQs, causing an extra RX byte. Corrected tests use automatic delivery once;
no product RX fix was made. An initial stale interpreter manifest was rejected
before DOS; actual tests use the current-source cbdee194 build. A first cold
receipt mistyped the header name; final checks use `chat-module/expected.h`.

Next isolate native process allocation/failure and fund parent memory without
reducing stacks, streams or capacities. Restore the ASPECT gate before promoting
this flag, then finish original echo, bounded delays and foreground TEXT keys.
Full BBS/package/deployment/physical acceptance remains open.

See the [receipt](validation/chat-text-transport.json),
[sender](CHAT_TEXT.md) and [foreground core](CHAT_FOREGROUND_CORE.md).
