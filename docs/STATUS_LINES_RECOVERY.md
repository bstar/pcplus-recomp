# Original status and line controls

The original normalized keyboard dispatcher routes Ctrl-] (WORD001D) to resident
46BA and Ctrl-- (001F, the menu's Ctrl-minus shortcut) to its inline1904 selector.
These paths belong to the existing1771-byte native keyboard recovery, not the
Alt-key scan table. The status handler123 bytes and its clear helper33 bytes
now rebuild exactly in flat form and assemble as relocatable OMF.

## Status visibility contract

The156 new bytes establish these operations:

- Capture whether screen last row CE3A and bottom margin CEE4 equal the old
  effective CSI bottom334A. Each field follows the change only when it matched;
  a custom margin remains unchanged.
- Toggle hidden WORD1D46: zero becomes1; every nonzero WORD becomes0. This is
  normalization, not bitwise inversion or a signed-positive test.
- Hiding uses runtime full rows7A74, sets effective count334C and maximum334A,
  then clears the status rectangle with the byte attribute D008.
- Showing uses runtime visible rows7A80. If the cursor is at/below that count
  under the original signed comparison, scroll once and request the new last
  row/current column before drawing status. Then update following margins.

The clear helper acts for any nonzero hidden WORD. It calls the rectangle service
with attribute, end coordinate, start coordinate and zero scroll count; the end
is coordinate base7A84 plus widthCEAE minus1. It does not define the color/pixel
meaning or validate malformed coordinates itself.

Runtime row fields are not inferred from zero-filled startup data. Fixtures
explicitly supply25/24,43/42 and50/49 full/visible rows. These are CPU inputs,
not proof those BIOS modes work on the physical card.

## Line-selector contract

Ctrl-minus uses a **two-selector cycle for configured video-mode WORD2070 zero**, or four
selectors for **every nonzero WORD**, including8000h..FFFFh. Current modeCEE6 is
interpreted as signed16-bit for IDIV. The requested selector is signed remainder
plus1. For legal nonnegative modes, it cycles1..2 or1..4. Corrupted negative
values can request zero/negative selectors; no input sanitization is invented
by this native proof.

The caller passes that selector, saved WORD1D4E and zero to DISPLAY2EAA. After
DISPLAY returns, it copies the **accepted** mode3252 back to currentCEE6. The
returned AX is not used as the committed mode. This distinction matters when
the display service falls back. The subsequent
[display-mode recovery](DISPLAY_MODES_RECOVERY.md) establishes the downstream
dispatch/font/row decisions using modeled BIOS effects. This earlier suite still
models DISPLAY at its boundary; it does not exercise that deeper implementation.

## Evidence

Fresh REA byte Evidence for status is
`ev_2f94ce8bfabdc384eebb9adeba43b091c7c3a5b22e13ba82ee1540854710d559`
with terminal RET4734 in
`ev_28962c32f0174abe03778607e35f09c9feb9592255b65899a43533bf95c62e78`.
Clear is
`ev_4975f0fb6ce248529200530cdaeda4d68ecd4da28b458ec7c5bba934bdb71f9b`;
the Ctrl-] call is
`ev_239ee0448ff45593061b5c015fce120e50f1cf2af7491bf45a17c50b575f8f3d`.
The inline selector is
`ev_539ffff285b2b9e61be90c030fd29c81165b10508e9b9ee957600e2744b4eefd`.
Public [provenance](../reconstruction/local_controls/status-lines-provenance.json)
binds bytes, fields and branch evidence. The DISPLAY prefix read is explicitly
partial, not a complete function/decompilation or runtime observation. Full REA
records remain ignored; the session was exported and closed.

The [receipt](validation/status-lines-native.json) separates source-only and
genuine-original comparisons. Each checks all65536 hidden WORDs,384 real
normalized-key status paths with standard/custom margins and cursor boundaries,
48 rectangle argument combinations and six direct clear cases. For Lines it
executes all65536 adapter WORDs, all65536 current-mode WORDs for each cycle
length (131072 inputs) and448 accepted/fallback/forwarded-argument combinations.
All cases retain DS=SS, stack guards and BP/SI/DI. The actual recovered keyboard
instructions execute; raw BIOS normalization is outside this suite.

Scroll, cursor placement, status drawing, rectangle rendering and DISPLAY are
explicit modeled services. No native status pixels, actual BIOS changes,
maintained application integration, DOS/BBS/SIP/physical or deployment acceptance
follows from these results.

## Integration still required

These are geometry operations, not cosmetic visibility flags. Establish the
maintained runtime display/BIOS row service and bounded safe selector policy
using the recovered native chain, then reconcile
canonical suppression, CSI bounds, scroll margins, cursor, RIS/reset baselines,
history, frames and child screen loans. The maintained status renderer currently
copies canonical suppression into a native snapshot; changing that snapshot
alone would be overwritten on refresh.

Hiding status can expose a25th terminal row. Existing notices, Auto Answer,
redisplay and transfer owners must retain correct underlays or refuse unsupported
geometry. In particular, Auto Answer currently requires a reserved status row.
Do not restore saved notice cells over newer incoming data in an exposed row.
Larger BIOS line modes also need adequate frame/storage sizing and fallback.

The current bridge/BBS acceptance uses fixed80x24 geometry. A native row change
needs coherent ANSI reporting and an explicit decision about bridge NAWS updates;
do not silently keep advertising a mismatched size or claim the extra row works
because a flag changed. SIP/Telnet remains in Linux. Retain normal RX/CPR/flow,
guarded key/reference/browser admission and call/timer/configuration ownership.
Then repeat source/DOS/BBS/package and physical gates before enabling controls.

Both entries remain among13 unavailable reference commands. Applicationd9eae89d,
ready archive4950ab99, active selection93a9db94 and installed9f2a37e7 are unchanged.
The full feature inventory and physical acceptance remain open.

```sh
./tools/dev --command python standalone/check_status_lines_native.py \
  --output build/NEW-status-lines
./tools/dev --command python standalone/check_status_lines_native.py \
  --output build/NEW-status-original \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```
