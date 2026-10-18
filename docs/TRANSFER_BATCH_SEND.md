# Original batch-send orchestration

This is a static recovery ledger for PCPlus 2.01, not an implemented live
YMODEM command. The maintained terminal currently links the ordinary native
single-file sender; the batch owner, pathname enumeration, metadata and empty
batch terminator below remain separate recovery work. No BBS sessions, disk
media or private configuration were accessed for this investigation.

The original EXE SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Saved REA exports are in
`analysis/pcplus-overlay-anchored-21/functions/0x1*.asm` and their adjacent
`-asm.json` records. Their analysis-input identity is the synthetic overlay
image; it is not an executable product or the original EXE identity. Original
bytes were independently read only after checking the EXE digest, using the
existing overlay manifest. No new REA session was opened. Nix supplied the
Python/NASM tools. Addresses below are original CS offsets; REA addresses add
`10000h`.

## Protocol distinctions and ownership

The selector and original data independently establish IDs 5 = YMODEM,
11 = YMODEM-G and 13 = SEALINK. DS:3996 is the selected protocol. The existing
[selector ledger](TRANSFER_BLOCKS.md) records the actual callback routes.
All three selected send routes enter overlay21:d394 through the resident
stub, but they do not share all wire behavior. The metadata primitives are now
source-built and tested separately; see [TRANSFER_METADATA.md](TRANSFER_METADATA.md).

| Stage | ID 5 | ID 11 | ID 13 |
| --- | --- | --- | --- |
| Per-file engine | de58 | de58 | de58 immediately delegates through resident d08f |
| Filename/length block | e762 | e762 | Separate overlay25:f0e0 implementation |
| Header ACK | Required; up to three transmissions | Not read | Unresolved delegated implementation |
| Post-header readiness | Must read `C` or `G` | Must read `C` or `G` | Unresolved delegated implementation |
| Data ACK | Required | Skipped because d656 sets CDCC=1 | Unresolved delegated implementation |
| Final empty batch header | efcc | efcc, skips final ACK read | d08f with pointer to the empty string at DS:77ef |

The original YMODEM-G path is not simply “no reads”: it still performs the
initial receiver negotiation, post-header readiness read, control-byte checks
and per-file EOT/ACK exchange. Nor does ID 5 reject a `G` readiness byte: de58
accepts either `C` or `G`; streaming is selected from protocol state, not
changed merely because that byte was `G`.

The raw resident d08f bytes encode an overlay-manager call with inline overlay
ID25 and a far jump to offset f0e0. Likewise the negotiated `U`55h and `W`57h branches
in de58 call resident d083 (overlay27:f2b1) and d0a7 (overlay23:f100).
These are explicit alternate engines, not successful no-op services. Their
complete contracts are outside this ledger.

## Batch owner d394..d55a

`d394` is a near, caller-clean routine with a near string pointer at `[BP+4]`.
It saves BP, SI and DI; ES becomes DS during string copying and is not restored.
It has no stable boolean return contract: final UI cleanup overwrites AX. A
maintained C wrapper must return its own explicit status rather than treating
this owner's final AX as sender success.

With a null pointer, it opens the filename prompt, validates a DOS search
result, and reprompts when no match exists. Escape/empty input leaves before
transfer setup. With a supplied pointer, it copies the complete string to both
CE6A and CE3E without bounds checks, invokes the initial search and proceeds
without checking that search's return. A maintained owner must validate lengths
and successful enumeration explicitly.

Actual iteration at d4ef..d50f is:

1. Update the transfer window, then call `de58(CE3E)`; retain AX in SI.
2. Call `5b68(0)` even if that file send returned zero.
3. Repeat only when FindNext succeeded **and** SI was nonzero.
4. On a nonzero last send, emit the protocol-specific batch terminator, then
   call e30a (completed). On zero, call e2f2 (aborted) and eb20 (wire cancel).

Consequently an enumeration failure after a successful file is treated as the
end of the batch; this owner does not distinguish “no more files” from other
DOS enumeration errors. It also does not promote failure of the empty batch
terminator into an aborted result: efcc has no checked result.

The enumeration dependency is actual DOS, not an inferred glob library:
resident5b54 sets DTA to DS:CEB4 with INT21/AH=1Ah and selects FindFirst4Eh;
5b68 selects FindNext4Fh. Both invoke common5b71, which returns AX=0 on DOS
carry or AX=1 after formatting the result. With the zero attribute argument
used here it copies the DTA filename at CED2 to CE3E. CE6A is the search pattern;
CEEA is the directory prefix prepended by de58. The owner uses3ed9 to prepare
that path state. FindNext relies on the still-valid original DTA/search state.
Complete path splitting, DTA restoration/interaction with other DOS callers,
search ordering and exceptional file attributes still need recovery.

## Filename block e762..e877

This is an independently bounded 278-byte candidate for the next native unit.
It takes a caller-clean near filename pointer and returns AX=1 or AX=0, saving
BP/SI/DI. Its 128-byte payload is zeroed on the stack; DS=SS is required by the
near pointers passed to CRC and string helpers. ES is set to SS and not restored.

The payload is the basename returned by3ea4, a NUL, the decimal representation
of the actual file-size DWORD at9006/9008, and remaining zero bytes. Conversion
calls9ae8 with radix10. It includes no observed timestamp/mode/remaining-files
fields. The initial file open and `ee10(1)` precede this header; ee10 obtains
size through9580 using the FILE's descriptor. The initial file is then closed
and later reopened in binary mode for data. File stability between those
opens is not guaranteed by the original.

It emits `01 00 ff`, exactly128 payload bytes, and CRC high then low via the
already recovered5c77 primitive. `40aa` is the resident zero-byte transmitter,
not a separate CRC or ACK helper. Local cancel or carrier loss invokes the
real longjmp9065(CD94,7/15). Before each header it invokes f03e: calibrated
50-unit delay, input flush, and repeat until RX count8e20 is zero. That flush
loop has no original deadline and may discard early peer input.

For ID5, non-ACK after timed read `aad9(10)` increments a local attempt count;
three header transmissions fail with AX=0. Other unexpected response bytes are
not passed to the double-CAN checker within this header function. ID11 returns
success immediately after sending its first header. In both cases de58 then
reads `aad9(10)` and requires `C`43h or `G`47h before sending data. These numeric
wait arguments are native service units; this document does not redefine them
as BIOS ticks or seconds.

The basename and decimal string copies have no checked 128-byte limit. A
maintained wrapper must stage and validate the whole payload before UART I/O.

## End-of-batch efcc..f01a

This 79-byte function first calls `aad9(15)` and ignores the returned byte.
It then calls f03e, sends `01 00 ff`, and transmits130 zero bytes:128-byte empty
filename payload followed by its two zero CRC bytes. For ID11 it returns
without reading an ACK. Otherwise it calls `aad9(15)` and compares against ACK.

There is a concrete original retry defect. At efef..eff2 both SI and DI become
`0082h`. SI counts down the130 zeros, while DI remains `0082h`. On non-ACK,
f00d computes AX=DI+1 (`0083h`), compares it with3, and therefore never takes
the apparent retry branch. It sends exactly one empty block, whether ACKed or
not. This follows the actual instructions; the pseudocode alone hides the
irrelevant comparison. No stable success/failure AX is returned, and d394
marks completion regardless. Preserve these bytes in an exact recovery, but
use an independently tested bounded retry/result contract in live policy.

Per-file EOT is separate: de58:e2a0 sends04h and waits for ACK, up to ten
attempts; unexpected controls pass through f050. Empty batch block0 belongs
after the final successful file, not after every file and not in place of EOT.

## Abort, status and separate filename exchange

- e2d2 selects the protocol-name pointer through2d82 into2dee, opens the
  transfer window and invokes3226. It provides UI setup, not negotiation.
- e2f2 displays `ABORTED:` and sets D124=1. e30a displays `COMPLETED:` and sets
  D124=0. Neither is a file transaction/ACK boundary.
- eb20 sends CAN18h five times, with calibrated6b72(100) delays, then sends
  five BS08h bytes. This is the owner's abort burst.
- de58 returns AX=1 after per-file success/EOT ACK, zero on ordinary failure.
  Its checkpoint maps local/remote cancellation7 to displayed status11;
  carrier-loss unwind15 retains status15; unwind1 maps status0. Open failure
  reports13, metadata failure10, read failure4. File close return values are
  ignored. f050 observes CAN followed by another CAN via5ca0 and longjmps7.
  Existing native sender tests cover this routine; batch ownership is not
  thereby tested.
- eb44 and ebb2 are **not** the YMODEM block0 path. ec48 calls them before
  de58 in a distinct legacy filename exchange. eb44 starts with11 spaces in
  CB68, copies the stem to its start and extension to CB70 (8+3 layout), with
  no length checks. ebb2 waits for NAK, sends ACK, then sends11 filename bytes,
  requiring an ACK after each. It sends SUB1Ah and requires the returned byte
  to equal the modulo256 sum of those11 bytes plus1Ah; success sends ACK and
  returns1. Timeout/local-cancel/non-ACK returns0. The initial retry counter
  uses postincrement comparison against40 (up to41 reads), not an unbounded
  wait. These helpers must remain distinct from CRC YMODEM metadata.

## Exact evidence and next units

All rows below cite retained REA **assembly** Evidence IDs. Coverage is static;
no new original-code runtime replay was performed for this documentation task.

| Original entry | Evidence ID |
| --- | --- |
| d394 | `ev_ad2b94688be53fc35550382aa1f7a0b7ef8e08e2795947e912b7b3d7fd7565e3` |
| de58 | `ev_c9beb57caf28b9f7acfdde54f6d78d941a7bcac553e5126c5277ef8f25aee23b` |
| e2d2 | `ev_380ba823ff617585517cac29287d9e0b177d5724e43aba56c6530aec1f451b5d` |
| e2f2 | `ev_d80ad96f61ccf584de29bf6ed3b79ddc97509ded84a5d29356bfd05d6844e5bb` |
| e30a | `ev_cce276cb37dc4d8a3a9dbbe5429f71317db50b0a35ac4249e124059131bc720b` |
| e762 | `ev_b93c508ad1284101b3fb69a7f0a1741ee5f721a4582d82d4558ac28fc1d51e57` |
| eb20 | `ev_fd88966c7c7c10ba889862a341a2b234db21c396f9f8e4033fa8802a794b6aa1` |
| eb44 | `ev_7f36bf7377888a6c1afcc5cbc0add19163b77dfb70a071b518d9c693ff7c7d0f` |
| ebb2 | `ev_329057f6c7bb0c4de663546e22ff104f1d1f1850b5633d08b4f0d586315ace92` |
| efcc | `ev_672de51b8e654cd30f4affaec0ecad57e1026ad091cb0a733e7b40cf1d7ed32a` |
| f03e | `ev_0e782875a0747cda224a66d1b03b087502ad6545afd099c9611df3e822f8034f` |
| d656 | `ev_18516253dc9dfbbe0289d9c1376677c3b8dc90356c7da59f88915ea6789b7122` |
| ee10 | `ev_b4f51559fe99a2a33b1b153864fd5246c7f269f6bccac548afa964b7941871ad` |
| ec48 | `ev_2a9ca69254e589213269fd35a5d4dbed5f3d2d50d68f5bee6f7a1865bfbce16d` |

Smallest next recoveries, in useful order:

1. Exact e762..e877 (278 bytes), efcc..f01a (79 bytes), f03e..f04f (18 bytes),
   with symbolic UART/CRC/name/conversion/checkpoint boundaries. Model both5
   and11, ACK loss, header overflow rejection and preserved baseline retry
   defect. Maintained empty-header policy must have a meaningful result.
2. Real path/DOS enumeration5b54/5b68/5b71 and3ed9/3ea4 contracts, including
   DTA preservation, bounded filenames, empty batches and mid-batch errors.
3. Batch d394..d55a (455 bytes) with real UI and file-owner callbacks, and a
   maintained explicit status wrapper. Exact eb20 is36 bytes; separate
   eb44/ebb2 are110/149 bytes. Those latter helpers are later protocol work.
4. Recover overlay25 SEALINK and negotiated alternate engines before enabling
   ID13 or delegating `S`/`W`; no substitute success callbacks.

Verified original byte anchors for reproducible recovery:

| Span (end exclusive) | EXE file offset | SHA256 |
| --- | --- | --- |
| d394..d55b |128580| `9609552c11dc10c498e7985ba6de95ccaff1f460e473e8aec79d800900bbf1de` |
| e762..e878 |133650| `5ccbc53a7ac5bb7f74371cc12e7d9876f8fa09e1895a26b235a551241078d0af` |
| efcc..f01b |135804| `90109b57c2b8a047f6ac37682e1b8874315efe3eaad210a3c5b7a573f9fced9c` |

These spans end immediately after the final RET and exclude following
alignment bytes. Full transfer/application completion, successful native batch
sessions, and all alternate-protocol semantics remain open.
