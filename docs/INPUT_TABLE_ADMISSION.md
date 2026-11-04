# Input storage candidate integration checks

The [input table storage variant](INPUT_TABLE_STORAGE.md) now passes an actual
DOS 8086 carrier-loss/redial/download-retry session through the staged SynthModem
proxy and stock Enigma. It remains a separate development candidate; this
checkpoint does not change the selected physical installation.

After DOS compiles the login script to 473 bytes, one terminal process authenticates,
starts a binary download, loses actual emulated modem DCD after a 4,096-byte
disk prefix, removes the unfinished stage, redials and authenticates again.
The second download saves the exact 65,539-byte file, including every byte value
and size-reply lookalikes. File search and clean BBS logoff then succeed.
Native carrier-loss/RX-complete notices, directory accounting, unchanged PRM,
and 42-byte hardware restoration are checked. An independent raw-wire/protocol/
artifact audit passes; an unchanged copied capture passes and nine damaged
copies fail, including coherent payload corruption.

A separate DOS session cancels a download locally after a 4,096-byte disk
prefix, verifies an empty stage before retry, and saves the exact 65,539-byte
file while retaining the same authenticated Enigma connection. Independent
BIOS-Escape/CRC/raw-wire/NAWS/hardware checks pass. An unchanged copied capture
passes and eight damaged copies fail. This complements carrier loss rather
than treating a local cancellation as a disconnect test.

The matched ten-file `C:\PCPLUS` package at
`build/connection-test-input-tables-20261104` reproduces all five executables
from 2,143 public source/tool files without ancestor Git or original application
inputs. Native START/precompiled-script, SETUP and splash checks pass with
COM3/IRQ5 omitted from the BIOS table. The archive is `PCPLUS-UPD.zip` in that
package directory. Its version record identifies source base
`cd27d1c54bffffcaee8a3f9305fe350ffe6dc96c`; the public receipt binds exact hashes.

The independent timer-based cancellation test also passes on both this variant
and the byte-identical default control. Each accepts a real 128-byte receive
block before delivering the owned INT1B event. The terminal exits 16, removes
the unfinished file and stage, restores vectors/flags/UART state and needs
no rescue BIOS key. There are 22 checks per workflow. This is actual emulated
DOS cancellation, not a physical Ctrl-Break or modem timing claim.

That older test needed fixture repairs: preserve intervening online flow
handling when injecting the partial frame, acknowledge the branded splash,
use the original command-reference transfer shortcuts, and supply admitted
VGA25 display settings. The application executables did not change. Failed
preflight/startup/recipe attempts remain retained and excluded in the receipt;
they are not counted as successful cancellation tests.

See [validation/input-table-admission.json](validation/input-table-admission.json)
for the source-package, native launcher, carrier and cancellation identities.
Package reproduction uses its recorded source base; later test-harness fixes
are separately identified and do not change the five application executables.
The preceding independent Enigma/Synchronet editor audits still apply to this
exact unchanged image. The fresh last-backed-up private configuration probe
is recorded only in private machine records; it is not a fresh remote readback.

SIP/audio/DSP, physical Boca/SPA2102 carrier/flow control, the reported physical
BUSY condition, other display/protocol/profile combinations and full original
feature parity remain open. The installed carrier/C0 release's final independent
remote readback is also pending; no job or deployment was resubmitted.
