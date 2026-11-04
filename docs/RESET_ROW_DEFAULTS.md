# Captured reset defaults for row changes

The optional `--reset-row-owner` component updates captured RIS row defaults
without capturing the current BBS cursor, colors, modes, tabs or keymap. It is a
maintained transaction helper, not byte-identical recovery of an original entry.
No key/menu/browser command calls it yet; Status/Lines remain unavailable.

Far register API `terminal_reset_resize_rows_far` accepts AX=new effective row
count1..50. AX returns0 success,2 uncaptured reset profile, or3 invalid input/
baseline/ABI. All other registers and entry flags, including IF/DF, are retained.
DS must equal SS. The caller must serialize foreground profile operations and
own the larger live geometry transaction. No DOS, BIOS, video, serial, speaker
or live canonical-geometry write occurs in this helper.

## Captured state contract

The lookup table and captured words already owned by `terminal_reset.asm` are
used directly. The helper reads old geometry from that captured profile, never
from the peer's current screen state. It checks count/max consistency,80 physical
columns,160-byte video stride,80/132-byte attribute stride and last column,
erase extent, cursor/visible columns, cursor offsets, row bounds and margin order.
Both old and requested geometry must fit the4096-byte near planes and8192-byte
far shadow. This is a storage limit, not proof of physical display support.

Every changed cell address/value is staged on the bounded DS=SS stack before
any default is written. A missing field, invalid old profile or invalid requested
size therefore cannot leave a partially updated default set. This is failure
atomicity under the caller's foreground ownership, not a generic interrupt-safe
transaction over the entire application.

The twelve affected defaults are:

- Effective row count, last row and erase cell count.
- Screen first/last row, origin top/bottom, current row, previous row and saved
  row. Bottom endpoints following the old maximum follow the new maximum;
  custom endpoints and other row values clamp only when beyond the new maximum.
- Video and attribute cursor offsets, recomputed from the new captured cursor
  row and the existing captured columns/strides.

Other captured defaults remain exact. Corrupt old margins are refused even if
clamping could happen to turn them into a valid pair. Invalid offsets are not
silently repaired. No pointers, parser state or current peer attributes become
new profile defaults.

## Validation and build isolation

The [receipt](validation/reset-row-defaults.json) binds the linked component,
checker and source-only reproduction results. Actual far-call, table-update and
RIS instructions execute in216 geometry/custom-margin/stride/flag compositions,
29 invalid-request/baseline/ABI/late-lookup refusals and three subsequent real
RIS restores. Write hooks admit only the caller's bounded stack and captured
word array; rejected calls perform zero captured-default writes. Register,
IF/DF and stack guards remain checked. Changed peer colors/duplex/tabs/keymap
are restored from the original captured profile during the RIS tests.

Rows43/50 and132-column combinations in this suite are metadata inputs, not
BIOS resize or full frame tests. The three linked RIS tests use only24/25 rows
and explicitly supply canonical visibility as a caller fixture. The helper
itself does not commit live geometry or establish that larger modes are usable.

The component adds752 bytes in CONFIG_CODE, no persistent data and no resident
code; CONFIG_CODE is56698 bytes and resident code remains65334 bytes. Without
the flag, the source-built executable is exactly the software-accepted7df99c1f
binary. Both builds reproduce exactly from their declared sources in empty
Git-free trees with no originals. The explicit flag has a separate default
output name and is retained by manifest-based reproduction tooling.

```sh
./tools/dev --command python standalone/check_reset_rows_live.py \
  --terminal build/COMPONENT/TERMINAL.EXE --output build/NEW-reset-rows
./tools/dev --command python standalone/prove_terminal_manifest.py \
  --terminal build/COMPONENT/TERMINAL.EXE --output build/NEW-source-proof
```

## Integration still required

The live status/line owner must preflight BIOS/mode, canonical geometry, active
owners, capacities, frames/history, notices and bridge size policy. It needs a
rollback strategy for all live effects and reset defaults if a later stage can
fail. This helper's success is not an atomic commit of that larger transaction.
It must not enable controls merely because these isolated default updates pass.

The tested package, active installation selection and installed application
remain unchanged. The internal30d680b1 component executable is not a packaged
hardware-test release and does not inherit7df99c1f's BBS/transfer acceptance.
No remote/card/private file, live BBS or bridge configuration was changed.
