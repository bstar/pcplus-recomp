# Explicit UARTs omitted by the BIOS

The first physical test stopped at `Selected COM port is not listed by the
BIOS.` The startup gate required the BIOS data-area entry to equal the selected
profile's base, even for the custom-IRQ build. Some older BIOSes omit manually
configured COM3/4 ports. A validated PRM alone could not pass that gate.

The custom-IRQ terminal and ASPECT now accept a zero BIOS slot for an explicitly
selected, validated standard COM1–4 address and supported IRQ. A nonzero entry
that conflicts with the selected address still rejects the request. Live port
migration uses the same rule and retains its idle/ownership checks. Default
builds keep their prior requirement. The application does not edit the BIOS
table or alter the user's profile to work around this restriction.

[Validation receipt](validation/bios-omitted-uart.json) records:

- 24 old-control and 24 fixed linked terminal ownership cases, including
  conflicting entries and restoration, plus 32 ASPECT cases with raw data.
- The existing custom-IRQ child serial regression suite against its rebuilt
  diagnostic, including interrupt, flow, ownership and restoration behavior.
- Actual DOS8086 packaged execution at COM3/IRQ5 with its BIOS slot deliberately
  cleared by a test utility, and a normal listed-slot control. Both execute a
  precompiled script and return with hardware and private files preserved.
- An empty public-source export reproducing all five executables and all ten
  package files exactly from 2,007 sources.

This is a targeted follow-up; the previous 68-workflow and BBS evidence applies
to the previous image. Physical compatibility and fresh broad BBS acceptance
on the new image remain unverified.

The card update goes into `C:\PCPLUS`. Its six active profile/resource files
remain byte-identical to `C:\UTILS\PCPLUS`, including COM3/3E8h/IRQ5, 9600 baud,
8N1, and both flow-control options disabled. The prior application files are
backed up in `C:\PCPLUS\APPBK01`. No configuration edits are part of this fix.

Run `START /D:555 /I:3` from `C:\PCPLUS`, press Enter at the splash, and enter
`LOC` at the bridge's `CONNECT>` prompt. If the same BIOS error remains, a
conflicting nonzero entry is possible; record the actual table before choosing
another fix. Do not move hardware jumpers solely to accommodate this gate.
