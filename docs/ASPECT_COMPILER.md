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
./tools/dev --command python standalone/test_aspect_when_compiler.py
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
* String assignment and `strcat`, `strcmp`, `rstrcmp`, `strcpy`, `strlen`, `strlwr`,
  `strpeek`, `strpoke`, `strset`, `strupdt`, `strupr`, `substr`; optional counts
  where established. `success`, `failure`, `comdata`, `forever`, `found`, `$NULL` and fixed string slots
  `S0` through `S9` are recognized operands.
* `when` with TRANSMIT/CALL actions, `cwhen`, DISCONNECT forms and
  `set whencase on/off` emission. WHEN CALL uses absolute C7/C8 procedure
  fixups and rejects parameterized handlers; application runtime support
  remains a separate integration step. See `ASPECT_WHEN_COMPILER.md`.
* `atoi`, `atol`, `itoa`, `ltoa`, `message`, `exit`, `pause`, `transmit` and
  `waitfor`, `comgetc`, `comgetcd`, `rget` and `waitquiet` command emission. Their availability
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

The existing original-free regression suite compares all **377** accepted authored
public outcomes against frozen ASPCOMP1.01 bytes and SHA256 values. The isolated
WHEN suite adds40 outcomes from its component and procedure-grammar corpora,
checking417 outcomes across both suites without changing prior fixtures. Compiler-only cases
remain separate from the runtime vector list. Those outcomes came from the
optional original compiler oracle, SHA256
`5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`.
Their provenance is retained in each fixture corpus. Test inputs, expected
runtime values and emitted bytes are distinct from compiler implementation.

The WHEN follow-up also preserves native unused-procedure behavior: repeatedly
remove zero-reference procedures with MAIN protected, retain mutually referenced
dead cycles, retain the initial MAIN jump when the first declaration is dropped,
and validate malformed unused bodies. These rules match the bounded authored
original corpus, rather than asserting full optimizer recovery.

Every frozen source is additionally compiled with renamed symbols, changed
keyword case, indentation and LF endings. Independent tests cover reordered
procedures, newly authored constants, comments, actual generated call targets
above 64 KiB, CP437 CLI input, failed-output preservation, variable-bank limits,
type/count errors and unsupported syntax. Original runtime evidence and native
DOS runtime diagnostics are documented separately; byte compatibility alone is
not proof that every emitted command has a fully reconstructed runtime service.

The console corpus preserves all 55 canonical compiler attempts: 33 accepted and
22 rejected. Its optional oracle is `standalone/aspect_console_probe.py`; the
freezer binds the private compiler report, probe source, authored predictions and
accepted ASX hashes in `standalone/fixtures/aspect_console_vectors.json`.
Earlier compiler01/02 errors remain private, including the discovery that TEXT
is a reserved word. The maintained compiler now rejects TEXT declarations.

Console grammar is concrete: `message string`, operand-free `exit`,
`pause integer`, `transmit string`, `waitfor string [integer timeout]`, and
`rstrcmp string string [integer count]`. PAUSE and the optional WAITFOR timeout
require signed integer operands; long variables, `L` suffixes, floats and the
positive constant 32768 are rejected. Native PAUSE subsequently rejects negative
values at execution. RSTRCMP compares a raw byte span, defaulting to 80 bytes;
its bytes beyond a NUL can matter, unlike STRCMP. Its corpus uses fresh zeroed
scratch backing or an explicit short span, rather than assuming these commands
are equivalent.

Runtime predictions were fixed before composed execution: MESSAGE uses the
native caret decoder and appends the default CRLF; EXIT terminates the whole
script, including caller continuations. The native default comes from overlay02
D6EA, which resets E38A to one (retained evidence
`ev_7f2a37333c76fe8f326ecc36a6ef20a640284f710c20b9e47a19c3288aa55d92`).
Caret bytes remain literal in ASX and are decoded at runtime; they are not host
compiler escapes. The maintained runtime now executes TRANSMIT/WAITFOR and the receive commands
through explicit raw UART platform services. [Receive-command evidence](ASPECT_RECEIVE.md)
distinguishes native semantics from terminal-rendering and scheduling gaps.
FOUND emits its established builtin index but remains unsupported at runtime.
FOREVER emits an integer builtin or a special timeout option according to its
grammar position; these forms have different native values and are tested separately.

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
