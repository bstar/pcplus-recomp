# Frontend error provenance and write ownership

The successful editor semantics in audio editor04 still had read ECONNRESET in
the producer's gateway-error list. Earlier captures retained the message but
not its emitting endpoint or phase. They cannot retrospectively establish that
it came from DOSBox, the answering modem backend or SIP/RTP. Do not relabel those
historical errors as expected from a similar-looking new test.

The audio frontend now retains every legacy error and adds a structured error
event. It records the source, code, syscall, call phase, command/online mode,
available socket state and write counters. Sources distinguish the DOS TCP
frontend, local write callbacks, answering backend, pool, originating/external
SIP, RTP, session activation/setup, dialing and PCM export. No error is filtered
or downgraded by this observer. Serial end, close/hadError and shutdown events
preserve their own snapshots and order.

This is lab observability. The source-built DOS products, normal framed modem
runtime and BBS are unchanged. It does not implement a Boca command set or make
a physical DTR/DCD claim.

## Byte evidence

The old serial-out.bin remains the complete frontend **attempt** stream. New
records reference exact offsets and lengths within that same byte stream:

| Artifact | Meaning |
| --- | --- |
| serial-write-events.jsonl | Attempt offset/length, phase, timestamps, actual write invocation, callback completion/error or closed-socket skip |
| serial-submitted.bin | Bytes passed to actual socket.write invocations, including any invocation that fails; not a peer-read acknowledgment |
| serial-completed.bin | Submitted bytes with successful local callbacks, kept in original attempt order; not proof DOS consumed them |
| serial-skipped.bin | Attempts skipped because the socket was absent or destroyed |

The observer calls the original socket writer once with the original bytes,
returns its backpressure result, and observes its callback. It preserves byte
boundaries and ordering. Synchronous exceptions are recorded and rethrown.
The data snapshot belongs to the observer, so later caller buffer mutation
cannot rewrite captured evidence. Teardown does not write to a destroyed socket.

The independent auditor reconstructs these artifacts from the original attempt
offsets, checks every final counter and callback, binds producer capture hashes,
and checks that the structured errors exactly retain the legacy list. It also
checks close/shutdown ownership, input byte accounting and write submissions
relative to the actual close event. An evidence-consistent result is not a
gateway or application acceptance pass.

Post-close DSP output may still be counted as an attempted frontend send while
diagnostic export runs. Neither that count nor a local write callback proves
that a closed DOS connection received later bytes. Actual pre-close editor
screens and the separate byte/media audits retain their existing meanings.

## Controlled endpoint reset

The [observer receipt](../../docs/validation/synthmodem-serial-io-evidence.json)
contains six checks: verbatim write/return ownership, failed versus skipped
writes, rethrown synchronous failure, exact artifact offsets, a real TCP RST,
and rejection of writes to the closed peer. The owned loopback client explicitly
uses resetAndDestroy. The server observes read ECONNRESET, close/hadError=true
and no FIN/end event. This proves the controlled source and observation shape;
it does not prove the source or intent of any previous DOS/audio reset.

```sh
./tools/modem-dev --command node lab/bbs/check_serial_io_evidence.js \
  build/bbs-lab/serial-io-evidence-new
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py \
  build/bbs-lab/audio-editor-with-observer-new
```

Use fresh output directories. The audit requires a completed producer cohort
with the new observer; it does not fabricate missing endpoint evidence in older
captures. Repeat the actual normal-image editor route, inspect the observed
source/phase and retain the reset gate until its meaning is established.

## Normal editor05 observations

The [actual normal-runtime receipt](../../docs/validation/synthmodem-serial-frontend-dos.json)
now records the reset's source and phase in this specific call. Its single error
is DOS-TCP/read/ECONNRESET at online phase,516.524335929 seconds. The frontend
close/hadError=true follows3.375ms later; there is no FIN/end event. Shutdown
starts after that close. The observed error therefore precedes modem teardown
and comes from the DOSBox-facing TCP endpoint. This does not retroactively
identify earlier uninstrumented resets or establish the peer's intent/kernel
reason for resetting.

All47983 attempted bytes were passed to actual socket.write invocations and
had successful local callbacks. No write failed, remained pending or was skipped.
No write was submitted after close. The endpoint's129 input bytes match the
complete serial input capture. The12-check independent ownership audit passes.
Local callback success remains distinct from DOS peer consumption.

Actual DOS enters the stock editor and passes every exercised Home/End/Delete/
Insert/overtype/Tab/page-boundary/Ctrl-Y response. UNSAVED is visible atOVR01,08.
No post is saved, the profile/server stay unchanged, DOS returns normally and
UART/timer state restores. All120 online bytes match the caller waveform
decoder, actual guest DATA_RX and Telnet input. This normal call does not
reproduce the prior intermittent upstream insertions.

The complete downstream gates remain false. The caller is the exact47961-byte
prefix of the bridge plus BBS display, with a616-byte missing suffix at close.
The suffix contains editor Escape-menu rendering. There is no internal byte
replacement in the captured prefix, but this normal call has no guest PCM or
arrival timing to prove a media cause or the missing suffix's precise generation
phase. It is neither trimmed nor accepted as delivered. Producer acceptance
stays false for the reset; the full byte audit also retains both downstream
failures. Next correlate actual input, BBS-output and endpoint-close timing and
inspect the owned emulator's close path before deciding expectedness or changing
any gate. Physical hardware, transfers and complete receive acceptance remain open.
