# Rebuilt d-modem and controlled network timing

The current DOS [guest-audio diagnostic](../../docs/validation/synchronet-audio-integrity-trace-01.json)
also exposes delay growth: two in-call silence frames interrupt an otherwise
exact caller waveform, and both answering and independent guest-PCM decoders
produce unwanted data. DISCARD_NONE prevents the shrinkage case below; it does
not prevent silence insertion when playback runs short of audio.

The additional `--network-profile buffered-increase` diagnostic begins without
artificial delay, then adds a persistent120ms FIFO delay after the caller's
destination/DA/CPR sequence. It keeps the packets' original contents and order.
Unlike `buffered-release`, its queue legitimately retains a bounded trailing
window while the caller continues transmitting. The check therefore requires
an exact delivered prefix and at most eight queued packets, rather than an empty
queue. Neither profile represents a physical network or hardware acceptance.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_receive_trace.py \
  --runtime build/bbs-lab/synthmodem-sparse-runtime-01/runtime \
  --dmodem candidate --network-profile buffered-increase \
  --output build/bbs-lab/jitter-increase-new
```

Retain a failed upstream-integrity result as a counterexample. Analyze its
captures with the PCM and two independent decoder commands below; a successful
producer process exit alone does not make the bytes exact.

The [retained delay-growth counterexample](../../docs/validation/synthmodem-delay-increase.json)
passes27 independent evidence checks while retaining failed upstream integrity:
34 exact caller bytes become38 guest bytes, with four inserted bytes after CPR
at authored offset29. The independent decoder of guest PCM emits36 bytes and
also fails identity. Every guest PCM sample reconstructs exactly from the
delivered RTP prefix plus three startup silence frames and six additional
silence frames at RTP frame647. Thus the guest delay grows from60ms to180ms.
The reverse6000-byte all-value payload stays exact. The delivered relay/tunnel
packets are unaltered, continuous prefixes, and real training/export/teardown
complete without modem errors. The initial run's incorrect empty-queue predicate
and its source remain retained separately.

```sh
./tools/modem-dev --command python3 lab/bbs/audit_jitter_increase.py \
  build/bbs-lab/jitter-increase-new
```

This demonstrates that the40ms DISCARD_NONE candidate does not absorb a120ms
increase in packet delay. A separately identified larger-buffer or timing
correction must preserve both delay-growth and delay-shrinkage cases before
normal DOS/BBS repetition. No production default or installed bridge is changed
by this diagnostic.

The paired Nix source builds now boot in the actual answering VM. Both baseline
and DISCARD_NONE candidate register, answer SIP, train at V.22/1200, exchange34
authored upstream bytes and6000 all-byte downstream bytes, export guest PCM and
tear down cleanly on the direct route. Their overlapping guest PCM samples match
the caller audio after fixed50ms (baseline) and60ms (candidate) delays. The candidate's source differs from the
baseline only by the explicit jitter-discard setting; both use the same rebuilt
PJSIP2.15.1 library and toolchain. These are modem diagnostics, not DOS/BBS or
physical modem acceptance.

## Controlled counterexample

An optional bounded FIFO UDP relay initially delays caller packets by300ms.
After the caller sends its destination, DA and CPR, the relay releases its
15-packet backlog in order and immediately forwards subsequent packets. There
is no deliberate loss, reordering, payload change or fabricated decoded data.
Actual RTP sequence/timestamp/SSRC continuity and byte identities are audited
at the caller, relay output and host tunnel input.

With progressive discard, the guest audio delay shrinks from350ms to50ms in
steps. The received stream contains89 extra bytes at authored byte offset29,
immediately after CPR, despite an offline caller decode recovering exactly the
34 authored bytes. The actual pre-resampling guest PCM contains the altered
waveform; its independent decoder also produces spurious data. All6000 reverse
bytes remain exact, and no carrier or SIP session is lost. The baseline remains
a failed transport result, retained as the counterexample.

The DISCARD_NONE candidate retains a constant360ms delay and preserves486400
overlapping PCM samples with zero differences. It recovers exactly34 upstream
and6000 downstream bytes; the independent guest-PCM decoder agrees. Its relay
also releases15 unmodified, ordered packets. This demonstrates that progressive
frame discard can corrupt modem data when packet delay decreases and that the
explicit candidate setting prevents this controlled failure.

The independent [pair auditor](audit_jitter_vm.py) passes23 provenance/transport
invariants per variant and6 comparison checks: identical fixture sources,
kernel/JavaScript identities, every boot-archive field/body except d-modem,
actual single guest carrier, framed data, authored payloads, independent caller
decode, captured waveform/decoder identities, RTP continuity, a bounded release
and normal resource cleanup. See the [VM receipt](../../docs/validation/synthmodem-jitter-vm.json).
The earlier [build/API receipt](../../docs/validation/synthmodem-jitter-policy.json)
preserves its narrower historical scope.

## Reproduction

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_receive_trace.py \
  --runtime build/bbs-lab/synthmodem-sparse-runtime-01/runtime \
  --dmodem baseline --network-profile buffered-release \
  --output build/bbs-lab/jitter-baseline-new
# Repeat with --dmodem candidate and a different fresh directory.
./tools/modem-dev --command python3 lab/bbs/analyze_receive_trace.py \
  build/bbs-lab/jitter-baseline-new
./tools/modem-dev --command node lab/bbs/diagnose_receive_pcm.js \
  build/bbs-lab/jitter-baseline-new/runtime build/bbs-lab/jitter-baseline-new
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js \
  build/bbs-lab/jitter-baseline-new/runtime build/bbs-lab/jitter-baseline-new
# Run the same three analysis commands for the candidate, then:
./tools/modem-dev --command python3 lab/bbs/audit_jitter_vm.py \
  --baseline build/bbs-lab/jitter-baseline-new \
  --candidate build/bbs-lab/jitter-candidate-new \
  --output build/bbs-lab/jitter-pair-audit-new
```

Use fresh directories. Omitting `--network-profile` selects the direct route.
Do not edit frozen inputs during a live run. Runtime binaries/images, waveform
and raw protocol captures remain in ignored build storage; public receipts bind
their identities. No installed bridge or BBS is changed by these runs.

## Normal startup and remaining acceptance

The [normal-runtime stager](synthmodem_jitter_runtime.py) replaces only d-modem
in the accepted sparse-helper gateway image. It preserves normal init, the
answering DSP, helper, kernel and39 source files, with no export daemon or
additional chardev. The [staging receipt](../../docs/validation/synthmodem-jitter-runtime.json)
establishes those identities, not a DOS/BBS pass.

The separate normal DOS cohort -07 now passes19 producer and19 independent
checks:64 exact upstream and46908 downstream bytes, authenticated Main ->
Messages -> Main -> Files, normal DOS return, UART/vector restoration, directory
accounting and real SIP/VM cleanup. See the
[audio receipt](../../docs/validation/synthmodem-audio-dos.json). The image has
normal init and no diagnostic export daemon or additional chardev.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_jitter_runtime.py \
  --variant candidate --output build/bbs-lab/jitter-normal-new
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --runtime build/bbs-lab/jitter-normal-new/runtime --dmodem candidate \
  --output build/bbs-lab/dos-jitter-candidate-new
```

The historical six-byte event occurred at the same CPR boundary but lacks guest
PCM and arrival timing. This controlled reproduction establishes a cause of the
same class of corruption, not proof of that specific historical event. Broader
DOS/BBS workflows, transfers, loss/late-packet behavior and sustained load remain
separate gates. DISCARD_NONE prevents this deliberate shrinking; it cannot
recover missing packets or provide unlimited queue capacity. Physical Boca/ATA
and negotiated14400-bps acceptance remain unverified.
