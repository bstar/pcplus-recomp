# Gateway package and transfer acceptance

The normal Gateway-enabled terminal now has a matching ten-file `C:\PCPLUS`
package. An empty export of 2,194 public source files, without Git metadata,
original binaries, private configuration or generated objects, reproduces all
five executable hashes and all ten package files exactly. The source revision
is `d3b2d994821f60afdef268993c549beb3e8ae0ae`; the terminal remains the unchanged
591-input image tested in the preceding Gateway checkpoints.

The package proof includes the corrected flag reconstruction for Alt-F7 path
control and Alt-F4 Gateway. Setup and translation helpers were rebuilt against
the same current source inputs. The README documents both commands. No settings,
dialing directory, key map, translation configuration or call log is supplied
as a replacement application file.

Three actual DOS8086 package runs pass: START with the magenta splash captured
by a passive timer, SETUP with its return path, and native script compilation
through START with COM3 omitted from the BIOS table. All use COM3/IRQ5 and check
the environment, private fixture configuration, final UART/PIC/interrupt-vector
restoration and unchanged packaged files. These are emulator observations,
not a physical splash, speaker or modem acceptance report.

## Stock Enigma transfer matrix

The same terminal passes four independently audited ZMODEM cases through the
staged SynthModem Telnet proxy and the owned stock Enigma server:

| Physical rows | Status bar | Direction | Exact payload |
| --- | --- | --- | --- |
| 25 | Visible | Upload | 65,539 bytes |
| 25 | Visible | Download | 65,539 bytes |
| 50 | Hidden | Upload | 65,539 bytes |
| 50 | Hidden | Download | 65,539 bytes |

Each upload/download pair has an identical payload hash. The payload contains
all 256 byte values and window-size-reply lookalikes. Audits check packet CRCs,
completion, exact destination storage, raw/proxy byte equality, NAWS 80x24 or
80x50, and the owned menu-size probe. The producer also freezes its application
and test-source inputs throughout the sequential matrix. Total transferred
payload is 262,156 bytes. Each direction runs in a separate DOS process; this
matrix does not establish same-process reconnect. That evidence remains in the
separate [carrier-loss](GATEWAY_TRANSFER_CARRIER.md) and
[cancel/retry](GATEWAY_COMPOSITION.md) checkpoints.

The linked [receipt](validation/gateway-release.json) binds the package,
source-only reproduction, three launcher runs and four transfer audits.
`standalone/record_gateway_release.py` revalidates their source and artifact
hashes and checks package/executable/geometry agreement before emitting it.

## Deployment and remaining acceptance

The tested payload is selected by the private
`build/connection-test-current.json`. It has been installed at `C:\PCPLUS`:
independent FTP readback matches all ten package files, and all eight existing
private configuration/history files match their pre-update snapshots. Only
TERMINAL.EXE, VERSION.TXT and README.TXT required replacement; their displaced
bytes are retained by the reversible release transaction. Deployment and
readback records remain private in the machine-management record. Those records, rather
than this package's staging-time `card_written` field or historical deployment
paragraphs, determine what is installed. Runtime acceptance is not inferred
from a successful file update.

The real Boca/SPA2102/SynthModem route still needs acceptance of this executable:
reboot out of network mode before modem use because the NIC and modem share
IRQ5; launch `C:\PCPLUS\START.BAT`, then check login, custom Main screen,
editor navigation, carrier status and alert, Alt-F7, Alt-F4/EXIT, transfer,
hangup and reconnect. Keep the existing modem configuration. No network, ATA,
boot, ROM or live BBS/service configuration was changed by these software tests.

Microsoft DOS6.22, physical flow timing, SIP/DSP/analog/audio, wider layouts and
protocol combinations remain distinct gates. File Directory, both viewer
routes, editor integration, directory/key tools, Chat and the remaining
ASPECT/emulation/protocol/Host inventory remain required for full parity.
