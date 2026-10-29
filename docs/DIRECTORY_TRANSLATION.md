# Translation in the directory resource transaction

The opt-in `--directory-translation` application stages the selected input
translation together with KEY/KBD. It implies `--directory-retirement` and
retains the LoC.6 splash. The existing R preview action runs the transaction
through disconnected PROGRAM kind 6. It still does not adopt the selected
entry, change active translation or dial.

```sh
./tools/dev --command python3 standalone/package_special_edition.py --build \
  --custom-irq --directory-translation --output build/translation-package
```

Original CLI /X provenance is captured before directory startup or a child CWD
change. All explicit KBD/KEY/XLT identities canonicalize before any are
published; a third-resource failure publishes none. Rebinding cannot reset a
successful or failed attempt. Preview validates the saved mode first, then
honors original /X by forcing proposed mode 1 and correcting its change mask.
The request factory uses the original CLI mask, never the augmented active mask.

Mode 1 requires exactly 256 bytes, preserving arbitrary binary values. With /X,
only its frozen canonical identity is used. Otherwise PCPLUS.XLT is resolved
from CWD, then the PCPLUS directory only when the current file is missing.
A damaged, unreadable or directory-valued current file cannot fall back.
Missing required translation fails. Modes 0 and 2 perform no XLT lookup or
read and stage an empty path and deterministic unused table bytes.

All three resource identities resolve before the first content open. The same
shared reservation covers them during reads. Handles are non-inheritable.
Only successful reads, closes and claim release publish the complete far
bundle; an XLT error cannot publish the earlier KEY/KBD bytes. An ambiguous
close or release retains the claim and blocks product EXEC and reset/retry.
No uncertain owner is forced free. Reservations exclude conflicting owners in
this process; they do not lock concurrent external writers or namespace changes.

The request grows from 248 to 314 bytes, bundle from 1,624 to 1,948, resource
snapshot from 142 to 206, and CLI snapshot from 138 to 202. The exact 694-byte
actual-session snapshot and its two damage seals move to frozen offsets
5,926 through 6,624. The page and proposal keep their original offsets. Both
63,000-byte histories, the 8 KiB stack and the 63,504-byte child memory loan
remain intact. Linked ABI and lease checks distinguish the two layouts.

The [validation receipt](validation/directory-translation.json) records exact
binaries, source closures, native workflows, fault injection and limitations.
Application workflows exercise real DOS8086 COM3/IRQ5 handoff. Translation
cases execute an actual source-built ASPECT child that changes CWD before
opening the directory, so startup has a valid table while a later selection
can encounter a missing/damaged table. Passive observers check quiescent DOS
boundaries and non-inheritable opens; all active settings/table/paths, private
files and serial hardware must return unchanged. Declared session-damage cases
remain separate from passive runs.

The component fault diagnostic uses the same production resource and XLT
readers with explicit DOS fault adapters. It covers close ambiguity both while
the handle remains open and after a successful kernel close, open/read/release
errors, fixed-claim conflicts, CWD drift between content opens, invalid arguments
and preservation of a previous bundle on a later failed stage. A deliberately
admitted test child independently verifies that the retained XLT handle is not
inherited; product EXEC itself remains refused. Fifteen linked cases exercise
the actual CLI APIs and startup adapter with only DOS canonicalization modeled.

Selected-entry adoption, active XLT owner publication/reload identity, script
staging and dialing remain open. Stock ENiGMA checks cover server interaction
and selected screen markers; their historical `exact_screen` name does not
establish a complete independent character/attribute oracle. The full F01–F16
application, physical Boca/SPA2102 and card acceptance remain open.
