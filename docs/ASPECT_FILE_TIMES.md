# ASPECT file date and time

The maintained compilers and production DOS interpreter now support GETFDATE,
GETFTIME, SETFDATE and SETFTIME. That checkpoint implemented100 of215 opcode slots
and rejected115. [DOS system queries](ASPECT_SYSTEM_QUERY.md) extend it to103/112.
All whole-application gates remain open.

```text
string date_value,time_value
proc main
setfdate "DOWNLOAD.ZIP" "03-07-93"
setftime "DOWNLOAD.ZIP" "13:45"
getfdate "DOWNLOAD.ZIP" date_value
getftime "DOWNLOAD.ZIP" time_value
if success
message date_value
message time_value
endif
endproc
```

Getters require an atomic path and writable string destination; setters require
an atomic path and string value. A single comma may separate the arguments.
The original compiler's 108 authored cases establish 38 exact accepted ASX outputs
and 70 rejections, including locals, parameters, registers, builtin inputs and
the 80-character boundary. The full actual8086 DOS compiler passes1,772 cases:
956 exact accepted outputs and816 rejections.

The native common handler opens the file in binary read-only mode and reads its
DOS timestamp through AX5700h. Date output uses `%2u-%.2u-%.2u`: a single-digit
month has a leading space, for example ` 3-07-93`. This differs from enumeration's
presentation getter `$FDATE`, which skips that space. Time output is HH:MM.
The date setter splits fixed positions2 and5 and interprets a year00..79 as
2000..2079, and80..99 as1980..1999. The time setter splits position2 and discards
seconds. SETFDATE preserves the old complete time word, including seconds;
SETFTIME preserves the old date word. Neither native parser validates a calendar
or separator character; malformed strings retain native decimal-prefix and
16-bit packing behavior. Do not treat these commands as a date validator.

Comparison reports only whether the file opened:0 for an open file,1 otherwise.
On failed open the second operand is still consumed, and a getter preserves its
old output. The original core ignores DOS get/set and close error results; this
maintained integration retains that policy rather than claiming a stronger I/O
status contract. Component tests explicitly characterize those ignored results.
Physical/filesystem-wide error behavior remains unverified.

REA/Ghidra identifies390 exact native instruction bytes for four wrappers, the
common handler, two parsers and DOS timestamp helpers. Another87 bytes reuse
the already recovered decimal CRT. Source-only builds consume assembly and
numerical provenance, never original executables or REA databases. The507
component cases and a separate matching original-byte replay cover all00..99
year pivots, hour/minute samples, malformed/short/80-byte inputs, destructive
parse offsets, getter formatting, open failures and raw DOS/close results.
String/stdio/formatting/kernel boundaries are explicit component models.

The runtime supplies a separate temporary FILE owner with the native eight-byte
prefix and descriptor at offset7, adapting the actual Watcom stream to the native
handler. It never consumes one of the six numbered script slots. Close retires
the owner before fclose; final unwind also closes an owner left active by a late
operand/read error. A new outer invocation resets this owner; EXECUTE continues
to use the common interpreter lifecycle.

Two maintained adaptations are explicit under `ASPECT_FILE_TIMES_RUNTIME`:

- Getters select writable destinations and flush far-global writeback, including
  unchanged values after failed open. The original source-reader loses far-global
  results, just as the earlier GETFATTR wrapper does.
- Setters parse a private, zero-initialized81-byte copy of at most80 input bytes.
  The original parser overwrites separators in local, parameter, register and
  readonly-builtin backing strings. The copy preserves those inputs while keeping
  the native parser's valid-field conversion and year pivot.

An actual DOS native-core control uses the same real stdio/prefix adapter and
original shared handler, and passes28 characterization checks: far globals stay
OLD, local/parameter/register inputs truncate to their first field, and `$FDATE`
backing truncates too. The maintained variant produces getter results and
preserves all those inputs. This is an explicit behavior correction, separate
from exact native-byte comparison and broader original CRT equivalence.

The full8086 DOS VM passes248 invocations and2,901 assertions in one process.
Real kernel reads verify1980/1999/2000/2079, leap day, preserved opposite fields,
seconds preservation/truncation and readonly-builtin inputs. Other cases cover
missing files, six occupied streams, EXECUTE continuation, and truncated/invalid
destinations after fopen. Used near/far heap blocks and the inherited handle table
stay identical after warmup; INT0/FLAGS/ABI restore each time. File bytes remain
unchanged. A production ASP CLI child compiles and exercises the same four commands.

A real terminal child gates login on the date/time roundtrip and returns to working
parent input. ENiGMA `--timestamp-login` includes the earlier query, enumeration
and attribute probes, then requires the exact ` 3-07-93|13:45` trace from the
DOS-compiled timestamp calls before authentication. All21 checks pass, including the custom search/index/DIZ/NFO route afterward. It uses an isolated patched owned board and
generated files; live decoder installation, actual catalog and physical modem
validation remain separate requirements.

```sh
./tools/dev --command make test-aspect-file-times test-aspect-file-times-compiler
./tools/dev --command python3 standalone/test_aspect_file_times_dos.py --label unique-times-run
```

The [validation record](validation/aspect-file-times.json) binds native/compiler,
actual native-control/VM, parent, ENiGMA, package and250-output clean source rebuild
evidence. The279 attribute/310 enumeration/155 query/341 stream regressions remain
passing against these same binaries.
Remaining ASPECT families/recorder and complete application UI, settings, other
emulations/protocols, Host and hardware requirements are still open.
