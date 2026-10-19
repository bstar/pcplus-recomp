# Selected SET compiler forms

The host compiler now emits eleven selected SET settings from authored source.
The production interpreter now links these eleven native setters; other SET
subcommands stop explicitly. See [ASPECT_SET_RUNTIME.md](ASPECT_SET_RUNTIME.md)
for real consumers, current invocation lifetimes and remaining dependencies.
This compiler proof establishes source grammar and bytes separately.

| Source setting | Subcommand | Value encoding |
| --- | --- | --- |
| DISPLAY | 12h | OFF=0, ON=1 |
| DUPLEX | 18h | FULL=0, HALF=1 |
| FINDCASE | 23h | OFF=0, ON=1 |
| KEYS | 29h | OFF=0, ON=1 |
| MSG_CRLF | 2Eh | OFF=0, ON=1 |
| PAUSECHAR | 30h | Compact integer operand |
| RXDATA | 3Bh | OFF=0, ON=1 |
| SWITCHCASE | 44h | OFF=0, ON=1 |
| TXPACE | 4Ch | Compact integer operand |
| WAITCASE | 55h | OFF=0, ON=1 |
| WHENCASE | 56h | OFF=0, ON=1 |

The SET opcode is 9Eh. For example, `SET DISPLAY OFF` emits `9e 12 00`;
`SET TXPACE 999` emits `9e 4c ab e7 03`. The original compiler accepts
TXPACE -1/1000 and PAUSECHAR 31/127. The host compiler preserves those bytes;
runtime bounds are a separate responsibility. Original probes reject DUPLEX
ON/OFF, numeric/variable/YES boolean values, TXPACE 10L and string PAUSECHAR.
Numeric operands also accept a leading comma and integer global/local/parameter
selectors. Parentheses, arithmetic expressions, long/float/string operands,
positive 32768, extra numeric operands and bracket-array syntax are rejected.
The boolean grammar rejects parentheses and a trailing comma. All other
settings and broader grammar remain outside this corpus.

The frozen public fixture contains 33 accepted and 19 rejected authored
sources from hash-identified ASPCOMP 1.01. It contains source, generated ASX
bytes and hashes, with no original executable or private dialing data.
`standalone/freeze_aspect_set_compiler.py` verifies the retained private report
and probe hashes before producing this fixture. Ordinary conformance reads
only maintained compiler source and public fixtures:

```sh
./tools/dev --command python3 standalone/test_aspect_set_compiler.py
```

All 33 accepted outputs match byte-for-byte, all 19 original rejections are
preserved, and 33 case/whitespace/identifier variants preserve output. Existing
377-case general and 40-case WHEN compiler suites also pass unchanged. These
checks establish selected grammar and encoding, not complete ASPECT support,
runtime effects, or physical modem behavior.
The [validation record](validation/aspect-set-compiler.json) binds the compiler,
fixture, checker and regression reports to this checkpoint.

Runtime integration must preserve shared native state: RXDATA writes the same
word used by the flow gate, and KEYS ON writes the native keyboard-disable
word. DISPLAY controls received-character rendering; it does not terminate the
resident renderer service or suppress every other output source. Nonzero
TXPACE needs native timing recovery rather than an arbitrary host delay.
