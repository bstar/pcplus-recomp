# Multiline ANSI reference checkpoints

`standalone/test_ansi_multiline_dos.py` extends the independent ANSI comparison
with cumulative editor-like input. Each checkpoint starts the unchanged DOS8086
application, replays the complete prefix through its actual UART, waits for its
real cursor-position reply, holds further input and captures video after normal
Alt-X exit. It compares all 1,920 character/attribute pairs with pyte's 80×24
CP437 projection. No product RAM, parser replies or return paths are supplied.

The sequence fills all 24 rows, establishes margins at rows 5–20, scrolls
forward through more lines than fit in that region, reverse-scrolls at its
top, inserts/deletes lines, edits characters, wraps through the bottom margin,
uses origin-relative addressing and restores full-screen scrolling. The last
three checkpoints repeat movement with colored rows, line edits and wrapping,
checking that attributes travel with their characters. Full-screen comparison
also checks that content outside a restricted scrolling region survives.

Both seven-byte and byte-at-a-time delivery use the same cumulative prefixes.
The latter exercises parser state across fragmented parameters and escape
sequences. Every checkpoint additionally checks normal DOS exit, the visible
status help label, unchanged settings and exact before/after UART/PIC/vector
state. The runner freezes its source hashes and all ten package files before
execution and verifies that they remain unchanged afterward.

The measured runs contain 22 native checkpoints: eleven prefixes with each
fragment size. The first ten prefixes agree exactly with pyte, including the
cursor. The final prefix disagrees in 79 blank foreground attributes and the
cursor, identically with both fragment sizes. Those raw runs deliberately exit
with failure; their reports and input streams remain acceptance evidence for
the unresolved differences, rather than being discarded or changed to pass.

A second independent implementation, [libvterm 0.3.3](https://www.leonerd.org.uk/code/libvterm/),
checks the same saved inputs through a separate Linux-only C projection adapter.
It comes from `libvterm-neovim` in the existing pinned Nixpkgs revision; the
similarly named `libvterm` package is a different library. Its shared-library
and header hashes are recorded. No parser/scrolling implementation is copied
into the adapter, and unsupported glyphs/styles/colors refuse conversion.

Libvterm agrees with every actual cursor, including the final `(1,1)` after
`CSI r`. The [original DECSTBM documentation](https://vt100.net/docs/vt510-rm/DECSTBM.html)
also specifies returning to the first column and line. Pyte's no-parameter
`set_margins` path returns without homing the cursor; its final `(19,2)` is a
reference limitation for this input. No PCPlus cursor change is indicated.

The final blank cells have VGA attribute `0D` in DOS, `05` in libvterm and `07`
in pyte. Glyphs and background colors agree at every checkpoint in both
references. The differing bytes are foreground/bold attributes on spaces;
this observation is recorded separately and does not turn raw mismatches into
exact agreement. They establish neither a confirmed visible defect nor full
attribute conformance. Application bytes are unchanged pending further
behavioral requirements; there is no renderer fix or closed rendering gate.

Run each variant into a new output directory. The final raw pyte discrepancy
above produces exit status 1 and a complete report:

```sh
./tools/dev --command python3 standalone/test_ansi_multiline_dos.py \
  --package build/special-status-geometry-final-20261031 \
  --output build/YOUR-MULTILINE-LABEL
./tools/dev --command python3 standalone/test_ansi_multiline_dos.py \
  --package build/special-status-geometry-final-20261031 \
  --output build/YOUR-BYTE-LABEL --fragment 1
./tools/dev --command python3 standalone/audit_ansi_multiline_references.py \
  --capture build/YOUR-MULTILINE-LABEL --capture build/YOUR-BYTE-LABEL \
  --output build/YOUR-REFERENCE-AUDIT
```

The second command-line tool validates saved evidence without running DOS.
Successful evidence validation reports `evidence_valid: true` separately from
`exact_reference_agreement: false`; its process exit does not assert rendering
acceptance. It checks exact cumulative input, captured pyte expectations,
single real CPR, native completion, status and hardware preservation before
recording both references' raw comparison results. No normalization is applied
to the actual or reference cell bytes.

The [validation receipt](validation/ansi-multiline-reference.json) records
checkpoint results, input/screen hashes, source identities and package identity.
The earlier [primitive comparison](ANSI_REFERENCE_GEOMETRY.md) and
[stock BBS snapshots](SYNCHRONET_SCREEN_REFERENCE.md) retain their own scopes.

This measures selected intermediate semantic states by complete-prefix replay,
not every frame of one continuous session. It does not establish actual BBS
multiline navigation, all timing/chunking patterns, non-ANSI profiles, font
pixels, sustained pressure, file transfers or physical modem acceptance.
Pyte remains an independent Linux/VT-style reference, not the specification for
every PCPlus emulation. Application/package bytes and the removable card are
unchanged; only owned loopback connections and ignored test storage are used.
