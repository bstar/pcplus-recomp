# Shared ownership for directory persistence

The new `directory_storage` component resolves and reserves a directory's
absolute DOS identity plus `PCPSTG.$$$` and `PCPBAK.$$$` before calling the checked
replacement backend. Actual replacement operations use that same absolute
spelling. The existing capture, snapshot, monitor, history and recording file
registry can refuse the operation before any target or staging-file mutation.

This closes a prerequisite for live selection adoption: retiring the old
selection's pending accounting must not replace a file another application
owner is still using. The current terminal's `directory_save_record` and
`directory_save_accounting` entry points are not yet routed through this new
component. LoC.5 still supports preview only; selection adoption is unfinished.
No application/package, card, live service or network change is made here.

## Transaction and recovery

The near-cdecl API uses DS=SS, a 222-byte inspect-only snapshot and a nonzero
DATA initialization cookie. Invalid arguments leave history untouched. A
successful claim covers all three canonical filenames, including during
source/staging close, rename, rollback and cleanup. Open or uncertain binary
owners reject the claim; later conflicting opens reject while it is held.
An unrelated binary sink can still open a different filename.

The registry currently permits one dynamic external owner. An existing recorder
reservation refuses a directory transaction even if its paths differ; the
directory guard never replaces another registration. Selection handoff must
honor recording ownership instead of stealing it.

Only a fully closed operation with no retained recovery files releases the
claim. An uncertain close, failed rollback, retained staging/backup file or
failed release leaves the owner held. Reinitialization and later writes refuse
without resetting its metadata, retrying a close or applying another delta.
There is no unsafe force-release API. Claims end with the process; recovery
files may still need explicit reconciliation before a later process writes.

The legacy replacement backend may also retain an inheritable DOS handle after
a failed close. The terminal integration must block child EXEC while this owner
is held, or replace those opens with a separately validated private-handle
backend. Filename claims alone do not protect child-handle inheritance.

The accounting helper validates Gregorian dates before IO and changes only the
selected record's date/count bytes. It updates the caller's baseline only when
the replacement was actually installed, including installed cleanup/release
failures. Count arithmetic retains the existing 16-bit modular behavior. Normal
record replacement leaves its read-only expected/replacement inputs untouched.

Canonical identity excludes same-process owners, not external writers, runtime
drive remapping, host aliases or FAT/power-loss races. The component does not
pause or restore UART ownership. Its caller must complete the foreground
quiescence handoff before making a directory write.

## Acceptance

The [receipt](validation/directory-storage.json) binds 22 actual DOS8086
workflows and 704 assertions:

- Successful accounting and ordinary record replacement preserve the entire
 23,050-byte file except the intended 114-byte record changes.
- Capture ownership of the target, stage and backup refuses before replacement;
 snapshot, monitor and history ownership of the target also refuses. A capture
 owner with an ambiguous close stays protected.
- Existing external registration, stale records, an existing stage file,
 invalid dates, failed canonicalization, overlong canonical paths and an extra
 source suffix refuse without altering the original source or caller baseline.
- Both a close error after releasing the handle and a close error retaining
 the real DOS handle keep all three names claimed. Install/rollback failure,
 installed backup-cleanup failure and release failure do the same. Repeated
 calls refuse, preventing duplicated accounting after actual installation.
- Actual monitor admissions attempted during replacement reject all three
 protected paths while an unrelated sink still opens and closes successfully.
- A deliberate CWD change immediately after canonicalization still updates the
 originally admitted file and preserves a decoy in the new directory.
- Hardware snapshots match before and after execution. A 20-source export outside
 every Git ancestor, with no original installation, reproduces STORAGE.EXE and
 all eight objects exactly and repeats the DOS workflows. The same proof passes
 from committed sources at `c8cc45a`, excluding pending telephone-log changes.

The diagnostic uses explicit wrappers for selected DOS close/rename/delete,
canonicalization and reservation-release faults around real kernel operations.
These are controlled fault witnesses, not evidence that DOS spontaneously
produced those errors. The normal replacement and shared owner code execute.

```sh
./tools/build test-directory-storage
./tools/dev --command python3 standalone/prove_directory_storage.py \
  --output build/directory-storage-source-NEW
```

## Next application integration

Place the guard and existing directory action code in CONFIG_CODE, with exact
near/far adapters for the resident replacement/patch calls. Route actual saved
record/accounting entry points through it without returning a prior installed
flag on a refused retry. Verify real parent accounting and installed-warning
handling, then use the quiesced selection owner to retire old accounting before
publishing the new context. Preserve held-owner admission across PROGRAM/ASPECT
as well as directory writes until handle-inheritance policy is established.

Canonical resource staging, baseline freshness, UART/profile confirmation,
selected-entry dialing, full original interface/F01–F16 and ENiGMA physical
Boca/SPA2102/card acceptance remain open.
