# Maintained ZMODEM sessions

`src/transfer/zmodem.c` implements standard ZMODEM batch send and receive over
the [maintained wire codec](ZMODEM_WIRE.md). It builds independently for 8086
DOS using the pinned Nix/Watcom toolchain. The production terminal integration is
documented separately in [live ZMODEM](LIVE_ZMODEM.md).
This is maintained source guided by the protocol and independently checked peers;
it is not recovered original C. [Native evidence](ZMODEM_NATIVE.md) separately
records original common/send/receive responsibilities and unresolved behavior.

## Session and file ownership

The caller supplies a 4,200-byte DOS workspace and a disjoint 40-byte callback
table. No static engine data, heap allocation or original binary is used. The
callbacks are far cdecl, allowing eventual engine placement in CONFIG_CODE while
transport/storage remain in resident CODE. Near arguments require DS=SS. The
DOS diagnostic checks the actual far callback ABI; future terminal segment
placement still requires its own linked validation.

Sending negotiates CRC16/CRC32, ESCCTL and finite receiver buffer capacity. It
offers safe DOS8.3 filenames with binary conversion requested, honors ZRPOS at
zero/interior/EOF offsets, answers bounded prefix/whole-file ZCRC requests and
rejects positions beyond the source. Source seek and exact read callbacks must
preserve a checked source size and propagate errors. Every packet uses ZCRCW
with a bounded ACK wait. ACK offsets must match the sent boundary; stale ACKs,
reposition requests and timeouts have finite retry paths. Recovery resets only
on a new verified high-water position. This sender currently waits after each
packet; original-style windowed sending and throughput tuning remain open.

Receiving advertises standard CRC32/full-duplex/overlap capability, accepts all
four subpacket endings and verifies ZDATA against the committed position.
Only CRC-accepted bytes reach the write callback. CRC failure, overflow,
timeout and wrong offsets request retransmission from committed bytes. Duplicate
offers for an active file reuse that stage rather than reopen it. Metadata size
is advisory; verified ZEOF position determines the actual length. Missing NULs,
unsafe filenames and malformed known metadata are rejected before file creation.
The existing metadata codec supplies bounded DOS8.3/device-name validation.

The receive commit callback must successfully close and install the file before
ZRINIT acknowledges ZEOF. It may skip an existing destination with ZSKIP; it may
not overwrite it implicitly. Many distinct skipped files are valid; repeated
same-name traffic remains retry-bounded. Earlier committed files survive a later
error. Recovery of an existing partial file from a previous session is not yet
implemented by the receiver adapter.

File callbacks own their handles durably outside the reusable engine workspace.
Failure cleanup aborts an active stage or source. A failed source close is
recorded as unresolved and is never called a second time. Receive abort must
preserve an ambiguous close; the DOS diagnostic composes the existing
`transfer_download_*` owner, which already enforces that rule. Cleanup status is
separate from the first session error. A sender's source closes after the peer
accepts ZEOF, because an intervening ZRPOS may require another read; a local
close failure therefore reports failure even if the peer already has the file.

ZFIN/OO completion, cancellation, optional attention-string receipt and challenge
echo are bounded. Remote command execution is not implemented. The engine gives
each wire read a three-second timeout and limits an event search to 8,192 input
bytes, with ten unsuccessful recovery attempts. These are component defaults;
terminal accepted-progress deadlines, profile-derived settings, serial servicing
and physical timing need explicit integration. The host stock-helper corruption
test exposed a one-second timeout racing Synchronet's one-second ZRPOS purge;
the three-second wait passes the same corruption workflow. The initial failed
attempt's stderr remains in ignored `build/zmodem-session/failures/`; its old
binary/wire stream was not retained, so it is not a replayable baseline.

## Validation

Run `./tools/build test-zmodem`. The target also exercises the wire codec.

- Eighty-four independent scripted host checks cover exact wire output,
  CRC16/CRC32, zero/odd/boundary lengths, every subpacket ending, metadata-size
  estimates, duplicate offers, CRC recovery, offset rejection, prefix CRC,
  timeout/cancel, file failures, cleanup retention, skipped files and lost OO.
- Eight pinned lrzsz 0.12.20 stdio transfers cover both directions, three files
  per session (empty, one byte and 65,797 bytes), CRC16 reception, control
  escaping and receiver window settings. Separate transfers inject one corrupt
  payload byte in each direction and verify exact final files after recovery.
  The package comes from the existing locked nixpkgs input, now in the default
  Nix shell. Nothing is installed through an unpinned system package manager.
- Forty-five source-built 8086 DOS workflows verify far callbacks, actual files
  across 64 KiB, receiver use of the checked exclusive stage/close/install owner,
  source seek/read failures, one physical source close after a close fault,
  foreign stage preservation, target skip and final-acknowledgment failure gates.
  The source side is a diagnostic stdio adapter; the terminal's checked batch
  source adapter and its seek extension remain required.
- A separate directory containing only maintained component C/headers produces
  a byte-identical DOS diagnostic. No original executable, installation or REA
  database is copied into that directory or read by the component build.

The optional stock-helper run uses:

```
./tools/dev --command python3 standalone/check_zmodem.py --sexyz /absolute/path/to/sexyz
```

The selected owned Synchronet helper is master `9de2c48d02`, independently
identified by binary hash in the report. Eight additional stdio transfers pass:
both directions, CRC16, control escaping and one corrupted byte in each direction.
These stock-helper sessions use the one-byte and 65,797-byte files only; empty
files were not exercised with this helper. They do not establish a logged-in
Synchronet BBS workflow. ENiGMA sessions and modem/UART tests remain open.

[Session/peer report](validation/zmodem-session.json) records source and peer
hashes, actual peer commands and retained consumed/delivered/output wire hashes.
[DOS report](validation/zmodem-dos.json) records case results and exact input and
output hashes. New peer runs use unique directories to preserve earlier evidence.

## Live integration and remaining work

The terminal now adds checked batch-source seek/skip, variable-length receive
storage, CONFIG_CODE placement, arena allocation and serviced UART/progress/UI
dispatch. Independent actual DOS lrzsz transfers pass; see `LIVE_ZMODEM.md` for
their scope and runtime identity. Stock Synchronet/ENiGMA logged-in BBS sessions,
broader live recovery/timing/cancel tests, auto-download, full settings, original
streaming/window behavior, persisted partial resume and hardware remain required.
All whole-application feature gates, including F08, remain open.
