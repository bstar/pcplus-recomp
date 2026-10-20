# SynthModem control-helper transport candidate

This isolated source patch targets `vm/ctrl/modemd-ctrl.c` at SynthModem revision
`b1752e4d0039e0cff72735924e03aa99922723a8`. Nix GCC builds the actual C source
for host-side tests. No installed bridge, VM image/prebuilt, DSP, SIP service,
BBS or DOS application is modified. This is a component candidate, not complete
end-to-end modem backpressure support.

The stock source has three reproduced transport faults:

- `wire_try_parse` returns a pointer into the receive buffer, then immediately
  compacts that buffer. A following coalesced frame overwrites the payload
  before the caller dispatches it.
- AT and DATA_TX paths call nonblocking PTY write once. Short writes, EINTR and
  EAGAIN leave unsent bytes unretried; the AT terminator can overtake its tail.
- Reverse `wire_write` can stop after a partial header when the host channel
  returns EAGAIN. Callers can ignore that failure and continue a truncated stream.

The patch copies the parsed payload before compaction, using a fixed4093-byte
scratch buffer. The single-threaded caller consumes it before the next parse.
One fixed4094-byte PTY transmit buffer owns an accepted payload plus optional CR.
Until it drains, the helper stops host-control reads and leaves other complete
frames in its existing bounded receive buffer. Kernel socket backpressure then
reaches a slow host sender instead of silently losing bytes at the PTY boundary.

POLLOUT advances the cursor only by bytes actually written. EAGAIN/EWOULDBLOCK
and EINTR preserve the cursor for later polling. Zero/fatal writes fail the
helper explicitly; they cannot report a completed transfer. PTY reads remain
serviced while writing or waiting for hangup guards. Carrier transitions are
processed before writable events, and observed carrier loss discards pending
session bytes rather than sending them into command mode. Bytes already accepted
by the kernel cannot be recalled.

The reverse path now admits complete header/payload frames into a fixed65536-byte
queue. PTY reads pause while host output is pending; PTY writes and host input
remain independently serviced. Host POLLOUT advances only the accepted prefix.
Would-block and interrupted writes preserve it, including a partially written
header. Capacity/zero/fatal failures set a sticky flag checked by main, so void
status producers cannot hide a truncated transport. Atomic admission leaves the
existing queue intact when a new frame cannot fit. Queue compaction retains its
unsent prefix. Unix socket test transports are explicitly nonblocking, matching
the production character-device path.

The existing1.1-second pre/post hangup policy becomes a monotonic-clock poll
state machine: preguard -> queued +++ -> drain -> postguard -> queued ATH/CR ->
drain. It no longer sleeps through inbound PTY service. These are helper-side
timing checks, not proof of modem audio/line guard timing or DSP queue drain.

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/synthmodem-control/check.py \
  --output build/bbs-lab/synthmodem-control-new
```

Use a fresh output directory. The runner checksum-pins/downloads only the two
public C/header files, preserves stock/candidate copies, applies the patch with
zero fuzz and records compiler/source/executable identities. Stock failures are
observed defects, not stock acceptance passes. The fault executable includes the
actual upstream/candidate translation unit and models only read/write transport
outcomes; its source and product dispatch routines are not replaced.

Sixteen candidate fault cases check parser lifetime, both write directions,
interrupted/would-block writes, partial headers, ordering/CR, fatal/zero writes,
carrier-loss cleanup, atomic capacity failure and queue compaction. A separate
actual helper process uses Linux raw PTYs and a Unix control socket. Twelve
checks cover262147 exact host-to-PTY bytes,1048579 exact reverse bytes, stalled
readers, opposite-direction progress during a host-output stall, hangup guards,
and prompt signal exit with both directions backpressured. Stock control helper
corruption/loss is independently reproduced by the transport models.

The earlier [one-direction receipt](../../../../docs/validation/synthmodem-control.json)
retains its nine fault cases/seven PTY checks and earlier source hashes. The
current reverse checkpoint is separate. The first integration fixture used
incorrect wire type constants and timed out; the failed attempt remains local.
The constants were corrected from the pinned header without production changes.

Remaining work includes Node's PjsipBackend/CallSession, which ignore stream-write
pressure, and native DSP writes without a flow-credit interface. Those boundaries
need explicit ownership and queue limits, followed by VM rebuild/integration and
DOS/BBS/physical tests before claiming an end-to-end fix. The host-built helper
has not replaced a VM prebuilt. Existing Telnet and BBS receipts describe a
separate, unchanged proxy candidate.

Upstream source and GPL-2.0-or-later attribution:
[modemd-ctrl.c](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/vm/ctrl/modemd-ctrl.c),
[wire.h](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/vm/ctrl/wire.h).
The patch retains upstream copyright/license headers; the maintained fault
fixture is GPL-2.0-or-later as marked. Full component notices are preserved in
the [Telnet candidate notices](../synthmodem-telnet/UPSTREAM-NOTICES.txt).
