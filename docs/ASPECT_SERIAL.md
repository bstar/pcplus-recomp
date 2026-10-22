# ASPECT serial commands and DOS port ownership

The [current known-carrier policy](MODEM_RECONNECT.md) uses ASIOv6/50bytes.
For a MODEM session whose parent observed DCD high, low DCD stops queued and
closing XOFF/XON; PROGRAM return retires its flow without contaminating ATZ.
Two actual DOS SOFT/BOTH reconnect workflows pass with clean ATZ/OK and unchanged
BBS streams. Direct/untracked links keep their prior behavior. Legacy ASIOv1..v5
remain supported. Initially-low/transient DCD, other reconnect paths, configurable
longer stalls, RTS/RX and physical validation remain open. Earlier sections below
describe their frozen checkpoints.

The [current flow handoff](ASPECT_FLOW_HANDOFF.md) adds ASIOv5/50bytes with
one guarded peer-pause word. It preserves an existing XOFF before child IRQ
installation and returns the final pause before parent IRQ restoration. Legacy
ASIOv1..v4 remain supported. Actual DOS SOFT/BOTH entry/resume and timeout/cancel
checks pass, with exact bytes and independently checked flow timing. The36-tick
transmit bound remains; configurable long stalls, CTS, sustained RX, reconnect
and physical validation remain open. The following describes the historical
ASIOv1 checkpoint.

The later [input-policy integration](ASPECT_INPUT_POLICY.md) adds native receive
mapping and ASIOv2 XLT/seven-bit inheritance. This document's ASIOv1 validation
remains a historical checkpoint; version1 parents are still supported.

The source-built ASPECT child now executes `TRANSMIT` and `WAITFOR` against the
terminal's selected UART. File → A → Run script temporarily lends the port to
`ASPECT.EXE`, then restores the terminal and returns bytes that the script left
unread. This advances F03/F09/F13/F16; it does not close any complete application
gate. The prior [runner checkpoint](ASPECT_RUNNER.md) describes the earlier
console-only build.

## Native instructions and maintained services

`src/aspect/serial_commands.asm` recovers 523 exact bytes across seven units:
TRANSMIT at 5176, WAITFOR at 5188, formatted transmission at 48CC, timeout decoding
at E9F5, ASCII uppercase at 8252, BIOS clock reading at 77FE, and the WAITFOR
result builtin at overlay16 DA32. These seven serial ranges plus 44 supporting
ranges total 3,659 bytes; all 51 match the pinned original. The component diagnostic exercises all 220 instructions with
1,261 paired CPU scenarios and 11,057 actual DOS assertions. Its device, clock,
delay and cancellation callbacks are controlled boundaries, not a modem test.

The composed interpreter now has 59 implemented slots and explicitly rejects
the other 156 in-range slots. The diagnostic compiles 297 authored script
fixtures with the maintained compiler and compares them against the frozen
original-compiler outputs. The wider compiler corpus checks 302 accepted
outputs and 302 presentation variants. This remains a subset of ASPECT.

The original `WAITFOR` matcher and its quirks are retained. It defaults to
ASCII case-insensitive comparison, uses first-character fallback rather than
a general substring algorithm, and polls after bursts of at most 82 bytes.
An omitted timeout is 30 seconds. Numeric timeout zero is an operand error;
`FOREVER` is a distinct encoded option. The `WAITFOR` integer builtin returns
one for a match and zero for timeout/cancellation; it is separate from
SUCCESS/FAILURE comparison state. Native deadlines use 18 ticks per second and
the BIOS day rollover. Control notation is decoded before matching or sending;
formatted transmission maps the internal FF representation of `^@` to wire NUL.
The default `~` character pauses rather than being transmitted.

The production adapter supplies raw received bytes. The original read/render
wrapper, terminal translation, capture and scheduling services are not all
reconstructed in this child. Local echo defaults off and intercharacter delay
defaults zero. Nonzero calibrated character delays remain unsupported rather
than being approximated. PAUSE and transmit pauses service flow control and
Escape cancellation through the maintained owner.

## UART and process lifetime

`serial.c` and `serial_backend.asm` connect the recovered UART core/ISR to a
bounded, source-owned DOS lifecycle. The child validates the COM port, divisor,
line-control and flow options before touching hardware. It requires an already
asserted DTR signal and preserves the baseline interrupt vector, PIC mask and
UART state. It does not toggle DTR as an implicit modem reset. Transmit and
close stalls have a 36-BIOS-tick limit, including midnight rollover.

Software control sends an initial XON before user bytes and a final XOFF before
handback. Hardware control observes CTS for data transmission. The `B` mode
preserves configurations that enable both policies. Flow-control bytes and
user bytes retain the recovered driver distinction. Receive overflow and
unread input without a return destination are explicit errors.

The menu prepares an ASIO version1 descriptor in retained parent storage. It
contains parent identity, a 4096-byte ring destination, capacity, publication
fields and a guard. The child checks the actual DOS parent PSP and allocation
bounds, copies unread bytes in order, and publishes completion last. The parent
validates the result and seeds its receive ring before restoring interrupts.
Queued input, pending parser state and active WAIT ownership prevent an unsafe
handoff. The parent reacquires its receive interrupt before the return-key
prompt and services flow control while the child console remains visible.
Incoming bytes stay in the ring until the terminal screen is restored; the
prompt does not run the terminal parser or consume remote input. Overflow is
still reported. This closes the observed unserviced-prompt gap: a pre-fix
actual DOS case overran the UART and exited with errorlevel6 when the BBS
sent bytes after the matched token. Both observer and observer-free failures
remain retained for the regression. The descriptor is an internal parent-child contract, not an arbitrary
far-pointer interface. Direct standalone use has no unread-byte destination.

## Running and verification

Build and stage current programs with `./tools/build package`. Keep ASPECT.EXE
beside TERMINAL.EXE; open Alt-Z, File, A Run script and choose a compiled ASX.
The separate-process handoff returns through the existing PROGRAM owner.
The package also includes LINK.ASP/LINK.ASX, which send CR and wait for
`login:` for ten seconds without dialing or submitting credentials. Adapt the
prompt to your BBS. Compile authored source on the host with the pinned toolchain:

```
./tools/dev --command python3 src/aspect/compiler.py LINK.ASP -o LINK.ASX
```

A bounded script can send a carriage return and await a prompt:

```
proc main
transmit "^M"
waitfor "login:" 10
if waitfor
message "Prompt received"
endif
endproc
```

Change the prompt to match the selected BBS; the timeout is in seconds. This
example does not dial or submit credentials.

For an already prepared COM1 port at 38400 baud, 8N1, no flow control:

```
ASPECT LINK.ASX /S1:0003:03:N
```

The divisor and line-control byte are hexadecimal. Flows are `N` none, `S`
software, `H` hardware and `B` both. COM1–4 are accepted. The internal descriptor
suffix is supplied by the menu; users do not need to construct it. Without a
serial option, console-only scripts continue to work and serial instructions
report an unsupported service.

Source-only checks:

```
./tools/build test-aspect-serial-commands test-aspect-serial test-aspect-runner
./tools/build test-aspect-script-serial-dos
```

The separate `test-aspect-serial-commands-compat` target compares the recovered
component to a locally supplied pinned original. Normal builds have no original
inputs. `test-aspect-serial-dos` exercises the real DOS UART owner with a local
serial peer. `test-aspect-serial-bbs` requires the owned local Synchronet and
ENiGMA fixtures and the existing Wi-Fi-modem simulator.

The UART owner passes 48 modeled inputs across 12 groups and six actual DOS
peer cases. The parent handoff passes 41 linked inputs and five actual DOS menu
workflows, including the trailing-ANSI/return-prompt regression.

The independent production script suite covers 28 actual DOS/UART cases and
224 checks, including exact output, resource restoration and unread-byte return.
Its wire tests use COM1/38400/8N1/no flow; the UART component tests separately
cover flow policies and other port masks. The two BBS smoke cases dial only
owned loopback services, recognize CONNECT and a greeting marker, and transmit
one carriage return. They verify exact unread greeting tails and restoration;
they do not establish login, menu navigation, every BBS workflow or physical
modem compatibility. Existing logged-in terminal/transfer tests are distinct.

`docs/validation/aspect-serial.json` binds the final checkpoint artifacts and
source hashes. Retained failures include the corrected numeric-zero timeout
prediction and an initial DOS fixture that had not asserted DTR. Synthetic
`.analysis.exe` carriers were used only for static REA analysis and never run.
The inactive patched BB2F return in one carrier is excluded from native claims.
