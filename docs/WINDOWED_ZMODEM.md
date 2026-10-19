# Bounded windowed ZMODEM sending

The maintained sender can send multiple subpackets before waiting for an ACK.
It keeps the wire cursor separate from the peer-confirmed position used by the
DOS progress display and accepted-progress watchdog. It reuses checked source
seeking for retransmission rather than retaining another payload buffer.

## Negotiation and framing

Asynchronous sending requires both CANFDX and CANOVIO. Other peers retain
synchronous ZCRCW packets. The maintained policy uses a maximum 8 KiB window,
clamped to a nonzero advertised receiver capacity; payloads remain at most
1 KiB. A separate segment counter enforces receiver capacity even when
asynchronous ACKs free window credits. The window policy is currently fixed in
source; exposing it in saved settings remains part of the unfinished schema/UI.

The first data packet after ZRPOS uses ZCRCW and requires the exact boundary ACK.
After synchronization, ZCRCG continues the frame; ZCRCQ requests an asynchronous
ACK at intervals of at least one quarter of the window. Reaching the outstanding
window or receiver storage limit ends the frame with ZCRCW. The final ordinary
packet uses ZCRCE, followed by ZEOF. Only ZRINIT after an emitted ZEOF completes
the file. Empty files and resumed EOF positions use the explicit EOF path.

The existing read callback accepts a zero-second poll. Partial headers survive
empty polls, including a split escape. Each packet samples incoming controls;
noise scans, duplicate controls, timeouts and repeated rewinds remain bounded.
ACKs cannot move backward or beyond transmitted bytes. Older ACKs cannot release
a synchronous wait; asynchronous confirmations can advance within the sent range.

Mid-frame ZRPOS closes the old stream with an empty ZCRCE, performs a checked
seek within the frozen source, and restarts with a synchronous first packet.
A rewind does not erase the historical high-water mark. Forward ACKs during a
long replay are useful but do not forgive repeated rewind requests until that
high-water mark is passed. This avoids both infinite replay and premature
failure while retransmitting a large previously confirmed prefix. The same retry
correction applies to the synchronous path.

## Evidence and provenance

This is maintained source, not recovered original C. Original static REA evidence
shows separate transmitted/acknowledged offsets, ZCRCG/Q/W/E selection, sampling
and window waits in overlay29 `0x1e99a` (Evidence
`ev_b40ea3704cb45a1ce2e03f1fc0397c1e23609e7c063273478d8970d3306a310c`).
Negotiation is at `0x1e69c` (Evidence
`ev_b1e782339e069f5f1aab480798650b16c383a7610620aa19bf7be5725d59d951`).
The immutable overlay image digest is recorded in [ZMODEM_NATIVE.md](ZMODEM_NATIVE.md).
These retained observations were reused without executing an analysis image.
The current REA view endpoint rejects older `procedure_pseudo_code` records;
their complete saved Evidence/pseudocode remains the review source. No new native
runtime observation is claimed.

Protocol decisions follow Forsberg's [1988 description](https://raw.githubusercontent.com/FGasper/zmodemjs/master/reference/zmodem.txt),
sections 8.2, 9 and 11, with independent reference to the owned pinned Synchronet
source. The maintained finite window and conservative two-capability gate are
explicit policy choices, not claims about identical original scheduling.

The targeted reactive peer checks delayed, immediate, fragmented, duplicate,
backward and future ACKs; advertised capacities 1 through 65535; all capability
combinations; mid-frame and EOF recovery; repeated rewind, noise and cancellation;
source seek/read/close faults; and long verified-prefix replay. It checks window
and receiver-segment bounds separately. Literal schedules additionally exercise
16-bit DOS far callbacks and actual files, including a complete 128 KiB rewind.
They do not reuse product output as their expected wire oracle.

The passive capture auditor now permits asynchronous/cumulative Q ACKs after
subsequent data while rejecting ACK positions beyond observed source data.
W ACKs remain exact and ordered before continuation. This is an audit correction
required by the protocol, not a change to any server or captured stream.

## Checkpoint boundaries

The initial `f6db44d2` binary is retained separately from the corrected
`0ee0a194` runtime, followed by the adapter correction in `d791eb10`. The former exposed the long-prefix retry bug in host testing;
its real DOS transfers had exact files and successful peers but failed a
post-transfer keyboard fixture whose fixed 80-second wait expired before the
scheduled 120-second input. The fixture now derives that bound from the explicit
recipe. Its ENiGMA upload reached successful protocol completion but remained in
the upload-details form; that failed result is preserved. The earlier broad
regression was intentionally stopped when superseded by the retry fix, with its
partial results and logs retained. It is not presented as a completed suite.

The `0ee0a194` engine fix passed the broad regression and peer tests but the
paced linked test then exposed an adapter watchdog issue: after an 8192-byte
confirmed prefix, a rewind followed by ACKs every 100 modeled BIOS ticks still
failed at 600 replay ticks against a 540-tick inactivity budget. The adapter now
observes downward position changes without refreshing, then refreshes on each
strictly forward confirmed replay offset. Engine historical retry accounting
remains separate. The paired test executes the actual foreground owner, UART,
callback and deadline code, and observes native refresh calls; it does not call
the progress routine on the product's behalf. Each interval is under the budget
while the complete replay exceeds it.

The current DOS engine workspace is 9,312 bytes plus an eight-byte live context,
within the existing 10,240-byte policy. Near data/stack remains 65,088 and resident
code 63,038 bytes. CONFIG_CODE is 38,744 bytes. Parent retention is20,393 paragraphs
including PSP, 70 paragraphs above the published8 KiB-receive checkpoint.

[Validation ledger](validation/windowed-zmodem.json) records final runtime,
source/build identities, actual DOS and logged-in BBS results, retained earlier
attempts and limits. Historical [8 KiB results](ZEDZAP_BBS.md) retain their own
binary and costs. Physical RS232/WiFi modem timing, full line-loss coverage,
auto-download, persisted partial receive resume, adaptive original block sizing,
remaining protocols/UI/emulations, ASPECT and Host are still open. No whole
application gate F01–F16 closes here.


Validation commands use the pinned Nix shell:

```
./tools/build test-zmodem
./tools/dev --command python3 standalone/check_zmodem.py --sexyz /absolute/owned/helper
./tools/dev --command python3 standalone/check_zmodem_progress_live.py
./tools/build test-terminal test-zmodem-owners-live
```

The full peer matrix has 24 real stdio sessions, including corruption in a
continuing frame for both lrzsz and the stock Synchronet helper. The source-built
DOS component has 61 cases; the reactive window peer has 79 cases; the passive
wire auditor has 88 cases. The current linked suite has 78 cases, including the
paced replay, and the terminal regression runs 78 commands. Four actual DOS
sessions cover empty, one-byte and 65,797-byte files, CRC16/CRC32 receive and
control escaping on send. Four logged-in BBS workflows separately check both
directions on Synchronet/ENiGMA with exact bytes, official metadata and later
menu input/replies. The source-only snapshot reproduces 64 outputs.
