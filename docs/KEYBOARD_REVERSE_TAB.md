# Native reverse Tab

The original half-duplex Shift-Tab path calls resident routine0BC0. Its complete
226 bytes are now recovered and assembled as both a flat baseline and an OMF
object. This component is a prerequisite for replacing the current explicit
unsupported result; it is not yet linked into the production keyboard path.

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
production path still rejects half-duplex reverse Tab before wire/echo output.

Production integration must bind the cursor, signed-division, protected-home
and attribute-repair services, validate table bounds and inconsistent wrap
modes before output, and exercise actual DOS screen and UART behavior. The
original table search assumes an FE terminator and has no30-byte bound. Full
Insert/Delete echo is covered separately by the shared keyboard integration;
all F01–F16 application gates remain open.

The [component record](validation/keyboard-reverse-tab.json) binds its native
baseline, checker and builder to the fresh156-output source-only rebuild.
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
