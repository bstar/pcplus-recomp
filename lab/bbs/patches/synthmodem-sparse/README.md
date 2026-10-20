# Sparse modem data candidate

This patch follows `synthmodem-control/control.patch` against upstream SynthModem
`b1752e4d0039e0cff72735924e03aa99922723a8`. It addresses an independently
reproduced cause of noninteractive BBS prompts: the helper retains a trailing
`N` in data mode while scanning for `NO CARRIER`, waiting indefinitely for the
next PTY read. A user waiting for the board's response supplies no next byte.

The candidate retains ambiguous bytes as DATA_RX and releases them after a
50ms monotonic deadline when the host output is writable. Further fragments do
not extend that deadline. Existing bounded queues and host backpressure remain
in effect; a stalled host can delay delivery beyond50ms. Complete carrier result
lines received within that window retain the existing status/AT-response path.

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/synthmodem-sparse/check.py \
  --baseline build/bbs-lab/synthmodem-control-reverse-03/candidate \
  --output build/bbs-lab/synthmodem-sparse-new
nix --extra-experimental-features 'nix-command flakes' build \
  ./nix#synthmodem-control-i386 --no-link
```

Use a fresh output directory. The checker verifies the prior source identity,
stages separate copies and compiles both with pinned Nix GCC. Actual helper
processes communicate through raw Linux PTYs and Unix sockets. The baseline
holds `N` until `X` arrives; the candidate delivers `N` and ten isolated keyword
prefixes without follow-up, measured at about50ms. A fragmented carrier result
still produces status and AT_RESPONSE. The existing16 transport fault cases
and12 real-PTY regression checks also pass. See the
[receipt](../../../../docs/validation/synthmodem-sparse.json) for source and
host/static-i386 build identities.

This is a bounded-lookahead improvement, not binary-safe carrier signaling.
A literal complete `NO CARRIER` line in user data still collides with status;
the checker deliberately preserves that known failure. A real carrier result
fragmented beyond50ms may instead become data. Reliable carrier notification
needs an out-of-band mechanism. Do not infer file-transfer or physical DCD
acceptance from these checks.

The new static i386 executable now boots in a separate normal runtime and
resolves the N stall through actual DSP/DOS. The full menu route and normal
cleanup pass, but an independent audit finds six additional upstream bytes
elsewhere; overall audio acceptance remains failed. See the
[DOS checkpoint](../../synthmodem-audio-dos.md). Stage the runtime with:

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_sparse_runtime.py \
  --baseline build/bbs-lab/synthmodem-gateway-01/runtime \
  --output build/bbs-lab/synthmodem-sparse-runtime-new
```

The stager verifies all gateway source/kernel identities and every original
archive entry, allowing only the helper executable body/size to change. It
rebuilds through Nix and requires the accepted sparse-candidate executable hash.
The DOS runner performs the same validation directly; a supplied staging receipt
cannot authorize an arbitrary runtime. See the
[staging receipt](../../../../docs/validation/synthmodem-sparse-runtime.json).

The failed audio receipt remains failed; neither
the installed bridge nor DOS application, BBS server, original images or physical
hardware is changed by this component test.

Upstream GPL-2.0-or-later copyright/license headers remain intact. Attribution
and component notices are retained in the adjacent control/Telnet candidates.
