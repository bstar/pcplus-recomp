# Shared-parent carrier-loss recovery

The shared parent passes eighteen transfer-loss cases on ordinary DOS8086 and
four observed ASPECT loss cases in a386/UMB configuration. Every accepted case
returns ownership, reconnects in the same parent process, answers the second
connection's terminal queries and accepts subsequent keyboard input. The
[receipt](validation/meta-shared-carrier.json) binds the exact products, sources,
protocol streams, files and passive observations. No application or installed
file changed.

The transfer matrix covers XMODEM negotiation/partial receive and unacknowledged/
partial upload; YMODEM and ZMODEM metadata/partial/previously committed receive
and metadata/partial upload; and interrupted upload metadata fragments under
legacy and strict cleanup policy. Checks require actual protocol progress,
carrier fault classification, completed cleanup, no RX drops, staging removal,
retention of earlier committed files where applicable, restored hardware, exact
call-log records and directory accounting. Virtual DCD/NO CARRIER comes from
closing the actual DOSBox modem socket; it is not written into the application.
The bounded carrier fixtures are distinct from the all256-byte protocol
round trips in the preceding transfer checkpoint.

ASPECT covers WAITFOR return and WHEN DISCONNECT, each with and without its
script window. The passive observer verifies a live child, wait service, handler
arming, window visibility, child exit, expected file markers and subsequent
parent reconnect. The full eight-publication trace remains enabled for original
call-start timestamp checks.

An ordinary8086 run with the diagnostic TSRs could not load this ASPECT child.
A separate passive diagnostic captured PROCESS_EXEC and DOS error8, with no
child progress. Reducing trace history to four publications still failed to
admit the child; under upper-memory configuration it also omitted observations
required by the timestamp gate. Neither attempt is accepted. The four accepted
observed ASPECT cases therefore explicitly configure386, UMB and LH for both
diagnostic TSRs, while retaining the same parent/interpreter bytes and full
trace. They do not replace ordinary8086 capacity evidence from the earlier
six-stream/nested-child checkpoint or establish unrestricted memory headroom.

Fixture corrections also remove doubled separators from the ASPECT action
path, allow the shared reference's disk load before transfer navigation, and
extend the overall transfer test deadline to include that menu wait. Protocol,
cleanup, timestamp and reconnect checks remain mandatory. Bounded concurrent
jobs use separate DOS media, sockets and observers.

Live BBS transfers, all-byte large-transfer loss/pressure, physical Boca/SPA2102
timing/CTS/SIP/audio and the broader original-parity inventory remain separate
acceptance gates. RCE81708 remains the last known installed package.
