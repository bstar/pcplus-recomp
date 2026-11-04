# ASPECT admission for larger terminal frames

The optional `--aspect-row-owner` extends the shared ASPECT parent renderer's
admission and per-control/command preflight to coherent28/43/50-row narrow text
layouts. It requires the existing external renderer, full-height PROGRAM owner
and composed canonical row owner. This is a parent-admission component; it does
not yet certify larger-height scripts or enable normal Ctrl--/startup preferences.

At larger heights, the policy checks the BIOS data area's supported physical
height against `ui_window_rows`, requires80 logical columns, and executes the
existing pure `terminal_row_status_layout` far helper. That helper verifies the
accepted canonical row count, last row, visible/hidden status, status stride and
physical-bottom offsets. The existing renderer checks then enforce cursor,
origins, cell counts, history/keymap/pointers, parser depth and owner exclusions.
Logical cells must fit the4096-cell metadata planes. The existing25-row
logical-wide contract remains available; larger logical-wide layouts are refused.

The policy retains its read-only contract: no BIOS/DOS/device IO, scheduler or
nonstack state mutation. The shared row/status helper only reads canonical state.
The code lives in the existing ASPECT_CODE bank; resident CS and near data/stack
sizes remain65372 and65104 bytes. No original-binary recovery claim is made for
this maintained admission policy.

## Evidence

The [receipt](validation/aspect-large-rows.json) binds exact images/manifests,
checkers, raw results and independent source-only rebuilds.

-223 actual linked CPU inputs execute the policy and real canonical row/status
 helper.160 cover all four heights, both status layouts, profiles4/6, disconnected
 state0/connected state6, admission and scoped preflight at parser depths1/16.
63 negative cases cover mismatched physical/canonical height, status/stride,
 cell capacity, cursor/metadata offsets and unsupported BIOS heights. Registers
 and DS=SS cdecl frames are checked; writes are restricted to the caller's stack.
 BIOS/DOS/UART setup boundaries are modeled, not the product policy/helper.
-The disabled control passes the same160 coherent-layout inputs, accepting25-row
 layouts and rejecting larger heights as before. It remains byte-identical to
 `e05186fee47c9ae0273dbe692d337d9cf7500202694709209a577e69d9faf59b`.
-Eight actual DOSBox-X8086 geometry observations cover25/28/43/50 physical rows
 in the normal and exclusive-output workflows. Each runs the real admission,
 control and command preflight after the real row transaction establishes the
 BIOS/canonical layout. A diagnostic far adapter borrows then restores suspended
 script state; it does not execute an ASPECT child. Visible status only is used
 in these DOS cases. Existing shared-view/PROGRAM diagnostics, synthetic PRM
 preservation, zero virtual serial output,42-byte sampled UART/PIC/vector
 restoration and diagnostic package rejection also pass.
-Ordinary/disabled/diagnostic images reproduce exactly from569/569/571 public
 source files in empty trees without originals or ancestor Git, using pinned Nix.

The ordinary internal image is
`build/aspect-rows-accepted-20261104/ordinary/TERMINAL.EXE`, SHA256
`644c76d66e3a07118e278c00ddb94dccb26f02e1466645d7e18b8ef715f111bf`.
The diagnostic is
`b8af06431c4ec9852d8c2d7ff67ea16ca7f8b9312f15d969820471b86b538f21`.
It uses `--aspect-admission-probe`, implies the startup display diagnostic,
excludes editor probes and is rejected by application packaging. Never deploy it.

## Reproduce

Build each variant with the exact receipt flags via `./tools/dev --command python
standalone/build_terminal.py ... --output-dir build/NEW`. Run
`standalone/check_aspect_large_policy_live.py --terminal ORDINARY --output
build/NEW` and repeat against the disabled control, inside that pinned environment.
Run `standalone/test_display_rows_terminal_dos.py --terminal DIAGNOSTIC --output
build/NEW` for actual BIOS-established admission observations. Use
`standalone/prove_terminal_variant.py` for the independent source-only rebuilds.
Output directories must be new; exact flags and input hashes are in the receipt.

## Remaining work

The [actual session checkpoint](ASPECT_LARGE_SESSIONS.md) now covers profiles4/6
queries, RIS, cooperative windows/lower updates and parent return at all four
heights. Extend this to partial CSI, errors and carrier loss.
The cooperative script window still saves/paints/restores a25-row prefix; prove
that it preserves and refreshes the exposed lower live background. Nested native
PROGRAM currently admits25/43/50 ROM heights and explicitly excludes28; extend
and verify its14-pixel font restoration, SAVE/NOCLEAR/return paths before claiming
all larger-height script workflows. No child admission or renderer output follows
from a pure policy check alone.

Normal line switching/startup preferences, other fixed-height modal owners,
broader profiles/emulations, owned Enigma/Synchronet sessions and physical
Boca→SPA2102→SynthModem acceptance remain open. No installed application, bridge,
physical card, private settings/call history or deployment pointer changed.
