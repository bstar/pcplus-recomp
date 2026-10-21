# Same-call cancellation and retry

The next audio integration gate exercises the ordinary DOS XMODEM sender twice
on one stock Synchronet connection. The first attempt must receive an ACK and
cancel at a complete CRC packet boundary. The second must send the same local
file, without an application restart, to a fresh remote filename and complete
the receiver's two-EOT NAK/ACK exchange. Files and Main must remain interactive.
This gate does not establish physical Boca/SPA2102 compatibility.

The reference connection in
`build/bbs-lab/synchronet-audio-retry-reference-01` passes eleven checks:
one connection, CRC/ACK/CAN, Files, a fourteen-block full retry, exact source and
padding, official metadata and preservation of the first partial and prior
files. This is a TCP reference, not evidence that the DOS/audio route passes.
The DOS keyboard probe passes six checks; fifteen initial ASPECT waits also
match the reference's raw bytes. Those are preparation checks only.

The first actual audio attempt,
`build/bbs-lab/synthmodem-synchronet-retry-audio-01`, failed. The sender cancelled
after two complete CRC frames, but its second attempt sent no data and showed
`TX timeout`. Synchronet reported a zero-length upload and later disconnected
the inactive session. The watchdog returned normally to DOS with UART, IRQ,
PIC and timer state restored. The [failed receipt](validation/synthmodem-synchronet-retry-audio-01.json)
preserves all three failed producer gates and the independent audit failures.
A read-only observer captured the first 2,048-byte partial, its inode,
modification time, content and complete official metadata before retry indexing.

The original recipe queues the second Alt-S three BIOS ticks after `n`, without
waiting for the receiver-ready banner. The decoded banner finishes 1.099 seconds
after that `n`. A separate linked native reproduction accepts a quiet CRC
handshake and two bytes of noise, but a 55-byte receiver banner exhausts startup
attempts with no data sent. Local application-consumption timestamps were not
captured, so this supports a sequencing diagnosis without proving the sole
cause of the failed audio run. Native startup noise tolerance remains a gap.

The revised `*_retry_ready*` harness waits for the complete
`transfer now (Ctrl-X to abort):` marker before opening the second local sender.
Its six DOS BIOS checks explicitly prohibit Alt-S at an incomplete banner;
the new TCP reference passes eleven checks and all fifteen ASPECT waits match
raw reference bytes. The fresh actual attempt,
`build/bbs-lab/synthmodem-synchronet-retry-ready-audio-01`, passes all 100 client
workflow checks. Separate source files preserve the original failing recipe.

The [accepted client retry receipt](validation/synthmodem-synchronet-retry-ready-audio-01.json)
binds 27 producer checks, 36 independent whole-stream/protocol checks, twelve
frontend ownership checks, twelve official metadata/custody checks and thirteen
control baseline/counterexample checks. The first attempt ends after two
complete CRC frames and CAN; the second sends fourteen unreplayed CRC frames,
all fourteen data ACKs and the two-EOT NAK/ACK finish. Both attempts use the same
11,521-byte local source and open application. The completed receiver file has
127 bytes of SUB padding, for 11,648 bytes total. Files/Main and normal DOS return
are verified, with identical before/after UART, PIC, IRQ and timer snapshots.

The exact online stream is 13,956 bytes, and the complete BBS display is 52,099
bytes. All 52,308 frontend bytes, including Hayes results and bridge text, have
successful local write callbacks with no skips, pending writes or gateway
errors. Caller audio is independently decoded; guest/Telnet byte identity,
continuous RTP and SIP cleanup also pass. The receiver records three startup
timeouts on the cancelled attempt and two on the retry, matching four and three
CRC requests respectively; no data-block errors occur. These are software
audio results at 1,200-bps carrier and 38,400-bps DTE.

The original 2,048-byte partial retains exactly the observed bytes, inode,
modification time and complete official metadata. It remains indexed, so the
receipt deliberately has `actual_same_call_retry_accepted: true` and
`server_partial_cleanup_accepted: false`, with overall `passed: false`. This
does not resolve native startup noise tolerance, carrier loss/reconnect,
sustained pressure, other protocol families or physical hardware acceptance.

The producers and independent audits bind the native executable, source,
ASPECT compiler and script, keyboard helper, runtime, server inputs and raw
transport captures. `audit_synchronet_retry_metadata.py` compares the retained
partial against that live snapshot and checks the full retry's bytes, padding,
official hashes and receiver records. `check_synchronet_retry_controls.py`
rejects twelve timing, source, cancellation and finish counterexamples using
copies of the captured streams. Its synthetic thirteen-check self-test passes;
the actual-capture checks require a completed, passing independent audit.

Stock Synchronet has already been observed publishing cancelled partials.
Retaining an indexed partial is a separate server cleanup gap even if a later
full retry succeeds. Neither an upload log entry nor an indexed filename alone
proves successful delivery. No test deletes the partial or changes the receiver
to make that gate pass.

Run official FileBase reference, preflight, observer and metadata commands in
`./tools/bbs-dev --command`; that pinned shell provides the official server's
shared libraries. Run the audio producer and offline Node decoder through
`./tools/modem-dev --command`, and linked native reproductions and DOS BIOS
probes through `./tools/dev --command`. A missing shared library is a lab setup
failure and does not establish a terminal compatibility defect.

After a fresh producer exits, the audit order is frontend ownership, offline
caller decoding, independent byte/protocol audit, official metadata and partial
custody, actual-capture counterexamples, then the public recorder. Each report
must pass its declared client gates before `record_synchronet_retry_ready_audio.py`
can accept that workflow. The recorder keeps overall success false while the
cancelled partial remains indexed. Original failed capture files are never
edited, and all subsequent attempts use fresh remote names and output folders.
