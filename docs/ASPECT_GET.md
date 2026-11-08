# Interactive GET recovery

Interactive `GET` is distinct from the implemented `FETCH` settings query.
The default compilers and runner keep GET disabled. The experimental
[compiler profile](ASPECT_GET_COMPILER.md) now emits the recovered ordinary GET
grammar for the opt-in [full interpreter](ASPECT_GET_VM.md). The selected and
installed packages remain unchanged. The component observations below retain
their original scope.

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

The original component recovery sequence was as follows. The linked owner and
opt-in compiler checkpoints above now cover parts of this sequence; the full
acceptance gates remain open:

1. Bind the serviced field described below to the real display, keyboard and
   cursor services; validate limits at the owner boundary.
2. Promote the checked typed-reader/writeback bindings below to the maintained
   runtime, with serviced UART/carrier and owner boundaries; recover floating
   conversion rather than substituting an opaque result.
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

## Serviced field checkpoint

The earlier [Meta Keys field recovery](META_TEXT_MODEL.md) supplied the shared
79D4 editing rules. GET uses different callbacks: string callback3F9C returns99
on Enter, causing the editor to return the trimmed length; numeric callbackF479
returns zero on Enter. Tab and Shift-Tab do not accept GET. String Tab becomes a
raw field byte, whereas the numeric callback rejects it with a bell. Escape
returnsFFFF without copying the working field into the destination.

REA analysis of the identified original executable confirms the seven-word
field ABI, separate initial/output pointers, masking and cursor handling. The
explicit [original replay](../standalone/capture_aspect_get_field_original.py)
executes original79D4, both callbacks and original CRT instructions with
synthetic buffers. Display, keyboard, cursor visibility/position and bell calls
are modeled services. The
[frozen traces](../standalone/fixtures/aspect_get_field_native.json) cover1,527
cases and25,873 pre-key states: widths1,2,10,50,80,81; empty/prefilled and separate
buffers; both callbacks; masked/unmasked display; visible/hidden saved cursors;
all byte keys; editing, full-latch and deterministic mixed-key sequences.
These are instruction/service-boundary observations, not actual VGA or UART
observations. The callback's all65,536-word filter proof remains separate.

[get_field.c](../src/aspect/get_field.c) provides a104-byte caller-owned state
with explicit far begin/key/render/commit/shape/visibility functions. Each key
returns to the caller, allowing the future runtime owner to service traffic
between keys. It allocates nothing and performs no DOS, BIOS, UART or file IO.
The DOS8086 diagnostic compares every recorded frame, cursor, shape, visibility,
bell count, final result and all82 output bytes, including preserved suffixes.
Initial data remains unchanged. Twenty API guards cover invalid widths/flags,
unterminated/oversized initial data, overlap/segment aliases, wrapping spans,
invalid states and premature commit. A diagnostic-only64-KiB pad forces separate
code segments; DS=SS is checked. A six-input isolated public-source rebuild
reproduces the exact EXE and result without originals or ancestor Git metadata.
The [field receipt](validation/aspect-get-field.json) binds these checks.

Widths1..81 and initial length no greater than width are maintained safety
guards, not recovered original validation. The original field has82-byte local
arrays and does not adequately validate arbitrary compiler-accepted widths or
initial lengths. No safe behavior is claimed for the original with zero,
negative or oversized widths. The source API requires82-byte source/output
buffers; the runtime still needs to validate actual destination capacity and
screen placement. In small-model DOS callers, a conditional optional source
must use explicitly far pointer branches: converting a conditional near NULL
can produce DS:0000 instead of the required0000:0000. The test harness exercises
both genuine NULL and non-NULL empty initial buffers.

This closes the memory-only field component checkpoint. Full GET owner bindings,
numeric conversions, cancellation dispatch, serviced live IO, both compilers,
runtime dispatch, memory/package gates and BBS composition remain open. Nothing
here changes the reviewed package, deployment selector or physical machine.

```sh
./tools/dev --command python standalone/build_aspect_get_field.py \
  --output build/my-get-field
./tools/dev --command python standalone/prove_aspect_get_field.py \
  --build build/my-get-field --output build/my-get-field-source
```

## Typed owner composition

The [owner replay](../standalone/capture_aspect_get_owner_original.py) now
executes the actual mode0 GET wrapper/owner, typed readers, global-string far
copy/flush, shared editor/callbacks and integer/long CRT instructions. Its142
authored cases span writable S0 plus global/local/parameter destinations of all
four types, Enter and three cancellation paths, optional/default/zero/bad
widths, last-line clipping, signed decimal prefixes and32-bit overflow. A
synthetic buffered FILE record backs the operand stream; native inline token
reads execute, while byte/word service reads update the same pointer/count.
Peripheral UI, confirmation decisions and nonreturning abort dispatch remain
explicit modeled boundaries. No private script or configuration is used.

The resulting [fixture](../standalone/fixtures/aspect_get_owner_native.json)
also exposes behavior which a replacement must preserve or deliberately change:

- With native range checks enabled, the optional width reader accepts0..80.
  Width81 and negative width reach native error1 before field entry. Compiler
  acceptance is broader than runtime acceptance; the separate field's width81
  observation does not override this command-level check.
- Width0 skips field entry/cursor handling but still clears FAILURE and writes
  back. Numeric conversion uses the existing scratch text.
- Escape sets FAILURE. A confirmed abort does not reach writeback; a declined
  confirmation or disabled KEYS path does. For example, with scratch `123`, a
  numeric destination becomes123 after declining Escape, even though the field
  itself never commits canceled edits. String cancellation retains its contents.
- Default width clips at the last row when WRAP is zero. The observed WRAP1
  path retains80 and can produce columns beyond79 in the modeled cursor service.
  Actual screen geometry/wrap behavior still needs live UI validation; these
  observations do not authorize unbounded direct VGA writes.
- Integer/long conversion uses the recovered CRT's decimal prefix and32-bit
  wrap semantics. `.5` converts to zero; `1.9` converts to one. These are not
  host-language numeric conversions.

[The source composition](../standalone/build_aspect_get_owner.py) links the
recovered owner, typed readers, far copy/flush and integer CRT with the serviced
field. Its explicit diagnostic bindings supply the synthetic stream, key input,
cursor bookkeeping, bells, confirmation and nonreturning error/abort boundaries.
Actual DOS8086 matches all142 final destination buffers, FAILURE values, widths,
field/cursor/confirmation counts, conversion requests and stream/key consumption.
It allocates a real far-heap string, checks DS=SS and forces the field model into
a different code segment. A14-input isolated public-source export reproduces
the exact executable and report. The
[owner receipt](validation/aspect-get-owner.json) records identities and scope.

Floating conversion remains a concrete gap. REA's overlay16/D408 dossier
`ev_701c8030fe4fa8cb72faf470c262cd45d861bd6bb75b6ce43c7b18686e03acd2`
shows a runtime request with selector5; its resource name at DGROUP497E is
`FLOAT.RTE`. GET supplies its text through E142 and copies eight result bytes
from E150. Both replays deliberately return an opaque authored eight-byte value
at that boundary. They verify request text and typed result routing, **not
floating-point conversion**. The source runner's existing unsupported float
policy is unchanged.

This is owner-component composition, not full dispatcher/compiler or application
integration. The opt-in [keyboard/service lease](ASPECT_GET_SERVICE.md) now has
actual DOS BIOS/UART checks; it still needs composition with this native owner.
Next work is the real parent display/cursor protocol, native abort lifetime,
serviced UART/carrier and cancellation ownership, and the
missing floating runtime. Then both compiler grammars and opcode49 can be
enabled with actual script/connection, memory and package tests. The installed
machine and deployment selector are unchanged.

```sh
./tools/dev --command python standalone/build_aspect_get_owner.py \
  --output build/my-get-owner
./tools/dev --command python standalone/prove_aspect_get_owner.py \
  --build build/my-get-owner --output build/my-get-owner-source
```
