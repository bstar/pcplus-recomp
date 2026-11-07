# Interactive GET recovery

Interactive `GET` is a missing ASPECT command, distinct from the implemented
`FETCH` settings query. It remains unsupported by the maintained compilers and
runner until its input owner is integrated. The current release/package stays
unchanged by this component checkpoint.

An explicit original ASPCOMP1.01 oracle, SHA256 `5664fdfa…`, compiles81 authored
probes on owned DOS media. The28 accepted cases establish opcode49 followed by
a writable destination and an optional numeric operand. String, integer, long
and float global/local/parameter destinations are accepted; writable `s0` is
also accepted. Optional comma syntax works. Literal/expression/parenthesized or
readonly destinations are refused. The optional operand accepts an atomic
integer, including the readonly FAILURE query, but rejects long/float operands,
parentheses, expressions and trailing commas. Constants0,80,81,255,256,-1 and
32767 compile unchanged;32768/65535 are refused. Compiler acceptance does not
prove runtime field-width validity. The public
[oracle fixture](../standalone/fixtures/aspect_get_compiler.json) contains only
authored scripts and their ASX bytes.

The existing pinned215-entry original dispatch inventory maps49 through
residentC717 to overlay17/F280. REA identifies its zero-mode wrapper and shared
owner F29F..F478, plus numeric callback F479..F4B5. The recovered
[assembly](../src/aspect/get_native.asm) rebuilds all566 bytes F280..F4B5 exactly
from source and also emits an OMF object without reading an original executable.
[The receipt](validation/aspect-get-native.json) binds original ranges/hashes,
Evidence IDs, compiler probes and the isolated reproduction.

The owner classifies typed destination tokens, obtains a string destination or
numeric scratch buffer and uses current cursor/attribute with an optional
width. Its default is80, clipped at the relevant last-line boundary. It calls
the external field service with seven words, restores the cursor, sets FAILURE
on field result-1 and conditionally enters cancellation handling before typed
writeback/conversion. These are recovered instructions, not yet an accepted
interactive implementation. The three adjacent sibling mode wrappers are also
rebuilt, but their source command names are not assigned by this checkpoint.

The numeric callback permits all key words255 and above, Enter/Escape/Backspace,
digits, minus and decimal point. Other byte keys ring the imported bell and
returnFF9D. The actual linked DOS8086 diagnostic checks all65536 key values
against that classification and bell-count behavior. The bell is a counter;
other reader/UI/conversion/cancel imports are unexecuted stubs. A six-input
empty public-source export reproduces the flat binary, linked diagnostic and
complete output without originals or ancestor Git metadata.

Next work is the full input owner, rather than making the compiler emit a
command that the runner cannot execute:

1. Recover field79D4 and its callback/keyboard/cursor ABI, including limits,
   editing and cancellation behavior.
2. Bind the recovered typed readers/writeback/converters and field buffer to
   the maintained runtime, with serviced UART/carrier and owner boundaries.
3. Add host and DOS compiler grammar matching the frozen oracle, then wire49.
4. Validate actual DOS interaction for all four types, cancel/retry, limits,
   special keys, state restoration and continued connection traffic.
5. Verify residency, source/package reproduction and BBS composition before
   offering a replacement package. Broader ASPECT and F01–F16 gates stay open.

```sh
./tools/dev --command python standalone/build_aspect_get_native.py \
  --output build/my-get-native
./tools/dev --command python standalone/prove_aspect_get_native.py \
  --build build/my-get-native --output build/my-get-source
```
