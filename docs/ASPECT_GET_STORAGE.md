# GET destinations across procedure storage

Seven additional full-parent cases now exercise compiled GET with local,
parameter and builtin string destinations. This extends the
[compiler evidence](ASPECT_GET_COMPILER.md) into the running experimental
interpreter. No application binary or installed package changes.

| Destination | Initial value | Edited value |
| --- | --- | --- |
| Local string | SEED | LoC42 |
| Local integer | 17 | -123 |
| Local long | 70000 | 65536 |
| String parameter | SEED | LoC42 |
| Integer parameter | 17 | -123 |
| Long parameter | 70000 | 65536 |
| Builtin S0 inside a framed worker | SEED | LoC42 |

Each main procedure sets a global integer guard to4321 and a separate global
string to GUARD, waits for LOGIN, sends GETREADY and calls the worker. Parameter
cases use the recovered `STRPARM`, `INTPARM` or `LONGPARM` declaration and ordinary
CALL WITH syntax. The worker owns local integer guards1234 and5678, performs
GET on the selected destination, checks both guards and transmits the edited
value. Main resumes, checks its global integer, and transmits `/GUARD` followed
by CR and the explicit directory password.

The exact wire confirms both destination writeback and procedure return. Integer
cases return cursor report row1,column26; string/long cases return row1,column27.
The passive observer admits BIOS input only after actual field configuration.
All seven cases retain the full parent file-table/sink/history checks, resumed
terminal keyboard input and clean hangup; child exit/error/file status are0.
The guards constrain accidental writes across the exercised storage; this does
not prove all frame layouts, aliasing or parameter semantics.

All seven complete ASX programs are compiled by actual DOS8086 ASPCOMP and match
host output byte for byte. GET declaration syntax is constrained by the earlier
frozen original compiler corpus; the new larger authored programs are not new
original-application execution observations. Parent `b25fe6d2…`, interpreter
`54590fd3…` and optional compiler `db9de7ca…` remain unchanged.

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD \
  --get-compiler-dir build/GET_COMPILER --storage-cases \
  --allocation-probe --output build/FRESH_STORAGE
./tools/dev --command python standalone/prove_get_vm_source.py \
  --parent build/PARENT --parent-profile keymap --child build/GET_CHILD \
  --compiler build/DEFAULT_COMPILER/ASPCOMP.EXE \
  --checks build/FRESH_STORAGE/checks.json --output build/FRESH_SOURCE
```

The isolated proof reproduces the seven exact cases and the existing twelve GET
cases: ordinary input/errors, repeated/EXECUTE, successful WHEN actions and
WHEN divide/cancel retirement. Compiler/serial/CLI/file/MZ checks remain part
of that proof. Exact source/report identities are in the
[receipt](validation/aspect-get-storage.json).

This covers one ordinary width10 field and one worker call per case. Nested or
recursive frames, local/parameter cancellation and event errors, numeric limits,
other S registers, floating GET, field policies beyond the
[eight width/status-row cases](ASPECT_GET_WIDTHS.md) and full memory/feature pressure
remain open. The attached tests use DOS386/UMB,640KB and a synthetic serial peer;
they do not establish physical Boca/SPA2102/SynthModem/BBS behavior, ordinary8086
parent capacity or three-process compiler residency. Package promotion and full
ASPECT/application parity remain open.
