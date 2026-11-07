# Shared-parent Enigma transfers through SynthModem

The unchanged shared parent completes actual stock Enigma ZMODEM download and
upload through the on-disk SynthModem Telnet proxy. The download is11521 bytes;
the upload is65539 bytes and includes every byte value and Telnet/window-control
patterns. [The receipt](validation/meta-shared-enigma-transfers.json) binds the
products, server/proxy sources, captured protocol streams and files.

Both run the source-built DOS application on8086 with COM3/IRQ5,19200,8N1,HARD,
explicit VGA25 rows and visible status, advertising80x24. The real BBS helper
owns ZMODEM; the Hayes shim supplies modem commands only. SynthModem owns Telnet
encoding/decoding. CRC headers/data, offsets, exact file length, ZEOF/ZFIN/OO,
subsequent BBS menu input/response, source/PRM preservation, hardware cleanup
and absence of staging files are checked. The upload additionally verifies
installed file bytes and official server metadata. Raw serial proxy input and
output must match the independently audited streams exactly.

The accepted proxy uses250ms input-sequence framing and0ms per-byte pacing for
these transfers. This is distinct from the20ms input pacing of earlier editor
interaction tests. Each proxy is an isolated loopback process using the actual
installed source files; the running physical SIP/audio service is untouched.
The server is the owned stock lab, not a modification to the user's live BBS.

The first probe used an older synthetic PRM with unspecified display settings.
It stopped with an unsupported-function notice before a BBS session formed and
is not accepted evidence. Explicit display settings fix the fixture. Shared
reference navigation also allows3000ms for disk loading before selecting the
transfer command. No application bytes changed.

The package tools still need to require/include the matched PCMETA.OVL before
this parent can become a connection-test package. Physical Boca/SPA2102
carrier/CTS/SIP/audio acceptance and current-product Synchronet file transfers
remain separate; no deployment or full original-parity claim is made.
