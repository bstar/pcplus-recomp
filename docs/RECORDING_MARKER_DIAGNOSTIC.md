# Recorder ready-marker diagnostic

The completed [diagnostic receipt](validation/recording-marker-audio-diagnostic.json)
records76 consecutive ready-marker samples before disappearance, with no
recipe keys or keyboard queue retries. See the
[layout counterexample and current fixture](RECORDING_MARKER_LAYOUT.md).
A separate [normal footer-gated run](validation/recording-footer-audio.json) now
passes selected-route audio acceptance; the diagnostic and stopped runs remain
ineligible for that acceptance.

The preceding normal audio run reached Files, but the BIOS helper delivered no
recipe keys before its watchdog. The [failure receipt](validation/recording-manual-reconnect-audio-failure.json)
does not establish why: the helper requires a visible `RECORDER READY` marker
through its initial dwell. Missing text and briefly visible text can produce
the same ordinary phase0 report. The current main application and unchanged
ordinary helper pass the ENiGMA TCP recording/compilation/replay control.

The optional `--recording-marker-trace` mode measures that distinction in the
actual SIP/audio route. It changes only the test TSR, whose private counters
observe its own phase0 screen scans. It does not write application or serial
state, change the ready-marker requirement, or shorten the key dwell. The
ordinary helper executable remains byte-identical to the retained preceding
binary. [Probe audit](validation/recording-marker-probes.json) verifies seven
ordinary and eight diagnostic BIOS cases, including a marker visible for two
samples that correctly admits no recipe keys. Three controlled admission tests
reject diagnostic evidence at the production helper, preparation and final
audio-receipt boundaries.

`RECTRACE.BIN` contains eleven little-endian words:

| Word | Meaning |
| --- | --- |
| 0 | Magic `0x5254` |
| 1 | Version, currently 1 |
| 2 | Phase0 screen scans |
| 3 | Scans matching the full ready marker |
| 4 | Separate matching runs |
| 5 | Helper elapsed tick at first match, or zero |
| 6 | Helper elapsed tick at last match, or zero |
| 7 | Longest run of consecutive matching scans |
| 8 | Current run length at the last eligible scan |
| 9 | Missing-marker scans after the first match |
| 10 | BIOS cursor DX at the first match |

The regular sixteen-byte `RECKEY.BIN` still reports phase, delivered recipe
keys, exit reason and elapsed ticks. A90-tick initial dwell needs91 matching
samples: the first starts the dwell. Visibility shorter than a BIOS sampling
interval may remain unobserved; zero sightings does not prove the text was
never painted. Sampling stops after phase0 admits its key sequence.

The diagnostic uses a declared12000-tick watchdog, nominally about11 minutes,
instead of the ordinary32000-tick limit. That bounds observation, not production
acceptance. Both producer and independent auditor explicitly fail a diagnostic
acceptance gate. The ordinary preparation/final recorders reject this mode even
if other workflow checks pass. Actual normal audio must still pass separately
after the cause is understood and corrected.

Run only after fresh ordinary BIOS/TCP controls pass and no other ENiGMA
session owns the lab log boundary:

~~~sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-buffered-runtime-01/runtime \
  --buffered-runtime-proof build/bbs-lab/synthmodem-buffered-runtime-01/result.json \
  --route recording \
  --recording-key-checks build/bbs-lab/recording-marker-normal-02/result.json \
  --recording-tcp-checks build/bbs-lab/results/enigma/recording-marker-control-01/recording-checks.json \
  --recording-marker-trace build/bbs-lab/recording-marker-trace-02/result.json \
  --output build/bbs-lab/recording-marker-audio-NEW
~~~

A nonzero producer exit is expected for diagnostic mode; inspect every failed
check rather than interpreting that status as an accepted or completed workflow.
After termination, retain independent DSP caller decoding, serial accounting and
the normal independent audio audit. `audit_recording_marker_trace.py flight`
then validates the raw counters, source/capture hashes and both helper binaries
reassembled using the admitted Nix NASM. It publishes diagnostic observations
with `actual_audio_accepted=false`. Physical Boca/SPA2102 and full application
requirements remain open.
