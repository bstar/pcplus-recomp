# Native media copy and screen printing

This diagnostic recovers365 exact overlay12 instruction bytes from PCPlus2.01:
`e084..e0f7` media-copy116, `e2f8..e3c8` screen writer209, and
`e3ca..e3f1` selection40. Flat hashes, original EXE offsets and retained REA
EvidenceIDs are in [provenance.json](../reconstruction/print_screen/provenance.json).
The verified original SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The analyst-only `recover.py` reads that artifact; normal builds do not read any
original, analysis executable/database, private configuration, or original data.

The assembly observations are `ev_2f719bdb438c8bc4be6d045eefdb5891b0e9439a983e0197cd8fcef6d3b35987`
(e084), `ev_e93d8b17d34c8a6d6de8681c47ca87d75edf0feb2859696d55402e512a275e0b`
(e2f8), and `ev_be9ebd36f995696b314f779b0ee5314a5e078a2aae90bc1b6a63b8c9536ee2ce`
(e3ca), retained under `analysis/pcplus-overlay-anchored-12/functions/`.

## CSI route and parameters

The recovered CSI dispatcher selects e9d8 for final byte `i` (69h), calls
media-copy e084, then returns through its ordinary completion path. e084 reads
parameter count CB5C and consecutive words at CB3C. No count calls selection
once; otherwise each parameter is processed in order:

| Parameter | Native action |
| --- | --- |
|0|Call selected screen print e3ca|
|1|Call e2f8 mode3, the current cursor row|
|4, CEAC nonzero|Force printer flag3988=1, then call1a76, closing8FF0 and clearing the flag|
|4, CEAC zero|No action|
|5, CEAC nonzero|Force3988=0, then1a76 opens PRN and enables copying|
|5, CEAC zero|Call overlay12:D0D0, an explicit unresolved application boundary|
|Other|No action|

The routine does not itself inspect a CSI private-prefix flag. It trusts its
parameter array/count and is not a bounded public input parser. Signed count
comparisons and callers' parser validation remain part of its original ABI.
The existing keyboard table independently proves Alt-L scan26h calls1a76:
that toggles stream copying, not screen printing. A distinct local key route to
e3ca/e2f8 is not established by the inspected exports/trampoline table; do not
relabel Alt-G's snapshot command or assume BIOS PrintScreen invokes these units.

## Rows, bytes and ABI

`print_screen_original(mode)` is near caller-clean2, preserving BP/SI/DI.
`print_selection_original()` and `print_media_copy_original()` have no arguments;
media-copy preserves BP/SI/DI. DS=SS is required, including the actual reused
6FA0 video reader's stack access. Other registers/flags are scratch unless a
specific reused service contract guarantees them.

Mode1 selects `[0,334C)`. Mode2 selects `[CE0E,CE3A+1)`. Mode3 selects the
current399C row only. Other modes read uninitialized stack locals and are unsafe;
they are not an additional supported mode. Empty/inverted intervals skip rows.
Selection e3ca chooses mode2 when3982 is nonzero, mode1 otherwise.

The writer saves cursor399C/399E, opens literal PRN through841A and replaces
shared FILE word8FF0. The mode at DS7522 is **`wb`**, verified in initialized
original data (EXE2CE72h); the diagnostic reauthors that short resource. It calls
1BBE for each row/column, then actual recovered6FA0 reads the character byte
at video offset3344. Columns0 through3258 inclusive are emitted, including
trailing blanks and NUL/SUB/FF bytes; attributes are not emitted. Every row adds
CR0Dh, LF0Ah and fflush. It closes8FF0, restores the saved cursor and refreshes
status. This differs from the trimmed screen-snapshot file format.

No fopen, putc, fflush or fclose return is checked. An existing printer-copy
FILE is overwritten without closing the previous handle.3988 is not cleared by
screen printing;8FF0 retains the just-closed pointer. If3980 requests a final
formfeed, e3ca calls actual36FC **after** e2f8's close. Thus it passes that stale
FILE to putc/flush. The fixture verifies this call ordering; it does not assert
that a real CRT accepts a null/stale pointer or that a physical printer received
anything. These are native ownership defects to avoid in maintained code.

## Reproduction and limits

```
./tools/dev --command python3 standalone/build_print_screen.py
./tools/dev --command python3 standalone/check_print_screen.py
# Explicit local-original corroboration, never a normal build input:
./tools/dev --command python3 standalone/check_print_screen.py --original
```

The source-only output is `build/print_screen/PRINTSCR.EXE`, Watcom8086/small
model with8192-byte stack; its `_print_screen_dos_test` returns0 and prints
`PRINTSCREEN PASS`. The DOS selfcheck covers a one-row write, row flush and
close using explicit memory CRT/cursor/status boundaries. CPU tests cover38
cases, with38 optional original-instruction comparisons: modes1/2/3,
full/region selection, optional post-close FF, ordered CSI parameters, policy
branches, null open, ignored IO failures, cursor restoration and BP/SI/DI/DS=SS
and stack invariants. Synthetic video includes NUL, SUB, FF and spaces.

The actual reused6FA0 video reader executes against synthetic B800 video memory;
CGA status is zero in these tests. Cursor positioning is an explicit fixture
with four-column geometry, not an assertion about all native viewport states.
CRT open/putc/flush/close and UI/status calls are explicit fixtures. Native36FC,
1A76 and6FA0 are reused from their existing modules and not counted again.
No original application or physical media was executed, and this diagnostic is
not live printer/screen-print support. D0D0 application behavior, local
screen-print binding, actual printer errors and safe live ownership remain
separate integration work.

The [recorded native evidence](validation/print-screen-native.json) binds the
38 linked/original comparisons and actual8086 DOS diagnostic to their exact
source and executable hashes. Re-record retained evidence with
`./tools/dev --command python3 standalone/record_print_screen.py`.
