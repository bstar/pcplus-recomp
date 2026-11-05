# Viewer, transfers and connection recovery

This validates the unchanged internal-viewer parent
`1aa5cdb84a595c96ebba6ce2b359690723881c6d56266c2377fa040f81f0902e`.
It complements the [viewer UI](FILE_VIEWER_UI.md) and
[BBS/pressure receipt](validation/viewer-bbs-pressure.json). The
[recovery receipt](validation/viewer-recovery.json) binds the runtime reports,
source identities and independent protocol replays. No installed package,
physical configuration or release selector changes in this checkpoint.

## Transfer and viewer composition

The frozen release matrix covers16 actual DOS8086 X/Y/ZMODEM cases: both
binary directions, CRC/NAK retransmission, local Escape and peer cancellation,
YMODEM cancellation/retry on one connection, retained completed files, empty
and odd-sized batch members, and independent lrzsz ZMODEM transfers. The
partial PRM fixtures now specify selector2,25 physical rows, visible status
and video preference0 when the candidate imports display preferences.
Unspecified poisoned words previously stopped those old fixtures at startup;
that was not a transfer result.

Six additional same-process cases open Alt-V before XMODEM receive/send,
YMODEM cancel/retry/send and ZMODEM receive/send. A passive timer captures the
complete2000-cell file page and exact live frame/cursor/shape return. The
source file remains unchanged and its filename stays local. A real ordinary
keyboard marker after Escape releases the independent peer to start protocol
negotiation; early receiver negotiation is not mistaken for an unchanged live
screen. The ordinary transfer, storage and post-transfer keyboard/DSR checks
then execute without substituted application callbacks.

## Carrier and automatic modal cleanup

Three logging/reconnect cases cover idle HARD flow and a deliberately delayed
call-log write with HARD and SOFT flow. Four XMODEM cases close the remote
socket during receive negotiation, a partial download, an unacknowledged
upload and a partial upload. Ten YMODEM/ZMODEM cases cover metadata, partial
data, completed-first-file retention and both upload phases. DOSBox's modem
generates CONNECT/NO CARRIER and actual virtual DCD; an owned peer supplies
protocol bytes and socket closure. Each test redials in the same parent and
checks call history, directory accounting, owners, post-redial input/CPR and
hardware restoration.

The viewer-specific carrier case supplies **no Escape key**. Its passive
observer derives the parent identity from the real IRQ5 vector, captures a
painted page while online, then records the ordinary offline notice closing
the view. The file descriptor becomesFFFFh, its canonical claim is released,
and the file owner reaches CLOSED. The same parent subsequently redials and
answers new input. This matches the existing notice path, which calls
`terminal_redisplay_stop`; retaining the modal page after the notice was an
incorrect test expectation.

The observer performs no DOS or UART calls and writes no application state in
its timer handler. Collection restores and reads back its original timer
vector before writing the owned report. These are virtual-carrier results,
not physical timing or analog acceptance.

## Stock Enigma through SynthModem

The exact parent uploads and downloads the same65,539-byte all-values payload
through the staged SynthModem serial-side proxy to the owned stock Enigma
server. Independent audits replay Telnet decoding, geometry, CRC/length,
ZEOF/ZFIN/OO, opposite controls and exact destination/catalog identity.
Binary terminal-size lookalikes remain payload data.

A separate Enigma run cancels an actual download, observes a nonempty4096-byte
source-prefix DOS stage, verifies an empty receive directory before retry,
then receives the exact65,539-byte file on the same DOS process and connection.
The independent audit verifies the two server-helper exits, one authenticated
session and the search/list transitions before and after retry. Eight damaged
copies of evidence are rejected; the unchanged copied control is accepted.
Those controls include coherent payload corruption, false disk cleanup,
incorrect Escape, geometry, hardware and extra-session evidence. No damaged
executable is run.

## Remaining boundaries

These runtime cases use25 physical rows and24 logical rows with the8086 CPU
model. The stock-server route covers serial-side SynthModem/Telnet behavior;
SIP/audio/DSP, physical Boca/SPA2102 timing and hardware acceptance remain
separate. Physical printers, configured external-viewer commands, OEM filenames,
full native filename editing, real DOS failure/shutdown composition and the
remaining ASPECT/emulation/protocol/Host feature inventory stay open.

The new viewer-before-transfer sequences do not establish a second viewer
opening after every transfer, cancellation or reconnect. Other physical text
geometries still need their own runtime composition checks. This checkpoint
closes neither full original feature parity nor physical deployment acceptance.
