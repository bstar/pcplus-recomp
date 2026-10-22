# Manual hangup and canceled-dial flow lifetime

The parent now retires the completed MODEM attempt's peer pause and driver-owned
flow state before returning to idle. The old state survived timed-out Alt-H and
canceled initialization, so the next Alt-D stayed paused and sent no ATZ.

Completion first clears the native receive queue, then retires flow metadata
under CLI with caller FLAGS restored afterward. This sends no XON/XOFF into
modem command mode. The existing helper releases RTS only when the driver owns
that lowered line. The DIRECT cancellation branch keeps its existing lifetime;
it does not enter this MODEM completion path. No ASIO or renderer capability
change is involved.

This explicit attempt boundary also covers cancellation before CONNECT/DCD high.
The controller cannot require previous high DCD to identify a completed canceled
attempt. Ordinary online XOFF remains effective until the attempt/session ends.

## Evidence

The [independent old/new audit](validation/manual-reconnect.json) binds the raw
DOS modem/socket streams, accounting, hardware restoration and source rebuild:

| Coverage | Observed behavior |
| --- | --- |
| Four linked SOFT/BOTH hangup/canceled-initialization cases | Native BIOS keys and UART receive IRQ execute. Old parent reaches idle with peer pause still set; retry times out without output. Corrected parent reaches response wait with exact ATZ/dial bytes. DCD/DTR is a stated hardware model here. |
| Two old/new actual DOS SOFT/BOTH Alt-H cases | The BBS sends XOFF after manual arm and never sends XON. Configured hangup expires, then DTR closes the first socket. Old parent opens no second socket; corrected parent initializes, dials, and answers a manual query on the second connection. |
| Fresh source tree | 26 application/component products reproduce without originals. |

The actual DOS fixture uses a two-second command deadline and enabled DTR abort.
The blocked hangup still reports timeout; the fix does not pretend its unsent
command succeeded. The first BBS never initiates socket close. Both complete
wire streams, modem commands/replies, one/two directory accounting updates and
42-byte hardware snapshots are verified independently.

The earlier remote-drop suite records successful redial with dirty ATZ/ERROR.
This manual-hangup baseline reproduces a distinct failure: no second init/dial
is sent at all. Its four linked and two actual DOS baselines remain preserved.
The first linked fixture expected successful hangup status despite the blocked
sender; its corrected baseline expects timeout. The first DOS fixture had a
missing adapter-global binding; it remains unaccepted. Accepted baselines are
manual-reconnect-flow/baseline-02 and manual-reconnect-dos/baseline-02.

The new parent1600a5b3 also passes the existing46 connection inputs,42 carrier
policy cases, eight normal/mouse startup ABI cases and13 attached DOS PROGRAM
cases. Near-code spare remains318/170 and near-data112/64. Mouse parent is
2d59d6fc, external-render parent0acebeaf, with child183f852d unchanged.

## Remaining scope

Canceled initialization under XOFF has linked hardware-model coverage; its
actual DOS UART/modem test remains required. DTR-disabled/ineffective hangup,
other abort policies, late/initially-low/transient DCD, watermark/RTS/sustained
RX pressure and other modem hardware remain separate requirements. The chosen
real Boca hardware still needs identification and physical integration testing.
Current-parent broader confirmation/BBS/audio acceptance is pending; the prior
accepted audio retains parentdd86139f. Every full F01–F16 gate remains open.
