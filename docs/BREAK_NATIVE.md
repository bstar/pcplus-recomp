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
   the argument as a status text pointer with zero display delay. The current
   DS2074 pointer's initialization is not recovered here; a nearby `*** BREAK ***`
   literal alone does not prove its dynamic pointer value in every profile.
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
physical duration. Existing MODEM_SEND/MODEM_CONFIGURATION documentation correctly
leaves these units unproved. Neither default350 nor the bit40h operation proves
**250ms**, **350ms**, or a BIOS-tick conversion. Do not import01A4h as milliseconds
or rename it `break_duration_ms` without further calibration-source evidence.
A lossless codec may expose `break_delay_units` with precisely this limitation.

| Retained helper | Evidence |
| --- | --- |
|829A actual IN|`ev_928bd51905a3f05952c6d5f5f02e0e3c58fcc8b9d469880962b0b5079ac29247`|
|82A8 actual OUT|`ev_57c74d58f2640b065c78c4db49db7b697b36facec0b40c7c84dcbc46738deb5a`|
|6B72 calibrated delay|`ev_a30bfa2cee5690318dc8252472fd4570367e365219605a4b4a1e2253170377fc`|
|Overlay19:E8A7 numeric accessor|`ev_c1f8ea49cff3f3018ddc4f2a30f73fd7ca4308ee9c8b949ec84f28be401e02ea`|

These correspond to ignored retained assembly under `analysis/pcplus-main/`
and `analysis/pcplus-overlay-anchored-19/`; normal source builds need none of
those artifacts.

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
Those tests and maintained runtime changes are outside this read-only scope.
Full F03 and physical BREAK interoperability remain open until that work lands.
