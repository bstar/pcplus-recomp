# Scrolling with field metadata

Full-width LF, IND, RI and wrapped line editing now keep text, field flags and
attribute values together inside the actual scroll region. This extends the
[field-aware character checkpoint](WIDE_CHARACTER_FIELDS.md). Peer width requests
remain unbound; the explicit width API still admits plain input only.

Previously, wrapped LF shifted the whole metadata plane even when its video
rectangle covered fewer rows. IND and RI moved video without moving metadata.
A later protected character edit could therefore use a boundary left behind by
an earlier scroll. The live rectangle owner now moves both planes within the
argument rectangle, clears vacated flags and fills vacated values with the same
attribute used for video. Rows outside the rectangle retain all three planes.

Only full logical-width wrapped scrolls are admitted. A nonzero partial-width
wrapped request fails with typed error `2D98` before mutation. Zero-count clears
retain their existing ownership, as do unwrapped native operations. Signed
scroll counts are clipped to the rectangle height, including high-bit values.
The recovered video instructions remain unchanged behind provider-only symbol
aliases in the application build. The near `RET8` bridge and far callback retain
their exact argument order, cleanup and relocation contracts.

A retained marker begins its own field. Otherwise, the first surviving field
inherits the preceding attribute. If that differs from its moved value, the
actual native mode2 repair repaints the surviving prefix, stopping at its next
boundary or the end of the rectangle. Downward scrolling begins this check after
the new blank row. A single-row rectangle has no surviving prefix. The existing
skip-scan setting is honored.

The shared metadata mover takes explicit first/last rows and never changes
cursor globals. Native repair temporarily borrows row, column, attribute offset
and scan count, then restores them. The serial interrupt continues owning its
root receive ring during this synchronous scan. Admission checks the plane
backing rather than demanding stable cursor caches: the recovered wrap-forward
consumer sets column zero before its LF callback refreshes those caches.

Wrapped ORIGINAL IL/DL now use the same bounded line owner while retaining their
column-home behavior. NETWORK preserves the column. Plain ORIGINAL operations
and the original monochrome M wait retain their previous owners. A live-only
line preflight clips repetition before the dispatcher's unconditional final
helper call. The one-row regression uses a nondefault inherited fill so an
extra helper call cannot pass unnoticed.

## Evidence

The [receipt](validation/scroll-fields.json) binds an initially build-free,
declared-source rebuild: ordinary, cold-bank, base transaction and branded
transaction products, the CSI diagnostic and both ASPECT runners/compiler.
No original executable is a build input. The terminal identities are:

- Ordinary: `20fa7d618af822acbd953b593cadfa660b97f1c43ff43c8c196dabb9f840f6a9`.
- Base transaction: `dba259e999c4ce9cceb25b718babb3c154a9736e72e03e1f67ef475838f5fa2a`.
- Branded transaction: `e8d38d593599c1807b1b37e415ae0b75603f8d5e34d009064049b90499fe4581`.

Each transaction parent checks 1,344 cases and 240 native prefix repairs across
80/132 columns, both profiles, both panes, visible/hidden status, restricted/full
margins, checking/skip flags and both line policies. Independent logical oracles
compare video, hidden columns, all 4,096-byte flag/value planes and outside/status
canaries. Another 21 cases cover signed counted rectangles, 16 malformed
requests verify refusal before mutation, and four interrupts deliver 512 binary
bytes each through the real UART ISR while temporary repair bounds are active.

Ordinary checks repeat 925 repair cases, 516 line-plane cases, ten character
groups and eight line-policy groups. The four added line regressions count the
actual helper calls and preserve the nondefault one-row fill under both policies.
Plain wide editing and width transaction/fault models repeat on both parents.
The separate CSI image remains exactly 2,018 bytes at
`3a1524f4c69e7e9da59fd67babc99c94dfdcff097c337dfd79f198705f4535b5`;
three independent code/data placements exercise its relocated references.

Four DOS witnesses cover base/branded products and visible/hidden status. A
late observer marker seeds the field planes; a second marker enables protected
checking. The real parser deletes a marker, scrolls a restricted region in both
directions, then performs protected DCH on nonblank surviving text. The exit
observer compares the full logical screen and both planes, CPR, DS=SS and the
42-byte hardware/vector snapshot. Product executable bytes are unmodified.
These are DOSBox software checks, not physical-machine acceptance.

The branded parent requires a 406,256-byte allocated module and has 348 bytes
remaining in its resident code segment. Four nested compiler cases cover
explicit/fallback/chained/rejected source launches under this larger parent.
The compiler is unchanged at 50,582 bytes with its full reserved stack. Grammar,
workspace and stack evidence is inherited by exact compiler input/product hash
from the earlier receipt; this checkpoint does not claim a fresh grammar run.

```sh
./tools/dev --command python3 standalone/prove_scroll_fields_source.py --output build/UNIQUE_SCROLL_PROOF --nested
./tools/dev --command python3 standalone/record_scroll_fields.py --proof build/UNIQUE_SCROLL_PROOF --output docs/validation/scroll-fields.json
```

Current manifests for all products are prerequisites. Only declared source is
copied into the proof tree. The accepted run is `build/scroll-fields-source-01`.

Partial-width wrapped scrolling, width changes with fields already active,
keyboard/UI/ASPECT/modal composition at 132 columns and width-changing BBS
sessions remain open. The card package is unchanged. Physical modem connection,
flow control, reconnection and file-transfer acceptance remain unverified.

The later [active-field width checkpoint](ACTIVE_FIELD_WIDTH.md) adds bounded
plane reshape and private native repaint during explicit width changes. The
identities and limitations above describe this earlier scroll checkpoint.
