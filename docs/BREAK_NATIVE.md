# Native serial BREAK

Resident0401..0444 is the Alt-B serial BREAK action,68 instruction bytes.
The dedicated-print controllerD0D0 calls it for exact BIOS word3000h; the
ordinary keyboard dispatch table's scan30h also points to0401. The original
help resource advertises `SEND BREAK        Alt-B` (EXE26A1Fh).
This is a UART line condition, not an ASCII character, Ctrl-Break handler,
modem command or file-transfer CAN sequence.

The routine has no separately retained0401 REA export. Its instructions were
decoded read-only from the original resident mapping, file offsets1601h..1644h,
the68-byte slice SHA256 is
`93d70ad8677f762a625e09f586fd2df2f8a2320faffaf84dafd4857d3dfe142f`,
after verifying EXE SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The surrounding retained keyboard/controller evidence corroborates the caller;
retained exports below establish its actual IO and delay helpers. No original
application, private PRM file, synthetic analysis executable or physical modem
was executed, and no new REA session or system update was needed. This ledger
adds no recovered-byte count or live BREAK compatibility claim.

## Actual instructions and ABI

`0401()` is near, no arguments. It saves/restores SI; BP and the stack follow
its callees' ordinary conventions. AX/BX/CX/DX/ES/flags are scratch.

1. Calls6B5A, the existing cursor/UI state bracket.
2. Calls31BB with words `[DS2074]` and0 (caller cleanup4). That helper uses
   the argument as a status text pointer with zero display delay. Follow-up
   [ASPECT recovery](ASPECT_BREAK_NATIVE.md) resolves the installed pointer:
   DS2074 contains0000h, a valid near offset to `*** BREAK ***` atDS:0000.
   Actual native6BF0 accepts offset0 and reads its characters directly; this
   is an initialized string-offset table, not an unresolved null resource.
3. Calls829A with `[DS8FEE]` (caller cleanup2).829A actually executes
   `IN AL,DX` on its word port argument and clears AH.
4. Copies the returned original LCR into SI, ORs40h, pushes the asserted value
   and `[8FEE]`, then restores SI to the original value before calling82A8.
   82A8 actually executes `OUT DX,AL`, with port atBP+4 and byte atBP+6;
   caller removes4 bytes.
5. Calls6B72 with word`[DS1D28]`; this helper removes2 argument bytes itself.
6. Writes `(original_LCR & 00BFh)` through82A8 to the same port.
7. Calls6B42 and restores SI before returning.

DS8FEE is the existing canonical `uart_port_lcr`; it is not a fixed COM1 port
constant. Bit40h is asserted and later cleared while the original other LCR bits
are retained. If bit40h was already set, native0401 nevertheless clears it on
exit rather than restoring prior ownership. No local transmitter-empty wait,
UART ownership admission, cancellation, status result or exceptional cleanup is
present. The source must not be characterized as a safe asynchronous API.

## Duration and PRM field

DS1D28 is a word inside the proved PRM memory image beginningDS1B84, so its
proved image offset is **01A4h**. Original initialized data holds015Eh,350 decimal.
That is an original installed-program default, not a user's customized file.
Overlay19:E8A7's ASPECT accessor writes the numeric helper's AX to1D28 when its
mode flagE38E is zero, or returns1D28 throughDE3A otherwise. No range or unit
conversion is performed in that local accessor. This establishes storage and
consumer, not a public semantic range beyond a16-bit word.

6B72 is already recovered exactly as
`reconstruction/modem_send/delay_calibrated.asm`,38 bytes. It reads a count at
7AC4 and a comparison floor at7A4E, repeatedly decrements CX until that floor,
then repeats this busy-loop for the supplied DX units. Zero units skips it.
It does not read BIOS ticks, PIT time, wall-clock milliseconds or cancel/carrier
state. Machine calibration and initialization of those two words determine its
physical duration. The further calibration investigation below now establishes
its startup initialization and nominal55 subdivisions per BIOS tick. This
upgrades the earlier unknown-unit ledger to a derived millisecond-style intent;
it still does not establish exact **350ms** on a particular machine or any
**250ms** default. Keep a lossless field named `break_delay_units`, distinguishing
native calibrated intent from a separately chosen maintained timer policy.

| Retained helper | Evidence |
| --- | --- |
|829A actual IN|`ev_928bd51905a3f05952c6d5f5f02e0e3c58fcc8b9d469880962b0b5079ac29247`|
|82A8 actual OUT|`ev_57c74d58f2640b065c78c4db49db7b697b36facec0b40c7c84dcbc46738deb5a`|
|6B72 calibrated delay|`ev_a30bfa2cee5690318dc8252472fd4570367e365219605a4b4a1e2253170377fc`|
|Overlay19:E8A7 numeric accessor|`ev_c1f8ea49cff3f3018ddc4f2a30f73fd7ca4308ee9c8b949ec84f28be401e02ea`|

These correspond to ignored retained assembly under `analysis/pcplus-main/`
and `analysis/pcplus-overlay-anchored-19/`; normal source builds need none of
those artifacts.

## Startup calibration: observed mechanism and timing limits

The retained startup routine overlay3:D7A6 calls7956 atD7AE,793A atD7B1,
6CD8 atD7B4 and enhanced-keyboard detection7916 atD7BB. Thus the calibration
is reached in original startup, not merely unused library code. Assembly
Evidence `ev_010f4b1aba1b5e1663beb661884ee38b3cf578c480c658a095be0412661f557b`
is retained at `analysis/pcplus-overlay-anchored-03/functions/0x1d7a6-asm.json`.

Resident7956..798D is56 bytes, original file8B56h..8B8Dh, SHA256
`880dc8d068d86442c2b8a6f6d98f5743e037f73aeee6d81a43220c3959908777`.
Its exact sequence:

1. CLI; read and save master-PIC mask from port21h; writeFEh to that port;
   STI. This leaves IRQ0 unmasked while masking the other master-PIC lines.
2. Set AX=DX=0, ES=0 and BX=046Ch (the BIOS low tick word at physical046Ch).
   Snapshot it in CX and wait for a change, aligning measurement to a tick edge.
3. Snapshot the new tick. Repeatedly ADD AX,1; ADC DX,0; compare CX with
   ES:[BX]; repeat while equal. DX:AX counts iterations until the next tick.
4. Divide that unsigned32-bit count by0037h, **55 decimal**. Store quotientAX
   atDS7AC4. There is no overflow/zero-result validation in this routine.
5. Restore the saved PIC mask through port21h underCLI, then STI and return.
   It does not preserve a caller's initially clearedIF as a general API would.

Original initializedDS7A4E is0000h andDS7AC4 is0000h.7956 replaces7AC4;
it never changes7A4E. A literal-address scan of the original resident and
appended bytes found only the6B72 operand referring directly to7A4E, and the
calibrator is the identified direct7AC4 writer. This does not exclude indirect
aliases, overlapping writes, a changed executable or later runtime modification.

With floor0 and a nonzero calibrated quotient,6B72 executes approximately
`floor(measured_iterations_per_tick / 55)` comparable inner iterations per
argument unit. Its SUB-CX/ADC-AX/compare/JNZ body closely matches the calibrator's
ADD-AX/ADC-DX/compare/JZ measurement loop. The **derived nominal duration is
one55th of a BIOS tick per unit**. Under the ordinary approximately55ms BIOS
tick interpretation, that is consistent with millisecond-style intent and a
nominal roughly350ms default. This is a timing inference from the observed
calibration, not a measured electrical BREAK duration or original source-level
unit declaration. It is not a direct mapping of350 to350 BIOS ticks.

The physical guarantee remains limited by integer truncation, instruction and
prefetch timing, IRQ0 service time, other interrupt load during the later delay,
CPU/emulator speed changes after startup, unusual BIOS tick rates and hardware
behavior. A quotient0 causes the decrement-to-zero loop to wrap through65536
iterations; an excessive32-bit count can overflow the16-bit DIV quotient.
The routine supplies no guard for either case. A maintained owner should not
copy its PIC manipulation, IF behavior or unbounded busy-loop policy.

### REA corroboration and provenance

The actual REA MCP session was inspected before opening: no target was open.
Ghidra12.1.2 opened the SHA-verified original, but its default analysis left7956
undecoded (Evidence `ev_37a44d83550bae2bf4917889d00066d8e0966c3e0ad203c24723e0d52154269f`).
An ignored **analysis-only** carrier changed only the MZ initialIP to7956 and
initialCS to0; all original load-module/code bytes were retained verbatim and
checked. Carrier SHA256 is
`af0539581b44f631e0ae7e847e7d31146b37da202eb32311b8969c2f19c929f8`.
It was never executed. This is explicitly derived analysis evidence rather
than a claim that an altered header was the shipped program's entry point.

Focused MCP `analyze_function(0x17956)` returned the full56-byte body and
assembly under Evidence
`ev_301b59d7d428ffc4e6d2e203d2b7d941d769914f04c6aeec63f1d5bfb7f25f71`;
`procedure_assembly` independently retained it as
`ev_2536be74379b7cdb2cd5aa7c841a6f2cf9be8ba099569cd51f0a1c8d029a9f5e`.
The decompiler incorrectly folds the BIOS tick-memory loop into an infinite
loop and labels later blocks unreachable; the complete assembly, not that
pseudocode, establishes the calibration and store. Ghidra does not emulate
the BIOS counter or device timing.

Ignored local evidence, carrier derivation and exported MCP bundle are under
`analysis/break-calibration/`; they are not normal build inputs or public
original data. The session was exported and closed. No original execution,
physical timing experiment, private configuration read, runtime edit or REA
configuration/global update occurred.

## Maintained implementation boundary

The line-register operation is proved and small enough to implement, but the
repository currently has no established live BREAK owner/API proved here.
The maintained dedicated-print key path recognizes Alt-B as a blocked local
action; it neither transmits the BIOS key as data nor claims a line BREAK.
This remains an explicit F03 gap in the present batch.
There are two honest choices:

- Keep Alt-B an explicit unsupported F03 action until duration and ownership
  are designed, with no wire byte substituted for it.
- Add a separate maintained nonblocking BREAK owner with a clearly named,
  bounded BIOS-day-tick duration policy. This is an intentional new timing
  policy; it must not pretend to be a calibrated1D28 conversion. Its public
  setting should say ticks (or separately validated modern time units), preserve
  the imported native word as opaque legacy units, and document the chosen
  duration/default explicitly.

Such an owner should admit only actual acquired UART hardware and idle/connected
terminal state, reject an existing LCR BREAK it does not own, and retain the
original register state for checked release. Assert/deassert operations can use
short interrupt-safe critical sections, preserving caller IF; never hold
interrupts disabled for the duration. Pending TX bytes must not be accepted as
physically transmitted while BREAK is asserted. RX, flow state, keyboard,
carrier and quit must remain serviceable, with an explicit rule for queued TX
and software-flow control bytes during the interval.

The first assertion starts a full32-bit BIOS-day-tick deadline with midnight
correction. Repeated Alt-B needs a defined busy/reject policy rather than an
unbounded restart. Every cancel/error/PROGRAM/UART-release/shutdown path must
clear an owned BREAK before restoring/releasing hardware, without clearing a
prior owner's bit. Hardware restoration must not later reassert a stale saved
BREAK. Do not use an unbounded native delay in an interactive controller.

Meaningful linked tests should observe actual IN/OUT register writes, selected
COM/LCR, preservation of framing/DLAB bits, ordinary and midnight deadlines,
repeated admission, key/cancel/carrier paths, pending TX behavior and exactly-once
release before hardware restore. An actual DOS virtual UART run can verify the
register/lifecycle behavior but not electrical timing at an external modem.
That maintained work is now implemented and tested separately in
[LIVE_BREAK.md](LIVE_BREAK.md), with its deliberate BIOS-tick timing policy.
This native dossier remains recovery evidence; full F03 and physical BREAK
interoperability remain open.
