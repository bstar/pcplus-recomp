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

The instructions do not bound DI before writing digits or their trailing NUL,
and do not bound the parameter count before its indexed write. The next word
after the 16-word area beginning at cb3c is the count itself. Caller-side bounds
and malformed-input behavior have not yet been verified. These are specific
boundaries to test, not a claim of an observed live BBS failure.

Next work: recover the outer parser and its state transitions; add original vs
reconstructed parser replays; build a relocatable maintained reader with explicit
input/parameter bounds; then link it to screen and keyboard services. A byte-exact
parameter routine alone does not constitute an independently working ANSI parser.
