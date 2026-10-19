# ASPECT string commands and comparison status

This records checkpoint `1a9be49`. The subsequent
[conversion/compiler checkpoint](ASPECT_CONVERSIONS.md) extends the runtime to
54 slots and 237 source-compiled fixtures; the counts below describe this
earlier checkpoint.

The standalone interpreter now executes concatenation, comparison, length,
ASCII case conversion, byte access, fill, update and substring commands using
recovered PCPlus instructions. It also implements the original comparison
status builtins used by `IF SUCCESS` and `IF FAILURE`.

The composed suite passes **361 actual 8086 DOS cases and 5,371 assertions**.
It runs 184 authored compiled fixtures: 159 complete, and 25 stop with their
expected distinct errors. Fifty of 215 native opcode slots are wired; the other
165 abort explicitly. Source compilation, the remaining command families and
terminal integration remain unfinished. No complete-application gate closes.

[Frozen evidence](validation/aspect-string-commands.json) binds sources,
compiler provenance, byte comparisons and composed file/heap execution.

## Reproduction

Use the pinned Nix toolchain for ordinary original-free checks:

```sh
./tools/build test-aspect-string-services test-aspect-string-commands test-aspect-runtime
```

Optional comparisons require the ignored local original executable:

```sh
./tools/build test-aspect-string-services-compat test-aspect-string-commands-compat test-aspect-runtime-compat
```

Normal builds consume public authored sources and frozen ASX fixtures. They do
not read ASPCOMP, the original installation or REA databases. `EXECUTE.EXE`
runs a fixed diagnostic suite rather than arbitrary user scripts.

The fresh [source-only rebuild](validation/application-components-source-build.json)
reproduces all 80 current outputs byte for byte with original installations,
analysis databases and previous build outputs absent from the copied checkout.
The composed `EXECUTE.EXE` SHA256 is
`dd2a01381dc0f6dbf72097d1bc7b15595c6b6b198a376e8718476dfd2d2727ad`.
This proves the current component builds, not a complete PCPlus application.

## Native commands and helpers

| Entry | Opcode | Behavior |
| --- | --- | --- |
| Native byte comparison | 9A | Compares an explicit byte span and stores status |
| STRCAT | AA | Appends a string, optionally limited by count |
| STRCMP | AB | Compares NUL-terminated strings or a bounded prefix |
| STRLEN | AE | Stores length in an integer destination |
| STRLWR | AF | Converts ASCII A..Z to a..z |
| STRPEEK | B0 | Stores an unsigned byte from a zero-based index |
| STRPOKE | B1 | Writes a byte at a zero-based index |
| STRSET | B2 | Fills a destination, optionally limited by count |
| STRUPDT | B3 | Copies a span into a destination at an index |
| STRUPR | B4 | Converts ASCII a..z to A..Z |
| SUBSTR | B6 | Copies a source span at an index into a destination |

String assignment AC was recovered in the
[parameter/string checkpoint](ASPECT_PARAMETERS.md). The 52 new compiled
fixtures establish the named command grammar above; the raw byte-comparison
entry has separate component evidence rather than a claimed source grammar.

The 11 entries add **401 exact bytes**, EEFF..EF1D and EF42..F0B5, with ends
exclusive. Their component diagnostic passes 2,058 CPU scenarios, covers all
196 instruction addresses and passes 27,819 actual DOS assertions. Optional
comparison verifies all 37 component code ranges against the original, rather
than pairing just the outer handlers with replacement helper mathematics.

The new service module adds **173 exact bytes** for strcmp, lowercasing, raw
fill, bounded byte/index operands, integer result storage and comparison status.
It reuses 168 existing recovered bytes for strlen, strncmp, concatenation and
uppercasing. Those helpers also execute unchanged in the composed runtime.
The service diagnostic passes 7,231 CPU vectors, including its 291-vector C
selfcheck, and 76,091 assertions in actual 8086 DOS. Optional replay verifies
all 341 new and reused bytes against the original and reproduces the CPU results.
Near DS=SS and DF=0 remain required. File, builtin, error and unavailable-float
callbacks in the command component remain explicit diagnostic policies.

Byte/index wrappers inherit the existing native range checker: byte values
0..255 and indices 0..79. Length operands accept 0..80. The maintained owner
enables range checking and always unwinds on errors; the component separately
preserves the native returning-error paths.

## Compiler grammar and CP437

The optional compiler oracle contains 65 authored cases: 52 compile and 13 are
rejected. Independent expectations predict 46 completions and six operand
errors. Earlier accepted outputs reproduce unchanged across the retained probe
runs. The original compiler is an oracle, not the final source toolchain.

Accepted forms include:

```text
STRLEN string integer_destination
STRPEEK string index integer_destination
STRPOKE string index character
STRCAT destination source [count]
STRCPY destination source [count]
STRSET destination character [count]
STRUPDT destination source index count
SUBSTR destination source index count
```

Direct quoted-string relational IF expressions fail in the authored probes.
Instead, STRCMP sets the signed comparison result and scripts test SUCCESS or
FAILURE. Numeric builtin 21 (`FAILURE`, native DA0C) returns -1, 0 or +1;
builtin 27 (`SUCCESS`, DA28) returns whether that result equals zero. The native
status routines operate on the shared D124 field. The maintained routing exposes
these two services; other numeric builtins remain unsupported.

The fixtures test equal/unequal and ordered strings, true and false branches,
empty strings, bounded prefixes, local and parameter operands, and raw result
snapshots. They use CP437 source bytes and expected strings. ASCII case
conversion preserves every high byte; for example `AéZÇ` lowercases to `aézÇ`,
and peeking `é` produces byte 130. The implementation does not apply Unicode
or locale case rules.

## Mutation, errors and zero counts

Native error 1 identifies an invalid range; error 3 reports a combined length
above 80. Both currently map to maintained operand error 7, while
`runtime_native_error_code` retains the original number. The compiled error
fixtures verify the original code as well as the maintained result.

A returning native error can permit truncated mutation. The maintained owner
instead aborts before copying or pending far writeback. Its six error fixtures
therefore retain the previously committed destination, free live string
allocations and close the file. This policy is distinguished from recovery;
the native handler instructions are unchanged.

Zero-length comparison reports equality. Zero-length concatenation leaves the
existing string unchanged in the tested owned buffers. Native concatenation
also depends on FLAGS from the preceding destination scan and DEC DI; reasoning
only from its zero REP count gives the wrong path. The actual DOS fixtures
verify the count-zero behavior.

STRSET preserves bytes after a bounded fill and forces byte 80 to NUL. STRUPDT
also forces byte 80 to NUL; SUBSTR terminates at the requested destination
length. Native near-copy direction and overlap behavior are retained rather
than replaced with memmove semantics.

SUBSTR checks index and count separately but does not check their combined
source span. Native pointers, indices, frame arithmetic and several string
operations remain unchecked. Authored fixture success is not arbitrary-input
safety. The standalone owner is not yet exposed as a general script runner.

## Remaining work

Other string/formatting and builtin services, floating-point runtime, source
compiler, recorder, serial/UI bindings and invocation/scheduling remain open.
Memory placement must be resolved before terminal integration. All F01–F16
whole-application gates remain open. The interactive terminal remains unchanged:
`731418bde8f3264d5f6c987195eb54b20c86a2981259ea1c721ba252e3c9a776`.
