# Recovered UART module

The source baseline is PCPlus 2.01, SHA-256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The resident code block is `[0xaa5c,0xaea7)`, 1,099 bytes including six scratch-data
bytes and one alignment byte. A separate receive-timeout routine adds 46 bytes.
`uart-layout.json` maps analyst-selected names to original DS offsets.

## Two build modes

The default flat-binary mode preserves the original addresses and encodings.
`build_compat.py` verifies both source units byte for byte before inserting them.
The mode with `UART_OMF` assembles the same UART instruction source to an OMF
object. State and application-service references become linker symbols; the ISR
loads the relocated data segment. Open Watcom's linker produces an independent
DOS MZ executable from that object and the newly written diagnostic host.

The standalone data layout is new. No source executable, original data segment,
original overlays or original UI resources are used by this link.

## Calling convention

All calls are near, within the common 16-bit code segment. **DS must equal SS**:
several routines read stack arguments through DS:BX rather than SS:BP. The
standalone entrypoint establishes this explicitly. Callers must not assume
volatile AX/BX/CX/DX/ES are preserved unless the particular implementation does so.

| Entry | Original offset | Arguments/result | Stack cleanup |
| --- | --- | --- | --- |
| `uart_carrier_detect` | aa5c | AX has masked DCD bit (0x80 or zero) | No arguments |
| `uart_receive_byte` | aa65 | AX is masked byte or 0xffff when empty | No arguments |
| `uart_available` | aad9 | One word timeout in seconds; reads a byte, not just availability | Callee removes 2 bytes |
| `uart_transmit_byte` | ab0b | One word, low byte sent; honors configured flow control | Callee removes 2 bytes |
| `uart_transmit_buffer` | ab92 | First word count, second near buffer pointer | Callee removes 4 bytes |
| `uart_transmit_string` | abac | One near zero-terminated string pointer | Callee removes 2 bytes |
| `uart_clear_receive_buffer` | abca | Resets count and read/write pointers | No arguments |
| `uart_unreceive_byte` | abde | Moves read pointer back; caller must ensure valid history | No arguments |
| `uart_set_rts` | abfa | Word 1 raises RTS; other values lower it | Caller removes 2 bytes |
| `uart_set_baud_divisor` | ac27 | First word baud, second word 1 forces divisor 1 | Caller removes 4 bytes |
| `uart_set_line_control` | ac5d | Parity, data bits, stop bits as three words | Caller removes 6 bytes |
| `uart_install_interrupt` | ad65 | One word interrupt vector number | Caller removes 2 bytes |
| `uart_restore_interrupt` | ada4 | One word interrupt vector number | Caller removes 2 bytes |
| `uart_transmit_cl` | ad93 | CL byte, bypasses configured flow control | No arguments |

Other exports enable/disable the UART/PIC, wait for transmitter empty and
save/restore hardware state. The baud API takes a 16-bit word: 115200 is selected
by its special second argument, not by truncating a 115200 literal.

## State and observed behavior

- A 4096-byte receive ring has independent read/write offsets and a word count.
- Flow control begins around 3072 queued bytes and resumes at 128 or fewer.
- Software flow mode consumes XOFF/XON into transmit-pause state rather than
  delivering them as payload. Binary tests exclude those control bytes in this mode.
- The transmit-pause path can wait 20 changes of DOS seconds, then clear its paused
  state and transmit. This inherited policy is not an indefinite XOFF wait.
- The independent BIOS receive timeout counts 36 BIOS tick changes. These are
  distinct clocks; decompiler pseudocode incorrectly removed the BIOS wait path.
- The recovered legacy transmit entrypoints retain their original blocking waits.
  The maintained diagnostic uses `uart_try_write` instead, so keyboard handling
  remains active during CTS, XOFF and transmitter-ready stalls.
- Controlled replay reproduced count 4104 after filling the ring and sending eight
  extra bytes with hardware flow enabled. The maintained OMF build now guards
  every ring insertion and drains/discards excess UART bytes without overwriting
  unread data. `uart_rx_dropped` counts discarded bytes, saturating at 65535.
  The exact flat build retains the original for comparison.
- Maintained OMF receive paths queue XON/XOFF instead of spinning on THRE in the
  interrupt. The foreground loop calls `uart_poll_flow` to send pending control.
  A later XON supersedes a not-yet-sent XOFF when the buffer drains quickly.
- Nine controlled replay cases now cover watermarks, overflow in all three modes,
  CTS recovery, bounded CTS/THRE/XOFF stalls, deferred flow, DOS-second rollover,
  divisor settings and hardware/vector restoration. Physical FIFO/IRQ behavior
  remains unverified.

The diagnostic's host services return DOS seconds and omit screen-save,
message and bell presentation. They are explicitly new host implementations,
not recovered PCPlus UI. Its Escape callback intentionally does not consume keys.

## Evidence

REA/Ghidra exports were used alongside instruction decoding. The interrupt entry
was discovered using a synthetic MZ entrypoint change, never by executing the
synthetic input. Selected exports are retained in `docs/evidence/uart`.

- ISR 0x1acb8: Evidence `ev_0ce93bfdceeb449f379dcaaaf1e5cef7471d936a6b5c8bd90a69faa9d4edb01d`.
- Seconds helper 0x13323: Evidence `ev_d1512304174bff6ee8621d2f8389779e4edc7d04eb90837e5e3a1c28b7ad36d4`.
- Escape helper 0x13f4b: Evidence `ev_2e16f7b28664c5e1fd7f71b5fa526ed427446dddb1ece938051a9346a47c4d47`.

Static exports establish original instructions; DOSBox-X tests establish only the
specific exercised runtime paths. A full source rebuild and physical-device
validation remain incomplete.

## Maintained foreground API

`src/uart/api.asm` exports two near-call services under the same DS=SS contract.
`uart_try_write` takes AL and preserves AX/DX. CF=0 means the byte was submitted;
CF=1 means CTS, software flow or transmitter readiness prevented it, with no
submission. The caller retains the byte and returns to its event loop.
`uart_poll_flow` preserves registers and FLAGS and performs one bounded attempt
to send pending XON/XOFF. Call it regularly from the foreground even when normal
output is blocked. The diagnostic keeps a pending output byte and continues to
check the keyboard while retrying. Its startup banner also uses the bounded API.

These source-only fixes are not inserted into the original-size compatibility
candidate. That candidate retains original UART behavior and only the historical
two-byte CSI-q fix. The maintained driver is intended for the full source rebuild.
