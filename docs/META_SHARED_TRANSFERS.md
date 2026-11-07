# Shared-parent transfer and reconnect checkpoint

The unchanged shared Meta parent passes sixteen DOS8086 X/Y/ZMODEM cases and
three carrier-loss/call-log/reconnect cases. [The receipt](validation/meta-shared-transfers.json)
binds the application, sources, UART streams, file hashes and captures. The
installed package has not changed.

Transfer cases exercise binary receive/send, CRC/NAK retries, local Escape,
remote cancellation, cancel-then-retry in the same connection, retained prior
files, and independent lrzsz ZMODEM peers using default/CRC16/escaped modes.
Each checks return to terminal input/parser service, hardware restoration,
unchanged PRM/source files and absence of partial staging files. The fixture
uses COM3/IRQ5,19200,8N1,HARD; it does not verify physical RTS/CTS.

The old test timing was unsuitable for the disk-loaded reference: it navigated
150ms after Alt-Z. The shared-profile fixture now allows3000ms. Its YMODEM upload
peer also delays the initial CRC request by an extra3s so it reaches the upload
prompt. Earlier failed attempts remain separate evidence; no application code
or protocol checks were weakened to obtain a pass.

The carrier suite closes a real socket behind DOSBox's modem, which produces
NO CARRIER and changes virtual DCD. Idle, held call-log write with hardware flow,
and held write with software flow each reconnect in the same process. Two real
initializations/connections, replies and keyboard input after redial, exact log
records, directory accounting and hardware cleanup are checked. Its former
redial sequence opened the recovered Alt-D directory; it now invokes the
command browser's Connection/D action to redial the selected target.

These results do not establish carrier loss during active binary transfer or
ASPECT, live Enigma/Synchronet file transfer, physical modem/CTS/SIP/audio timing,
or full original feature parity. Those gates remain before packaging/deployment.
