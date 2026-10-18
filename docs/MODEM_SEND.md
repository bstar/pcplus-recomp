# Original modem command sender

Actual PCPlus2.01 sender `48cc..4934` (104 bytes) and its calibrated delay
`6b72..6b98` (38 bytes) and BIOS delay `6b98..6bb6` (30 bytes) are recovered as
exact source/OMF modules. The source-only diagnostic links these routines to the
already recovered caret expander and **actual recovered UART transmitter**.
Its loopback DOS test sends binary NUL correctly and restores hardware state.
This is the original blocking sender, not the maintained live connection
engine's nonblocking send policy or a complete modem application.

No private PRM/dialing data is read. Default build/test inputs are maintained
source and tracked provenance; original executables and REA exports are optional
analyst evidence only. Original SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.

## Callable routines and dependencies

`modem_send_original(command_offset)` is a near C call. Caller removes its two
argument bytes; DS must equal SS and DF must be clear. It reserves a130-byte
stack buffer and calls actual recovered `modem_expand_original` (`4934`) into
that buffer, then walks the expanded NUL-terminated result. The last byte of that stack area (BP-1) is also the current-character local,
so safe expanded content is at most128 bytes plus its terminator below that
local. It has no source length, validation/status result, cancellation argument
or deadline. Call it
only with a separately validated bounded command; malformed/trailing caret or
oversized input can overrun the original stack buffer. See MODEM_CONFIGURATION
and the separate maintained `modem_expand_bounded` API for validation rules.

BP/SI are explicitly saved. Other registers/ES/flags are affected by its callees;
there is no defined success/error return value. It does not preserve the caller's
ES across original delay calls. The three state imports map as follows:

| Original DS | Symbol / storage |
| --- | --- |
| `1d66` | `modem_send_pause_marker`, byte compared against each expanded byte. |
| `1d1a` | `modem_send_local_echo`, word: ordinary bytes echo when nonzero. |
| `1d68` | `modem_send_pacing_units`, word passed to calibrated delay after ordinary output. |
| `7a4e` | `modem_send_delay_floor`, calibrated busy-loop comparison word, outside PRM. |
| `7ac4` | `modem_send_delay_count`, calibrated loop initial count, outside PRM. |

The near service boundaries are:

- `modem_expand_original(source,destination)`: caller removes four bytes.
- `uart_transmit_byte(word)`: actual recovered `ab0b`, callee `RET2`.
- `modem_send_echo_character(word)`: original application `0610` terminal
  renderer, caller removes two bytes. The diagnostic supplies an explicitly
  maintained BIOS teletype service; it does not claim original0610 recovery.
- `modem_send_delay_calibrated(word)` and `modem_send_delay_bios(word)`: both
  actual recovered helpers remove their two argument bytes with `RET2`.

Overlay5's recovered dial attempt temporarily disables local echo, raises pacing
to at least30 through signed comparison and sends prefix + number + suffix,
then restores settings. It can bind its explicit `dial_send_command` import to
this sender once all state/UART/UI boundaries are closed. That does not make
the original blocking policy appropriate for a maintained interactive engine.

## Byte ordering, pause and echo semantics

For each expanded byte, the sender checks pause-marker equality first. A match
calls BIOS delay with9 and sends/echoes nothing. Otherwise byteff means transmit
NUL and skip local echo and calibrated pacing. Every other nonzero byte optionally
echoes through0610, transmits through the actual UART and then incurs configured
calibrated delay. Expanded zero terminates the walk. Thus `^@`'s ff sentinel
sends NUL, while an escape that expands directly to zero terminates sending.
Rawff receives the same sentinel treatment. A configured pause marker offf wins
over sentinel transmission because it is checked first.

The caret rules come from the real4934 decoder: `^@` ->ff, `^^^` ->literal caret,
`^^` ->1e and other `^x` ->`x & 1f`. No extra CR, LF, modem prefix, retry or result
handling is added by48cc. Command construction belongs to its caller.

## Actual timing and cancellation limits

The BIOS helper enables interrupts with STI, zeroes ES and observes the BIOS
tick low word at0040:006c. It increments the requested word then waits for that
many tick **changes**, always entering the wait loop at least once. The sender's
argument9 therefore waits ten changes. Tick low-word wrap is naturally accepted
by equality/change detection. General argumentffff wraps its incremented count
to zero but still waits once; no cancellation is polled. The helper does not
restore the caller's previous interrupt-enable flag.

The calibrated helper returns immediately for zero units. Otherwise it loads CX
from the calibration count, repeatedly decrements CX until it equals the floor
word, then repeats that loop for each requested unit. A wrapped count can take
65536 iterations for a unit. It sets ES=DS for a nonzero delay and does not
restore ES. The physical duration/unit and complete original calibration setup
remain unproved. The diagnostic explicitly chooses synthetic count1/floor0;
those values are not an assertion about the original clock or a physical PC.
Legacy units must not silently become BIOS ticks or milliseconds in live code.

48cc itself never checks keys or cancellation. Actual UART ab0b polls THRE in a
blocking loop without an elapsed-time/keyboard check. Its CTS wait can consult
an Escape callback, but Escape exits that **wait** and still proceeds to transmit
the byte; it does not cancel the remaining command. Original3f4b peeks/reads a
key and returns true for Escape. The diagnostic provides a real BIOS Escape
callback for that specific path. The original UART's software-pause handling
has its own UI/time path; that is separate from sender cancellation.

Tests corroborate that THRE stuck false never returns, Escape does not interrupt
a BIOS pause, a stalled BIOS clock never finishes a pause, and Escape while CTS
is false still sends the byte. Instruction limits bound these CPU tests; no
host hang is required. A maintained sender should use the existing bounded
`uart_try_write`, explicit cancellation/deadline checks and separately named
pacing policy. Such a live sender is intentionally separate from this recovery.

## Source-only diagnostic and tests

```sh
./tools/dev --command python3 standalone/build_modem_send.py
./tools/dev --command python3 standalone/check_modem_send.py
./tools/dev --command python3 standalone/test_modem_send_dos.py
```

The independent build checks172 exact flat sender/delay bytes against tracked
hashes and links `MODEMSND.EXE` with actual4934 and recovered UART core. No UART
transmission routine is replaced by a capture/no-op service. It uses fixed
COM1/38400/8N1 with flow disabled and compile-time valid synthetic command
`AT~X^@^M^^^`. Receive interrupts are not installed: this diagnostic only polls
TX. Original UART's unused application screen-save/message callbacks trap if
unexpectedly reached; they are not passed off as recovered UI. Diagnostic echo
uses BIOS teletype, while the normal original0610 renderer remains an import.

Six CPU groups pass across270 cases: output order/marker/sentinel/calibrated
pacing, echo exclusion,254 caret controls, BIOS tick wrap and explicit loop
counts, stalled transmitter, and CTS/Escape/pause cancellation behavior. Actual
sender, expander, delay and UART instructions execute. Only hardware ports,
BIOS teletype/keyboard and tick memory are modeled; no UART or delay routine is
skipped. The raw blocking behavior is a tested limitation rather than silently
fixed baseline code.

The actual DOSBox-X test captures six serial bytes `41 54 58 00 0d 5e`
(`ATX`, NUL, CR, caret) over loopback. Actual BIOS delay runs. An independent DOS
sampler captures vectors and UART/PIC state before/after; all42 bytes match.
The executable SHA256 is
`e7cfa5511c5a0fa10b1158f6137eeb585fef1aa8c20bf3b206e435aef14f4809`.
Reports/captures remain under ignored `build/modem-send/` and
`build/modem-send-dos/`. This proves that source-built path in DOSBox-X, not
physical modem timing or the complete dial-attempt application.

## Provenance

Retained REA assembly exports were reused; a live REA query reaffirmed the
sender evidence without setup/global changes. Exact ranges/hashes are recorded
in `reconstruction/modem_send/provenance.json`.

| Routine | REA assembly Evidence |
| --- | --- |
| Sender48cc | `ev_3a29c9753cf6188658686eb46944e813fddeb172758c9bded7dc265f9aeac907` |
| Calibrated delay6b72 | `ev_a30bfa2cee5690318dc8252472fd4570367e365219605a4b4a1e2253170377fc` |
| BIOS delay6b98 | `ev_cc5df7fd3b4baa1350abfad9245198f09d55989c263134af069ea519ff7a51f9` |

Original local-echo0610 integration, calibration initialization/units, full
application flow UI and physical UART/modem tests remain open. No terminal
source, shared builder, Makefile or live application binary was changed by
this independent recovery.
