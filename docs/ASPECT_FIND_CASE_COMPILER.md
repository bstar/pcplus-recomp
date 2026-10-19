# FIND and SWITCH compiler conformance

The maintained host compiler now emits the observed FIND and SWITCH/CASE subset. The frozen corpus contains **54 accepted sources and 72 rejected sources**, compiled by private ASPCOMP 1.01 before implementation. Normal checks read only public authored sources, expected bytecode and maintained compiler source. They do not run the original compiler.

```
./tools/dev --command python3 standalone/test_aspect_find_case_compiler.py
```

The checker verifies every accepted ASX byte, the original accept/reject boundary, case/whitespace/symbol-renaming variants, and seven independently specified novel emissions. One novel program places CASE/default/end targets beyond 65535 to verify real 32-bit absolute offsets. Compilation does not establish runtime availability: native FIND/SWITCH execution has a [separate runtime proof](ASPECT_FIND_CASE_RUNTIME.md), and serial BREAK remains unfinished. This increment preserves all prior 377 original outputs and presentation variants, 40 WHEN cases and variants, and 33 SET cases and variants.

## FIND

```
find haystack needle
find haystack needle position
find "ABCABC", "BC", position
```

The first two operands are atomic strings: literals, globals, locals, string parameters or proved string builtins. The optional third operand is an integer **destination**, not a starting offset or count. Long, float and string destinations and readonly integer builtins are rejected. Parenthesized operands and expressions are rejected. A single comma may separate operands; leading, doubled or trailing commas are rejected. The compiler accepts the empty string and 80-character literals; ordinary shared string-literal limits still apply.

Emission is `3B <string> <string> <option> [<integer-destination>]`, with option `00` absent or `01` present. String operands use the existing compact literal/variable encoding. For two global strings and global integer destination0:

```
02 CF 3B 8C00 8C01 01 8D00 94
```

The leading `02` is the global string count; FIND itself begins at `3B`. This compiler corpus does not assert the runtime match-index convention or update semantics; those require the native handler proof.

## SWITCH / CASE

```
switch selected
case 1
    result = 7
endcase
case 2
    result = 8
endcase
default
    result = 9
endcase
endswitch
```

SWITCH takes one atomic integer or string. Each CASE has one operand of the same type. Integer globals, locals, parameters and builtins are accepted, as are signed word constants including −32768. Long/float variables and literals, positive32768, numeric expressions and parentheses are rejected. String CASE operands can be variables or builtins as well as literals. Empty/high-CP437 strings are covered. Commas, colon labels, numeric ranges and multiple operands on one CASE are rejected.

A switch with no cases is accepted. DEFAULT is optional, can appear first, middle or last, and may occur only once. Duplicate CASE values are accepted by the original compiler. A final open CASE or DEFAULT requires ENDCASE before ENDSWITCH. Unmatched markers, extra operands and unfinished blocks are rejected. Nested switches, IF/ELSE, WHILE/EXITWHILE, procedure calls, local variables and parameters are covered by accepted sources.

### Fallthrough and ENDCASE

**ENDCASE jumps to the end of the whole SWITCH.** An empty CASE followed by an explicit ENDCASE still exits; it does not enter the next case.

Omitting ENDCASE before another CASE is accepted and falls through to that next case's **body**, bypassing its comparison. This also works after a nonempty body:

```
switch 1
case 1
    result = 7
case 2
    result = 8
endcase
endswitch
```

The compiler inserts a jump over the second CASE comparison. An implicit CASE→DEFAULT boundary falls directly into the DEFAULT body because DEFAULT has no comparison record; DEFAULT→CASE inserts the corresponding jump over the CASE record. Nested control blocks must still be balanced.

`BREAK` is an ordinary no-argument command that emits **0D**, the serial line BREAK action. It is not a switch exit. `EXIT` emits **33**, the existing whole-script exit command. `EXITCASE` is rejected. Compiler acceptance of `BREAK` does not claim a working ASPECT BREAK runtime service.

### Exact record layout

- `B8 <atomic-switch-value> <DWORD-first-case-or-fallback>` begins SWITCH.
- `0F <DWORD-next-case-or-fallback> <atomic-case-value>` is a CASE record.
- DEFAULT has no opcode; its address points at its body, including any generated fallthrough jump.
- Explicit ENDCASE emits `62 <DWORD-switch-end>`.
- An implicit boundary before CASE emits `62 <DWORD-next-case-body>`.
- ENDSWITCH emits no bytes and patches pending addresses.

Every DWORD is an absolute byte offset from the start of the ASX file, including its first header byte. The initial SWITCH link skips a DEFAULT that appears before the first CASE. CASE comparison links visit CASE records in source order; the final comparison links to DEFAULT if present, otherwise to switch end. All explicit ENDCASE exits target the same switch end. Empty switches and DEFAULT-only switches use the corresponding fallback directly.

For `switch 1 / case 1 / endcase / endswitch`, without global strings:

```
00 CF B8 B501 09000000 0F 15000000 B501 62 15000000 94
```

The CASE begins at9, and both its failed-comparison target and explicit ENDCASE target are21, the final return. Adding later cases changes the failed-comparison target but does not turn ENDCASE into fallthrough.

## Provenance and limits

The optional `freeze_aspect_find_case_compiler.py` verifies the private report/probe hashes before recreating the public fixture. It is an explicit oracle-maintenance step, not a normal compiler/build dependency. Compiler original SHA:

`5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`

The private report hashes are recorded in the public fixture; the three bounded batches contain 48,58 and20 attempts. All sources are authored for this investigation, with CP437 source hashes and accepted ASX hashes retained. No private configuration, vendor source listing or compiler binary is published.

This establishes bounded grammar acceptance and byte compatibility, not complete ASPECT compilation or matching original error wording. Unprobed constructs such as include preprocessing, array indexing and arbitrary declaration keywords remain outside the claim. Runtime case matching, case-folding flags, FOUND values, handler bounds and carrier/serial behavior need their own native execution evidence. No shared runtime or DOS product was rebuilt by this compiler increment.
