# GET across fields and EXECUTE

The full DOS parent/interpreter now passes two additional compiled-source
scenarios. This extends the [GET compiler checkpoint](ASPECT_GET_COMPILER.md)
with actual field retirement and script replacement. It adds evidence for the
existing experimental binaries; no application binary or selected package changes.

The repeated-field scenario performs four GET operations in one invocation:
string `A`, reuse of that destination with `B`, integer `-2`, and long `65536`.
The peer receives exactly `GETREADYB/-2/65536` followed by CR and the explicit
directory password. The passive observer records fresh native GET generations
1,2,3,4. The final cursor report is row1,column31, matching the field lengths.

The replacement scenario accepts string `A` and integer `-2`, changes BREAK to
1234, then executes a separately compiled NEXT.ASX. The target verifies the
retained integer and BREAK setting, transmits the new global string between
angle brackets, and accepts `B` in a new GET. The peer receives exactly
`GETREADY<>B`, CR and the explicit password. Observed generations are1,2,3;
the final cursor report is row1,column26. The empty brackets matter:
[recovered EXECUTE semantics](ASPECT_CHAIN_RUNTIME.md) release per-file global
strings and allocate fresh empty strings, while numeric/settings banks remain
invocation-owned. Execution never returns to the old script's trailing command.

All three source files are compiled by actual DOS8086 ASPCOMP and compared with
host output before execution. Input batches enter the BIOS queue only after the
passive observer sees the expected live child, configured GET field, valid
field cookie, empty queue and a new native generation. Later-field keys are
withheld from earlier fields. This exercises real field acquisition/retirement
rather than preloading all answers into a single field's keyboard interval.
Neither observer nor peer edits interpreter state or evaluates script commands.

Both scenarios retain the existing exact file-table/sink-owner checks, far
history checks, normal terminal-key resumption, parent cursor reports and clean
hangup. Child exit/error/file status are zero. The parent remains the full
capability22 keymap candidate `b25fe6d2…`; the GET interpreter remains `54590fd3…`
and optional compiler `db9de7ca…`.

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD \
  --get-compiler-dir build/GET_COMPILER --lifetime-cases \
  --allocation-probe --output build/FRESH_LIFETIME
./tools/dev --command python standalone/prove_get_vm_source.py \
  --parent build/PARENT --parent-profile keymap --child build/GET_CHILD \
  --compiler build/DEFAULT_COMPILER/ASPCOMP.EXE \
  --checks build/FRESH_LIFETIME/checks.json --output build/FRESH_SOURCE
```

The isolated proof repeats the two scenarios, compares exact wire and passive
observations, then repeats the six ordinary compiled/raw GET cases and the
existing compiler/serial/CLI/file/MZ checks. The
[receipt](validation/aspect-get-lifetime.json) binds sources and reports.
Compilation occurs before the full parent starts. The attached matrix uses
DOS386/UMB,640KB and an owned synthetic modem peer. It does not establish
three-process compiler residency, physical Boca/ATA/SynthModem/BBS behavior,
full memory co-residency, WHEN actions during GET, repeated cancellations,
local/parameter/S0 fields, floating GET or whole-language parity.

Earlier exploratory inputs are not runtime failures: one fixture used
unsupported string expressions in IF, another used a long FETCH destination,
and an intermediate expectation incorrectly retained a global string across
EXECUTE. The corrected scenarios preserve the recovered behavior.
