# Live static-shadow viewport

The interactive terminal now binds its recovered cursor's pane-switch services
to the recovered viewport copy, with a maintained admission owner over the
existing static far shadow. The [receipt](validation/viewport-live.json) verifies
the changed default application. This is a live renderer component integration;
normal peer width requests still stop at the explicit width boundary.

`src/terminal/viewport_live.asm` keeps short resident entries and runs admission
and pane operations in `ASPECT_CODE`. `viewport_rows` and
`viewport_physical_columns` alias existing live geometry words; no new near
data is allocated. Native copy/switch instructions use the declared owned
8,192-byte shadow and retain the separate maintained DS correction. Far
callbacks reach the ordinary resident CGA helpers with the application's DS.

Admission requires the inherited DS=SS ABI, IF enabled/DF clear, initialized
profile4/6 state, mode3/page0 with80 physical columns/25 BIOS rows,132 logical
columns, coherent pane/stride/region metadata, declared near-plane pointers,
the exact static shadow pointer and a disabled CGA retrace port. A visible
status row limits logical pane copying to24 rows; a hidden status permits25.
Modal UI, program, transfer and other competing screen owners refuse before
copying. The live enter/leave entries also require an actual transition from
the other pane: a redundant native restore could otherwise replace current
visible edits with stale shadow data.

Capture's paired error-refresh token remains independent. The shared refresh
service consumes that token first; otherwise it admits the pane commit. Panning
does not repaint the unchanged physical status row. Cursor offsets are not
validated halfway through the recovered cursor's own commit, when it has
updated pane metadata but has not yet updated its cursor offsets.

## Evidence

The real linked application passes80 cursor transitions and60 parser
output/erase cases across profiles4/6, logical heights1/5/24/25 and supported
visible/hidden status layouts. An independent logical-screen model checks
overlapping pane saves/restores, actual cursor/video/attribute offsets and the
entire shadow. Printable characters and full logical-row erasure execute through
the real UART/parser. The protected status row, existing receive data and callee
ABI remain intact. Every observed viewport hardware callback has the owned DS.
186 invalid geometry, backing, ownership, BIOS, FLAGS and redundant-transition
cases refuse before a copy. Capture refresh-token consumption is checked
separately.

An unchanged DOS8086 terminal passes a declared test-only132-by-24 geometry
fixture. A TSR seeds that state at one BIOS cursor boundary; it patches no
product code. Subsequent serial bytes use the real parser, output, erase,
cursor and BIOS pane copies. An independent final logical-screen comparison
checks characters across columns79/80/131, a complete132-column row erase,
the far-shadow tail guard, a real column132 cursor report and return to the
left pane. The canonical connection test confirms unchanged configuration,
initial banner handling and all42 sampled hardware bytes. This is not a normal
configuration path for enabling wide mode or a vendor BBS session.

405 declared source/test files reproduce the application exactly and replay
the same linked viewport oracle in a fresh tree. Removing only
`VIEWPORT_PRESERVE_DS` produces a different executable that fails on a foreign-DS
hardware callback; the build and failing replay are retained. The diagnostic
glob counterexample also remains checked. No original executable, existing
object or REA database is an input.

The final default terminal SHA256 is
`cd7aa3cec0c689bb8f3406b89efa5333aaededb4c3845d66a7f241b37bf88137`.
Its near data/stack remains65,440 bytes. Existing512 attribute cases/192 field
repairs,480 logical-plane kernel cases, seven RIS groups,24 callback cases and45
layout controls also pass on this exact image.

## Reproduction and remaining scope

```sh
./tools/dev --command python3 standalone/build_terminal.py
./tools/dev --command python3 standalone/check_viewport_live.py
./tools/dev --command python3 standalone/test_viewport_live_dos.py --label UNIQUE_PANES
./tools/dev --command python3 standalone/prove_line_metadata_source.py --viewport --output build/UNIQUE_PANE_SOURCE
```

Use `standalone/record_viewport_live.py --proof ... --dos ... --output ...` after
the existing attribute/metadata/RIS/callback/layout regressions. The pane oracle
is included in the ordinary test and application-component source workflows.
The earlier DOS pilot remains evidence for its earlier image; the final DOS
repeat includes the redundant-transition guard.

Width request/reset ownership, general132-column field-repair admission,
scrolling and broader display operations, snapshots/local menus, shared script
renderer/child lifetimes, BBS width workflows, current branded package checks
and physical display/modem acceptance remain open. No package or card file was
replaced, and no complete compatibility or application gate closes here.
