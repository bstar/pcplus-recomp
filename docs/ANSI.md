# ANSI reconstruction ledger

The parameter reader at original CS:e3f2 is recovered as
`reconstruction/ansi/parameters.asm`. It is 175 bytes, 77 instructions, in overlay
12. The loader-derived original file offset is 94370. The compatibility build
assembles and compares every byte before inserting it; no parser behavior change
is applied to that original-size candidate.

REA Evidence: `ev_eee26e941827e00c190eae7fd9e329a0be13e93287e5be2fd0722da4241d6207`.
Assembly and pseudocode are preserved under `docs/evidence/ansi`. Provenance is
in `reconstruction/ansi/parameters-provenance.json`. Names and descriptions below
are analyst interpretations of those instructions.

| Original DS location | Role observed in the reader |
| --- | --- |
| cb3c + 2 * count | Collected numeric parameters |
| cb5c | Word parameter count |
| cd38 | Last received command/terminator |
| ceac | Private `?` prefix flag |
| cee2 | Secondary `>` prefix flag |

| Original call | Required interface |
| --- | --- |
| 5ca0 | Timed receive, byte in AX or ffff for timeout |
| abde | Undo receive so ESC can be interpreted by the outer parser |
| 0610 | Process control character, caller removes one word argument |
| 984e | Decimal conversion of a near string pointer, caller removes argument |

The reader collects decimal digits into a 32-byte stack buffer. A semicolon with
no digits adds a numeric zero. NUL and DEL are skipped. Other control characters
are passed to the terminal character handler while collection continues. ESC is
put back and returns token `A` (abort). Leading `?` or `>` sets its respective
flag and returns `D`; ordinary parameter/terminator completion returns `S`.
Those token names describe return values; the complete outer state machine is
still being traced.

## Linked maintained module and deliberate fixes

The same reader now supports `ANSI_OMF`. All state and host services become
linker symbols; a checked decimal converter is maintained in `src/ansi/decimal.asm`.
`standalone/ansi_host.asm` provides a memory byte fixture and control-call recorder.
NASM and Open Watcom link them into `build/ansi/PARSER.EXE` without original files.
The executable performs its own ordinary-input and digit-overflow checks in DOS.
It is a parameter-parser diagnostic, not a complete terminal.

The original instructions do not bound DI before writing digits or their trailing
NUL, or the parameter count before its indexed write. Original-code replay now
reproduces the faults: 32 zero digits overwrite saved BP (babe becomes ba00), and
17 empty parameters overwrite the count at cb5c, leaving count 1 instead of 17.
This is fixture-driven native instruction evidence, not a live BBS observation.

Maintained mode limits digit storage to 31 bytes plus NUL, accepts unsigned values
0..65535, and limits the array to 16 words. Overflow returns token `A`, leaves
existing parameters intact and records `ansi_parse_error`:

| Error | Meaning |
| --- | --- |
| 0 | None; an ordinary ESC putback can still return `A` |
| 1 | Digit run exceeds its buffer |
| 2 | Decimal value exceeds one word |
| 3 | Parameter array is full |
| 4 | Input provider reports timeout |

Digit overflow consumes the remaining digits through their terminator before
returning; array overflow aborts at the excess parameter's delimiter. The future
outer/event parser must explicitly resynchronize after an error. This fixture
provider reports end-of-buffer as timeout; it does not implement a modem clock.
The preserved original wraps 65536 to zero and stores a partial number with
command ffff on timeout. Maintained mode rejects those cases deliberately.

`standalone/check_ansi.py` tests actual linked instructions, frame/register
preservation, adjacent array canaries, maximum digit/word/count cases, control
characters, prefixes and input-provider fragmentation. Seventy unsigned-decimal
vectors include deterministic random values. `test_parser_dos.py` executes the
program's built-in checks inside DOSBox-X. The optional original comparison runs
the original reader, original decimal converter and original transition helper;
receive/unreceive and control presentation are fixture callbacks. Eleven normal
cases match, with four documented deliberate differences. It does not establish
full screen behavior, escape timing or BBS compatibility.

## Confirmed outer state transitions

A focused REA session analyzed the overlay-14 context including parent overlay 12.
Its escape entry at CS:ecd2 resets count, first parameter and prefix flags for CSI,
then runs a token loop: `D` calls the parameter reader, `S` calls the transition
helper, and `L` calls the command dispatcher. Other tokens return from this loop.
The shared transition helper at CS:e4a2 returns `D` for semicolon, `L` otherwise.
Its 16 original bytes are recovered exactly and also linked in maintained mode.

Evidence `ev_affa93fbfa603209be50ad0dfe0c499e94c70ee8819a6fab2f66b066eec914dc`
identifies the helper; escape-entry Evidence is
`ev_11f20bd04542aced412c36c7eb3b31ad664d7138536c41bde318852fbeb544c3`.
Exports are under `docs/evidence/ansi`; all created native sessions were closed.
The analysis image is synthetic and was used only for static analysis.

Next work: recover and independently link the full escape entry and CSI command
dispatcher with actual screen services; add bounded event input and complete error
resynchronization; integrate keyboard and UART services. Other terminal emulations
and the remaining PCPlus application are still unreconstructed.
