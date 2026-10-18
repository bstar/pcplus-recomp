# Retained directory context

The terminal now retains the selected directory header/record and logical request
identity during startup. This supplies the original250-byte legacy dialing-code
table for later in-memory configuration staging. It does not reread a possibly
changed directory while connected. Running-terminal setup and commit/hardware
handoff remain unfinished.

`directory_live_read_context()` extends the maintained eight-argument reader
with an optional ninth near-cdecl context pointer. The existing reader delegates
with NULL and keeps its prior interface, read order and error details. Successful
validation commits the serial/modem/directory plans and the496-byte context:

| Offset | Bytes | Field |
| --- | --- | --- |
|000|2|Selected entry number|
|002|250|Original raw directory header|
|252|114|Original raw selected record|
|366|2|Literal0 / legacy1 code mode|
|368|64|Requested PRM path, NUL and zero padding|
|432|64|Requested directory path, NUL and zero padding|

Compile-time C checks and shared NASM constants bind this layout. Paths are
captured before any plan commits, including the compatibility case where path
storage aliases an ordinary output plan. Context overlap with paths, any plan
or result is rejected before I/O. Failed loads/validation leave all four outputs
unchanged. A directory reader returning a selection tag different from the
requested entry is rejected as RECORD before publishing plans or context.

The startup assembly passes the ninth argument and cleans18 bytes. The context
lives in near BSS under explicit DGROUP relocation. Its valid flag is cleared at
the start of configuration loading, set on successful directory decoding and
cleared if subsequent connection preparation fails. Non-directory/failed loads
do not expose old bytes as a valid selection. The retained record is separate
from the accounting baseline, which can change after a successful save.

`directory_live_context_matches()` is a pure logical request check: entry and
code mode must match, and path spellings compare with ASCII case folding. It
rejects malformed extents and unterminated/empty requested paths. It does not
normalize dot components, drive-relative paths, aliases, CP437 case variants or
CWD changes. Matching selectors are not a canonical filesystem identity or a
namespace lock. A live editor owner still needs to resolve/freeze its working
namespace and validate the active selection generation before applying changes.

Build and verify:

```sh
./tools/build test-directory-context test-live-configuration
```

## Evidence

The linked context suite passes507 inputs: all200 entries in both code modes,
exact raw headers/records/path padding, retained legacy-code decoding with no
reread after the modeled file changes, logical identity, file/semantic failures,
wrong selection tags, alias/extent guards and the actual startup path under all
CLI override combinations. Every interrupt and IN/OUT is forbidden; only the
explicit PRM/directory read boundaries are modeled. A stack hook enforces the
terminal's8KiB budget; kernel stack use is outside that measurement.

The standalone DOS diagnostic uses an8KiB stack and passes24 assertions against
real generated files. It compares retained selection bytes with a separate raw
reader, intentionally changes only the scratch directory's code header, observes
the old retained target versus a new fresh-read target, installs real accounting
updates, and checks complete-context/three-plan rollback on a truncated file.
The immutable source fixtures remain unchanged; only STATE.DIR is intentionally
modified and its exact header/accounting changes are independently checked.

A separate actual-terminal test dials a loopback modem using legacy AB codes,
then launches a source-owned PROGRAM/COMSPEC child. The child finds its parent
through the PSP chain, checks the parent MCB covers the context, snapshots all496
bytes, allocates/fills a disjoint16KiB DOS block and compares every context byte
again. The saved sample must match the independently generated header, record,
entry, code mode and paths. Actual modem commands/replies, deferred accounting
and final UART/PIC/vector restoration are checked independently.

The initial startup test caught the new BSS pointer being relocated relative to
its segment rather than DGROUP. The explicit group declaration fixes that
near-pointer error; the independent actual-terminal child also verifies the
correct retained bytes. No failed build/test is treated as runtime evidence.

Hash-bound summaries are in `validation/directory-context.json`; full current
terminal regressions and isolated source-only rebuilding remain separate from
individual CPU/DOS checks. No original EXE, private directory, public BBS or
physical modem is a test input. This closes context retention, not F02/F06 or
the complete PCPlus application goal.


The current terminal14bdd486 passes all45 terminal regression commands. The
context CPU replay observes4538 bytes of caller/callee stack with file I/O
modeled, and the real DOS diagnostic runs with8KiB. The isolated source checkout
reproduces60 byte-identical outputs. The current candidate diagnostic still
passes389 inputs; it is not yet linked into running-terminal setup.
