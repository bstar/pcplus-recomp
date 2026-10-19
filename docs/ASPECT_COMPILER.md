# Maintained ASPECT compiler increment

`src/aspect/compiler.py` compiles authored ASPECT source into ASX for the
maintained DOS runtime. It is a host Python compiler with no external Python
packages. Its ordinary inputs are its own source and the requested `.ASP` file;
it does not invoke ASPCOMP, read an original executable, or look up fixture
outputs. This is a functioning compiler increment, not a complete ASPECT
implementation or a DOS-hosted compiler executable.

Use the pinned toolchain:

```sh
./tools/dev --command python src/aspect/compiler.py example.ASP -o example.ASX
./tools/dev --command python standalone/test_aspect_compiler.py
```

The importable interface is `compile_source(source: str) -> bytes`. Unsupported
or malformed source raises `CompileError`, including a physical line number.
The CLI reads CP437 source and writes output only after successful compilation.
It preserves an existing output if compilation fails.

## Implemented source forms

* Case-insensitive names and keywords; quoted CP437 strings preserve their case
  and bytes. Blank lines, semicolon comments, LF and CRLF source are supported.
* Independent integer, long, float and string global banks; typed local storage
  and initializers; `intparm`, `longparm`, `floatparm`, `strparm` declarations.
* `proc` / `endproc`, forward and recursive `call` / `gosub`, typed `with`
  arguments, caller cleanup and callee local-frame allocation.
* Numeric assignments and chained assignments, `+= -= *= /= %=`, decimal and
  hexadecimal integer constants, `L` suffixes, floating constants, unary minus,
  prefix increment/decrement and standalone postfix increment/decrement.
* Arithmetic `+ - * / %`, parentheses, comparison `== != < > <= >=`, short-circuit
  `&& ||`, precedence and distinct indexed intermediate results. Binary
  operations are emitted, including constant expressions and division by zero;
  this compiler does not silently evaluate them on the host.
* Nested `if` / `elseif` / `else` / `endif` and `while` / `endwhile`,
  `exitwhile`, `loopwhile` with absolute 32-bit jump offsets.
* String assignment and `strcat`, `strcmp`, `strcpy`, `strlen`, `strlwr`,
  `strpeek`, `strpoke`, `strset`, `strupdt`, `strupr`, `substr`; optional counts
  where established. `success`, `failure`, `$NULL` and fixed string slots
  `S0` through `S9` are recognized operands.
* `atoi`, `atol`, `itoa`, `ltoa`, and `pause` command emission. Their availability
  in any application depends on that application's runtime service wiring.

Calls and commands accept atomic operands, with optional commas between them.
Arithmetic call arguments must first be assigned to a typed variable, matching
the established original grammar. Direct string comparisons in numeric
expressions are rejected; use `strcmp` followed by `success` or `failure`.

## Wire compatibility and verification

The compiler emits the global-string-count header, original procedure entry and
return records, per-type global/local/parameter selectors, numeric metadata,
indexed expression temporaries, and absolute call/branch fixups. String literals
use the established position and physical-line keyed transform. Empty strings
emit the original null-string builtin. Local numeric declaration lists preserve
the original chained initializer record form.

The original-free regression suite compares all **237** authored public vectors
against frozen ASPCOMP 1.01 byte outcomes and SHA256 values: 19 execution, 86
arithmetic, 27 parameter, 52 string-command, 38 conversion and 15 independent
compiler-validation cases. Those outcomes came from the separate optional
original compiler oracle, SHA256
`5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`.
Their provenance is retained in each fixture corpus. Test inputs, expected
runtime values and emitted bytes are distinct from compiler implementation.

Every frozen source is additionally compiled with renamed symbols, changed
keyword case, indentation and LF endings. Independent tests cover reordered
procedures, newly authored constants, comments, actual generated call targets
above 64 KiB, CP437 CLI input, failed-output preservation, variable-bank limits,
type/count errors and unsupported syntax. Original runtime evidence and native
DOS runtime diagnostics are documented separately; byte compatibility alone is
not proof that every emitted command has a fully reconstructed runtime service.

## Explicit limits

Only the grammar and commands above are implemented. Includes, macros, arbitrary
labels, other control structures, most system operands, general PCPlus command
families and a DOS-hosted compiler remain work. Error wording, accepted identifier
sets, declaration-order corner cases and all original compiler permissiveness
have not been exhaustively reproduced. The compiler accepts source lines up to
253 CP437 bytes; it deliberately rejects longer physical lines rather than
claiming compatibility with the original 255-byte `fgets` chunking behavior.

String literals are limited to 80 non-NUL bytes; globals are limited to 128 per
type and locals to 128 variables per procedure. No original undocumented maximum
expression-depth or procedure-count guarantee is inferred from these fixtures.
The one-byte intermediate index has an explicit encoding bound. Decimal integer
overflow retains the observed low 32 bits, rather than promising modern checked
arithmetic. Floating literals and record forms are emitted; the maintained
runtime's unavailable FLOAT.RTE dependency remains an explicit execution stop.

Source compilation is source-only; running an arbitrary resulting ASX on physical
hardware or in an original application is a separate integration test. There is
no claim here of complete PCPlus source recovery.
