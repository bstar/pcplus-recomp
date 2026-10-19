# Native ZMODEM automatic reception evidence

This is a static review of PCPlus 2.01, using retained REA exports and direct
read-only decoding of verified original bytes. No original program, analysis
carrier, DOS peer or BBS session was executed. It establishes an original
automatic-reception path; it does not establish a maintained implementation or
physical-modem behavior.

## Identity and evidence coordinates

Original `analysis/pcplus-originals/PCPLUS-main-2.01.EXE` is 214016 bytes,
SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resident-relative address `x` maps to original file offset `1200h+x`.
Initialized DS bytes map to `25950h+x`. These mappings come from
`analysis/pcplus-overlays/manifest.json` and
`analysis/pcplus-overlay-entry-images/manifest.json`.

Retained Ghidra addresses add `10000h` to resident-relative code addresses.
Overlay addresses require their image identity: overlay28 uses analysis image
SHA-256 `c447368de641e667a975ae8b4fcfcb25910b99637e7e4deae23d38d689905971`,
overlay30 uses `f8eff0d71e5a42be1678a1c6d603a749f31131d4c563280468eafb7385180d71`,
and overlay19 uses
`0a2f9bca3d7d9efe33005f88554145bb7ee99f1cf0c5316dbc8d1506f0d22780`.
These carriers were not executed. The saved provider is REA/Ghidra12.1.2,
profile `3cd9d21bc233a2347f0fed1a0c26c0e45668a7f3052b5e412f5c16e41c7e55dd`.

The resident handler `11a8..123b` is **absent from the retained procedure
exports**. Its instructions below were decoded from the verified original
resident slice using GNU objdump (GNU Binutils)2.47, i8086/Intel mode. They are
not REA-returned pseudocode and have no invented REA Evidence ID. The exact
148-byte slice, original file offsets `23a8..243b` inclusive, has SHA-256
`c03ba8dc253cd662c4e1737901860fec220ae7114a90e648e720922a6062932b`.

## Original trigger and setting

Resident `0610` dispatches control characters through DS `44a0+2*character`.
Its ANSI control jump table also routes CAN18h to that dispatch path at `06a3`.
The verified DS word `44d0` is `11a8`; its bytes `a8 11`, original file offsets
`29e20..29e21`, hash to
`06dedca7fa511ad15e24ba635f70e31a5df38e70f0daae93de54ffb8a426be31`.
Retained assembly: `analysis/pcplus-main/functions/0x10610.asm`, Evidence
`ev_d53d1c66282bc50e670ae82baf3d89c2e48f0e66887e64c4c498cb484047acbb`.

The handler first respects emulation states: DS903e nonzero calls B9EB,
DS9026 nonzero calls6DCA, and DS9020 nonzero calls1EA0, each returning without
testing the automatic-reception prefix. These are live emulation states, not
proved PRM options for automatic reception. When all three are zero:

| Resident range | Verified behavior |
| --- | --- |
|11cc..11d1|Compare word DS1fb0 to zero; disabled returns at123b.|
|11d3..11dd|Read using AAD9(1); require AX0042h, ASCII `B`.|
|11df..11e9|Read using AAD9(1); require AX0030h.|
|11eb..11f5|Read using AAD9(1); require AX0030h.|
|11f7..1210|Two cursor-back/space display operations, consistent with removing the visible header padding. The handler does not validate preceding stars.|
|1211..122e|Call0DAE(1), then BB83 with near arguments `(1,0)`, then0DAE(0).|
|1232..123a|Three fall-through calls to ABDE provide staged reinsertion after a mismatch.|

Thus the actual trigger is receipt of CAN/ZDLE followed by `B00`, gated by
DS1fb0. It does **not** validate the remaining flags, header CRC or line ending
before entering transfer mode. It does not recognize a `ZFILE` header as its
automatic trigger. No requirement for literal `rz` text or exactly two preceding
stars exists in this handler.

The setting is inside the independently proved saved PRM memory image
DS1b84..2073. Combined with the actual trigger load, this proves **PRM offset
042c, little-endian word, zero disables/nonzero enables**. This is not a field
name inferred from the DS address alone. The persistence evidence is
overlay3:D60C, which writes one04F0h-byte element from DS1B84, and D734, which
reads that same range: retained assembly Evidence
`ev_39cec3eeeb0684b87998dd63fdacb5e25ecc38140de5a9226de9d84532418bab`
and `ev_45e3897063c74080373317d5c7421f5f9cf03ff252df70c61a29e4c5641afde9`.
Files are `analysis/pcplus-overlay-anchored-03/functions/0x1d60c.asm` and
`0x1d734.asm`; see [the configuration recovery ledger](CONFIGURATION.md).
The resulting field arithmetic is `1FB0h - 1B84h = 042Ch`.
Overlay19:F181 additionally accesses
the same word through E6BB: `functions/0x1f181.c`, Evidence
`ev_b5c65d5aa71c9ce4e48e6d8187e441c0e8e0fea9ce3a068d02a0b7d446c980bc`.
E6BB reads/writes a word through its caller-supplied pointer according to the
ASPECT/settings access direction; the separate PCSETUP child and complete
settings enumeration remain unproved. Requiring only0/1 in a maintained
importer would be a new validation policy, stronger than this original test.

## Partial input, mismatch and ownership

AAD9(1) is a blocking ring-buffer reader. With queued input it calls AA65
immediately. Otherwise it polls3323 until the DOS clock seconds field changes
once or input arrives, then calls AA65. It is not a one-BIOS-tick delay, a
nonblocking detector, or necessarily a full second of elapsed time.
`3323` calls778C with DS8f02 and returns DS8f08; `778C` uses INT21h/AH2Ch and
stores DH at that offset. Saved assembly Evidence:

- AAD9: `ev_84e05a4fe21a021e88cd2d075d70cd9d4b78c87d5e7785b70e0ce80cff40e0d7`.
- 3323: `ev_3a201917bb29b457a187c41bb1f5763da7ae218ddb1fadd6e65e2b344c90184a`.
- 778C: `ev_125ef5931c19bbcdbef33aac7555cc4a950c874fc11db0b086e25ce498f80355`.

These files are under `analysis/pcplus-main/functions/`, named by their
Ghidra address with `10000h` added and `-asm.json`/`.asm` suffixes.

A mismatch in the first, second or third comparison branches to1238,1235 or
1232 respectively, executing one, two or three ABDE calls. ABDE atomically
backs the UART ring read pointer, wraps it at7E20/7E1D, and increments count8E20
(`0x1abde.asm`, Evidence
`ev_05593e022160576b67d3dca58b67d5e3143b7ed740b7a79e4b8e2091019db3b6`).
This restores consumed lookahead when every attempted read actually acquired a
byte. **The handler does not distinguish an empty-read timeout before doing
reinsertion.** AA65 returns FFFFh if the ring is empty; the same mismatch path
still increments the ring count. The original path therefore must not be
described as proven lossless for truncated prefixes. A maintained lossless
recognizer needs its own explicit empty-input and replay rules.

The slice has no explicit current-file owner, pending-transfer, script or
unresolved-handle guard. It is reached through terminal control dispatch;
that does not prove reentrant safety.0DAE copies a declared memory region
between the live area and saved storage; its interpretation as suspension of
all application ownership is not established. Its retained pseudocode is
`0x10dae.c`, Evidence
`ev_91150e52e0b234bf82c9791d716d9aaf8f507477099fd8df44a31b2d21a61fb2`.

Manifest trampoline file offset52611 (`cd83h`, residentBB83) targets
overlay28:D0D0. The original common entry treats first argument **0 as send**
and **nonzero as receive**; `(1,0)` therefore selects receive without the manual
send filename prompt. This numbering must not be copied into the maintained
`zm_run(..., sending)` ABI, where1 means send. Retained common-entry Evidence:
`ev_e4ab98ab2374306446b1af8f9a83f300404f92b0e6db9438763207c743887c6e`.

## Destination handling

The original receiver file setup30:E391 copies DS1ea0 into its output filename
buffer and appends the basename extracted from received metadata before open.
Resident3EA4 strips through the last backslash or colon. This establishes the
default download prefix independently of the automatic trigger. Relevant
retained pseudocode:

- `analysis/pcplus-overlay-anchored-30/functions/0x1e391.c`, Evidence
  `ev_b0ba3fa36f252e3de053b3091bba94ba99f0e71b64ffc31443325b75513d874a`.
- `analysis/pcplus-main/functions/0x13ea4.c`, Evidence
  `ev_fd505e43c59736d95e68fe6c0374283050166eab7f33427288941ec1fa560682`.
- Overlay19:E95B passes `(40h,1ea0h)` to directory-string helperE6DD;
  assembly Evidence
  `ev_ce7d6f7122eaf73847100068a2ae5f99b1b3dd5db2bd326f2605ac6a0efa5292`.
- E6DD delegates editing/access, then appends a separator when a nonempty
  updated path has room and does not already end in backslash/colon;
  assembly Evidence
  `ev_7a07c50e2e47a85ec98cb28c241655ecd0bfc5858bdea4305a57f6cf3e6c776c`.

Together with whole-image PRM persistence, these prove **PRM offset031c** is
the default download path storage, with a40h-byte access/edit parameter. That
parameter does not independently prove every caller enforces safe termination
or bounded concatenation. Original receive setup uses unchecked string
operations. The exact accepted path grammar, drive availability checks,
overwrite/resume modes and failure ownership need separate validation.

Original help resource `PCPLUS-main.HLP` is23558 bytes, SHA-256
`6aa2a38b1bae7c81d082d4efae4c7cd2becaf048bbdb93af4467b74bba9543d5`.
Its Receive Files passage around file offsets3a0a..3bcb corroborates automatic
reception in Terminal mode when enabled, and use of the configured download
path or current directory. This is static bundled documentation, not executed
evidence; no user PRM file was opened.

## Protocol boundary and maintained policy

Forsberg's [primary protocol description](https://gallium.inria.fr/~doligez/zmodem/zmodem.txt),
sections8.1–8.2 and11.1, allows terminal applications to detect ZDLE followed by
`B00` as a receive invitation. Optional `rz` text precedes that invitation;
the receiver responds with ZRINIT. ZFILE and its metadata follow negotiation.
ZRQINIT flags distinguish normal data transfer from a command request.

A full CRC-valid, bounded, lossless header recognizer is a maintained design
decision, stricter than the original three-character lookahead. Its malformed
prefix, timeout, replay, settings and transfer-ownership behavior require
independent tests. The saved active-transfer header scanner28:DBDF and receiver
init30:E5DF are useful framing/handshake evidence, **not** the automatic trigger:
`ev_76036ec5857604d0527e0c2c8adb55227beb71cb87dd12750f965407f415316c` and
`ev_e7d891a524f8c5f3a6c4fa3e2c1a6eb932ec06dd30f5ee6621b54e617049404d`.
No evidence here establishes automatic ZFILE triggering, binary-header
autostart, safe remote commands, physical modem packetization, or complete
PCPlus reconstruction.
