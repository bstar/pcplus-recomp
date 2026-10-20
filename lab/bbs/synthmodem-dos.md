# DOS transfers through the SynthModem proxy candidate

This lab composes the actual source-built DOS terminal with the isolated
[SynthModem Telnet candidate](patches/synthmodem-telnet/README.md), then transfers
files using independent Nix-provided lrzsz. It exercises the serial/controller,
bridge prompt, Telnet transport, ZMODEM and DOS filesystem together. SIP/RTP,
answering-modem DSP, analog audio and the Boca/SPA2102 are not involved.

```text
DOS PCPlus in DOSBox-X
  -> loopback serial socket -> synthetic ATZ / ATD1 answering adapter
  -> actual candidate TelnetProxy -> loopback TCP
  -> independent server-side Telnet framing -> independent lrzsz sz/rz
```

PCPlus automatically dials numeric local target1 using a synthetic PRM with
autobaud disabled, COM1/38400/8N1/HARD. Real emulated BIOS keys enter the loopback
server address at CONNECT>, then choose ZMODEM through Alt-R/Alt-S and two F2
protocol selections. No Internet hostname is placed in ATD. The source-built
terminal answers the readiness and post-transfer DSR queries itself; the bridge
does not synthesize terminal replies or ZMODEM messages.

The adapter in `synthmodem_serial.js` loads the unmodified staged candidate class,
configuration and logger. Configuration changes exist only in that test process:
ANSI/80x25, loopback hosts, binary-safe default menu policy and disabled idle
timers. `synthmodem_dos.py` supplies a separate server-side Telnet frame decoder
and records negotiation, both raw TCP directions and both transfer-peer streams.
It verifies the candidate/config/logger hashes, freezes executable/map and
helpers, preserves each failed attempt and never deploys a service.

```sh
# First stage the isolated candidate as described in its README.
./tools/dev --command python3 lab/bbs/synthmodem_dos.py \
  --candidate build/bbs-lab/synthmodem-telnet-03/candidate \
  --output build/bbs-lab/synthmodem-dos-new
./tools/dev --command python3 lab/bbs/synthmodem_dos.py \
  --candidate build/bbs-lab/synthmodem-telnet-03/candidate \
  --output build/bbs-lab/synthmodem-dos-large-new --large
./tools/dev --command python3 lab/bbs/audit_synthmodem_dos.py \
  --candidate build/bbs-lab/synthmodem-telnet-03/candidate \
  --output build/bbs-lab/synthmodem-dos-large-new
```

Choose fresh output directories. Normal runs cover empty, one-byte and1029-byte
fixtures; `--large` replaces the last with65797 bytes. Both directions require
exact destination names and bytes, unchanged source/profile/executable, actual
TTYPE ANSI and NAWS80x25, BINARY acknowledgments in both directions, independent
peer exit0, restored terminal screen/keyboard/DSR, no staging leftovers and exact
42-byte before/after UART/PIC/vector snapshots. Socket/error/thread cleanup must
also succeed. The read-only auditor rechecks hashes/files/hardware and decodes
both raw TCP captures with the older independent Python lab codec before
comparing every payload byte with the transfer-peer streams.

Initial attempts transferred correctly but failed an invalid harness assertion
that required literal FF to be present on both streams. A receive control stream
need not contain FF, and the maintained DOS sender represents FF using ZMODEM's
ZDLE/ZRUB1 escape. The final checks require exact encoded/decoded byte equality
instead. FF counts remain observations; the separate proxy byte oracle exercises
literal FF in both directions. Failed attempts remain failed, with raw evidence
retained under ignored build storage. No production change was made to satisfy
those assertions.

The [recorded receipt](../../docs/validation/synthmodem-dos.json) passes all84
checks across four routes: small and over64KiB batches, each uploaded and
downloaded. Independent audits require exact decoded TCP streams, source and
destination hashes, peer exit status and hardware restoration. Accepted cohorts
are `synthmodem-dos-03` and `synthmodem-dos-large-02`. The application executable
and candidate proxy are unchanged from their preceding source checkpoints.

This is not a logged-in BBS transfer or a modem-line throughput test. Stock
Synchronet/ENiGMA sessions through this exact bridge, other protocols, transfer
cancellation/retry, slow-modem backpressure, SIP/DSP operation, disconnect and
reconnect under carrier loss, and physical hardware acceptance remain open.
Existing direct-lab BBS results retain their own bridge and executable identities.
