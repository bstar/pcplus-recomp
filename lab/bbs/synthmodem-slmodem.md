# Rebuilt software-modem wrapper and carrier-channel groundwork

The baseline daemon now builds under pinned Nix as a static ELF32 i386 program.
This is SynthModem's Linux answering wrapper, not the DOS PCPlus application.
Its source manifest pins 29 upstream inputs at
`b1752e4d0039e0cff72735924e03aa99922723a8`, including the unchanged `dsplibs.o`.
The DSP object is still a binary dependency; this does not establish complete
DSP source recovery. The only baseline source adjustment adds the missing
`time.h` declaration needed by the pinned compiler.

## Actual software-DSP baseline

```sh
./tools/build-slmodem baseline --no-link --json
./tools/modem-dev --command python3 lab/bbs/synthmodem_receive_trace.py \
  --runtime build/bbs-lab/synthmodem-sparse-runtime-01/runtime \
  --dmodem candidate --slmodem baseline \
  --output build/bbs-lab/synthmodem-slmodem-baseline-01
./tools/modem-dev --command python3 lab/bbs/analyze_receive_trace.py \
  build/bbs-lab/synthmodem-slmodem-baseline-01
./tools/modem-dev --command node lab/bbs/diagnose_receive_pcm.js \
  build/bbs-lab/synthmodem-slmodem-baseline-01/runtime \
  build/bbs-lab/synthmodem-slmodem-baseline-01
./tools/modem-dev --command python3 lab/bbs/audit_slmodem_baseline.py \
  build/bbs-lab/synthmodem-slmodem-baseline-01
```

Use a fresh output directory for a new run. The retained baseline passes all
nine producer gates: VM registration, actual RING/init responses, both DSPs
connecting, exact upstream/downstream data after the idle interval, PCM export,
teardown, no errors and unchanged inputs. It recovers 34 upstream and 6,000
downstream bytes. Independent analysis finds 486,400 exact guest PCM samples at
a fixed 60 ms delay; the independent native decoder recovers all 34 authored
upstream bytes. The RTP comparison covers the common captured prefix: capture
ends before the external caller's final teardown packets, so the files are not
claimed identical in length.

The stager checks every archive entry and changes only the requested modem
executables plus the existing trace-export init/script. The separate audit
rechecks frozen sources, runtime files, captures, analyzer/decoder identities,
PCM alignment and the exact rebuilt daemon in the boot archive.
See [build receipt](../../docs/validation/synthmodem-slmodem-build.json) and
[runtime receipt](../../docs/validation/synthmodem-slmodem-baseline.json).

## Carrier-channel client candidate

The normal helper still recognizes `NO CARRIER` in online PTY payload. The
candidate in `patches/synthmodem-carrier` now implements both sides of an
independent status channel and passes host tests. Full runtime integration
remains required; it is not selected by the normal lifecycle runtime or
installed as a service.

```sh
./tools/build-slmodem-carrier --no-link --json
./tools/bbs-dev --command python3 lab/bbs/test_carrier_client.py \
  --output build/bbs-lab/carrier-client-new \
  --modem-executable /nix/store/REPLACE-WITH-BUILD-OUTPUT/bin/slmodemd
```

The optional `SYNTHMODEM_CARRIER_PATH` selects a Unix `SOCK_SEQPACKET` channel.
When set, startup requires a same-UID peer and an acknowledged HELLO before
device setup or PTY creation. Connection retry is bounded to five seconds and
each acknowledgement to 1.5 seconds. The socket is nonblocking and close-on-exec.
The new hook sends DOWN at the beginning of `modem_stop` while the modem is
started. It requires acknowledgement and flushes pending input on the PTY master
before the modem stops its driver, enters command mode or writes result text.
Failure terminates the daemon rather than proceeding with an unacknowledged
transition. With the variable absent, the candidate preserves legacy behavior;
that mode retains the existing carrier/data ambiguity.

The protocol is two bytes per packet: version `01`, then HELLO `10` or DOWN
`11`; acknowledgements use the same version and type OR `80`. Incorrect length,
version/type, closure and missing acknowledgements fail. The helper candidate
authenticates its peer, stops accepting DATA_TX, discards pending PTY transmission,
queues structured carrier-loss status, then acknowledges DOWN. Its session
retires without consuming further PTY data or stale host frames. The channel
is serviced ahead of PTY writes. A Telnet disconnect that leaves analog carrier
up must continue returning to `CONNECT>` without retiring this channel; the full
runtime must verify that behavior with the new candidate.

The [client receipt](../../docs/validation/synthmodem-carrier-client.json)
records the host fault checks and actual rebuilt-daemon startup failure checks.
These do not execute the real `modem_stop` callback, establish callback ordering
over SIP/DSP, or prove physical DCD/DTR behavior.
Remaining gates include literal/fragmented carrier-like payloads over the
complete stack, actual carrier loss while transmission is queued, teardown
pressure/timeouts, reconnect isolation and existing helper regression suites.
No Boca/SPA2102 or negotiated 14,400-bps result follows from these tests.

## Helper receiver and paired host checkpoint

```sh
./tools/build-control-carrier --no-link --json
./tools/bbs-dev --command python3 lab/bbs/test_carrier_helper.py \
  --helper /nix/store/REPLACE-WITH-HELPER-BUILD-OUTPUT/bin/modemd-ctrl \
  --client-probe build/bbs-lab/carrier-client-03/client-probe \
  --baseline build/bbs-lab/synthmodem-sparse-04/candidate \
  --output build/bbs-lab/carrier-helper-new
```

The helper builds as a static i386 executable with the previous control/pressure
and sparse-prefix repairs, then the new carrier patch. The tests check the
baseline source identity, compile the existing fault harness against the actual
patched translation unit and run the Nix executable through Linux PTYs/sockets.
The paired run uses the production carrier client from the prior probe build.
It deliberately starts before the PTY path exists, proving HELLO does not depend
on PTY startup, then exercises CONNECT ordering and online binary payloads.

Review and a retained reproduction found a second collision at the transition
boundary: the command parser preferred a later `NO CARRIER` payload over an
earlier CONNECT in the same read. Status-channel mode now honors the first
transition, emits the complete CONNECT line/status, then sends its remainder as
data. The reproduction records zero online bytes and an erroneous nocarrier
event before this correction. The corrected paired test includes that literal
in the same write as CONNECT, plus all-byte data, slow fragments and a lone N.

The [helper receipt](../../docs/validation/synthmodem-carrier-helper.json)
records 29 new checks, all 16 existing fault cases and all 12 existing PTY
checks. With PTY transmission stalled, DOWN clears pending transmission and
the client flushes already admitted kernel input before continuing. The helper
delivers exactly one structured nocarrier status and exits. Closing a Unix
control socket with unread stale host input can produce a reset; the test
requires the complete status and no partial output frame before that reset.
It does not reinterpret a reset as a missing status pass.

Malformed/closed status channels fail, startup accept/HELLO waits are bounded,
and the helper does not delete existing or replaced socket paths. The listener
is private to its UID. During retirement the host output gets a one-second
drain budget. A deliberately blocked host receives no successful-delivery claim:
the helper acknowledges admission of the carrier status, then logs a drain
timeout and exits with failure if output cannot drain. The host must handle
that failure as session termination.

The next integration must enable the same path in both VM processes, preserve
the normal init contract, and teach the Node backend to retire its writer on
structured nocarrier, SIP termination and control failure without duplicate
hangups or late CONNECT resurrection. Actual modem-stop callback ordering,
queued transmission under real carrier loss, normal SIP/DSP cleanup, TCP-only
reconnect and complete DOS/BBS audio workflows remain open. The host checkpoint
does not close those gates.
