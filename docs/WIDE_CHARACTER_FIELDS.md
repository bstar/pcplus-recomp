# Field-aware character editing

Wide ICH/DCH now preserve the logical attribute planes, respect field boundaries,
and repaint surviving fields when deletion removes a marker. This extends the
[plain wide character checkpoint](WIDE_CHARACTER_EDIT.md). The normal peer width
request remains unbound; the explicit width API still requires plain input.
These edits apply to field modes enabled after entering the wide layout.

Protected checking scans from the cursor to the next marker or protected cell
(flag mask `0x81`), including the final logical column. An edit ends before that
cell. A current protected cell or a field with no complete one-/two-cell unit
is a bounded no-op. Both video and metadata outside the admitted field/row remain
owned by their existing contents. Protected checking leaves metadata fixed;
attribute-wrapping mode without protected checking moves metadata with the text.

For wrapped metadata, insertion/deletion shifts each flag and value cell with
its corresponding video cell. Vacated cells retain their values/marker bits
and clear the protection bit. Two-cell units keep both metadata cells together;
this is a maintained coherent-pair policy, rather than copying the native
helper's single-byte metadata shift for double-width video. Deleting a marker
invokes the real checked native mode2 repair, including hidden columns and
following rows up to the next field boundary. The cursor and pane are preserved.

## Repetition before mutation

The dispatcher always makes a final helper call after its repetition loop.
Clipping a request inside the first helper was too late when a field allowed
only one unit. A three-unit request in a three-cell double-width field edited
twice and erased the surviving cell. Both80- and132-column character controllers
now preflight the count before the dispatcher enters that loop. Helpers retain
their own validation for direct callers. The live-only hook uses
`TERMINAL_CHARACTER_PREFLIGHT`; ordinary CSI diagnostics and flat recovery do
not enable it.

The ordinary protected controller also checks complete pairs against the actual
field span. A pair cannot cross a protected marker merely because it would fit
the physical row. Invalid states keep a bounded no-op, and the unsupported-repair
error contract is retained.

The shared ordinary admission body now runs in ASPECT_CODE behind the same near
API. Keeping it resident caused the branded splash plus the near bank to cross
a code-segment layout boundary. The memory inspector rejected the resulting
shared/nonzero ASPECT frame. Moving the argument-free admission body restores
an independently addressed far bank without changing its return flags or error
ABI. The branded parent has420 bytes of resident code space remaining and a
405632-byte minimum allocated module. Its extra code still passes the nested
compiler gate with the unchanged size-optimized compiler.

## Validation

The [receipt](validation/wide-character-fields.json) binds a clean declared-source
rebuild of the application products and the separate CSI diagnostic.
The ordinary terminal is
`9bb862f3ad6491ca9678fce07dea6cc55c7aa8a0d0e93809d874f232853553ec`,
the base transaction is
`5c0e54a08ce1e228fbe97cb7a05f1cd1a73698b0c45240121b7a3eaa2d6a69ed`,
and the branded transaction is
`746478e8d2998b28a76eadf2cf0443e98b523bbb63e5f64fce1448e700af3779`.

Each parent checks1296 field cases through the actual parser,2144 admitted
edits,136 native repairs and416 blocked edits. The independent logical oracle
covers both profiles, both panes,1/5/24/25-row ownership, markers at/current/near
and final-column boundaries, and one-/two-cell units. It compares all video,
4096-byte flag/value planes and shadow/status canaries. Twelve additional cases
exercise wrapped/protected editing after returning to80 columns with the
recovered active-pane flag still set.

The ten ordinary character groups include an explicit paired-field clipping
regression. Existing repair925 cases and bounded line-plane512 cases repeat.
The plain wide editing, foreign-DS UART interrupt and live width rollback
models repeat on both parents. The flat CSI image remains exactly2018 bytes at
`3a1524f4c69e7e9da59fd67babc99c94dfdcff097c337dfd79f198705f4535b5`;
three independent code/data relocation placements exercise its jump tables,
indexed parameters, cursor commands and DS string pointers without originals.

Four DOS8086 witnesses cover base/branded parents and visible/hidden status.
A declared observer seeds field flags and values only at an explicit late
cursor marker, after the normal banner and character-edit stream. Actual parser
DCH removes the first field marker and repairs the field across column80.
The exit observer compares the exact logical screen, metadata flags/values,
CPRs, DS=SS and the42-byte hardware/vector snapshot. The product MZ is unmodified.
An early fixture accidentally activated during ordinary row rendering; that
failed pilot remains in `build/width-fields-dos-base-02`. The accepted fixture
requires the exact logical cursor and root DS before seeding.

All four nested source workflows must still pass under the larger branded
parent. ASPECT and ASPCOMP sources, build flags and exact products are unchanged,
so the compiler grammar/stack/workspace evidence is inherited from the prior
receipt after checking every compiler input hash. The compiler is rebuilt from
source and the new parent repeats explicit/fallback/chained/rejected-source
admission; this does not claim a new grammar corpus run.

```sh
./tools/dev --command python3 standalone/prove_width_fields_source.py --output build/UNIQUE_FIELDS_PROOF --nested
./tools/dev --command python3 standalone/record_width_fields.py --proof build/UNIQUE_FIELDS_PROOF --output docs/validation/wide-character-fields.json
```

The accepted run is `build/width-fields-source-02`. Current ordinary/cold/base/
branded terminal, CSI, ASPECT and compiler manifests are prerequisites. Only
source inputs are copied into the initially build-free proof tree; no original
or prebuilt executable enters a build.

Width changes while field modes are active, protected scrolling, full keyboard/
UI/ASPECT/modal composition, and a width-changing BBS session remain open.
The card package has not been changed. Physical modem and machine acceptance
remain unverified.
