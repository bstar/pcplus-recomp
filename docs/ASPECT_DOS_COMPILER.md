# DOS compiler port

The DOS compiler is being ported from the maintained host compiler, preserving
its existing language coverage and original-compiler bytecode expectations.
The first two C stages now run under8086 DOS. They are developer diagnostics,
not an ASPCOMP replacement: neither generates ASX, and the interpreter still
reports unsupported when an ASP needs compilation.

The normal builds use the pinned Nix Open Watcom toolchain, large-model C and
an8192-byte stack. They read only maintained C sources and public headers.
Neither the original compiler/executable, host ASPECT compiler, fixture database nor REA
analysis is an input to their application build.

```sh
./tools/build aspect-compiler-lexer aspect-compiler-unit
./tools/build test-aspect-compiler-lexer test-aspect-compiler-unit
```

## Streaming lexical stage

`compiler_lexer.c` borrows a binary FILE and reads one physical line at a time.
It retains the host's253-byte line bound, original source bytes, counted token
lengths and32-bit physical line/byte positions. CRLF is one line boundary;
standalone CR/LF and the remaining CP437-representable host `splitlines`
boundaries are handled explicitly. SUB is not an implicit EOF. Quoted strings
retain CP437 bytes, semicolons, carets and embedded NUL; outside quoted strings,
ASCII tokens fold to lowercase and the host's whitespace classes are retained.
The lexer recognizes the entire host token grammar, including incomplete-number
prefix boundaries, exponent/suffix combinations and longest operator forms.

No whole-file input allocation is required. A returned line/token view belongs
to the caller until the next read. Explicit token lengths prevent NUL from
silently truncating a literal before the later operand validator can reject it.
Read/length/character/position failures are sticky, and neither the reader nor
token copier closes the source. The ALX1 output from ASPLEX is a diagnostic
stream, not bytecode.

Actual DOS tests compare all1154 unique corpus/boundary sources with the host
regex, including accepted lexical forms inside grammatically rejected sources.
The comparison covers92290 physical lines,75155 tokens and2130319 output bytes.
It checks exact normalized bytes, spans, original source positions, four actual
CLI outcomes, source offsets/line counts beyond65535, reader errors, unchanged
output on rejected token copies and borrowed FILE lifetime. The diagnostic
reports2369 DOS checks. This is lexical evidence, not language acceptance.

## Declaration and procedure inventory

`compiler_unit.c` allocates owned declaration/procedure records, global indices,
local offsets and parameter offsets, plus source ranges for declarations,
hoisted initializers and executable body lines. It retains procedure order,
local/global shadowing, per-type global limits, local limits, reserved builtin
names and the host's parameter-layout arithmetic. Parameter words retain their
wire-width wrap; this is not evidence that an oversized parameter frame is safe
to execute. Every declaration line remains available to the validation pass,
including a trailing part the host inventory did not materialize.

Names and ranges do not borrow the lexer's reusable line buffer. One owned
allocation registry retires partial or complete units. Failure preserves the
borrowed FILE and diagnostics, clears public references and releases each
allocation. A loaded unit rejects another load until retired; disposal is
idempotent. Large-model pointers allow records to use memory outside DGROUP.
The AUN1 stream from ASPINV is an inventory diagnostic, not ASX.

The1164 actual DOS first-pass cases compare with the maintained host's
collection pass with emission disabled.1123 produce an inventory and41 fail in
this pass. Comparisons cover complete symbol/procedure order, type/space/index,
frame size, parameter bytes, initializer token slices/chaining and all retained
source ranges. Unknown or malformed body expressions can legitimately pass an
inventory; every body and initializer still needs validation before compilation.

Eighteen allocation-failure positions and200 successful load/dispose cycles
restore independently observed heap allocation addresses and sizes. A foreign
block and the borrowed source stay live. Six controlled heap corruptions or
capacity failures test the observer's rejection paths. The final suite performs
3326 checks, including actual ASPINV CLI children.

## Pinned CRT heap-check boundary

A separate malloc-only DOS program reproduces a far-heap-check failure before
any frontend code is linked: the pinned `_fheapchk` reports3 with one ordinary
allocation and after it is freed. An independent read-only observer sees a valid
heap with used count1 then0. The native near-heap checker remains part of the
ownership test; the allocator and production CRT have not been replaced.

REA/Ghidra observation
`ev_d1a5f2f22b386770e1316405e3db283a854074f3496c79f5004bb421f01b9b66`
recovers the linked267-byte `__HeapWalk` in the retained malloc-only probe artifact. Its
NULL-entry path depends on the nonzero heap segment, bypassing the expected
entry-offset check. This is a static observation of that pinned binary, combined
with the separate DOS reproducer; it does not claim an upstream fix or diagnose
every Watcom release. The upstream implementation uses based pointers in its
[far-heap walker](https://github.com/open-watcom/open-watcom-v2/blob/master/bld/clib/heap/c/heapwalk.c).

`standalone/compiler_heap_snapshot.c` avoids based-pointer null conversions.
It checks the actual segment chain,22-byte headers, tagged block boundaries,
four-byte end marker, allocation/free counts and circular free-list links and
sizes. It records used blocks without allocating or changing the heap. Cached
rover/largest-block hints are outside this observer's validation scope. Failed
observer attempts, the corrected diagnosis and complete REA evidence remain in
ignored local history; current reports bind the successful observer and its
isolated reproducer separately.

## Remaining compiler work

The target remains a working DOS compiler and runtime source fallback, not these
diagnostics. Continue the port through these stages:

1. Parse expressions, typed constants/builtins, lvalues, temporary allocation and
   numeric/boolean/string validation with all existing host/original vectors.
2. Emit operands/commands and positional string encryption directly into ASX;
   preserve32-bit file positions and checked branch/procedure fixups.
3. Validate every initializer and body, including unused procedures. Retain
   declaration source lines so malformed or omitted inventory parts cannot
   disappear from validation unnoticed. Native grammar for previously unproved
   malformed declaration edges still needs an original-compiler oracle.
4. Implement all current statement, command, argument, WHEN and settings forms.
   Validate unused bodies before repeated zero-reference pruning; preserve
   mutually referenced dead cycles and the original first-procedure jump rule.
5. Provide the DOS compiler CLI and transactional output/error handling. Compare
   complete emitted ASX with the existing host and frozen original compiler
   corpus, including files and branch targets beyond64KiB.
6. Integrate explicit ASP and missing-ASX ASP fallback into the checked loader.
   Preserve the UART lease, flow/error handling, script settings, filename label,
   file/global cleanup and source namespace across compiler invocation; test the
   actual result in DOS and the local BBS workflows. Scope INT0 ownership
   across nested compiler EXEC so a compiler fault cannot reenter an interpreter
   trap with the compiler's DS/SS; verify child PSP and vector restoration.

Full original compiler coverage beyond the maintained host subset, scripting
recorder and remaining application services stay in scope. No F01–F16 gate is
closed by these frontend stages.
