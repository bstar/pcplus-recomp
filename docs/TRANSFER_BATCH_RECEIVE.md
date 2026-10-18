# Native batch receive metadata: static findings

This is a bounded static audit of retained REA exports and the SHA-verified original PCPlus2.01 executable, not a batch-transfer runtime pass. Ordinary source-built XMODEM tests do not establish YMODEM, TELINK, MODEM7 or streaming interoperability. No new REA session, BBS session, original application execution or media access was used for this audit.

## Evidence ledger

Original executable SHA256: `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`. Retained authoritative assembly is under ignored `analysis/pcplus-overlay-anchored-21/functions/`; addresses below are overlay21 CS offsets. REA's linear addresses add10000h. The saved analysis image is a synthetic analysis carrier, never a DOS execution input. Nix `tools/dev` was used to verify the original digest, map ranges using `analysis/pcplus-overlays/manifest.json`, hash the original bytes and inspect entry instructions with `ndisasm`.

| Unit | Assembly Evidence ID | Observed role |
| --- | --- | --- |
| d6a4 | `ev_5627e54d9f87691801201530328b3cd53d294b87c896a38d9c5b1d3c1e62851b` | Shared block/session receiver, block-zero dispatch and recursive file receive |
| d55c | `ev_0ba54a33f3c4ff6338d0f65779dcd76099a158b0d75d60707ce312e189ef4b51` | YMODEM/YMODEM-G outer batch loop |
| e4c2 | `ev_c2b69ad75556f5fe6bfea2c0808a1d804bf86dad8bdae0d38528c9b04da51fbd` | TELINK binary metadata decode |
| e52a | `ev_0576baf8c5c63af88658ca6518fa23d52f31a29574837742931ce982a848936a` | YMODEM filename and textual length decode |
| e878 | `ev_67cf7776b32cf82fe5ea8e9a3c5dd790a94b8efa982ac402562f9d97dbfce740` | MODEM7 filename exchange; **not** the YMODEM block-zero decoder |
| eb20 | `ev_fd88966c7c7c10ba889862a341a2b234db21c396f9f8e4033fa8802a794b6aa1` | Cancellation wire helper |

Supporting pseudocode evidence is secondary to assembly: d6a4 `ev_99808875a63518207d155d1f93353d27621e76eedf722eb97cdcee154a344775`; e52a `ev_b143a3d24179ee7efc2ff18bc9214595bd38912a3e2c42212a4c440f1eded67e`; e878 `ev_8c3ea8c7eea94dd7df991b25c9216ad7c25ba8a8384dc9dd7a0c3e9c54f8eeac`; eb20 `ev_387a654e2d2a833938e2e62cd3756cc523ca1eda68f28d4acff880018bb43b68`.

Selected original byte spans, end exclusive:

| CS range | Original file offset | Bytes | SHA256 |
| --- | --- | --- | --- |
| d55c..d656 |129036|250|`262dbbbe991d1b573ebc70ca4003fc4e7f4f4450b71cedf69179505cec38e623`|
| e4c2..e52a |132978|104|`3665fea53d28569b6e4ea7e32e711617fe9427a2019a7bcca684bc0f1d0dbaee`|
| e52a..e5d9 |133082|175|`1b29fae53e475509fcad5f2473a44ee510541e3e445f05498efa03401d65118b`|
| e878..eb20 |133928|680|`32163047c24d452b89e3d6a4cb777a26ed7fe770ba6aac2d365812f5d48a02b6`|
| eb20..eb44 |134608|36|`feacf0fa69795e72825b781ba932d5a530fffd6c8492b60219158a556694f041`|

Protocol names/IDs are corroborated by the previously recovered selector, not guessed from packet contents: ID3 TELINK, ID5 YMODEM, ID11 YMODEM-G, ID1 MODEM7. See [TRANSFER_BLOCKS.md](TRANSFER_BLOCKS.md). The selected-ID word is DS3996.

## Near ABI and shared state

`d6a4` takes one near filename pointer at BP+4, caller removes two bytes, returns AX0/1 failure/success; a NULL pointer requests metadata before opening a file. It saves BP, DI and SI and allocates58h stack bytes. `d55c`, `e52a`, `e878`, `eb20` take no explicit arguments; `e52a` saves BP/DI/SI and allocates80h bytes, `e878` saves BP/DI/SI and allocates72h. `e4c2` saves SI. These are near real-mode routines; stack buffers are passed to DS-based string/file services, requiring DS=SS. ES is modified by outer string-copy paths and is not a generally preserved register contract. Neither metadata helper returns a typed validity status.

| Original DS state | Contract proved at these sites |
| --- | --- |
|39c0|Near payload-buffer pointer; metadata helpers read from the buffer start|
|cb68|Received filename destination; YMODEM writes at most65 characters plus NUL; TELINK copies exactly16 bytes|
|9006/9008|Low/high expected-length words; zero means unknown-length in receiver commit logic|
|cb56|Batch-end flag, set1 by empty YMODEM filename|
|904a byte|Metadata-already-handled latch; batch outer owner clears it before each receiver entry|
|cd76/cd3a|TELINK packed two-byte fields from payload4..5 and6..7; later timestamp/UI consumers require their own contracts|
|cc9a/cc9c/cd32|Last accepted block, received number and received complement|
|cb5e/cd34|Current payload length128/1024, buffered byte count|
|8ffa/8ffc, cb2c/cb2e|Accepted-byte totals and secondary byte totals|
|cbaa|Native CRT FILE pointer, not a DOS handle|
|cdcc|Streaming mode; initialized for IDs10/11|
|1ea0|Download-path prefix used by legacy path helpers|
|2040|Controls native failed-file deletion policy|

BP-0eh in `d6a4` is the current metadata-frame flag, BP-14h retry count, DI is checksum/CRC selection, BP-58h.. is the local assembled file path. The true setjmp context at DS cd94 is documented in [TRANSFER_SESSION.md](TRANSFER_SESSION.md).

## Block-zero validation and ownership

`dc6a..dce7` selects128 bytes for SOH01/SYN16 and1024 for STX02. It reads number/complement; their word sum must be00ff except in streaming mode. Only when last accepted block and received block are both zero does protocol3/5/11 set the metadata-frame flag. The ordinary expected-block gate is bypassed for metadata, but payload/trailer reception still occurs.

The byte loop at d90e stores each byte before checking a negative timed-read result. The original short-frame behavior described in TRANSFER_RECEIVE remains applicable. CRC/checksum comparisons at d9a6..da31 govern entry into the metadata application branch. TELINK metadata uses the byte-sum path even when DI selected CRC: d934 checks protocol3, d99f masks the sum to8 bits, and da01..da0e allows a matching first trailer word to pass. This is an observed special case, not a runtime-established modern peer contract; DI may still cause two timed trailer reads before that fallback.

At da3a the metadata latch is checked/set. Protocol3 flushes queued input, ACKs and calls e4c2, then resumes the current receiver. The YMODEM-family path at da84 flushes, calls efb0 (which zeros **both expected length and byte/timestamp totals**), then e52a. Empty filename returns success and, except protocol11, ACKs it. Nonempty filename resets retries, flushes, ACKs except protocol11, performs the legacy existence check, then recursively invokes `d6a4(cb68)` to receive/open the actual file. That inner call initializes ordinary per-file state and owns the file stream. The outer receiver returns its AX result immediately.

`d55c` supplies the batch loop: flush; clear904a; call `d6a4(NULL)`; update UI; repeat while receiver success and cb56 remains zero. cb56 ends the batch. Failure invokes eb20 and may delete the last path when2040 is set. A source-built batch integration therefore needs an outer session owner **and** per-file storage ownership; it cannot reuse the ordinary one-file checkpoint by merely enabling the block-zero branch.

## YMODEM metadata decoder e52a

Observed algorithm:

1. Copy the buffer filename into cb68 until NUL or65 characters; terminate destination with NUL. The second copy loop has the same65-character limit. A long unterminated filename is truncated, not rejected; SI then advances one position as though a delimiter had been found.
2. If payload byte0 is NUL, set cb56=1 and return. No filename or length syntax validation is performed first.
3. Otherwise, if the byte after the assumed filename delimiter is NUL, return without assigning length. The real da84 caller already zeroed9006/9008 using efb0, so the live native path retains **unknown length zero**, not a previous file's length. Other callers would need that initialization contract explicitly.
4. Copy the length token into an80h-byte stack array until space/NUL. After each copy, increment the absolute payload index and return immediately if it exceeds120. This bounds the examined token portion but supplies no explicit failure status. It can leave the caller's zero length unchanged.
5. NUL-terminate the token, call resident9b32 (a verified near JMP to resident a7ce, the signed decimal parser), store DX:AX in9008:9006, then call ee10(0), a size/progress UI computation.

No octal modification time, mode, serial number or remaining YMODEM header fields are applied by this helper: parsing ends at the first size-token separator. There is no explicit decimal digit check, full-token consumption check, overflow check or negative-size rejection at this caller. The retained a7ce decimal helper (`ev_2f19af5bd866e32c598d443f1ec38c5d9da88d4357acd72af84f9c66e27830ff`) accepts leading spaces/tabs, optional sign and numeric prefix, with32-bit arithmetic; The original resident bytes at fileoffset AD32h (CS9b32) are `e9 99 0c`, independently decoded as `jmp a7ce`; the thunk binding is therefore corroborated directly against the verified original. This establishes permissive signed numeric-prefix parsing, not a strict unsigned metadata length validator.

## TELINK metadata decoder e4c2

| Payload offsets | Observed decode |
| --- | --- |
|0..3|Unsigned bit-pattern length, little endian, reconstructed into9006/9008 by four shift/add steps|
|4..5|Little-endian word into cd76|
|6..7|Little-endian word into cd3a|
|8..23|Exactly16 bytes copied into cb68 using resident9888|

It calls ee10(0) and returns without an explicit validation result. It does not force a terminating NUL in the16-byte filename field, reject embedded path components/devices, or reject oversized lengths. The byte order is proved by instructions; naming fields4/6 as DOS date/time rather than merely packed timestamp words requires the consuming timestamp contract. No filename from cb68 is opened in this e4c2 branch: TELINK's enclosing native route already supplied a file path. This distinction matters when designing a maintained batch-storage selector.

## MODEM7 e878 and cancellation eb20

The e878 owner is a separate character filename exchange. It flushes then sends NAK, waits for ACK/EOT/CAN, and limits ordinary handshake attempts to15; bytes greater than127 are discarded by an inner timed-read loop. It ACKs each filename character, accumulates an8-bit sum, receives up to13 characters, terminates the local buffer and requires SUB1a to complete the name. It adds SUB to the sum, sends that checksum and requires ACK. It reconstructs a local filename from the first8 padded characters, a dot string and the extension, probes existence, clears904a and calls d6a4(filename). No original file length is conveyed here. The inner discard loop and original timed-callback units must not be described as bounded wall-clock safety without a maintained watchdog.

`eb20` emits five CAN18 bytes, each followed by delay6b72(100), then five backspace08 bytes. It is a wire cancellation helper only; it neither closes a FILE nor resets storage ownership and returns no status. Cleanup and failure propagation belong to the caller.

## File length, paths and safety gaps

Native finalization is length-aware but not a safe transactional receiver:

- Zero expected length takes the unknown-size tail and writes all buffered padding. Therefore this native representation cannot distinguish a genuine zero-byte file from omitted/invalid length. A maintained plan needs a separate `has_length` flag.
- Nonzero length computes `expected % current_block_size`; a nonzero remainder writes `buffer_used - block_size + remainder`, while a zero remainder writes the full buffered count. Neither final-tail branch checks fwrite/fclose results before success. See [TRANSFER_FILES.md](TRANSFER_FILES.md).
- The periodic-flush boundary compares expected length to received totals before deciding whether to defer the final buffer. Its high-word compare uses signed jumps. No metadata gate proves that declared size agrees with the accepted stream, that a short sender actually delivered the declared size, or that malicious sizes cannot produce an invalid tail count. Exact expected/accepted byte accounting must be independently validated before maintained install.
- Resident3717 (`ev_75d5920f8f93bfe388624b671cc1eb8c84c750b2b39fbc094be3d1d91554ed1c`) checks whether the filename contains backslash or colon. If either exists, the native caller omits the configured download prefix. It is **not** a safe-relative-path validator.
- Resident369a (`ev_e8fae2c3f6b8e2554866cecf62b3acba4580e964334f21b49a7246932018b748`) concatenates that prefix/name into a66-byte local and calls3673 to probe existence by opening/closing the file. The metadata caller changes only the first name byte to `$` on an existing path and reports status14; it does not establish an exclusive target or recheck the resulting name. Prefix concatenation and subsequent local-path copies are not bounded by combined length.
- Filename case, DOS devices, wildcards, traversal, alias collisions, ambiguous close, stage ownership and preserve-existing-target guarantees are absent from the demonstrated metadata helpers. A safe source-built integration must retain the maintained read/write/close/install backend rather than expose raw received names to fopen or deletion.

## Minimal integration dependency ledger

| Needed component | Existing source / unresolved work |
| --- | --- |
|Frame payload, integrity, sequence, cancellation context|Recovered transfer_receive + transfer_session; ordinary maintained live path exists, batch application checkpoint remains explicit|
|Metadata decode|e4c2/e52a are statically identified here; not newly assembled or tested by this audit|
|Outer batch owner|Recover d55c lifecycle and recursive d6a4 metadata/file handoff, or document a maintained bounded state machine; MODEM7 e878 is a separate scope|
|Decimal length parser|9b32→a7ce binding verified; recover/link exact parser if preserving native semantics, or use an explicitly maintained strict uint32 parser with tests|
|Per-file expected-size state|Relocate9006/9008, cb56,904a, filename arena, cd76/cd3a; separate unknown/zero/known length, reset per header|
|Remote-name admission|Maintained bounded DOS83 basename policy, explicit target directory, device/path/alias rejection, reserved stage paths and exclusive install; do not link369a as validation|
|Storage callbacks|Existing maintained stage backend plus native FILE bridge; begin/seal/error gate/install per file; never install on native AX1 alone|
|Length enforcement|Bound expected size, accepted bytes and final padding independently; reject truncation/overflow and prevent unchecked native tail count|
|Session control|Preserve foreground cancel, carrier checks, bounded deadlines, binary-safe UART and per-file/batch cleanup; validate YMODEM-G separately because it intentionally omits ACKs|
|UI/date-time|ee10 progress arithmetic, e2d2/e2f2/e30a/f01c lifecycle, native timestamp consumers remain dependencies unless explicitly replaced by maintained policy|

Answered statically: header routing, metadata layout, near ABI/state, empty-batch handling, cancellation bytes, path/existence behavior and major storage/length gaps. Partially answered: full packed timestamp interpretation and broader TELINK outer lifecycle. The9b32→a7ce numeric-helper thunk identity is directly verified. Unresolved: source-built batch integration and any genuine YMODEM/TELINK/MODEM7 runtime interoperability. No new passing runtime claim follows from this document.
