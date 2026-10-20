# SynthModem control-helper transport candidate

This isolated source patch targets `vm/ctrl/modemd-ctrl.c` at SynthModem revision
`b1752e4d0039e0cff72735924e03aa99922723a8`. Nix GCC builds the actual C source
for host-side tests. No installed bridge, VM image/prebuilt, DSP, SIP service,
BBS or DOS application is modified. This is a component candidate, not complete
end-to-end modem backpressure support.

The stock source has two reproducible faults:

- `wire_try_parse` returns a pointer into the receive buffer, then immediately
  compacts that buffer. A following coalesced frame overwrites the payload
  before the caller dispatches it.
- AT and DATA_TX paths call nonblocking PTY write once. Short writes, EINTR and
  EAGAIN leave unsent bytes unretried; the AT terminator can overtake its tail.

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

Nine candidate fault cases check parser lifetime, short writes, interrupted and
would-block writes, AT CR ordering across coalesced frames, fatal/zero writes and
carrier-loss cleanup. A separate actual helper process uses Linux raw PTYs and
a Unix control socket: two coalesced AT frames,262147 exact binary bytes with
the PTY reader initially stopped and then throttled, observable host-send
backpressure, inbound service during hangup, guard timings and signal-responsive
exit with another pending transmission. The initial integration fixture used
incorrect wire type constants and timed out; it is retained as a failed attempt.
The constants were corrected from the pinned header without production changes.

Remaining work includes the reverse host-output path: `wire_write` still has
no queued recovery for a nonblocking host channel that returns EAGAIN, and some
callers do not propagate its failure. Node's PjsipBackend/CallSession also ignore
stream-write pressure; native DSP writes have no flow-credit interface. Those
boundaries need explicit ownership and queue limits, with VM rebuild/integration
and DOS/BBS/physical tests before claiming an end-to-end fix. Existing Telnet and
BBS receipts describe a separate, unchanged proxy candidate.

Upstream source and GPL-2.0-or-later attribution:
[modemd-ctrl.c](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/vm/ctrl/modemd-ctrl.c),
[wire.h](https://github.com/synexo/synthmodem/blob/b1752e4d0039e0cff72735924e03aa99922723a8/vm/ctrl/wire.h).
The patch retains upstream copyright/license headers; the maintained fault
fixture is GPL-2.0-or-later as marked. Full component notices are preserved in
the [Telnet candidate notices](../synthmodem-telnet/UPSTREAM-NOTICES.txt).
