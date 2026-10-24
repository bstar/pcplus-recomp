# Character editing across the logical row

The later [field-aware checkpoint](WIDE_CHARACTER_FIELDS.md) adds protected
bounds, coherent attribute metadata and dispatcher preflight clipping. The
hashes and receipt below describe the preceding plain-cell checkpoint.

Plain ICH and DCH now work after the explicit132-column width transaction.
Previously the character controller required an80-byte logical stride, so
`CSI 3 @` and `CSI 3 P` silently returned without editing a wide row. Its
active-pane check also rejected the coherent80-column state produced when the
width transaction returned to narrow mode. Existing narrow behavior continues
to use the recovered helpers; the controller now admits either inactive or left
pane state when the viewport is disabled and its offset is zero.

The maintained wide owner first checks the real owned geometry through the
attribute/viewport admission. It accepts plain cells only: attribute wrapping
and protected-field checking remain bounded refusals. It merges the current
physical80 cells into the selected logical row of the owned shadow, shifts the
bounded suffix of that132-cell row, fills the vacated cells, and repaints the
same physical pane. The operation changes neither the logical cursor nor the
pane selection. Hidden columns stay part of the same edit. No allocation or
foreground UART polling occurs, and no near data reservation is added.

The parser retains repetition ownership. Each helper call edits one unit;
positive counts are clipped to the remaining row, and signed high-bit counts
keep the existing one-unit policy. Double-width line flags select two-cell
units and require an even cursor and a complete pair. Insert fills with the
attribute at the insertion cell; delete fills with the normal attribute. The
pending-wrap latch clears after an admitted edit. Unsupported layouts bound the
outer repetition to one and leave video, shadow and metadata untouched.

## Memory admission

The new code increases the branded transaction parent's minimum allocated
module from404848 to405232 bytes. That384-byte increase initially prevented
nested source compilation: the ASPECT parent returned error5 before producing
LOGON or NEXT bytecode. The failed pilot remains in
`build/width-character-chain-01`; it is not an accepted gate.

ASPCOMP now builds with Open Watcom's `-os` size optimization. The same24576-byte
stack,256-byte borrowed metadata tail, grammar, source line and node bounds are
retained. The executable decreases from52118 to50582 bytes,1536 bytes smaller.
The new compiler is
`ae0fe208df788b0b3023d723d80afb02443d36751c6bee301402b7eec321b142`.
Chained compilation then passes under the larger parent. The compiler corpus
and checked CLI/API/fault builds use the same size policy; this is not a change
to accepted source or publication semantics.

## Evidence

The [receipt](validation/wide-character-edit.json) binds a fresh declared-source
rebuild and replay. The source proof's ordinary terminal is
`081457b0836fbf940aa41c12cf10cced9f02dec0ae5d60b34d15a3380d9ac75f`,
the base transaction is
`1f4be2184504e33613da0d6f11ba87c5dc6b6bd1a7e0c6d3f5a704c0d9708ab3`,
and the branded transaction is
`f573f754400789182548d962b3ae89bc6929cd03e97e536d7e84fa02836caaf8`.
The recovered instruction files and flat UART source are unchanged.

Each transaction parent executes160 independent plain line/scroll cases after
an actual width transaction: NETWORK IL/DL, IND, RI and LF with restricted
margins, both profiles and panes, and1/5/24/25-row layouts. These cases confirm
existing plain scrolling behavior; they do not certify protected scrolling.
The character suite adds528 parser-driven edits, double-width cases, signed
counts, both sides of column80, status/shadow/metadata canaries, cursor and
callee-register/DF checks, two narrow-return cases and12 bounded refusals.

Four additional cases per parent inject the actual root UART ISR during the
shadow move while DS names the shadow and SS remains root. Insert runs with
DF set for the backward move; delete runs forward. All512 binary input bytes
must remain exact in the root RX ring, and the helper must restore DS=SS and
clear DF. These are hardware-model interrupts, not physical UART timing.

All nine existing80-column character groups repeat, including protected cells,
marker repair, count clipping, double width, HTS and arbitrary caller ES. The
previous live-width ownership/rollback model repeats too. Four DOS8086 witnesses
cover base/branded parents with visible or hidden status: unmodified MZs,
explicit API calls from real startup geometry,132-column parser output, edits
across pane boundaries, exact logical screen/CPR, and restored hardware/vector
snapshots. The optional observer supplies the explicit call, not a peer request.

The source proof also rebuilds the unchanged ASPECT children and optimized
compiler, checks all2043 compiler cases,18 deep checked CLI cases,16KiB checked
API and24KiB checked CLI/fault stacks with overflow controls, borrowed workspace
ownership/fault tests, and all four nested source workflows. Explicit source,
ASX fallback, chained execution/state retention and rejected source recovery
must all pass; the explicit case preserves32 preexisting logs.

```sh
./tools/dev --command python3 standalone/prove_width_edit_source.py --output build/UNIQUE_WIDE_EDIT_PROOF --nested
./tools/dev --command python3 standalone/record_width_edits.py --proof build/UNIQUE_WIDE_EDIT_PROOF --output docs/validation/wide-character-edit.json
```

The accepted source run is `build/width-character-source-01`. Product manifests
for the ordinary, cold-only, base/branded transaction terminals, both ASPECT
children and compiler must be current before invoking it. The proof starts with
no build products in its fresh tree and verifies source hashes again afterward.

Normal peer width requests remain unbound. Wide protected-field character
editing, protected scrolling, wider HTS/UI/ASPECT/modal composition and an actual
width-changing BBS session remain open. The new transaction build is excluded
from the staged/card package, and no physical modem or card acceptance is claimed.
