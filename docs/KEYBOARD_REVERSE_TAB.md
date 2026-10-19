# Native reverse Tab

The original half-duplex Shift-Tab path calls resident routine0BC0. Its complete
226 bytes are now recovered and assembled as both a flat baseline and an OMF
object. The live shared keyboard path now calls this recovered routine after
bounded admission, including during admitted ASPECT sessions.

REA12.1.2 identifies source offset1DC0 for linear address10BC0 in the verified
2.01 original, SHA-256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The current Listing has no defined procedure/instruction at that entry.
Mapped bytes were therefore decoded with ndisasm and reassembled byte for byte;
the absence of a Ghidra procedure is retained as a limitation. Evidence IDs:

- Bytes: `ev_18c8c70cf3ca03428dbba938dcd9734175e4633b2374c73b2277463a36d018e0`.
- Mapping: `ev_e1ead9b45f6bb15a132bb0ee8b82e26c2c73d6ad7baf4413fbe0b05fa715173f`.
- Undefined instruction: `ev_642fb8fa9d9a12470cd8535e3d4aab08919280f44dd810ceed8a10acad3cf792`.

Ordinary builds read only maintained assembly and provenance. The separate
analyst recovery script reads the private verified original and is never an
application build input. Run the checks through the pinned toolchain:

```sh
./tools/build test-keyboard-reverse-tab
```

The3846 CPU cases execute the recovered instructions with six FE-terminated
tab tables,80 columns and all eight combinations of the three tab-mode words.
They cover previous-stop selection, fallback to column0, the empty-table mode
guards, reverse wrapping, protected attribute search, attribute-repair dispatch,
signed-division argument order and protected-home dispatch. Stack, SI, BP, ES
and DS=SS are checked. External cursor/attribute/division/home services are
declared scalar models rather than recovered video implementations.

One counterexample additionally executes the actual recovered cursor-left
routine. At column0 with a populated table, tab-wrap enabled and cursor-wrap
disabled, reverse Tab calls cursor-left and recursively retries. Cursor-left
does not move under that configuration, so the pair does not return within
20000 instructions. The screen-position callback remains a scalar model;
the inherited recursion and cursor-left control flow are real recovered code.
This is characterized behavior, not a fixed production vulnerability. The
production preflight now rejects this nonprogressing configuration before any
wire, cursor or video effect. The original flat routine remains byte-exact.

The application binds the real cursor, signed-division, protected-home and
[attribute-boundary services](ATTRIBUTE_BOUNDARY.md). They share ASPECT_CODE
with explicit near/far bridges to resident cursor and notice providers. This
avoids exceeding the resident64KB segment; an initial near-only link failed
by940 bytes and is retained in the private build log.

Plain-tab admission requires a strictly increasing, FE-terminated prefix within
the30-byte table. Empty tables retain native mode-dependent no-op/home behavior.
Only the branch that reads stops validates that table: protected navigation
does not fail because of unused tab data. Read-only lookahead checks the actual
protected path before transmission. It rejects doublewidth underflow,
nonprogressing reverse wrap, stale offsets from suppressed wrap and protected
scroll paths that would reach the still-unrecovered repair services. It does
not move the cursor or consume those mode flags while deciding admission.

The630 linked cases exercise native code and far bridges on ordinary and
protected fields, circular boundaries,1..25-row planes, doublewidth rows,
malformed tables, empty tables and mode guards. Rejected calls preserve cursor,
video, metadata and parser parameters and emit no bytes. Full-duplex bindings
still transmit without requiring a local echo plane. The16 actual DOS cases
include default/custom reverse-tab stops in both profiles, script continuation
and retained unsupported local-key handling. Insert/Delete echo is covered
separately by shared keyboard integration. All F01–F16 gates remain open.

The [component record](validation/keyboard-reverse-tab.json) binds its native
baseline, linked checker and builder to the fresh source-only rebuild.
An initial expanded proof failed only because NASM's OMF module header used
an absolute checkout path. The builder now supplies a stable relative source
path; the failed report remains at
`build/keyboard-reverse-tab/source-proof-expanded.log`, and the corrected
proof includes all three new flat/object/oracle artifacts byte for byte.

The existing saved REA overlay-loader inventory also resolves the related
keyboard echo calls: resident trampolineB9F7 selects overlay12 entryD270,
and BA03 selects overlay12 entryD440. These are the already recovered
`csi_insert_character` and `csi_delete_character` routines, respectively,
with source offsets89888 and90352 in the verified original. They are already
linked for CSI editing. Keyboard integration should reuse those helpers with
preflight before wire output and preserve parser parameters, rather than
recovering duplicate implementations. The mapping is static loader evidence;
its runtime use is tested separately in [shared keyboard output](ASPECT_KEY_OUTPUT.md).
