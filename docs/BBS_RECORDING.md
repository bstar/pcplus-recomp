# Recording and replay on Synchronet and ENiGMA

The [carrier-build checkpoint](validation/recording-abort-carrier-audio.json)
accepts parent7b6ded5c/runnerdfee1e95 on the normal recorder route. All26
producer,34 independent and12 serial checks pass:60,926 BBS display bytes
plus187 bridge bytes arrive exactly, with78 online bytes independently
waveform-decoded. Normal hardware/timer/SIP/VM cleanup passes.
[Fresh direct BBS recorder/replay](validation/bbs-abort-carrier-compat.json) and
[stock-window checks](validation/bbs-abort-carrier-window.json) also pass.
This does not cover script-time windows over audio, full parent carrier/status,
other profiles or physical hardware. Older checkpoints keep their identities.

The [confirmation-build regression](validation/bbs-abort-owner-compat.json)
repeats all four recorder/replay sessions with parent7b6ded5c, runner12d40249
and the24KB-stack DOS compilerfc200c8c. [Two fresh script-window sessions](validation/bbs-abort-owner-window.json)
also pass, including regular parent-menu return. [One fresh normal ENiGMA
recorder audio route](validation/recording-abort-owner-audio.json) passes26
producer,34 independent and12 serial checks:60,389 BBS display bytes plus187
bridge bytes arrive exactly, with77 online bytes independently decoded. This
is V22/1200 software SIP/RTP/DSP/Telnet; physical hardware and script-time
windows over audio remain open. Earlier checkpoints below retain their identities.

The [current validation record](validation/bbs-recording-prompt.json) accepts
selected read-only recording/replay workflows on both existing loopback BBSes.
The production DOS terminal records navigation through File/C, actual DOS
ASPCOMP compiles the unedited source, and a fresh authenticated session launches
it through File/A and the production ASPECT runner. A second manual navigation
then proves return to the parent, followed by normal exit and exact sampled
DOS/UART restoration. Credentials precede recording and are absent from its TX.

| Server | Recorded route | Recorded user payload | Replay session |
| --- | --- | --- | --- |
| Synchronet 3.22a development snapshot | Main → Files → Main | `5451` | Script route, then same route manually; actual display/video checked |
| ENiGMA½ 0.5.1-beta | Main → Messages → Main | `4D0D510D` | Server log confirms both script and manual routes |

The terminal SHA256 is
`98ef7cd5466b8c3e55079e49dfc87d2813d511f645230dc1685073f6ff0ea7e5`.
The runner is the ordinary source-built ASPECT executable, not the diagnostic
observer used to investigate the earlier failures. The independent audit checks
raw Telnet/user bytes, the original recorded source, frozen inputs and manifests,
normal DOS exit, hardware snapshots and actual server/display semantics. Earlier
failed attempts remain [preserved separately](validation/bbs-recording-failure.json).

## Receive stream and prompt selection

The original raw tap recorded ANSI continuations that native WAITFOR cannot see.
Normal recording now follows input translation; parser continuations remain
outside matching. An unread parser lookahead enters recording only if delivered
as a normal lead. This preserves native ASPECT receive/render behavior.

A separate source-built diagnostic runner then logged the actual mapped stream
and send/wait outcomes. It showed two further causes. ENiGMA's prompt of thirteen
spaces followed by three ESC leads occurs in the captured stream, yet the native
prefix-only matcher misses it. Synchronet's final recorded prompt referred to a
different message area from the next session. Increasing the diagnostic delay
exposed timeout/return; it did not make ENiGMA send its missing command.

The recorder now selects the longest observed suffix that the unchanged native
matcher can find reliably. A bounded prefix table identifies prefixes whose
proper borders would require a fallback longer than the native zero/one-byte
fallback. ASCII case folding matches native defaults. ENiGMA's example becomes
one space followed by three ESC leads. Pure repeated-byte prompts keep their
full length. Existing quote/caret/control encoding and bounded writes remain.
Sixty-eight native CPU checks include the actual 1908-byte diagnostic stream:
the old pattern occurs but fails; the generated suffix matches at byte69.
These CPU tests model transport/time callbacks and remain distinct from DOS.

Stopping flushes accepted pending TX and writes the source footer. It does not
emit a wait for the final RX tail: no later recorded action depends on it, and
the resumed terminal renders the response. Prompt waits before following user
output remain bounded and exit before that output on timeout. This avoids
stalling completed scripts on session-specific final status text. Generated
recordings are not edited to obtain the accepted BBS results.

## Reproduction and scope

With current source-only terminal/ASPECT/ASPCOMP builds and the existing synthetic
loopback servers listening on 23231/23233, use fresh labels:

```sh
./tools/dev --command python3 lab/bbs/recording_dos.py synchronet --label NEW
./tools/dev --command python3 lab/bbs/recording_dos.py enigma --label NEW
```

The optional observer builds independently:

```sh
./tools/dev --command python3 standalone/build_aspect_match_trace.py
./tools/dev --command python3 lab/bbs/recording_dos.py enigma --trace --label TRACE_NEW
```

Its manifest identifies diagnostic code, unchanged production baseline hashes,
record layout and timing effects. Diagnostic success alone does not accept the
production runner. `./tools/build test-aspect-recorder` includes the portable
native prompt checks; the recorded-stream option is an additional local proof.

Tests use COM2,19200,8N1,HARD in DOSBox-X with the Hayes/Telnet model. The model
forwards configured shutdown `+++`/`ATH` bytes and does not implement real escape
to command mode; the audit requires that exact modem-owner suffix separately
from navigation. Software audio, physical Boca/SPA2102 timing, other profiles,
transfers, arbitrary dynamic prompts and complete ASPECT remain unverified.
This checkpoint closes no full F01–F16 gate.
