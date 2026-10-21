# Automatic download over the software modem line

This route exercises the source-built DOS terminal's automatic ZMODEM receiver
against the owned, stock ENiGMA server through SynthModem's SIP/RTP/audio path.
It uses the existing 11,521-byte `PCXTEST.BIN` fixture, full server artwork and
the server's configured SEXYZ ZedZap helper. It does not inject protocol replies
or modify server code. Physical Boca/SPA2102 compatibility is a separate gate.

The `download` route in `synthmodem_audio_dos.py` enables automatic receive in
the isolated test profile and selects `D:\RECV\`. Its ASPECT child logs in,
finds and tags the fixture, selects the download and exits after starting the
server helper. The parent can then acquire receive ownership; leaving the child
active would prevent the parent's automatic signature detector from running.

`audio_download_keys.asm` is a test-only BIOS input helper. It waits for the
visible receiving screen, then the returned File Base prompt, before searching
for the same file and exiting through Alt-X. It cannot generate a successful
transfer or a pass marker. Its watchdog bounds a failed prerequisite through
ordinary BIOS input. The [separate DOS helper proof](../../docs/validation/audio-download-keys.json)
checks the phased key sequence and timer restoration with shortened test-only
delays. That proof establishes no real transfer result.

## Acceptance evidence

The producer's file/helper/menu checks are preliminary. After the call is
terminal, run the independent byte and ownership audits followed by the transfer
audit, using the pinned Nix environment:

```sh
./tools/modem-dev --command python3 lab/bbs/audit_synthmodem_audio_dos.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_audio_download.py COHORT
./tools/modem-dev --command python3 lab/bbs/check_audio_control_timing.py COHORT
```

The transfer audit reconstructs both Telnet application streams from recorded
relay events. It validates the complete decoded frontend write/input manifests
against those same streams and checks control timing on one Node monotonic
clock. BBS emission can precede DOS delivery by many seconds on the audio link;
it cannot supply a receiver-delivery deadline. The
[retained queue/timing witness](../../docs/validation/audio-transfer-clock.json)
matches12 independently diagnosed CRC arrivals and13 DOS controls on audio02.
These are transport-boundary times, not application-consumption timestamps.
The audit requires source-matching ZFILE metadata, every data CRC and
payload, verified offsets, ZEOF, opposite-direction control responses and the
ZFIN/OO finish handshake. It also requires the exact DOS file, absence of receive
staging files, one genuine helper with successful exit, official server metadata
and counter advancement, and a fresh keyboard search/list after helper exit.
Full audio byte identity, normal DOS return, restored UART/timer state, frozen
input identities and absence of gateway errors remain required.

The protocol/timing logic was checked read-only against the retained direct
download `synthmodem-enigma-download-01`: 11,521 verified bytes and four
corroborated opposite-direction controls. This validates an audit input example;
it does not establish an audio download pass.

## First audio counterexample

The first audio download cohort, `synthmodem-audio-download-01`, is terminal and
[failed](../../docs/validation/synthmodem-audio-download.json). Its ASPECT child
completes and the parent starts receiving, but no file installs. SEXYZ exits255;
the DOS screen shows RX timeout. Post-helper input, normal DOS return and
UART/timer restoration fail. The ownership audit passes all12 consistency
checks, without implying application acceptance. No gateway error is logged.

The42-byte restoration aggregate includes the test helper's INT1C vector.
Detailed comparison shows that only bytes32..35 differ: actual IRQ vectors and
the six UART/PIC bytes restore exactly, while the test helper remains installed
on premature exit. Both original aggregate/timer gates remain false. This is
not evidence of a separate UART register-cleanup defect.

`diagnose_audio_download.py COHORT` reconstructs packet CRC/source matches and
frontend timing without writing to the modem or BBS. On this failure it verifies
eight observed sender packets and independently reproduces the66,060-byte exact
caller prefix and29.618-second cancellation interval after the previous complete
packet's CRC. The [diagnostic receipt](../../docs/validation/audio-download-diagnostics.json)
also records the split hardware snapshot. These are evidence-consistency checks,
not transfer acceptance. Frontend CRC arrival is not an application-consumption
timestamp or proof that storage accepted that packet.

All167 online DOS bytes match the independent caller decoder, guest frames and
Telnet stream. The downstream caller is an exact66,060-byte prefix of the
82,294-byte BBS stream, so complete downstream acceptance remains false.
The receiver's cancel is observed29.62 seconds after the previous verified
packet's CRC. The next4KiB packet takes35.24 seconds to arrive and its CRC reaches
the frontend5.64 seconds after cancel. The live watchdog selected540 BIOS ticks
from the fixed38400 DTE setting, although carrier negotiation was1200 bps.

`standalone/check_carrier_transfer_deadline.py` reproduces this with the linked
production receiver, UART ISR, watchdog and storage. Quantized1200-bps input
fails with timeout3 at38400 DTE; identical input installs exactly at1200 DTE.
The [counterexample receipt](../../docs/validation/carrier-transfer-deadline.json)
preserves the failed probe prerequisites separately. This model does not claim
physical timing or a corrected product.

The next change must distinguish fixed DTE speed from the carrier's packet-time
budget while preserving bounded verified progress. The stock helper's retry and
finish deadlines versus audio queue backpressure also need investigation: fixing
the local deadline alone is not yet proof the unchanged server transfer passes.
Keep the original fixture, full artwork, CRC/control/finish, return-input and
cleanup gates. Do not rerun merely because an observation times out. Uploads,
cancellation, retry/fault behavior, sustained pressure, other peers and physical
hardware acceptance remain open.

## Corrected deadline and completion follow-up

Audio download02 now stores the exact file, preserves all360 online bytes and
the full83244-byte BBS display, and exits with restored IRQ/UART/PIC/timer state.
Its [retained failure](../../docs/validation/synthmodem-audio-download-02.json)
is the missing final `OO` and corrupted post-helper command input. Actual BIOS
`S`/Enter is sent, but late protocol controls have already reached the BBS menu.
The [completed-replay correction](zmodem-completed-replay.md) reproduces and fixes
the queued-data/closing-header behavior in the linked receiver.

## Accepted normal audio download03

The [unchanged full-workflow repeat](../../docs/validation/synthmodem-audio-download-03.json)
passes25 producer,26 independent byte/cleanup,15 protocol/file/resume and12
ownership checks. All205 online DOS bytes match the independent caller decoder,
guest and Telnet input. The entire89233-byte BBS stream plus187 bridge bytes
survives exactly. The installed11521-byte file matches its source SHA-256.

Every observed data/replay CRC, offset, EOF, required opposite-direction control
and literal ZFIN/OO finish passes. No post-commit ZNAK or late protocol control
reaches the returned BBS menu. Actual BIOS S/Enter and filename input enters
Search and displays the file list. The terminal exits normally, restoring the
IRQ vectors, UART/PIC and keyboard-helper timer vector. The frontend has no
gateway error, skipped write, failed callback or pending output.

The timing verifier retains the original successful captures and rejects copied
ACK and ZFIN times moved before the corresponding decoded data. Its two
negative cases do not generate protocol replies or modify the product capture.

This accepts one automatic download on the frozen V.22/1200 software SIP/RTP/DSP
path, unchanged stock local ENiGMA/full artwork, explicit250ms bridge key framing
and38400/8N1/HARD emulated UART. Uploads, transfer cancellation/loss/pressure,
Synchronet over audio, arbitrary remote TCP fragmentation, physical Boca/SPA2102
and14400-bps or whole-application acceptance remain separate requirements.
