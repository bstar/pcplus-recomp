# Warmup timer ownership candidate

The upstream pool races backend startup against a timer promise but never clears
the timer when startup settles. A stopped bridge can therefore retain a live
Node process until the original warmup deadline (45 seconds in the lab).

`pool.patch` owns the timer inside the startup operation and clears it in
`finally`, on success or failure. The timeout still rejects and stops a backend
that never becomes ready. The existing stop-before-replacement ordering stays
in effect. This source patch targets upstream SynthModem
`b1752e4d0039e0cff72735924e03aa99922723a8`.

```sh
./tools/modem-dev --command python3 lab/bbs/patches/synthmodem-pool/check.py \
  --source build/bbs-lab/synthmodem-gateway-01/runtime/source \
  --output build/bbs-lab/synthmodem-pool-new
```

The checker verifies its three source files against the accepted gateway
receipt, stages baseline/candidate copies and runs each scenario in a separate
real Node process. Backend startup is modeled; pool methods and process exit are
real. With a1500ms deadline, successful startup, rejected startup and a completed
recycle retain the baseline process for about1.5s; the candidate exits naturally
in35–47ms. A genuinely stalled startup still times out at about1.5s, with backend
cleanup and final stopped state checked in both versions. No forced process exit
or timer unref hides a failure. See the
[receipt](../../../../docs/validation/synthmodem-pool.json).

The later [combined lifecycle test](../../synthmodem-lifecycle.md) now verifies
actual VM recycle/cleanup and normal DOS/BBS composition. This isolated receipt
retains its eight modeled-backend process scenarios. No installed bridge changes;
carrier/data ambiguity, DSP pressure and physical modem acceptance remain open.
Upstream copyright/license headers
remain intact; component notices are retained in the adjacent Telnet candidate.
