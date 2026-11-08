# Full-interpreter GET width policy

Eight additional compiled-source cases now exercise width admission and the
[recovered status-line policy](ASPECT_GET_POLICY.md) through the full capability22
parent and experimental interpreter. They add runtime evidence for the existing
binaries; no application binary or installed package changes.

| Case | Observed editor width | Result |
| --- | --- | --- |
| Width omitted, ordinary row | 80 | LoC42 accepted; cursor row1,column27. |
| Explicit80 | 80 | LoC42 accepted; cursor row1,column27. |
| Explicit1 | 1 | A accepted with the full-field latch; cursor row1,column22. |
| Explicit0 | No editor input | Existing SEED preserved; no BIOS answer needed; cursor row1,column22. |
| Explicit-1 | No editor input | Typed operand error7; no trailing password. |
| Explicit81 | No editor input | Typed operand error7; no trailing password. |
| Default at row24,column76, status shown | 5 | LoC42 accepted; cursor row24,column80. |
| Same start, status hidden | 80 | LoC42 accepted; cursor wraps to row25,column1. |

Rows and columns in the table are one-based. The final two cases use the normal
PRM status-hidden preference and an incoming ANSI cursor position before LOGIN.
Only visibility differs in the configured policy. The native default-width
calculation clips the last available text row when the status line is shown;
a hidden status line allows the field to span the next physical row. This does
not reinterpret visibility as terminal autowrap.

For fields receiving keyboard input, the passive observer samples width from
the actual configured far GET field before admitting keys. That value is
compared with the prediction. The observer width word stays at its initialized
zero in no-input cases; it is not an independent field-absence sample.
Zero and refused widths complete without input injection; the exact output and
error checks distinguish no-op success from operand failure. Width admission
0..80 is the maintained runtime bound. Original compiler acceptance is broader;
these checks do not claim safe execution of oversized widths in the original.

All eight programs are compiled by actual DOS8086 ASPCOMP and match host output.
The matrix retains the existing exact wire/value/password, cursor, parent
file-table/sink/history, normal keyboard and hangup checks. Native exit identity
is0 for successful cases and7 for the two refusals. Fields which accept five
characters near the last column deliberately have different final cursors:
the width5 full latch stays on its last cell, while the width80 field advances
to the next row after five characters.

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD \
  --get-compiler-dir build/GET_COMPILER --policy-cases \
  --allocation-probe --output build/FRESH_WIDTHS
./tools/dev --command python standalone/prove_get_vm_source.py \
  --parent build/PARENT --parent-profile keymap --child build/GET_CHILD \
  --compiler build/DEFAULT_COMPILER/ASPCOMP.EXE \
  --checks build/FRESH_WIDTHS/checks.json --output build/FRESH_SOURCE
```

The isolated proof reproduces these eight cases and the previous nineteen GET
cases, along with compiler/serial/CLI/file/MZ checks. Exact source/report
identities are in the [receipt](validation/aspect-get-widths.json).

This covers ordinary mode0 string GET in the standard80-column,25-row view.
Other geometries, viewport origins, explicit field placement/masking in sibling
modes, status changes during an active field, other variable widths, floating
GET and full memory pressure remain open. Attached tests use DOS386/UMB,640KB
and a synthetic serial peer. They do not establish physical modem/BBS behavior,
ordinary8086 parent capacity, three-process compiler residency, package admission
or full ASPECT/application parity.

The first exploratory source tried an unsupported SET STATUS command. The test
now loads the actual PRM preference. An intermediate expectation copied the
shown-status cursor for the hidden80-column field; the recovered cursor adoption
and actual wire correctly wrap to row25,column1. Correcting the fixture did not
change application behavior.

The first isolated replay stopped before GET because its driver supplied both
storage and policy suite flags. Correcting flag selection required a new fresh
source proof; the failed tree is not acceptance evidence.
