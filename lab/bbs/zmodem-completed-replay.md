# Completed files and queued ZMODEM traffic

The [second normal audio download](../../docs/validation/synthmodem-audio-download-02.json)
stores the exact11521-byte file and passes the complete360-byte online input,
83244-byte BBS display, helper exit and DOS/UART/IRQ/timer restoration checks.
It still fails transfer acceptance: no final `OO` arrives and post-transfer
keyboard input does not enter Search.

The capture contains eight timeout-driven data retransmissions already queued
behind the original EOF. After checking and installing the file, the receiver
sent ZNAK for each queued ZDATA header. Those replies consumed the stock
sender's closing attempts. Three ZNAKs and the receiver's eventual ZFIN arrived
2117..6038ms after the external helper exited, becoming BBS command input.
The actual BIOS `S`/Enter follows that protocol tail, explaining the unusable
command prompt without blaming the input helper. The transport captures are
byte-exact in both directions. The initial file-progress deadline correction
remains valid.

The [pinned sender source](https://github.com/SynchronetBBS/sbbs/blob/e7a825704ef5329c7ef8408749671291a85ef7f2/src/sbbs3/zmodem.c)
alternates ZFIN/ZABORT during bounded finish retries and sends `OO` only after
receiving ZFIN. A successful external-helper exit alone therefore cannot prove
the finish. All original protocol/return gates remain mandatory.

## Native correction

After checked EOF, the receiver now silently drains CRC-framed data whose
range lies within the completed file. It neither reopens nor writes the file,
sends a new ACK/NAK, increments file/byte counts, nor refreshes accepted progress.
Each stale frame consumes the existing retry allowance. Invalid CRC, an
out-of-range packet or an empty continuing packet fails explicitly. This is
discarding already queued traffic, not accepting new content for a closed file.

The receiving finish path now consumes bounded, CRC-valid closing headers before
literal `OO`, instead of returning after32 raw bytes. Only zero-position
ZFIN/ZABORT headers are allowed after the initial ZFIN. An initial ZABORT before
that closing state remains fatal. The receiver sends its one ZFIN response,
preserving the next BBS input boundary. The parser permits fewer than ten queued
closing headers and at most512 observed bytes; the one-second per-read idle
bound and live verified-progress watchdog remain active. Missing `OO` stays an
unconfirmed finish. No corrupt/noise header can turn a later `OO` into success.

The change reuses the transfer arena and preserves the64832-byte DS=SS extent.
It adds no persistent buffer, changes no BBS/helper/runtime configuration and
does not treat an exact installed file as completed protocol acceptance.

## Evidence and remaining test

The [saved predecessor counterexamples](../../docs/validation/zmodem-completed-replay-counterexample.json)
and [corrected native proof](../../docs/validation/zmodem-completed-replay-fixed.json)
use the same linked checker. Three cases isolate queued data, queued closing
headers and their composition. Each corrected case passes seven checks: no
fault, exact file, one checked create/install, closed handles, complete peer
exchange, confirmed-success notice and only `APP` left for normal input. The
predecessor saves the same file but fails finish/tail checks in all three cases.

Thirteen strict C89 component cases verify corruption, range/iteration limits,
initial abort, literal-OO handling, flow control and missing-OO failure. The
existing component regression also passes92 scripted cases and24 independent
lrzsz/stock-SEXYZ sessions. These are native/component evidence, not a real
audio or physical hardware pass.

The [full native regression](../../docs/validation/zmodem-completion-regression.json)
also passes78 linked workflows, five cancellation cases, three far-call/IRQ/layout
groups and the slow-carrier recheck on this executable. The
[actual DOS automatic-transfer repeat](../../docs/validation/zmodem-completion-dos.json)
passes all14 checks with three files including65797 bytes, resumed DSR/keyboard,
normal exit and UART restoration. It uses a fast direct emulated serial link.

```sh
./tools/dev --command python3 standalone/check_zmodem_completed_replay.py
./tools/dev --command python3 standalone/check_zmodem_completed_replay.py --counterexample
./tools/dev --command python3 standalone/check_zmodem_completion_bounds.py
```

The optional counterexample command uses only the ignored source-built
predecessor under `build/terminal/completed-replay-baseline`. The default checks
are in `test-terminal-zmodem-live` and `test-zmodem` respectively.

The [normal audio download03](../../docs/validation/synthmodem-audio-download-03.json)
repeat now passes25 producer,26 independent byte/cleanup,15 protocol/file/resume
and12 ownership checks on the unchanged file/art/server/bridge. The full205-byte
online input and89233-byte BBS stream are exact; checked file, CRC/control/OO,
actual resumed search/list and clean DOS/UART/IRQ/timer return all pass. No ZNAK
or protocol control follows helper retirement. The new core/native proof and
runtime inputs remain independently verified against their frozen hashes.
Uploads, cancellation/loss/pressure, other peers, physical Boca/SPA2102 tests
and full-application completion remain separate requirements.

## Current download queue measurements

The [current-terminal timing diagnosis](../../docs/validation/current-enigma-download-queue-01.json)
rechecks the accepted download's complete canonical streams, all packet CRCs and
source bytes, and both relay/frontend manifests without modifying the captures.
It aligns the relay's absolute host monotonic timestamps with the frontend's
Node clock. The first EOF enters the bridge at566.073s and reaches the decoded
frontend at656.789s: a90.716-second queue interval. These are transport
observations, not timestamps of DOS application consumption.

All eight verified replay packets (8320 payload bytes) have already entered the
bridge before that EOF reaches the frontend. They enter at approximately
11.011-second intervals, with lengths4096,2048,1024,512,256,128,128,128. They all
reach the frontend after the original EOF. The reverse stream contains only the
initial ZRPOS0; these replays are not responses to additional observed receiver
ZRPOS requests. This narrows the efficiency investigation without proving an
exclusive timeout cause or changing the existing successful transfer result.

The next controlled comparison should bound data queued between checkpoints
on the same slow audio path. The current receiver advertises8192 bytes with
CANOVIO enabled. Reducing that value alone needs care: the inspected Synchronet
sender chooses a checkpoint based on its current block length, but still reads
and sends a whole block and grows the block after successful delivery. Receive
credit therefore must not be assumed to cap individual packets or guarantee a
reply before a1200-bps path drains them. Compare receiver capability/credit and
observed acknowledgment timing against the unchanged peer, retaining every
CRC/source/finish/file/menu/cleanup gate. No candidate has yet passed this audio
comparison, and the active multiline editor campaign retains its frozen inputs.

```sh
./tools/modem-dev --command python3 lab/bbs/diagnose_audio_download_queue.py \
  --receipt docs/validation/current-enigma-download-audio-01.json \
  --output build/bbs-lab/download-queue-new.json
```
