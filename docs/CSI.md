# Combined ANSI reconstruction

The combined diagnostic links the recovered ESC entry, parameter reader,
parameter transition, complete CSI dispatcher, attribute helpers and cursor
routines, reporting core and erase services. The dispatcher contains 2,018
original bytes, 615 instructions and two
explicit word tables (48 SGR entries and 94 command entries). Analyst names and
interfaces are maintained source, not recovered original identifiers.

The flat dispatcher reproduces overlay 12 CS:e4b2..ec94 exactly. Provenance is in
`reconstruction/ansi/dispatch-provenance.json`; the original REA record is
`ev_5054c5700c911ddb639380e599bef490251714e34d8e56b6b3cc7c11b9667ba4`.
The explicit analysis script `analysis/recover_csi_dispatch.py` writes review
candidates under ignored `build/recovered-csi`; ordinary builds never run it or
read original binaries.

## Build and verification

```
./tools/build csi
./tools/build test-csi
```

`build/csi/CSI.EXE` is a source-only DOS self-check, not the full application.
`standalone/check_csi.py` drives real linked instructions with memory byte input,
records BIOS cursor calls and checks parser-to-screen state, SGR colors,
scroll/origin handling, replies, J/K/X video updates, malformed input and CSI-q
payload preservation.
`standalone/test_csi_dos.py` also runs the executable inside DOSBox-X. Manifests
and results record the exact executable hash under `build/csi` and
`build/csi-dos`.

Two jump-table operands and an indexed parameter operand require relocation
although ndisasm presents their original high addresses as negative offsets.
They use linker symbols in OMF; retaining the original displacements made the
combined program jump outside its rebuilt code. Exact flat-byte equality alone
could not catch that integration defect. Both jump tables and multi-parameter
SGR now execute in the linked diagnostic.

Maintained OMF mode deliberately bypasses the historical CSI-q payload read;
flat mode preserves it for comparison. The parameter reader also retains its
explicit length/count/numeric/timeout fixes. See `ANSI.md` for their boundaries.

Maintained CSI `X` also defaults omitted/zero counts to one and clamps the
erase rectangle to the remaining row. Original-dispatch replay demonstrated
inverted rectangles for omitted/zero counts and row overflow for large counts.
The optional `standalone/compare_csi_x.py` records six actual original rectangle
calls before rendering; it does not establish the BIOS response to invalid
rectangles. Combined source tests verify default, zero, 65535, oversized and
right-edge cases against video memory. The flat original path remains unchanged.

## Remaining application work

External application services remain explicit interfaces. Unrecovered services
trap with their original service address rather than silently succeed. Terminal
modes, tab handling, save/restore cursor, viewport/protected attributes, ordinary
character rendering, serial input/output and terminal-specific keyboard maps
still need complete application integration. Passing the diagnostic does not
establish a complete terminal, physical modem compatibility or full PCPlus
feature coverage; those requirements remain in `../PLAN.md` and `FEATURES.md`.
