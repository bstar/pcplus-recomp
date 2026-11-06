# Full-frame SAVE at standard VGA row counts

The unchanged normal capability18 pair (`61757956` parent, `b61f3a03` ASPECT)
passes repeated nested PROGRAM SAVE at80 columns and25,28,43,50 physical rows.
Each workflow runs a real DOS child twice, leaves graphics mode13h active on
each return, and exercises six streams and missing-file recovery between calls.
Keyboard output, hangup, exact final body cells, private/staged inputs and the
42-byte UART/PIC/vector snapshot are checked afterward.

There are eight actual DOS runs: four normal8086 workflows without observers,
plus four separate386/XMS/UMB workflows with a passive inner screen observer.
The latter captures the complete physical frame and BIOS mode, geometry, font
height, cursor, cursor shape and page before/after each nested PROGRAM, before
the outer ASPECT return can repaint it. Both pairs match exactly at every size:

| Rows | Font height | Bytes per physical frame | Bytes compared across two pairs |
| --- | --- | --- | --- |
| 25 | 16 | 4000 | 8000 |
| 28 | 14 | 4480 | 8960 |
| 43 | 8 | 6880 | 13760 |
| 50 | 8 | 8000 | 16000 |

The observer allocates four bounded records appropriate to the selected row
count. The25-row executable is byte-identical to the preceding default observer.
For each size,36 assembled hook identity/ABI cases pass across DF/CF combinations,
and nine damaged captures are rejected. Controls include corrupting the final
character or attribute of a returned frame, covering the upper half of the
8000-byte case. These144 component cases and36 rejection cases are distinct
from the eight actual DOS workflows. The observer adds resident memory; its
UMB runs do not establish the capacity of the unobserved8086 workflow.

Reproduce with fresh output directories:

```sh
./tools/dev --command python standalone/test_aspect_heap_startup_dos.py \
  --terminal build/terminal-lease18-final-20261106/TERMINAL.EXE \
  --runner build/aspect-lease18-unwind-disabled-20261106/ASPECT.EXE \
  --nested-program --nested-graphics --display-rows 50 \
  --cpu 8086 --output build/rows50-save-repeat
```

For full inner captures use `--inner-screen --cpu 386` instead of `--cpu 8086`.
`check_snapshot_screen_watch.py --rows 50 --output build/rows50-observer-repeat`
repeats the observer component controls. Exact receipts are in
[`validation/snapshot-lease-rows.json`](validation/snapshot-lease-rows.json).

This is test infrastructure and evidence; no production executable, package
selection, physical installation or bridge is changed. Downloaded fonts,
nonstandard geometry, hidden-status composition, faults/cancellation at each
larger geometry and physical VGA acceptance remain separate requirements.
