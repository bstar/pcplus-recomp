# Bounded line attributes in the application

NETWORK CSI L/M now supports the admitted attribute-plane mode instead of
aborting at2d98. Insert/delete counts still clip to the current row through the
scrolling region's bottom, and the public wrappers preserve the caller's column.
The standalone exact recovery and `/A:ORIGINAL` calls remain unchanged.

The native line helpers hardcode23 in their metadata-copy lengths. On the
physical last row that subtraction underflows. Delete also fills a row beginning
at the logical plane's end, and its repair can continue beyond a restricted video
rectangle. Those instructions remain available for exact recovery comparison;
the application does not execute those metadata paths under NETWORK policy.

`src/terminal/line_attributes.asm` owns the bounded operation in ASPECT_CODE.
It validates the existing80-column, fixed-video and real-backing contracts before
mutation. The native helper performs only its real cursor/video operation while
its metadata flag is temporarily disabled and its normal fill word holds the
chosen attribute. Both raw words restore exactly. Metadata then shifts in the
correct overlap direction within the active region. Insert clears the new row's
flags and fills its values from the preceding attribute; delete clears the last
region row and fills it from the preceding attribute at the region's end.

If deletion removes a field boundary, the real recovered mode2 repair runs with
a temporary logical end at the scrolling region's end. Its ordinary marker stop
behavior is retained. The original whole-plane count restores before return;
fields and video below the region remain unchanged. The implementation uses no
new near data or shared buffer and keeps DS=SS and DF clear. The renderer's far
segment owns the additional instructions. Two explicit register-only resident
callbacks retain the native near-call ABI; memory inspection verifies their
instructions, targets and relocations plus all three public far-entry references.

Verification includes512 actual-linked UART/parser cases with192 required field
repairs and45 malformed-state rejections before editing. The independent model
checks entire4096-byte backing planes, video and canaries,1/5/25-row geometry,
restricted regions, the final row, repeated counts, both profile gates, raw wrap
words, full fill-word/count restoration and register/stack conventions. Existing
line-policy checks retain ORIGINAL column-home and bounded Control-N wait tests.

The actual DOS probe runs the unmodified application executable. An explicit
test-only BIOS cursor boundary seeds plane data and guard tails; this is not a
normal configuration path for protected plane mode. All subsequent UART bytes,
parser calls, BIOS scrolls, bounded shifts and native repair execute the product.
A passive observer records post-edit cursor snapshots and exit state. The probe
requires exact video and both4096-byte planes after restricted-region boundary
deletion, clipped repeated insert and huge counts at the physical last row. A
protected marker below the region must keep its existing video attribute. Normal
DOS exit, cursor reports and hardware restoration remain canonical checks.

Two retained probe failures were observation mistakes: the exit notice covered
the last row in the first capture; the revised observer found an additional BIOS
cursor refresh beyond the three expected edit positions. The passing observer
captures the edited screen before the notice and permits that extra refresh.
No product change was needed for either observation correction.

Run the checks through the pinned toolchain:

```sh
./tools/dev --command python3 standalone/check_line_attributes_live.py
./tools/dev --command python3 standalone/test_line_attributes_dos.py --label new-label
```

The current validation also binds an owned ENiGMA search/NFO regression, DOS
ASPECT renderer edits and a fresh source-only rebuild. See
[the validation record](validation/line-attributes.json). Viewport/general video
support, complete keyboard/UI behavior, live server installation, physical modem
validation and all whole-application gates remain open.

The public controller now also executes through [checked far entries](LINE_CONTROLLER_FAR.md),
freeing resident address space while retaining this metadata policy and native
video/repair dependencies. Its current placement has a separate validation record.
