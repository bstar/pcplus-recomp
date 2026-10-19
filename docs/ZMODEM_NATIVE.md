# Native ZMODEM evidence

This report describes retained static REA evidence for the original PCPlus 2.01
ZMODEM overlays. It does not claim a working native reconstruction or observed
runtime interoperability. The maintained wire codec is an independent source
implementation; these observations establish original responsibilities and useful
comparison cases, rather than an instruction to preserve every original quirk.

## Artifact identity and coordinates

The original executable SHA-256 recorded by
`analysis/pcplus-overlay-entry-images/manifest.json` is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The following synthetic analysis images incorporate the resident image, active
overlay parents and overlay32. Their hashes were independently recomputed from
local image bytes during this review. They are analysis inputs only and were
never executed.

| Overlay | Parent chain | Original overlay file offset / bytes | Analysis image SHA-256 |
|---|---|---|---|
| 28 | 28 | 141216 / 4688 | `c447368de641e667a975ae8b4fcfcb25910b99637e7e4deae23d38d689905971` |
| 29 | 28,29 | 145904 / 3360 | `37085362aadf9d1670c910bb02fd9d9b94d640cf563b48eddfc81b2d7531f5c1` |
| 30 | 28,30 | 149264 / 2448 | `f8eff0d71e5a42be1678a1c6d603a749f31131d4c563280468eafb7385180d71` |

Functions use the saved Ghidra linear address coordinate: 0x1d0d0 corresponds to
resident-relative 0xd0d0, and 0x1e320 to relative 0xe320. Overlay29 and overlay30
occupy the same address window and must always be qualified by image identity.
The manifest gives their overlay-relative starts as 53456 and 58144 respectively.
Addresses are not direct original EXE file offsets.

Evidence was reused from `analysis/pcplus-overlay-anchored-{28,29,30}/`;
`evidence-bundle.json` retains 66, 36 and 32 records respectively. The providers
are REA/Ghidra 12.1.2, x86 real mode, analysis profile
`3cd9d21bc233a2347f0fed1a0c26c0e45668a7f3052b5e412f5c16e41c7e55dd`.
Retained subject paths name the earlier `/home/bstar/projects/DOS/analysis/`
location; image digests establish identity after repository relocation. No new
session or provider operation was required. The empty bundle unknown lists do
not establish that all behavior is understood.

## Observed structure

Overlay28 owns common framing, quoting, CRC dispatch, timed byte input and
transfer progress/state initialization. Overlay29 implements sending; overlay30
implements receiving. These responsibility names are analyst interpretations of
the explicit frame constants, data direction and file-service calls below.
Pseudocode is generated, not recovered original source. Segmented far-call
signatures and compiler helper arguments can be imperfect; retained `.asm`
listings are available beside each function for instruction-level checking.

Each row cites the complete pseudocode Evidence ID and canonical address. Its
local file is `analysis/pcplus-overlay-anchored-N/functions/ADDRESS.c`; the
corresponding `-c.json` and bundle retain full provenance and limitations.

| Overlay / address | Static observation | Evidence ID |
|---|---|---|
| 28 / `0x1d0d0` | Common entry: initializes transfer globals, sets initial subpacket size 0x400, dispatches by direction, restores UI state. | `ev_e4ab98ab2374306446b1af8f9a83f300404f92b0e6db9438763207c743887c6e` |
| 28 / `0x1d6a9` | Binary header writer: emits 2a 18 then A or C; frame type and four bytes enter CRC and quoting. | `ev_defc7a0eb1735474fc3fabcc1e3a1148098c9f12b64bef2577157eba30ac290e` |
| 28 / `0x1d72c` | CRC32 header writer: initial ffffffff, complement, four low-byte-first quoted CRC bytes. | `ev_e41973fd80b7512aaf47a79bc9e89aa83899b3de6e5353a149f873647f1e28da` |
| 28 / `0x1d7a5` | Hex header writer: emits 2a 2a 18 42, five bytes and CRC16 as hex, CR 8a, XON except types 3/8. | `ev_8c5afab31c0220ddea9bd1900a49170dda76d3b8e6db1cf240369ab1347159ce` |
| 28 / `0x1d841` | CRC16 data writer and CRC32 dispatch: payload then 18/frameend; frameend enters CRC; XON for 6b. | `ev_06de24a497acfa94a5bd2b06e35dd8da9ab3c7391f08dcdaed2bfc243c1af80a` |
| 28 / `0x1d8f1` | CRC32 data writer: payload plus terminator, complemented CRC in low-byte-first order. | `ev_a65ced5e14b4ca6375843d0c303d905f726b269f28f3f5fd3518e33df9ad5c52` |
| 28 / `0x1dbdf` | Header scanner: recognizes A/B/C, scans padding, converts four received bytes to position, detects cancellation. | `ev_76036ec5857604d0527e0c2c8adb55227beb71cb87dd12750f965407f415316c` |
| 28 / `0x1dd7d` | Binary CRC16 reader: type plus four bytes plus two CRC bytes; accepts zero residue. | `ev_5bd8031c91853843c6afbf178e22aa9335feece3d852f7583fbedb1d883cfbb4` |
| 28 / `0x1de12` | Binary CRC32 reader: type plus four bytes plus four CRC bytes; accepts debb20e3 residue. | `ev_b95fc03e3cc579102fa4a71c808f0e7089c8c20d3da9974b48b7dd3784c53368` |
| 28 / `0x1da98` | CRC32 data reader: distinguishes terminator tokens, checks debb20e3 residue, reports payload count. | `ev_02c710793b00ca66db08e78c95c1abf8043a120ba5bed33f300f1261efea3bba` |
| 28 / `0x1df93` | Byte quoting: ZDLE/control escaping, ESCCTL state and conditional CR/8d after @/c0. | `ev_8ba22609d3e09e45bdb42799d6a754e3b8600f908f30d2ba51fba2459b34abf1` |
| 28 / `0x1e061` | Byte decoder: flow-byte filtering, ZRUB0/1, XOR40 decoding, 100-bit tagged terminators and cancellation. | `ev_3ba095d08d09cfe7078eb0d6f8a27244c8d1c22ef36aa3c42d480e506b74cfa8` |
| 28 / `0x1e13a` | Parity-stripped header input: preserves CR/LF while filtering flow/control bytes. | `ev_5cc63578220d2ceb73485783c1760470904d3c22d1b27a8091fe95385f65677e` |
| 28 / `0x1e2ae` | Timed receive: BIOS tick changes, Esc cancellation and carrier test; no timeout unit claimed here. | `ev_5f2eb71d7bd566c55b58251cfadc8a7103e9ae137afa1a9eb410912923528d8c` |
| 29 / `0x1e69c` | Sender init: parses ZRINIT flags/buffer; CANFC32 and ESCCTL; answers ZCHALLENGE with ZACK. | `ev_b1e782339e069f5f1aab480798650b16c383a7610620aa19bf7be5725d59d951` |
| 29 / `0x1e7a7` | Sender optional ZSINIT: attention string plus ZCRCW, then await ZACK; hex header for ESCCTL. | `ev_78ea2a2d47b35e01d4f765f7c7c36eab3a6ffd04ebbd45e83e344e5d2529b203` |
| 29 / `0x1e828` | Sender ZFILE handshake: sends metadata, handles ZRPOS seek, ZSKIP, ZCRC and terminal responses. | `ev_6cb8f1d519bde984b6082a012826c7af04fffd06737e47c26e53d4eaeb4571dd` |
| 29 / `0x1e99a` | Sender data state: ZDATA, ZCRCG/Q/W selection, reverse-channel sampling/window waits, ZEOF and recovery. | `ev_b40ea3704cb45a1ce2e03f1fc0397c1e23609e7c063273478d8970d3306a310c` |
| 29 / `0x1ecfe` | Sender response/recovery: updates ACK position, seeks on ZRPOS, reduces block size after repeated same-position requests. | `ev_01c4106830d856a50818106dabb2680fb826397b8e92aca427c1744d92c16c8e` |
| 29 / `0x1ee00` | Sender cleanup: ZFIN exchange then raw OO. | `ev_8f222b857980df01c96d0402330b9c86de23323ccdf98bdd2d1a7af5d40515b2` |
| 30 / `0x1e391` | Receiver file setup: parses decimal length/octal time, evaluates existing-file options and free-space path. | `ev_b0ba3fa36f252e3de053b3091bba94ba99f0e71b64ffc31443325b75513d874a` |
| 30 / `0x1e5df` | Receiver init: emits ZRINIT (07 plus optional 20/40), handles ZSINIT/ZFILE/ZFIN/free-space request. | `ev_e7d891a524f8c5f3a6c4fa3e2c1a6eb932ec06dd30f5ee6621b54e617049404d` |
| 30 / `0x1e582` | Receiver write service: writes accepted bytes and aborts if count differs. | `ev_e52569de95c05f056265cf1ce04b5a247623d665dfbbd7c07cc3395982b20af6` |
| 30 / `0x1e729` | Receiver data state: ZRPOS, ZDATA offset validation, four subpacket endings, ACKs, bounded recovery and ZEOF offset match. | `ev_704a8b8e89452b2f2b169ba67ce53accd247b56171ef7ea69bfdb41d760297d8` |
| 30 / `0x1ea12` | Receiver file completion: close result and optional timestamp application. | `ev_d6402f93f9ae99c0011e8a02731a7d081c04909d33760149f17d343187f6de3b` |
| 30 / `0x1eaac` | Receiver cleanup: bounded ZFIN retries and wait for O. | `ev_3e1f07d98c8762ac36a5f8af078a0e3dc67b9cc6134a8d7cea79d57fcf61b442` |

## State and framing implications

The shared transmit mode at DS:8fea selects binary A/CRC16 versus C/CRC32;
DS:8ff2 records the active transmit data CRC mode. DS:d112 records received
header style, and DS:9000 tracks its CRC32 form. DS:d006 controls expanded
control escaping. DS:9002 stores the last transmitted byte for conditional CR
quoting. DS:cd26..cd29 holds four received header bytes; DS:cd2e..cd31 holds
four outgoing bytes. These names follow observed loads/stores, not original
symbols (28:1d6a9, 1d7a5, 1dbdf, 1df93).

The original uses CRC16 update/finalization helper calls at resident 5c42/5c5c.
This review establishes zero preset, high-byte-first transmission, terminator
coverage and zero receive residue, but does not independently recover those
resident helper bodies or their polynomial. CRC32 send paths preset all ones,
complement, and shift out the low byte first; readers explicitly compare residue
0xdebb20e3 (28:1d72c, 1d8f1, 1de12). The latter comparison was checked in
assembly at 0x1de92/0x1de99 as well as pseudocode, assembly Evidence
`ev_e0b206d02e481c73d1c8a1b3c97623ee217c54096cab6f8e4be67aa6dcba433a`.

The original hex writer emits CR followed by 0x8a, then XON except after ZACK
and ZFIN. Preserve receiver tolerance for parity-marked hex line endings. The
quote routine includes conditional CR/0x8d escaping after a byte whose low seven
bits equal @, as well as explicit ZDLE and negotiated control handling. The
receiver recognizes ZRUB0→0x7f, ZRUB1→0xff and all four frame endings. It tags
endings with 0x100 internally, so those values are parser events, not payload
bytes (28:1d7a5, 1df93, 1e061).

The sender tracks current data offset at DS:cb60/cb62 and last acknowledged
offset at DS:904e/9050. Incoming ZRPOS updates the file seek and offset state;
repeated requests for the same position eventually halve the block size above
0x20. ZACK matching is stricter when waiting at a frame boundary than during
streaming/window sampling (29:1ecfe). Initial/default subpacket size is 0x400;
negotiation and repeated-error paths can change it (28:1d0d0; 29:1e69c, 1ecfe).

The receiver tracks committed file offset at DS:9052/9054 and received payload
count at DS:d11a. It requests ZRPOS at the committed offset, verifies ZDATA's
position, advances/writes only accepted subpackets, acknowledges ZCRCQ/ZCRCW,
and accepts ZEOF only at the matching position. Receive advertised size and
mtime are held separately at DS:905e/9060 and cb64/cb66. Size metadata does not
replace the explicit final-offset test (30:1e391, 1e729, 1ea12).

## Inferences and unresolved behavior

- The original receiver advertises base ZRINIT F0=0x07, adding CRC32 bit 0x20
  unless configuration disables it and ESCCTL bit 0x40 when selected. This is
  a static outgoing-header construction, not a captured negotiated session
  (30:1e5df). It differs from modern Synchronet's default 0x23.
- Original sender ZCRC processing is present (29:1e828), but its decompiled loop
  decrements the count around byte acquisition in a way that warrants separate
  assembly/runtime validation for prefix lengths and zero meaning whole file.
  It should not be used as the sole CRC oracle.
- Receiver 30:1e729 has a special heuristic for an odd-length subpacket before
  the advertised file end: it records the previous position, then forces a
  later error/seek-back path. Its purpose and runtime consequences are unknown.
  Do not infer from this that baseline ZMODEM requires even-length subpackets.
- Exact timeout durations, UI string meanings, attention-string special control
  operations, file-management modes, pathname policy and write-failure cleanup
  are only partly understood. Timed input observes BIOS tick changes, keyboard
  Esc and a carrier-service result; parameter names alone do not establish
  seconds (28:1e2ae).
- The retained evidence has no executed wire capture, DOS peer transcript,
  packet loss test, or instruction-emulation trace for these routines. Empty
  files, long transfers, offset overflow and final-handshake failures remain
  runtime unknowns. No evidence here establishes ZedZap, variable headers,
  RLE, compression, encryption, ESC8 or remote command support.

## Independent implementation and validation boundary

Baseline maintained framing should follow the primary protocol and independent
peer checks. [Forsberg's protocol specification](https://gallium.inria.fr/~doligez/zmodem/zmodem.txt)
§§7–11 defines standard framing/handshake/recovery. Baseline subpackets are at
most 1024 bytes; 8192-byte ZedZap is an extension. Protocol constants alone do
not establish original extended-feature support.

Owned stock Synchronet is independently preserved under
`build/bbs-lab/synchronet/source/src/sbbs3/zmodem.{c,h}`, source commit
`9de2c48d0265b07e1a8406d8a55d31df4fad7ee8` in its provenance file. Its normal
protocol command uses `sexyz rz/sz` without `-8` in runtime `ctrl/file.ini:122`.
Source references include header/data encoding at zmodem.c:438/504/537/583/629,
receive decoding at 813/1068, capability parsing at 1555, and file receive
recovery at 2437/2507. This establishes a source reference and available native
peer; it does not claim a session was run during this review.

The repository-pinned nixpkgs revision in `nix/flake.nix` supplies independent
lrzsz 0.12.20. Read-only evaluation resolved its output to
`/nix/store/78dra5pddiyzxcn4zcdhg90ppkxkfai1-lrzsz-0.12.20`; it was not realized
or invoked in this review. Neither default dev PATH nor this evidence review
establishes an already installed `lsz/lrz` command.

High-value regressions suggested by the original are CR/0x8a hex framing,
conditional CR quoting, all four terminators, CRC16/CRC32 switching, ZRUB0/1,
fragmented escape sequences, stale ACKs, repeated same-position ZRPOS, wrong
ZDATA/ZEOF offsets, dropped acknowledgments, cancel versus quoted CAN payload,
empty files and odd lengths. These are proposed tests, not claimed results.
