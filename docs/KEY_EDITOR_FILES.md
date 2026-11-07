# Checked Meta Keys file backend

The serviced Alt-M controller now has a separately tested storage component.
It is not yet linked into the live dialog or installed PCPlus. The existing
VGA probe still deliberately fails its L/S requests. This is maintained IO
around the recovered KEY format, not recovered original file-picker code.

`src/key_mapping/key_editor_file.h` exposes near-cdecl, DS=SS entry points with
explicit far 540-byte definition buffers and optional near result buffers.
Load reuses the strict reader: exact length, ten kind WORDs in 0..3, and a NUL
within every 52-byte text slot. It commits the caller's destination only after
successful close. Opaque bytes after the terminators are preserved.

Paths must be explicit absolute ASCII DOS 8.3 names, at most 63 bytes, with a
parent prefix no longer than 53 bytes. Case/slashes are normalized. Relative
paths, devices, dot components and reserved recovery leaves are refused before
IO. This keeps operations independent of the current drive/directory; it does
not establish the future application's canonical resource claim.

Save requires either the complete expected old file or an explicit NULL request
to create an absent file. It refuses read-only targets and existing recovery
files. For an existing file it compares every old byte and exact EOF, closes,
exclusively creates `KEYSTG.$$$`, writes and closes all 540 replacement bytes,
then reopens and compares the old file again. The original is renamed to
`KEYBAK.$$$` before installation. Installation failure attempts rollback; success
removes the backup. New-file creation rechecks absence before installation and
never uses an overwriting rename.

The existing 20-byte directory replacement result reports installed, stage,
backup, close, cleanup and rollback outcomes. Callers must inspect those flags
on failure: cleanup failure can leave the new file installed with the old backup.
An uncertain close or failed rollback retains recovery files. An uncertain
handle requires owner quarantine/DOS recovery, not a blind retry. The test
harness knows its injected handle and closes it for fixture cleanup; the product
cannot infer that knowledge from a DOS error.

This is optimistic checked IO, not a power-loss transaction or external lock.
Another writer can still intervene after the final comparison. Attributes and
timestamps are not preserved. Two nested load staging buffers and the near
stack/code footprint have not been admitted into the application memory budget.
The caller must provide file/EXEC admission, immutable source buffers, recovery
policy and safe live-table adoption. Filename selection, native VGA equivalence,
foreground scheduling, application capacity, BBS regression and physical
acceptance remain open. No complete feature-parity gate closes here.

## Verification

```sh
./tools/dev --command python standalone/build_key_editor_file.py \
  --output build/NEW-key-file
./tools/dev --command python standalone/prove_key_editor_file_source.py \
  --build build/NEW-key-file --output build/NEW-key-file-source
```

The source-built DOS8086 diagnostic passes 5,899 checks. It uses owned synthetic
files and real DOS IO, with explicit injected boundary failures: open/read/create,
fragmented reads, write/short write, closes before and after the actual close,
move/install/rollback and cleanup. It verifies retained recovery bytes, failed
load destination preservation, short/extra files, malformed records, stale
rechecks, a competing creation, read-only targets, recovery conflicts, pointer
wrapping/aliasing, immutable input records, and unchanged drive/directory.
Definition buffers live outside DGROUP; runtime DS=SS and linker null-guard
placement are checked. These checks are not a native behavior comparison.

An isolated 16-file export, without original binaries, private data, prior
objects or ancestor Git, reproduces the executable and all DOS results exactly.
The outer pinned Nix environment supplies tools. The existing strict reader's
11 real-DOS and 22 fault checks still pass; the default reader EXE is byte-for-byte
equal to pre-seam public source at `94ccaf0`. Only the optional test-seam macro
changes the reader's build path. The special baseline check uses Git history;
normal component builds do not. See the [receipt](validation/key-editor-files.json).
