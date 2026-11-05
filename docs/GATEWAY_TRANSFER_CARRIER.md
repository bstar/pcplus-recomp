# Carrier loss during transfer on the Gateway-enabled parent

The unchanged normal Gateway executable passes the stock Enigma transfer-loss,
cleanup, redial and exact retry workflow. The receipt is
[gateway-transfer-carrier.json](validation/gateway-transfer-carrier.json).
This extends the earlier [loss-drain correction](TRANSFER_LOSS_DRAIN.md) to the
current 591-source normal image; it does not open Gateway during the transfer.

DOSBox's built-in modem owns Hayes/result codes and DCD. An explicit raw relay
interrupts its socket after a source-prefix disk write; the staged real SynthModem
proxy owns Telnet. The terminal observes carrier loss, retains binary ownership
through cleanup, removes the partial stage, redials through real BIOS menu keys
and runs the second automatic ASPECT login. Native ASPCOMP compiles the login
script identically to the host compiler. Both authenticated sessions, directory
accounting, carrier/completion notices, target search and BBS logoff are checked.

An independent audit verifies the 4,096-byte prefix stage, an empty receive area
before the second login, and all 65,539 retry bytes exactly. The payload contains
all 256 byte values and 215 size-reply lookalikes. CRC-valid metadata/data, EOF,
finish/control exchanges, real 80x24 NAWS, raw relay/proxy byte identities,
source/runtime identities and hardware restoration pass. Eleven copied-evidence
checks accept the untouched capture and reject ten mutations, including source
count, stage cleanup, notice, geometry, native compilation and coherent data
corruption that preserves raw/proxy equality but fails the packet CRC.

The auditor previously fixed the source count at 570. It now validates the
selected source-built product and each source hash, then requires the manifest's
count to equal the producer's recorded count. The new source-count mutation
confirms that accepting a newer source closure did not remove that check.

The first run retained the old 60,000 ms post-transfer keyboard schedule and failed
because the retry was canceled before completion. Its second wire contained the
local CAN/backspace sequence at 163.679 s, with the first retry data at 107.900 s and
a last ZDATA position 41,984. The RX-canceled notice and scheduled later Escape
keys support a fixture-budget explanation; no product timeout was changed.
The passing run uses the already accepted 150,000 ms recipe allowance. Both results
remain bound; the failed run is not counted as acceptance.

The normal application bytes remain
`ae6cbad95094fd59f98fd95a7831cbdc014b404ec37886a290294fe05089d90b`.
The tested route is DOS 8086 COM3/IRQ5 at 19200/HARD through a staged loopback
proxy. Relay pacing is synthetic, not measured modem throughput. Physical
Boca/SPA2102, SIP/DSP/audio, upload/layout/protocol combinations and full original
feature parity remain separate gates. No physical deployment or live service
configuration changed.
