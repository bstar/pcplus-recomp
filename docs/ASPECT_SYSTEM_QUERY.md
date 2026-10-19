# ASPECT DOS system queries

Both maintained compilers and the production interpreter support DISKFREE,
DOSVER and GETDIR. The runtime now implements103 of215 opcode slots and rejects
112. The full application, compiler/recorder and physical modem gates remain open.

```text
long available
string folder,version
proc main
getdir 0 folder
if success
message folder
endif
dosver version
diskfree 0 available
endproc
```

GETDIR and DISKFREE take an atomic integer drive operand, then a writable string
or long destination respectively. Drive0 selects the current drive; other values
pass to the original DOS helpers. DOSVER takes one writable string destination.
One comma may separate two operands; expressions, parenthesized operands, wrong
types and readonly destinations reject. Global, local, parameter and string
register destinations are covered. The113 authored original-compiler cases
produce38 exact accepted ASX outputs and75 rejections. Both maintained compilers
match them. The complete actual8086 DOS compiler passes1,879 deduplicated cases:
989 exact accepted outputs and890 rejections.

## Recovered behavior and maintained correction

REA/Ghidra identifies167 exact instruction bytes across the three handlers and
four native helpers. Their source-only flat binaries match the original ranges
and hashes. Ordinary builds read source/numerical provenance and never originals
or REA databases. The3,782 component cases and matching original-byte comparisons
exercise drive words, current-drive selection, DOS return values, directory
prefixes, version formatting, arithmetic boundaries and the DS=SS near ABI.
Operand/format/DOS replies are explicit component boundaries; real DOS evidence
is separate below.

GETDIR replaces drive0 with the actual current drive, formats a drive-letter
prefix, then calls DOS47h into the remaining string buffer. It stores0 on success
or the raw DOS error in the comparison result and flushes the destination.
An invalid drive retains the newly formatted prefix rather than the old string.
It queries the selected drive's retained directory without selecting that drive.
Native drive-word/prefix arithmetic is preserved; this is not a drive validator.

DISKFREE uses DOS36h and returns FFFFFFFFh for its invalid-drive sentinel.
Otherwise it multiplies sectors-per-cluster by bytes-per-sector, **discards the
first product's high word**, then multiplies that low word by free clusters to
produce the32-bit result. A64KiB first product consequently becomes zero.
This native behavior is retained; the command is not a modern large-disk API.
DISKFREE does not update the comparison result.

DOSVER calls DOS30h and formats major/minor as `%d.%02d`. It also leaves comparison
unchanged. The original uses the source-string reader and fails to publish a
far-global result. The explicit `ASPECT_SYSTEM_QUERY_RUNTIME` adaptation selects
the writable destination reader and flushes it after formatting. Native flat
units and the baseline object retain the original behavior for comparison.

No new C stream/heap owner or numbered file slot is introduced. Formatting uses
the existing source-owned Watcom adapter; all four small DOS helpers are recovered
assembly. No terminal resident allocation or callback ABI changes are required.

## Actual DOS and application evidence

The actual8086 DOS suite runs341 interpreter invocations over31 same-process
rounds and passes2,899 assertions. It independently queries DOS for free-space
geometry and version, retains distinct C/D directories, checks current and
explicit-drive results, and exercises an unmapped E drive's error15 and prefix.
It covers far/local/parameter/register destinations, six held streams, EXECUTE,
all three commands' truncated/invalid destinations and repeated heap/JFT/INT0/
FLAGS/ABI restoration. A separate native-core executable passes14 control checks
while retaining `OLD-VERSION` in the global; the maintained version updates it.

The production ASP CLI compiles and executes the same commands. The terminal
parent test withholds login until its current directory, version and free-space
queries succeed, then runs the earlier file/timestamp/attribute/enumeration gates.
The timestamp suite still passes248 invocations/2,901 assertions and its native
control; the real directory mutation/drive-retention regression also passes.
The composed runtime passes1,113 cases/26,730 assertions, including all112 explicit
unsupported-slot checks.

Initial fixtures incorrectly treated DOSBox's built-in Z drive as absent and
misescaped paths in generated C. Corrected fixtures use unmapped E and canonical
paths; those failed attempts remain retained separately. These were fixture
failures, not changes to the recovered DOS error policy.

```sh
./tools/build test-aspect-system-query test-aspect-system-query-compiler
./tools/dev --command python3 standalone/test_aspect_system_query_dos.py --label NEW
```

The expanded isolated ENiGMA source-login mode adds GETDIR/DOSVER/DISKFREE to all
earlier file probes, writes `QUERY.LOG` before authentication and retains the
actual custom search/index/DIZ/NFO route. It requires a root C directory, a
well-formed DOS version and positive numeric free space in that trace. This is
a staged decoder/generated-catalog workflow, not installation on the live board
or physical RS-232 modem validation. The [validation ledger](validation/aspect-system-query.json)
binds current binaries and evidence, including the clean source rebuild.
All22 expanded ENiGMA checks pass. The refreshed DOS package matches the tested
binaries, and a fresh original-free snapshot reproduces258 normal outputs
byte-for-byte. The terminal's resident binary and64832-byte DS=SS layout remain
unchanged. No whole-application gate is closed by this checkpoint.
