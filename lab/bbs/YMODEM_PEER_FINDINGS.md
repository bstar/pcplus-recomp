# Synchronet YMODEM final ACK loss

The owned Synchronet upload `ymodem-upload-1` installed the exact 11,521-byte
source and passed the official FileBase metadata audit. It did **not** deliver
an ACK for the final empty YMODEM block0. The strict passive protocol audit
correctly failed that handshake; file installation alone cannot make it a
standard YMODEM pass. No new BBS session or server change was made during this
investigation.

## Bound artifact identities

- DOS terminal SHA256:
  `793b99122049ba49b99b9d7d815573389a1e4af555cc835290f67457819025dd`.
- Official Synchronet development commit:
  `9de2c48d0265b07e1a8406d8a55d31df4fad7ee8` (3.22a).
- Official source archive `sbbs_src.tgz` SHA256:
  `b6c1ccc4a6b0eaeb38acd2c3e8f02a7e8cfaaaade6bc7ccf72e85aa1161f94a4`.
- Extracted `src/sbbs3/sexyz.c` SHA256:
  `4200ee429ef648e1cb89fdb24c8a59f374ed2b081a0d29c4b62c586a2c3ee03d`.
- Actual helper `runtime/exec/sexyz` SHA256:
  `03bc778bfefe2cc8cc67e02cbff8c574bb890e352e88941fa3048d5875a8df82`;
  ELF build ID `cc60151f07ad067e4f10abdbf6f7f5189de8419e`.

The helper is the pinned official **binary bootstrap**, not a locally compiled
helper. Its hash agrees with the existing transfer setup manifest. Its actual
unstripped machine code independently corroborates the relevant supplied-source
control flow. This investigation does not claim to have reproduced the entire
helper build from source.

Local evidence remains under ignored
`build/bbs-lab/results/synchronet/ymodem-upload-1/`: `protocol.json`,
`trace.json`, `display.bin`, `serial-received.bin`, `server-audit.stdout`, and
`helper-buffer-replay.json`. No capture, database or helper executable is
included in this document.

## Wire and server observations

The DOS sender emitted a valid empty block0 at decoded DOS offsets11987..12120,
observed at52.837 seconds. Relevant decoded BBS controls immediately before it:

| BBS offset | Observed seconds | Byte |
| --- | --- | --- |
|30304|52.761732|ACK06, final data block |
|30305|52.762930|NAK15, first EOT |
|30306|52.765191|ACK06, second EOT |
|30307|52.766307|`C`43, request next block0 |
|30308|52.938061|ESC1b, start of `ESC[0;37;40m` |
|30318|52.943897|Processing-upload application text |

The processing text names `PCYUP01.BIN`. The independent official metadata
check confirms its physical contents and declared size11521 exactly. The
server's `node1/PROTOCOL.LOG` also records a successful11521-byte receive,
zero errors and final128-byte block size. That file log alone does not certify
the later final batch ACK.

Timestamps describe observed socket-reader chunks, not physical serial-byte
transmission times. Both the decoded receive stream and its trace exclude an
ACK between the final empty header and the processing banner. There is no
basis here for inventing an unobserved ACK or suppressing the audit failure.

## Cause: an ACK remains outside the output ring

The actual source explains why ordinary ACKs work but the final one is lost:

1. `sexyz.c:2005` selects `send_buffered` from ZMODEM window/streaming settings
   **without checking that the chosen protocol is ZMODEM**. The default
   zero-window/streaming settings also enable producer buffering for this
   YMODEM receive operation (defaults at1753 and1759).
2. `send_byte`, lines733..750, appends to static `txbuf` and increments
   `txbuf_len`. It returns success without placing that byte into `outbuf`.
3. `recv_buffer`, line447, calls `tx_flush(10)` before waiting for more peer
   input. Thus the next receive normally pushes each pending ACK into the
   real output ring.
4. The successful header path queues ACK at line1257. An empty filename then
   returns success immediately at lines1268..1270. Unlike an ordinary file
   header, no subsequent receive is performed to flush this final ACK.
5. Main teardown, lines2154..2165, waits for `RingBufFull(&outbuf)` and then
   sets `terminate`. It never calls `tx_flush` for the separate producer
   buffer. `bail` exits the process; C stdio flushing cannot flush this private
   binary buffer.

This is more specific than a speculative output-thread race: the byte has not
entered the ring which teardown checks. The source also has a general
ring-versus-output-thread drain distinction, but that is not needed to explain
this observed one-byte loss.

REA MCP corroborated the actual helper using a fresh, single Ghidra12.1.2
session, then exported the complete retained bundle to the ignored run
`rea-peer/evidence-bundle.json` and closed the session. Evidence IDs:

| Function | Retained Evidence ID |
| --- | --- |
| `send_byte` | `ev_46110ef2a10cbb637c89e29558e070b16e1c25191f1c91e9d2be363624340df4` |
| `recv_buffer` | `ev_fe67e6c9e28ce2dc6884897793edfafcca6085ebd69f01d35a39115d3dc404e3` |
| `main` | `ev_7b4058f4e214e605e5d17794d7c9703947a871fb8991916973188530897a3533` |

The main dossier exceeded the MCP transport budget but was retained complete;
its procedure view is
`ev_eabe3cfc94f020efad3d0ee85db4433d0d100cd82d88233361812e55b5c243c6`.
The exported pseudocode independently shows the unguarded buffering selection,
empty-header success jumping to common teardown, and no `tx_flush` call in
main. Main high-p-code value-flow is explicitly truncated; the conclusions
here use the retained pseudocode, exact relevant assembly and source, not a
claim of exhaustive value-flow coverage. REA addresses use image base100000h;
the following addresses are ELF relative virtual addresses:


- `send_byte`9420 reads `send_buffered`4e9c4;943a reads `txbuf_len`4e9c8;
  9473 stores the pending byte into `txbuf`4e9e0 and9478 increments its length.
- `recv_buffer`8f9c calls `tx_flush`8df0.
- The inlined termination path at770a..771d logs the empty header and jumps
  directly to teardown6670. Teardown668a calls `RingBufFull`, then reaches
  `terminate`/`bail`; it contains no producer-buffer flush.

An isolated Nix/Unicorn replay executed the actual helper's `send_byte` machine
instructions with explicit `send_buffered=1`, `telnet=1`, empty producer buffer,
and byte06. It returned0, changed `txbuf_len` from0 to1, left pending byte06,
and left the128 observed bytes of ring state unchanged. Its JSON records the
actual helper hash and the modeled state. This is a controlled instruction
replay, **not** a measurement of the now-exited BBS helper's live counters.
Together with the actual wire and static teardown path, it supports the
producer-buffer-loss explanation without opening another connection.

## Minimal maintained compatibility policy

Keep standard success conditional on receiving the final ACK. A small,
truthful extension is appropriate once all files have completed their own
EOT/ACK exchange and the final empty header has physically transmitted:

- ACK means confirmed batch success.
- Timeout or NAK retains bounded standard retry behavior.
- A first byte outside the controls recognized in this final-ACK state is
  returned to the terminal input stream through the existing one-byte unread
  mechanism. End protocol ownership with distinct
  `YM_END_UNCONFIRMED` (status10), restore the terminal and display
  `Batch sent; ACK?`.
- Do not send CAN or further block0 retransmissions after that application
  byte. The peer has resumed application processing; injected protocol bytes
  would become menu input and risk disturbing an otherwise installed upload.
- Do not convert this state into a confirmed-ACK result. Keep the passive
  handshake audit false/unconfirmed and report physical/metadata evidence
  separately. Never apply this exception to a missing data-block or EOT ACK.

For this capture the unread byte is ESC; preserving it is essential to the
subsequent ANSI processing banner. Any further queued bytes must remain in
order. A non-ACK byte is not independently proof of installation; the product
notice therefore says ACK is uncertain rather than claiming remote install.
Protocol cancellation controls still need their existing explicit handling.

Waiting longer cannot recover a byte left in a process's destroyed private
buffer. Repeated empty headers after the banner would not repair the helper
and would pollute the BBS menu. A strict error with preserved input is truthful
but less useful than the distinct unconfirmed status, because it obscures the
completed per-file handshakes.

A separate upstream peer fix would flush `txbuf` before final teardown and/or
restrict `send_buffered` to actual ZMODEM streaming. A tested peer fix could
restore a normal ACK-confirmed run, but changing the lab helper would change
the stock-peer baseline and must be recorded as a separate configuration/build.
No such change was performed here.

## ENiGMA observed the same missing control, with a different helper

Owned run `enigma/ymodem-upload-1` used DOS SHA256
`dde20366e816384a1884152c58bac41b650c20ac7770862a7344a83213f85e3e`
against ENiGMA commit `6c25317168b762f7d9088a54d3f8295438827a0e`.
Its exact installed11521-byte `PCYUP01.BIN`, official FileEntry metadata,
normal DOS exit, hardware restoration and ordered post-upload file-menu/list
interaction passed. The default strict handshake audit failed on byte27
(ESC) while waiting for the final empty-header ACK. This remains a strict
protocol failure, even though the installed file and menu are correct.

| ENiGMA decoded BBS offset | Observed seconds | Byte |
| --- | --- | --- |
|44166|86.150552|ACK06, final data block |
|44167|86.152810|NAK15, first EOT |
|44168|86.155065|ACK06, second EOT |
|44169|86.195904|`C`43, request next block0 |
|44170|86.270013|ESC1b, start of `ESC[0m ESC[2J ESC[H` |

The valid empty block0 occupies decoded DOS offsets11926..12059. Its first
observed chunk begins86.198696 seconds, and its last byte arrives86.267120.
No ACK follows before the application screen-clear bytes. These data are
retained in that run's `protocol.json`, `trace.json`, `display.bin` and
`server-audit.stdout`; no new connection was made to obtain them.

ENiGMA used its bundled SE/X/Y/Z3.6 helper, whose original binary SHA256 is
`7aa339b40482a99a6854253d9e0c336a7bec3ed55a2072f7fe5ce7a72323893b`.
The Nix-loader-adapted copy actually configured for the lab has SHA256
`d1aeb1347fee332be75dd638dd4cb10a1bf7c418d96d0ebb79ca90470b0ed4bd`.
Its bundled manifest identifies Synchronet source commit
`e7a825704ef5329c7ef8408749671291a85ef7f2`. This is a different helper from
the newer Synchronet executable analyzed above. Its **internal cause has not
been recovered in this bounded follow-up**; the newer producer-buffer defect
must not be attributed to it merely because both captures lack the same ACK.
The application-byte preservation/unconfirmed-status policy is useful for
both observed cases without requiring that causal assumption.

## The ENiGMA idle log belongs to an older closed connection

The line at06:43:54.753 UTC saying “Node1 idle timeout of10 minutes expired”
is not evidence that the111-second upload session exceeded its idle limit.
Node numbers are reused; the session IDs distinguish the connections:

- Actual upload session `JOUgYe6eQYJ` connected06:42:28.399, authenticated
 06:42:51.731 and reached fileBaseMainMenu06:44:04.980. Its file move follows
 at06:44:04.984.
- The idle line and subsequent idleLogoff belong to `mkU0LroBMzv`. That older
 short connection opened06:33:51.735 and immediately had a socket EPIPE and
 disconnect06:33:51.736. Its theme/menu callbacks nevertheless continued
 from06:33:54.735. Repeated idle messages for that same old session appear
 a minute apart after06:43:54.753.

Pinned source provides a concrete explanation consistent with those logs:
`core/servers/login/telnet.js:36` schedules an uncancelled3000ms callback to
`_clientReady()`. That method (246..252) checks `clientReadyHandled`, but not
`clientEnded`, before emitting ready. The unconditional ready listener in
`core/login_server_module.js:72..77` calls `client.startIdleMonitor()` and
continues preparing menus. `core/client.js:640..668` performs timer cleanup
only the first time `end()` sets `clientEnded`; `startIdleMonitor()` itself
(495..555) does not reject an ended client. Thus a socket ending before the
three-second ready timeout can start a new idle interval after its one-time
cleanup, consistent with the exact old-session timeline.

This is a source-and-log-derived lifecycle race, not an observed global
server-start timestamp shared by active clients. There was no synthetic timer
replay or live patch in this follow-up. The authoritative transfer session
audit already selects the actual connection's session ID; filtering by only
nodeId would mix in this unrelated timeout. Server source/configuration and
running sessions remain untouched.
