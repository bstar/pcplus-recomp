# New PCPlus: ready for a hardware connection test

Follow-up: the first hardware startup exposed the BIOS enumeration gate.
The [BIOS-omitted UART fix](BIOS_OMITTED_UART.md) is now installed at `C:\PCPLUS`
with configuration matching `C:\UTILS\PCPLUS`. The package/evidence below is
the preceding readiness checkpoint; the follow-up has its own scoped receipt.

The current goal is maximum compatibility through the real Boca → SPA2102 →
SynthModem → LoSs oF CoNtRoL Enigma path. Software/package readiness is verified;
the user-operated physical connection and real-account login are still pending.
This is not a claim of complete original PCPlus feature parity.

Use the [hardware acceptance record](HARDWARE_CONNECTION_TEST.md) for the real
session; its outcomes start as not tested and must come from actual observations.

## Package and setup

The local archive is
`build/connection-test-package-02/PCPLUSSE-CONNECT.zip` (ten files, 257,383 bytes).
SHA256: `aec45524db64c276895ce3dc09679c5607550271a318ff57cae4ec7f9ad15c1d`.
It contains the matched terminal, ASPECT, ASPCOMP, PRMEDIT, XLTEDIT, authored help,
launchers and instructions. It contains no private PRM, directory or key files.
The known DOS card is not currently visible on the workstation; it has not been
written. Preserve the working installation and configuration before staging.

Copy the application files into `C:\PCPLUSSE`, retaining/copying the known working
`PCPLUS.PRM` and associated KEY/KBD/XLT resources. Preserve the established Boca
COM3, `3E8h`, IRQ5, 8N1, DTE/flow settings and working initialization string.
Do not copy the Linux VM's AT+MS command into the Boca profile.

From the DOS prompt:

```text
C:
CD \PCPLUSSE
START /D:555 /I:3
```

Press Enter at the splash. The numeric destination 555 is routed by the ATA to
SynthModem. After modem carrier and `CONNECT>`, type `LOC` or `1` and Enter.
The Internet/BBS target is selected after carrier, not sent in Boca's ATDT.
`/I:3` enables acknowledged initialization with a selectable three-second bound.

Alt-Z opens the original reference; plain L opens call-log status/retry. Alt-L
retains printer dispatch; Alt-R records and Alt-S/Alt-P opens setup. Use the
reference's PgUp/PgDn send/receive choices to preserve assigned BBS page keys.
Alt-X returns to DOS. Dim reference commands remain unavailable.

## Compatibility evidence and remaining check

[Readiness evidence](validation/connection-test-readiness.json) binds:

- 68 actual DOS workflows for menu, logging, access/flow, scripts, transfers and
  carrier/reconnect, plus linked menu/key and bank-ABI checks.
- Fresh owned Enigma/Synchronet editor sessions with exact 1,920-cell/cursor and
  call-log checks on the combined image.
- COM3/IRQ5 packaged launch/setup/splash and precompiled-ASPECT execution, with
  configuration, hardware vectors, environment and executable preservation.
- An isolated 2,006-source rebuild producing all five executables and all ten
  package files byte-exactly, without originals or previous objects.
- The installed TelnetProxy/config connecting through LOC to the actual live
  Enigma service and receiving ANSI after real TCP/Telnet negotiation. Serial
  output was collected for this route check; SIP/audio was not simulated as a pass.

The live bridge was idle according to its current process/performance monitor.
Only its terminal height changed from 25 to 24, matching the tested status-enabled
PCPlus 80x24 layout; the service was restarted and checked active. Addresses,
aliases, backend and host-network configuration were retained. A private backup
is in ignored local test storage.

First hardware checks are carrier, `CONNECT>`/LOC selection, reliable login/input,
ANSI/CP437 and editor navigation, then hangup/redial. Follow with owned small
upload/download files and compare hashes. Record actual carrier separately from
DTE speed; software tests do not prove analog rate or audible speaker operation.

Known conventional-memory limit: invoking automatic `.ASP` compilation while
the terminal and ASPECT are retained fails in this candidate. The failing run
is preserved. The validated classic workflow is `ASPCOMP SCRIPT.ASP` at the DOS
prompt before START, followed by running `SCRIPT.ASX` through Alt-F5. This keeps
the standalone compiler available without claiming the nested-memory issue fixed.

All physical modem/SIP/audio observations, real-account interaction and broader
original-feature acceptance remain open until exercised. The live BBS, ATA,
host network and card were not reconfigured by these checks.
