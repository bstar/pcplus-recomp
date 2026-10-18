# DOS character translation editor

`XLTEDIT.EXE` edits the native headerless 256-byte translation table. Each input
byte is an index; its stored byte is the replacement. Binary values including
NUL, SUB and FF are preserved. Files shorter or longer than 256 bytes are rejected.
The editor builds from maintained C source using the pinned Nix DOS toolchain;
no original executable, installation or REA database is a build input.

```sh
./tools/build xlt-editor
./tools/build test-xlt-editor
```

Copy `build/xlt-editor/XLTEDIT.EXE` to the DOS directory containing the table:

```dos
XLTEDIT PCPLUS.XLT
```

`XLTEDIT /N NEW.XLT` explicitly stages a new identity table. It requires a missing
target and creates nothing until F1. Names are current-directory ASCII 8.3 leaves
using letters, digits, `_` and `-`, with an optional extension. DOS devices and
the reserved recovery names are rejected. An 80-column BIOS text screen in mode
2, 3 or 7 is required. The active page's 2,000 cells, cursor position and cursor
shape are restored on exit.

The display uses eight columns of 16 source/replacement pairs per page, following
the [recovered editor](TRANSLATION.md#original-editor-and-save-invocation).
Arrows select a pair; Home/End select the first/last pair on the page. G opens a
decimal source-byte prompt. Enter edits the replacement, with bounded decimal
input from 0 to 255, cursor editing and Escape cancellation. Changed mappings
are highlighted.

| Key | Maintained behavior |
| --- | --- |
| F1 | Save staged bytes after checking the disk baseline |
| F2, PageUp, PageDown | Toggle inputs 0–127 / 128–255 |
| F3 | Reload from disk; confirm discarding unsaved edits |
| F4 | Stage an identity table; F1 saves it |
| Escape | Exit; confirm discarding unsaved edits |

This is an offline editor. F3 and F4 do not enable/disable the running terminal's
mode or change a PRM image. That differs from the original parent's shared-memory
editor. Select the saved mode with PRMEDIT at startup, use a confirmed
[Alt-F10 mode change](LIVE_TRANSLATION_SETUP.md), or select a table explicitly
with `/X:FILE.XLT`. A dedicated same-mode live reload/editor command remains open.

## Save and recovery

Before writing a changed table, the owner checks the target's attributes and
rereads all 256 baseline bytes. External changes, truncation or a missing target
refuse the save and retain edits. A new target must still be missing. An unchanged
existing table returns success without filesystem I/O.

The owner creates `XLTEDIT.$$$` exclusively, writes exactly 256 bytes and checks
close before touching the existing target. Replacement moves the old target to
`XLTEDIT.BAK`, installs the stage using DOS no-overwrite rename, then deletes the
backup. Failed installation attempts to restore the backup. Existing stage or
backup files are never overwritten.

Failures retain unsaved bytes. A failed stage close retains that stage rather
than deleting a file whose handle state is uncertain. Any recovery remnants
created by this attempt lock further saves. If installation succeeded but backup
cleanup failed, the document adopts the installed baseline and reports the
retained backup. Exit and inspect recovery files before continuing.

This protocol does not lock out another writer or guarantee recovery from power
loss during FAT updates. A comparison-to-replacement race remains. There is no
automatic recovery-file deletion or version conversion.

## Validation

[Editor validation](validation/xlt-editor.json) records executable/source hashes,
293 production DOS filesystem-owner assertions, 931 assertions with injected DOS
failures, and 17 additional actual DOS keyboard/entry workflows (19 reported
cases in total). The fault build links the production document and checked loader
to deterministic filesystem adapters. It covers create/write/short-write/close,
rename/rollback/cleanup and baseline-read errors, retained edits, recovery locks,
collisions, and argument rejection before I/O.

Actual DOSBox-X UI cases include both pages, source-byte jump, invalid input,
identity save/discard, reload confirmation, new-file save/cancel, read-only and
recovery-file failures. An independently linked host checks all screen cells,
cursor position/shape and active page in color, monochrome and page-one cases;
the exact production EXE is also exercised separately. All media are synthetic.
These tests do not establish physical hardware or live UART behavior.
