# Original transfer sender session

`reconstruction/transfer_send/` recovers the selected PCPlus2.01 sender session,
its double-CAN handler, and the native nonlocal return mechanism. The source-only
SEND.EXE diagnostic builds and runs without original binaries or a REA database.
It is an independently linkable recovery with declared external services, not a
live upload command or a complete transfer application.

The selected original SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
`provenance.json` records exact source ranges, file offsets, hashes, DS aliases,
external boundaries and saved REA evidence IDs. Overlay21 assembly evidence is
`ev_c9beb57caf28b9f7acfdde54f6d78d941a7bcac553e5126c5277ef8f25aee23b`.
These static exports used an explicitly synthetic overlay entry image; genuine
original replay separately verifies behavior against the SHA-identified artifact.
No synthetic analysis EXE was executed.

| Unit | Original range | Exact bytes |
| --- | --- | --- |
| `session.asm` | overlay21 CSde58..e2d2 | 1146 |
| `cancel.asm` | overlay21 CSf050..f070 | 32 |
| `checkpoint.asm` | resident CS9048..9086 | 62 |

All1240 bytes assemble exactly in flat mode. OMF mode replaces original addresses
with named state/services, preserving instructions and legacy behavior. The
existing real CRC update/finish/buffer routines and generated polynomial table
are linked from `transfer_blocks`; no duplicate framing implementation substitutes
for the sender's header, payload, checksum or CRC instruction paths.

## Entry and dependencies

`transfer_send_session(filename)` is near C caller-cleanup two bytes, DS=SS.
AX1 means completed EOT/ACK; AX0 means failure for the ordinary block path.
Delegated protocols return their own result. BP/SI/DI and the caller's stack are
restored. ES is volatile. The original routine uses an80-byte stack frame and
unchecked directory-prefix/name concatenation; it is not a bounded public path
API. Maintained integration must validate combined path length before invoking
it or use a separately documented bounded controller.

`send_checkpoint(buffer)` and `send_unwind(buffer, value)` are exact setjmp-like
and longjmp-like near helpers, both caller-cleanup. The buffer is ten bytes:
BP, DI, SI, SP and saved return IP. Checkpoint returns0 initially. Unwind restores
the saved frame and returns the requested AX there, translating0 to1. No UART,
filesystem or application event dispatcher is required for this mechanism.

The full DS mapping is in provenance. Principal words are protocol3996,
buffer pointer39c0, total padded bytes8ffa/8ffc, declared size9006/9008,
session bytescb2c/cb2e, block sizecb5e, FILE pointercbaa,
block numbercc9a, buffer offsetcd34, counted blockscd80, errorscd8a,
checkpointcd94 and streaming flagcdcc. They are original state aliases, not a new
on-disk format. The word block number increments normally; the wire uses its
low byte and low-byte complement.

External services remain explicit: session reset, UI/progress, FILE open/read/
close, UART transmit/receive/timeouts/flush, local Escape/carrier checks and
alternate protocol/metadata handlers. The diagnostic supplies clearly labeled
memory fixtures for these boundaries. Only recovered session/cancel/unwind/CRC
code is claimed as original instruction execution. In particular it does not
replace unknown production services with no-op implementations for live use.

## Negotiation and deadlines

The session calls native resetd656 before the recovered body. Saved reset
assembly establishes streaming only for protocol10/11, clears session counters
and FILE state, selects bufferDS9062 and loads a baud-indexed timing value.
That reset remains an external dependency in this module. Tests explicitly
initialize synthetic equivalent state; the complete application startup is not
being replayed.

The negotiation loop has fifteen outer attempts. Each calls the UART timed-byte
reader with argument1 up to ten times while it returns a negative timeout.
Timeout-only negotiation therefore makes150 such calls before unwinding with
value1. Received unrelated bytes consume an outer attempt immediately. The
recognized bytes are:

| Peer byte | Branch |
| --- | --- |
| NAK15h | Checksum trailer |
| `C`43h or `G`47h | CRC trailer |
| `U`55h | Separate U-protocol delegate |
| `W`57h | Separate W-protocol delegate |

`G` selects CRC here; it does not set the streaming flag. Protocol13 bypasses
ordinary negotiation through another delegate. Protocol3 performs an external
metadata exchange; protocols5/11 perform another and require a subsequent C/G.
Their metadata and alternate wire protocols are not recovered by this unit.

The actual UART timed-byte routine aad9 counts changes from its DOS-seconds
clock helper. Arguments1 and10 are clock-transition counts, not calibrated
millisecond delays or guaranteed full wall-clock seconds. A boundary transition
can occur shortly after entry. These deadlines are distinct from the36 BIOS
tick-change header reader used by the double-CAN helper.

## Blocks, retries and EOT

Ordinary sending begins at block1 and128-byte blocks. Protocol2, protocol5 or
an already-set streaming flag permits1024-byte blocks when the declared file
size is at least1024. The sender reads up to10240 bytes after filling the whole
buffer with1ah, so the final block is padded. It sends SOH1 or STX2, block byte,
complement, payload and checksum/CRC. CRC is high byte first. Its signed-byte
checksum arithmetic still yields the ordinary modulo256 byte sum.

Without streaming, every block waits with timed-byte argument10. Only ACK06
accepts the attempt. A non-ACK response passes through the CAN handler, increments
error count and requests status9. There are fifteen attempts per block. Streaming
bypasses per-block ACK waits; if the queued-count word is nonzero, it consumes
one queued byte and checks it for cancellation.

After a counted block, offsets and byte totals advance by padded block size.
Except protocol4, the sender changes subsequent blocks to128 when remaining
declared bytes are below897. Empty input sends no data blocks and proceeds to
EOT. After closing the input FILE, EOT04 is sent up to ten times, each followed
by a timed-byte read with argument10. Only ACK06 completes successfully.

Local Escape posts unwind value7; failed carrier check posts15. The exact CAN
helper examines a first CAN18 with a separate header-byte read and posts7 only
for a second CAN18. A lone CAN consumes that next byte even when it is unrelated.
The session maps unwind1 to status0,15 to status15 and other values to status11,
closes the FILE and returns0. No direct CAN transmission appears in this recovered
session/cancel code. Caller-level cleanup and other protocol branches remain
separate dependencies.

Preserved historical edges are explicit:

- After fifteen failed attempts, the code still increments block and padded-byte
  counters before closing and returning failure. These counters do not establish
  that the peer accepted that block. No EOT follows that exhausted block.
- Double-CAN during EOT unwinds to a cleanup path which closes the already-closed
  FILE again. With the initial pre-data close, the diagnostic records three
  close calls. This is preserved evidence, not a safe maintained close policy.
- The second binary FILE open is not checked before the read loop. Prefix/name
  concatenation and fixed10240-byte buffer assumptions are unchecked originals.

A maintained live controller should retain negotiated wire compatibility while
bounding path/buffer IO, closing once, using accepted-byte counters and servicing
cancellation/flow during waits. Such changes must have separate tests and must
not silently alter this exact mode.

## Verification

```sh
./tools/dev --command python standalone/build_transfer_send.py
./tools/dev --command python standalone/check_transfer_send.py
./tools/dev --command python standalone/test_transfer_send_dos.py
# Optional ignored, SHA-verified original; bounded CPU replay only:
./tools/dev --command python standalone/check_transfer_send.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

The diagnostic SHA256 is
`437f069804ac8b6eeff6307944286ed7c4db3d8f4761b2b90873c6ab52014a75`.
93 linked cases pass and93 genuine-original comparisons agree, including complete
wire bytes, return/status values, close counts, timed-read counts and counters.
Cases span checksum/C/G, empty/partial/128/1024/multiple blocks, padding and size
switching, retransmission, exhausted negotiation/block/EOT, local/carrier/CAN
unwind, alternate delegates and streaming with control-byte polling. Original
comparisons use the same declared synthetic external boundaries; they do not
establish real UART timing or real FILE error behavior.

The actual DOS8086 self-check executes recovered sender/CRC/unwind code with
memory fixtures and checks a padded checksum frame, ACK, EOT/ACK and counters.
It has all serial ports disabled. No real file transfer, physical modem, remote
BBS upload, batch metadata, upload menu or complete PCPlus UI is claimed.
`recover.py` is an explicit analyst-only regeneration tool requiring the ignored
SHA-verified original; normal build/check/DOS paths never invoke it.

## Live ordinary sender integration

The interactive terminal now links this session and cancel code alongside the
receiver, reusing its exact CRC/checkpoint helpers and near arena. Maintained
Alt-S, read-only DOS ownership and serviced UART/UI callbacks replace the
diagnostic fixtures for the live path. Independent DWORD ACKed-byte progress
gates successful completion; native attempted-block counters stay unchanged.
Protocol abort closes a partly prefetched source without inventing a disk error.
The exact diagnostic and its baseline limitations above remain separate. See
[LIVE_UPLOAD.md](LIVE_UPLOAD.md) and [UPLOAD_SOURCE.md](UPLOAD_SOURCE.md) for
current runtime evidence, safety differences and remaining protocol scope.
