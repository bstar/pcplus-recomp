# EXECUTE script-replacement compiler grammar

The original ASPCOMP 1.01 command is **EXECUTE**, emitting opcode **CB** with one string operand. `CHAIN` is not a source keyword: all 17 authored CHAIN spelling/form probes were rejected. The maintained compiler implements strict EXECUTE syntax and does not invent a CHAIN alias.

```
./tools/dev --command python3 standalone/test_aspect_chain_compiler.py
```

The frozen corpus has 35 accepted sources and 41 rejected sources from 76 original compiler attempts. The normal checker verifies every accepted bytecode output, case/whitespace/symbol-renaming variants, rejection variants and seven independent novel emissions. Normal checks read maintained source and public authored fixtures, never an original executable. Native script replacement, loader resolution, restart state999 and ownership cleanup require separate runtime evidence.

## Accepted source forms

```
string next_script
proc main
    next_script = "NEXT.ASX"
    execute next_script
endproc
```

The single filename operand can be a literal, global/local string, string parameter, or proved string builtin such as `$D_SCRIPT` or `$NULL`. Empty strings, high CP437 bytes and 80-byte literals are accepted by the original compiler; an 81-byte literal is rejected. Empty/compiler-accepted strings are not a guarantee that a file can be opened.

EXECUTE has no parameter-list syntax. A second string or numeric argument and `WITH` forms are rejected. A string parameter can supply the filename from an ordinary called procedure, but this does not pass arguments into the replacement script. A single quoted string containing spaces, such as `"NEXT.ASX ARG"`, compiles as one filename string; the compiler does not split it into a filename and arguments.

Numeric operands, undeclared bare filenames, a procedure name used as the operand, parentheses, string-concatenation expressions, leading commas and trailing commas are rejected. This strict syntax intentionally does not reuse a comma-stripping generic command path.

## Bytecode and raw filenames

Emission is:

```
CB <compact-string-operand>
```

There is no optional-argument flag, parameter count, procedure address or compiler-generated EXIT after this instruction. Examples:

| Authored source | Whole ASX |
| --- | --- |
| `execute ""` in main | `00 CF CB 6E13 94` |
| global string0 as filename | `01 CF CB 8C00 94` |
| `execute "NEXT"` at physical line3 | `00 CF CB AA B70C 6D7EFF71 94` |

`AA` introduces the existing encoded string literal; its bytes depend on file position and physical source line. `6E13` is the existing empty-string builtin. Local and parameter operands use the existing native near-frame encodings. The literal encoder and parameter ABI are shared with other proved compiler commands, rather than a special filename serialization.

Filename spelling remains unchanged. The corpus includes a bare stem, `.ASX`, `.ASP`, `.EXE`, an unknown extension, mixed/lower case, relative/root/drive paths with single backslashes, doubled separators, forward slashes, drive-relative paths, spaces, long names, `.` and `..`, and caret characters. These are compiler acceptance and byte-preservation observations. The compiler neither appends `.ASX`, compiles an `.ASP` file, validates DOS8.3 names, normalizes separators, expands a command line, nor establishes that any of those paths will open at runtime. Native loader extension/search rules belong to the runtime investigation.

## Called procedures and following code

EXECUTE is accepted in MAIN, in called procedures, and in a procedure containing parameters and local storage. The frozen procedure cases verify ordinary C7/C8 calls and frame setup together with the CB operand.

The original compiler retains statements following EXECUTE. A source assigning1, executing `"NEXT"`, then assigning9 contains both assignments and its normal return in the ASX. The called-procedure cases likewise retain later assignments in the called body and caller. This is bytecode emission evidence, not a claim that those statements run after a successful replacement. Runtime success/failure determines whether the old execution context resumes or is abandoned; that behavior is not implemented by compiler reachability pruning.

An unreferenced helper procedure is still removed by the existing procedure-pruning rules. The compiler does not rewrite EXECUTE as CALL, GOSUB, DOS EXEC or an early return. One novel checker case also verifies a real procedure target beyond byte65535 while its target body emits EXECUTE of `$NULL`.

## Provenance and limits

`freeze_aspect_chain_compiler.py` is an optional oracle-maintenance tool. It verifies private probe/report hashes before rebuilding the public fixture. The two original compiler batches contain62 and14 authored attempts; original compiler SHA:

`5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`

The public fixture records CP437 source hashes, accepted ASX hashes, rejected compiler diagnostics and private report/probe hashes. Originals, generated compiler output files and user configuration remain private. No analysis-only executable or original PCPlus application was executed for these compiler probes.

This establishes a bounded source grammar and exact emission, not complete ASPECT support, original diagnostic-wording compatibility, native file loading, transactional replacement, state preservation, UART/WHEN/renderer lifecycle or a working CHAIN alias. No shared runtime or DOS product build is changed by this compiler increment.
