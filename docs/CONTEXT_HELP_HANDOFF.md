# Native contextual Help handoff

The original resident `57AE` descriptor producer is now recovered as132 exact
source-assembled bytes. A source-built DOS parent executes it and launches a
source-built child which reads the parent's still-live descriptor, path and
title, then selects an authored help topic. This establishes the process ABI;
it does not yet enable global Help in the terminal or reproduce PCHELP's UI.

## Original behavior and source boundary

Ordinary Alt-Z dispatches the already recovered `56FE` command-reference
window. The keyboard poll intercepts another Alt-Z when its signed context
word is enabled, invoking `57AE`. These are distinct entry points. The native
reference window enables context41; this work does not establish a general
original F1 binding from the dispatcher table alone.

`57AE` resolves `PCPLUS.HLP`, copies that path to its stack, constructs nine
words, formats ` PCHELP %lu` with the descriptor's DS:offset encoded as an
unsigned decimal32-bit value, resolves `PCHELP.RTE`, then calls the external
PROGRAM controller with path, tail and three zero words. The stack remains
live while the child runs synchronously. Recovered `strcpy` and `getDS` add53
previously recovered bytes, reused without duplication.

| Descriptor byte | Native value |
| --- | --- |
| 0 | Path offset in parent DS |
| 2 | Title offset in parent DS |
| 4 | Raw context word at397A |
| 6 | Raw UI word at1D3E, meaning unresolved |
| 8,10,12 | Normal, bold and reverse attributes |
| 14,16 | Configured mouse X/Y scales |

The producer copies the raw context and UI words verbatim. Signed or
out-of-range context fallback belongs to the helper. The diagnostic child uses
the existing source-owned format decoder and authored47-topic HLP data; no
vendor help text is copied. The native118-byte frame allows66 bytes for the
path before the30-byte command buffer and18-byte descriptor. Its original
`strcpy` has no bound: tests cover resolved paths through65 characters plus
NUL. Production admission must bound the path before invoking this producer.

The native assembly leaves ES equal to DS through `strcpy`. The diagnostic C
entry wrapper preserves its caller's ES. DS=SS, original BP/SI/DI, stack
balance, return value and clear direction flag are checked in isolated native
execution. Do not infer a stronger original ABI from the wrapper.

The original resolver, formatter and external-program controller remain
explicit dependency boundaries. The DOS probe binds them to a diagnostic
resolver, a fixed-signature wrapper around the pinned CRT's `sprintf`, and
synchronous `spawnl`. It deliberately reuses one resolver scratch buffer:
resolving the executable overwrites the original resolved-path storage, while
the native stack copy must survive. This is real DOS EXEC, but it does not
exercise the application's native PROGRAM ownership/UART controller.

## Evidence and verification

[The receipt](validation/context-help-handoff.json) binds the exact source,
products, checkers and results:

- 1728 isolated instruction cases pass as source and against the matching
  original-file slices: three DS segments, odd/even stacks, eight context
  values, four path lengths, three raw UI profiles and three controller return
  values. Resolver, formatter and PROGRAM calls are declared models. The
  original executable is hash-checked and used only for selected byte slices;
  neither it nor any synthetic analysis carrier is executed.
- The actual8086 DOS parent passes182 checks across eight real helper launches
  and three rejected requests. The helper reads foreign parent memory while
  its frame is live, checks all nine words and both strings, reads the authored
  HLP record/text, and returns a binary record for parent verification. Invalid
  marker, low segment and decimal overflow create no output record.
- A fresh15-file public-source tree, without originals, configurations,
  analysis state or previous objects, reproduces both EXEs and the authored
  HLP byte for byte, then repeats1728 source CPU cases and182 DOS checks.

Fresh REA producer assembly is
`ev_d9f426ad32032b1f5e33c9129443266507450309678c399665faa683811abb74`;
the supporting string read is
`ev_aa52c3b5e93853a2378b90f6ad14c7cb2dd293c76c7d2454834ca959ab937060`.
The synthetic carrier SHA256 is
`4ae6ee164991ab772dcb0dba4974fe30d00ee97429719dbbe0b56d5756fbc868`.
It was used only for static analysis. Selected evidence is retained in ignored
`analysis/context-help-producer-20261106.rea.json`; REA is closed. Original
identity and file ranges are in
`reconstruction/context_help/provenance.json` and the reused dependency proof.

Two failed attempts remain in ignored build history: the first ASM binding
assumed the wrong CRT symbol spelling; a fixed-signature C adapter resolves
that ABI explicitly. The first DOS negative fixture expected the memory-stage
error for a zero pointer, although the existing parser rejects it earlier.
The final low-segment fixture reaches the intended memory check. Neither
failure was addressed by relaxing product checks.

Reproduce in fresh output directories:

```sh
./tools/dev --command python standalone/build_context_help.py --output build/context-help-new
./tools/dev --command python standalone/check_context_help.py --build build/context-help-new
./tools/dev --command python standalone/test_context_help_dos.py --build build/context-help-new --output build/context-help-new-dos
./tools/dev --command python standalone/test_context_help_cold.py --build build/context-help-new --output /tmp/pcplus-context-help-new
```

The CPU check's optional `--original` adds the separate analyst audit and
requires the ignored, hash-matched original. Ordinary builds and tests do not.

## Remaining application work

The child is a controlled ABI probe, not a production PCHELP replacement. It
bounds conventional-memory reads but trusts the diagnostic parent's identity;
production parent admission, integration with PROGRAM's active ownership,
context mapping, screen/mouse lifetime, navigation/search, error cleanup and
live receive/carrier behavior remain open. Existing resource-backed PROGRAM
notice help and authored F1 help remain separate maintained interfaces.

No terminal binary, selected physical package, remote files, modem/bridge
configuration or machine boot settings were changed. Global Help, hardware
acceptance and the rest of the full-parity inventory remain in the active goal.
