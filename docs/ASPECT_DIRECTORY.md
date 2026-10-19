# ASPECT selected directory expressions

The original2.01 compiler accepts eight read-only string builtins for the selected
114-byte directory record. Both the original compiler and actual original getter
instructions prove the following mapping:

| Identifier | String selector | Overlay16 getter | Record offset | Stored maximum |
| --- | --- | --- | --- | --- |
| `$D_LDATE` |0 |`DAA2` |61 |8 |
| `$D_KBDFILE` |1 |`DAA6` |95 |8 |
| `$D_METAKEY` |2 |`DAAA` |86 |8 |
| `$D_NAME` |3 |`DAAE` |0 |24 |
| `$D_NOTE` |4 |`DAB2` |105 |8 |
| `$D_PHONE` |5 |`DAB6` |25 |20 |
| `$D_PWORD` |6 |`DABA` |75 |10 |
| `$D_SCRIPT` |7 |`DABE` |52 |8 |

The compiler names **KBDFILE1 and METAKEY2 select offsets95 and86 respectively**.
Do not exchange them based on an interpretation of editor labels. Each original
getter consists of `MOV AX,record_pointer; RET` and returns an alias to the
selected record. The maintained module relocates those pointers to the owned
`aspect_directory_record` symbol. It neither copies nor transmits the strings.

The maintained runtime clears its owned record and selected entry before each
script, then copies an explicitly supplied directory snapshot. With no selected
entry, these builtins return empty strings and entry0. This is a maintained
default policy; the getter investigation does not establish original application
startup behavior when no entry was selected.

`$D_ENTRY` is integer selector3. Its original getter `D9B5` reads wordDS:e482;
maintained source relocates that word to `aspect_directory_entry`. The selected
entry is separate from the114 record bytes. `$D_BAUD` is long selector0. Its
original `DA59` getter uses record word46 as an index into the global DWORD baud
tableDS:3270; compiler support does not establish that table's runtime binding.
The baud vector remains explicitly compiler-only in this phase.

String operands encode as `6E selector`, integer operands as `6F selector`, and
long operands as `70 selector`. For example:

```text
string target
proc main
 target = $D_PWORD
endproc
```

The original compiler emits `01 CF AC 8C 00 6E 06 00 94`. Explicit
`TRANSMIT $D_PWORD` emits `00 CF BF 6E 06 94`. This proves a script can request
transmission; it does not establish automatic password transmission. All fields
in this investigation are authored synthetic bytes. No real directory,
credentials or PRM files are opened.

The complete retained builtin keyword group has22 string selectors. It has no
selected-directory username identifier. The four authored spellings
`$D_USERNAME`, `$D_USER`, `$D_PASSWORD`, and `$D_NUMBER` are rejected by the
original compiler. `$H_NAME` occupies separate string selector16; that name
alone does not establish a directory username service.

## Reproduction and limits

```sh
./tools/dev --command python3 standalone/build_aspect_directory.py
./tools/dev --command python3 standalone/check_aspect_directory.py
./tools/dev --command python3 standalone/test_aspect_compiler.py
# Optional explicit private original comparison:
./tools/dev --command python3 standalone/check_aspect_directory.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

The source-only component contains36 exact native bytes: entry4 and strings32.
Its checker exercises2056 CPU cases preserving registers, flags and return
stack, and16 actual8086 DOS cases checking OMF relocation, string aliases and
entry values. Optional original comparison verifies all36 bytes against the
SHA-bound original. A separate original replay exercised24 actual getter
bodies using empty, maximum-length and CP437 synthetic fields. That replay
supplies the selected record and near return stack; it does not execute the
original application loader or selector dispatcher.

The public authored corpus has45 original-compiler attempts:19 accepted and26
rejected. Eighteen vectors carry independent synthetic record/entry outcomes;
one baud vector is compiler-only. Cases cover assignment, MESSAGE, TRANSMIT,
concatenation, locals, parameters, empty and CP437 strings, reserved declarations,
destination misuse and operand type errors. Normal compiler/tests consume source
and the public frozen authored outcomes, never the private original executable.
Private reports, original compiler outputs and the corrected initial human
assumption about offsets1/2 remain under ignored `analysis/aspect-directory`.
This component is not a complete ASPECT compiler, complete directory editor,
application loader, renderer or whole-program compatibility claim.
