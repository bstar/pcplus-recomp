# Wide field repair and navigation

Native field repair and attribute-boundary navigation now accept the live
132-column logical screen through the existing static-shadow viewport owner.
The [receipt](validation/attribute-repair-wide.json) binds the changed default
terminal to modeled, actual DOS8086 and fresh-source results. Normal peer width
requests remain disabled pending width/reset ownership and broader integration.

`attribute_plane_admit` retains its ordinary80-column checks and delegates a
132-column plane to the shared viewport admission. That proves physical video,
logical rows/stride, status exclusion, backing pointers, pane metadata and
foreground ownership before native repair writes. Whole-plane repair still
permits its own temporarily stale cursor offsets. Current-cursor admission
separately verifies logical bounds and attribute offsets, then computes the
physical video offset from the active pane and checks the visible column.
It does not confuse132-byte logical rows with160-byte physical video rows.

The recovered boundary, coordinate, repair, advance and write instructions are
unchanged. This adds maintained live admission around those instructions. No
near storage is added; the native buffers and near/far ABI remain owned by the
application.

The actual linked image passes:

- 360 repair cases across profiles4/6, logical heights1/5/24/25, supported
  visible/hidden status layouts, all five native repair modes, multiple field
  marker patterns and starting columns79/80 or the last logical cell. Both
  panes compare against an independent field oracle, including complete
  metadata planes/tails, video, shadow, receive preservation and callee ABI.
- 84 actual boundary searches in both directions, including circular wrap,
  pane edges and overlap. A separate circular-search and pane-copy model checks
  the destination cursor and complete backing without replacing native calls.
- Thirteen invalid current-cursor, pointer, pane, region and owner cases refuse
  before changing metadata, video, shadow or receive data.
- The existing925 ordinary live repair/consumer cases,512 bounded line cases,
  480 line-kernel cases, seven RIS groups, viewport cases and callback/layout
  checks pass on this same image.

The field oracle now accepts an explicit shadow origin. Its component fixture
continues to default to offset40h. The live snapshot begins at the application's
owned pointer, so its relative origin is0. The first wide comparison exposed
that fixture difference; native write inspection confirmed the pointer-relative
address before the oracle was corrected. Video matched in that comparison;
the discrepancy was the oracle's hidden-shadow origin.
The complete1,928-case recovered component suite also passes with its existing
40h-origin fixture, preserving that independent native comparison.

## Actual DOS consumer and source reproduction

The unmodified DOS8086 application runs a test-only132-by-24 viewport fixture.
The observer seeds a field boundary inside a restricted scrolling region, a
second boundary outside it, and a preceding value of1Eh. Serial CSI delete-line
removes the first boundary. The real line owner calls native repair, which
repaints only logical rows3..5 (zero-based) with attribute1Eh. The outside marker survives. Later
output/panning and132-column erasure still match the entire independent logical
screen; both4KB planes and their guard tails match exactly. Actual cursor
reports, return to the left pane, DS=SS and all42 sampled hardware bytes verify.
This explicit fixture enables wide state for testing; it patches no application
instructions and is not a normal configuration or BBS width workflow.

407 declared source/test files reproduce the executable exactly and replay the
same viewport, repair and navigation oracles in a fresh tree. The native width
diagnostic remains excluded from the application glob, and a build without the
viewport DS correction still fails the hardware-callback check.

The default terminal SHA256 is
`01f55dfbf5385136931c96700be3173cf8594be1c17677e9852fb0f1d025e447`.
Near data/stack remains65,440 bytes.

```sh
./tools/dev --command python3 standalone/build_terminal.py
./tools/dev --command python3 standalone/check_attribute_repair_wide.py
./tools/dev --command python3 standalone/check_attribute_repair_live.py
./tools/dev --command python3 standalone/test_viewport_live_dos.py --fields --label UNIQUE_FIELDS
./tools/dev --command python3 standalone/prove_line_metadata_source.py --viewport --wide-repair --output build/UNIQUE_FIELD_SOURCE
```

After the ordinary viewport/line/RIS/callback/layout checks, record matching
results with `standalone/record_viewport_live.py --wide-repair --proof ... --dos
... --output ...`. The wide oracle is included in ordinary test and component
source workflows.

Normal width/reset ownership, broader wide scrolling/editing/keyboard workflows,
local menus/snapshots, shared script renderer/child lifetime, BBS integration,
updated branded package checks and physical display/modem acceptance remain
open. The package, staged card payload and card are unchanged; no complete
application or compatibility gate closes here.
