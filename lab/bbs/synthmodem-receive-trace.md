# Guest receive-audio diagnostic

Overall DOS/audio acceptance remains failed on the six inserted upstream bytes
recorded in [the DOS cohort](synthmodem-audio-dos.md). This diagnostic provides
actual guest audio and host packet timing without replacing either DSP binary.
Its short workload is not a substitute for the failing DOS/BBS workflow.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_receive_trace.py \
  --runtime build/bbs-lab/synthmodem-sparse-runtime-01/runtime \
  --output build/bbs-lab/synthmodem-receive-trace-new
./tools/modem-dev --command python3 lab/bbs/analyze_receive_trace.py \
  build/bbs-lab/synthmodem-receive-trace-new
./tools/modem-dev --command node lab/bbs/diagnose_receive_pcm.js \
  build/bbs-lab/synthmodem-receive-trace-new/runtime \
  build/bbs-lab/synthmodem-receive-trace-new
```

Use a fresh output directory. The stager verifies all accepted gateway inputs,
copies them and changes only the normal startup script to launch an additional
export daemon. A single added shell file reads the modem's existing dumps when
the host sends DUMP on a separate loopback virtio channel. QEMU's normal kernel,
init and backend arguments remain, with one additional chardev. Existing startup,
SIP, d-modem, slmodemd and control-helper binaries execute normally. The two
archive-entry changes and every unchanged body/metadata field are verified.

The actual native originating and VM answering DSPs train at V.22/1200. After a
declared idle interval the caller sends a numeric destination, DA, CPR, a45-second
idle and a final marker, while receiving6000 all-byte downstream bytes. No
connected flags or received bytes are injected. The fixture logs control/data
events and monotonic packet arrival times at the external and tunnel UDP sockets.
After the workload it exports the existing signed16 PCM dumps:

- `modem_rx_8k.raw`: received audio before resampling.
- `modem_rx.raw`: received audio after conversion to9600Hz for the guest DSP.
- `modem_tx.raw`: guest DSP output before outgoing resampling.

The first short cohort passes9 producer checks. All34 authored upstream bytes
and6000 downstream bytes match. Independent native decoding of the guest's8kHz
PCM also recovers exactly34 bytes. Sample-level comparison finds486480 matching
overlapping samples after a constant400-sample/50ms delay and no altered samples.
All267 unique waveform anchors show that same offset. A comparison limited to
20ms packet boundaries initially looks different; sample alignment proves this
is fixed latency in this run, not corruption. Maximum observed tunnel arrival
gap is35.08ms. The external/tunnel streams share an exact prefix;10 external
packets arrive after tunnel shutdown. Export snapshots end before the final
captured RTP tail, so only their actual overlap is compared.

See [the capture receipt](../../docs/validation/synthmodem-receive-trace.json) and
[the current PCM analysis](../../docs/validation/synthmodem-receive-pcm.json). This short
run does not reproduce or resolve the long DOS insertion. PCM, compiled images,
timing captures and raw session data remain in ignored build storage.

The full DOS runner also has an explicit diagnostic option using the exact
accepted diagnostic runtime identities:

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-receive-trace-01/runtime \
  --receive-trace --output build/bbs-lab/synthmodem-audio-dos-trace-new
```

The full traced cohort -06 passes19 producer/19 independent checks, with exact64
upstream and46908 downstream bytes. Its3559200 overlapping guest samples match
the input after a constant60ms delay, and both offline decoders recover exactly
the DOS input. The earlier -05 six-byte failure remains unresolved.

The optional observer records DOS input and actual guest data timestamps, and
freezes the workload stream at serial close before exporting audio. Export occurs
before bridge teardown; later export/teardown events stay distinguishable from
application traffic. This adds diagnostic instrumentation, not an installed
bridge change or physical hardware evidence.

## PJSIP source finding

The pinned d-modem source initializes jitter prefetch/min/max to40ms but does
not override `jb_discard_algo`. PJSIP2.15.1 defaults that field to
`PJMEDIA_JB_DISCARD_PROGRESSIVE`; stream creation applies that policy separately
from prefetch. In contrast, `pjmedia_jbuf_set_fixed()` also selects
`PJMEDIA_JB_DISCARD_NONE`. Equal prefetch bounds alone therefore do not disable
progressive frame discard. This is a concrete configuration gap; it is not yet
proven to explain the DOS insertion.

[`nix/dmodem.nix`](../../nix/dmodem.nix) provides paired source builds against
the same pinned PJSIP2.15.1 sources and Nixpkgs lock. Baseline and candidate use
identical library/build options; only the candidate explicitly selects DISCARD_NONE.
Use `./tools/build-dmodem baseline --no-link --json` or `candidate` in place of
baseline. Impure evaluation only resolves this checkout's path; all downloaded
source hashes and the toolchain remain pinned. These builds are separate from
ordinary DOS builds and do not include original PCPlus executables.

The paired binaries build as static ELF32/i386. `./tools/build-dmodem jitter-check
--no-link --json` also builds/runs an actual PJSIP API sequence test: a bounded
initial burst followed by3000 balanced sequential arrivals/reads, with no network
loss or reordering and no capacity exhaustion. Constant2-frame prefetch bounds
with progressive discard skip24 input sequence numbers (2988 normal reads);
DISCARD_NONE gives3000 normal reads and zero sequence gaps. The raw library
counters are retained in the [receipt](../../docs/validation/synthmodem-jitter-policy.json).
This establishes a policy effect, not the cause of the earlier DOS failure.

The [paired VM comparison](synthmodem-jitter-vm.md) now boots both builds and
reproduces upstream corruption after a lossless, ordered backlog release. The
candidate preserves the waveform and all authored bytes under that profile;
the independent comparison verifies that only d-modem differs in the images.
Normal DOS/BBS composition, broader packet delay/loss tests and transfers remain
separate acceptance gates. No14.4 or Boca/ATA result
follows from a1200-bps software diagnostic.
