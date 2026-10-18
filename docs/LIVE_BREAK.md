# Serviced serial BREAK

Alt-B now sends a real UART BREAK from the source-built DOS terminal. It works
in ordinary terminal mode, the raw monitor and the dedicated printer controller.
It does not transmit a NUL or a textual modem command. Serial/modem ownership
must be idle or connected; transfer, macro, PROGRAM and ANSI-wait owners deny
admission. Repeating Alt-B during a pending pulse does not extend its deadline.

The owner waits for LSR TEMT, protecting an already shifting character and its
stop bit. THRE alone is insufficient. While waiting and while asserted, the
maintained UART API holds both ordinary writes and queued XON/XOFF. Incoming
bytes, IRQ receive buffering, RTS watermarks, keyboard and normal parser/display
service continue. Pending terminal bytes retain their order and flow control
resumes before ordinary output. New PROGRAM, macro and transfer requests are
denied until release. No child can inherit this owned pulse through those paths.

Alt-X, Alt-H, Alt-D, explicit connection cancellation/start, observed carrier
loss and terminal shutdown cancel the owner before hardware restoration or
modem commands. Release clears only the owned LCR bit40h, preserving current
framing and DLAB bits; an initially asserted BREAK or DLAB denies admission.
A foreign BREAK appearing while waiting for TEMT is left alone. A framing change
aborts an owned pulse. Normal shutdown clears it before releasing flow, disabling
the UART, restoring the interrupt vector and restoring original hardware state.

## Timing and configuration

[Original instructions and startup calibration](BREAK_NATIVE.md) establish a
native delay word at PRM01A4h, default350. The original measures a BIOS tick's
busy-loop iterations and divides by55. That supports nominal one55th-tick units,
roughly millisecond-style intent, rather than an exact electrical measurement.
The maintained implementation uses BIOS ticks and never copies the native PIC
masking or busy wait.

For a nonzero raw delay `u`, the pulse clears at the first serviced poll with
elapsed tick count at least `ceil(u / 55) + 1`. The extra edge covers the unknown
starting phase. Default350 therefore requires eight tick transitions (roughly
seven to eight complete tick intervals). This deliberately rounds conservatively;
it does not claim an exact350ms pulse. Once TEMT is ready, zero performs immediate assertion/release.
All65536 raw values are retained; the largest needs1193 tick transitions.

At each drain poll, TEMT readiness takes precedence. If still unready, waiting
expires at19 tick transitions, allowing at least18 complete tick intervals.
Pulse timing starts after assertion, independently of drain time.
Full32-bit BIOS-day ticks handle both the low-word wrap and BIOS midnight reset.
Deadlines are foreground serviced: DOS/BIOS calls or other unserviced work can
extend physical time. Physical modem acknowledgement and electrical timing
remain unverified.

Without a full modem plan the maintained default is350. Explicit-target PRM
startup and directory startup import the raw word; DIRECT directory entries
retain this line-action setting while still skipping modem command/response
validation. Serial-only `TERMINAL @FILE.PRM` imports its existing serial/display
subset and retains the BREAK default. No new settings UI or command-line delay
switch is included. The read-only modem plan grows from366 to368 bytes, appending
`break_delay_units` without moving existing fields or changing the PRM format.
The lossless host codec exposes `LegacyPrm201.with_word("break_delay_units", u)`
for an explicitly selected image, changing only01A4h..01A5h. Neither PRM nor
directory files are rewritten by the live BREAK command.

`terminal_break_state` is0 idle,1 draining or2 asserted. The near
`terminal_break_status` records1 accepted,2 busy,3 foreign BREAK/DLAB,4 missing
hardware ownership,5 drain timeout,6 completed,7 cancelled or8 framing change.
These are diagnostic state, not a new status overlay or a complete native UI.
Public owner entry points preserve all general registers, ES and FLAGS/IF.

## Verification

Run with the pinned Nix toolchain:

```sh
./tools/build terminal test-modem-import test-terminal
```

The linked BREAK checks execute actual owner, UART ISR, TX/flow API and key-route
instructions; only UART registers, BIOS keyboard and BIOS clock are modeled.
They cover four configured ports, five line formats, low-word/midnight timing,
full-word delay boundaries, TEMT stalls, foreign ownership, repeated requests,
binary RX, software watermarks, held replies/keyboard bytes, handoff denial and
cancel/carrier/error paths. No product callback is patched or skipped.

The actual DOS tests add normal pulse and early Alt-X cases. An independent
INT1C TSR reads the virtual UART LCR, chains the previous timer and unhooks
before exit. It samples changing RX text on the video screen while BREAK is
asserted; multiple observed digits prove display progress during that interval.
The early-exit case checks observed assertion and restored UART/PIC/IRQ state.
The peer captures only actual DSR replies and the scheduled ordinary key,
verifying that BREAK adds no fake serial byte. This is virtual UART evidence,
not an external modem test.

[Hash-bound report](validation/terminal-break.json) records the selected runtime,
linked checks, actual DOS samples, importer checks, complete terminal regression
and fresh source-only rebuild. The full application gates in FEATURES.md and
physical F03 verification remain open.
