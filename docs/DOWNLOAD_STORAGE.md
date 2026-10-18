# Maintained streaming download storage

`src/transfer/download_file.c` provides the DOS file boundary needed to connect
recovered transfer sessions to real files. It supports streaming binary output
beyond64KiB without a full-file near buffer. It creates a caller-named stage
exclusively, checks every write and close, then renames without replacing an
existing destination. This is maintained policy, separate from the exact native
CRT in [TRANSFER_FILES.md](TRANSFER_FILES.md).

The native periodic receiver writes one large `fwrite` element and rejects a
partial element. Its final EOT tails ignore final write and close returns. The
maintained storage boundary prevents such failures from installing a download.
This does not by itself fix the native wire ACK-before-final-file-commit order.
A live owner must treat protocol completion and successful local installation
as separate evidence and implement its chosen EOT policy explicitly.

## Ownership and ABI

The near-C ABI requires DS=SS and16-bit unsigned/32-bit unsigned long. The
148-byte `transfer_download_result` layout is compile-time asserted. One
foreground download owns its stage and handle. The application may read the
snapshot but must not alter it. No DOS file operation runs in an ISR.

`transfer_download_begin(target,stage)` validates explicit ASCII8.3 DOS paths
of at most63 bytes, normalizes case/slashes, and requires the same lexical
parent. Nested, rooted, absolute and drive-relative paths are supported.
Devices, dot/dotdot, wildcards and target/stage aliases are rejected. The target
must be absent. Stage creation uses DOS exclusive create; a preexisting stage
never becomes owned and is never removed by an abort. Concurrent target creation
is also protected by DOS rename's no-overwrite contract. This is a new-download
policy; an overwrite dialog/replacement policy remains application work.

`transfer_download_append(data,count)` accepts a nonwrapping near span up to
32768 bytes, disjoint from owned metadata. It records actual bytes written,
including a partial prefix on a DOS error. A positive or zero short write is a
failure even if DOS reports success. A write failure poisons installation.
Count0 performs no DOS call: DOS40h with CX0 can truncate/extend a file and must
not be used for an empty append. Invalid public append arguments leave the
active file unchanged so the caller can correct them. Byte-total overflow is
rejected before IO.

`transfer_download_seal()` closes once and retains the owned stage. It does
not install the target, which lets a recovered `fclose` callback close canceled
transfers without accidentally publishing them. `transfer_download_finish()`
requires successful sealing, then installs with no-overwrite rename. A rename
failure retains a closed complete stage for explicit retry or abort. The
snapshot preserves the first failure even if an explicit later retry succeeds;
use the current operation's return and `state` to distinguish recovery.

`transfer_download_abort()` closes once, then removes only the owned stage.
First failure, close failure and cleanup failure have separate fields. A close
failure leaves handle ownership uncertain. The backend will neither retry a
possibly recycled handle nor remove its stage; further transfer attempts return
busy/recovery until the application/operator resolves the situation outside
this API. There is no silent reset of unresolved ownership. A deletion failure
can be retried explicitly without repeating a successful close.

| Result state | Meaning |
| --- | --- |
| IDLE | No file acquired |
| OPEN | Owned stage open for exact appends |
| CLOSED | Sealed stage retained; explicit install or discard |
| INSTALLED | Destination installed; abort cannot remove it |
| ABORTED | Owned partial removed; repeated abort is safe |
| BROKEN | Write/IO failure; inspect ownership/recovery flags |
| UNCERTAIN | Close failure; automatic handle reuse/delete forbidden |

The API supports a single DOS foreground owner, not threads, concurrent writers
or authenticated file identity after external stage replacement. It does not
promise crash-atomic FAT updates, physical-media durability, timestamps or file
attributes. Native per-protocol exact lengths, ordinary XMODEM padding, batch
metadata/names, upload storage and restart recovery are separate responsibilities.

## Native receiver callback bridge

`native_file_bridge.c` supplies cdecl open/write/close callbacks for the recovered
receiver's opaque `FILE*` call sites. Prepare the stage first, pass its normalized
name and binary mode `wb`, and use an empty native download prefix with bounded
filename validation before entering native code. The adapter returns token1,
which is **not** a real CRT FILE object and must never enter native CRT code.
Only these three callbacks consume it.

The write bridge converts `(pointer,size,count,token)` to a bounded exact append
and returns complete-element count or0. Nonzero invalid writes poison the stage
as well as returning failure, so an original EOT tail ignoring `fwrite` cannot
hide a failed local write. A zero-element call remains a harmless no-op. The
close bridge seals without installing and handles repeated successful closes
without touching a recycled DOS handle.

After the native owner returns, the maintained owner must check both native
success and storage failure state, then explicitly finish. On native failure or
cancellation, abort. Native return1 or an earlier ACK alone cannot authorize
installation. This adapter contract is ready for composition; it is not a claim
that the terminal application already has live download UI/UART sessions.

## Verification

```sh
./tools/build download-file test-download-file
```

The real DOSBox-X8086 test installs65,673 exact binary bytes (including NUL,
1Ah and all high-bit values), empty files, nested absolute and drive-relative
paths. It verifies exclusive creation, actual DOS no-overwrite rename, competing
target preservation, cancellation and removal only of owned stage names.
The second compiled DOS executable uses a deterministic stateful filesystem
boundary to inject short/zero/error writes, close ambiguity, rename races,
cleanup failures, 32-bit counter overflow, invalid near spans and ignored native
callback errors. The implementation executes in DOS in both tests; the fault
kernel is explicitly modeled, not a physical disk-failure test.

Exact results and executable hashes are recorded in
`docs/validation/download-storage.json`. Original executables/private data are
not build or test inputs.

## One native owner with actual DOS storage

`./tools/build test-transfer-storage` composes the actual receiver entry once
with its native handshake, CRC/checksum engine, frame/context lifetime, ACK/NAK,
retry and periodic/final file controllers. The scheduled peer releases a future
frame only after the appropriate transmitted control byte; it does not put
future blocks into a flushable buffer prematurely. File callbacks use the real
DOS backend and checked native bridge above.

Six actual DOS modes verify normal11x1024 output,79x128+1024 at the mixed-size
flush boundary, an injected positive short final write, an injected close error,
real double-CAN nonlocal cancellation and timeout exhaustion. Normal output is
byte-compared independently. Native success after ignored EOT errors cannot
install a failed stage. A close error retains the exact recovery file. Native
cancellation seals its partial and the outer owner discards it; native timeout
can leave its FILE open, so the outer owner explicitly closes/discards it.

The composed receive arena reserves11264 bytes: the native10240-byte threshold
is tested after copying a full block, and a legal10112+1024 mixed case must fit.
The earlier10240-byte diagnostic arena corrupted state on this case; the failure
and correction are retained in the session evidence. This is a diagnostic arena
correction, not proof of the original application's allocated capacity.

The controlled UART/time/UI remain fixtures; serial ports are disabled in this
DOS storage test. The separate real-UART diagnostic does not itself establish a
combined modem transfer. Terminal integration and an EOT policy that acknowledges
only the intended local completion state remain required. Current results are in
`docs/validation/transfer-storage.json`.
