# Maintained DOS settings editor

`PRMEDIT.EXE` edits the 44 currently mapped fields in an existing PCPlus2.01
PRM image. It builds entirely from maintained source with the pinned Nix
Open Watcom8086 toolchain. It is an offline settings editor: save the file,
exit, then start the terminal with that explicit file. The terminal also offers
[setup before connecting](SETUP_STARTUP.md) with `/S @PCPLUS.PRM`. It is not the original
PCSETUP shared-memory child. The recovered parent protocol and missing child
consumer are documented in [SETUP_NATIVE.md](SETUP_NATIVE.md).

Build and verify from the repository:

```sh
./tools/build setup
./tools/build test-setup
```

Copy `build/setup/PRMEDIT.EXE` to DOS, change to the directory containing an
externally identified2.01 configuration and run:

```dos
PRMEDIT PCPLUS.PRM
```

Paths are current-directory ASCII8.3 leaf names using letters, digits, `_` and
`-`. The editor rejects device names and reserved recovery names before I/O.
It requires an80-column text screen, BIOS mode2,3 or7. It preserves the active
page's2000 cells, cursor position and cursor shape on return.

## Editing and save ownership

Tab/Shift-Tab and Up/Down move between fields. PageUp/PageDown move through
Serial, Terminal, Modem, Commands and Responses. Home/End, Left/Right,
Insert/Delete and Backspace edit the selected value. Field help appears below
the values; F1 supplies a source-owned usage prompt. F10 validates and saves.
Escape discards unsaved edits after a Y/N confirmation. Failed field validation
retains the edit buffer so the value can be corrected.

The serial page supports COM1..4 and exactly the existing importer's rates:
300,1200,2400,4800,9600,19200,38400,57600 and115200. Selecting a COM port installs
that port's standard base/IRQ; other table entries are preserved. Custom UART
bases/IRQs are not supported by the current terminal importer. Profiles4 and6
remain partial VT220/ANSI implementations, not claims of complete emulation.

Six command strings use native caret notation. Eleven response slots hold
already-expanded bytes, so their editor uses hex pairs, for example
`43 4F 4E 4E 45 43 54` for CONNECT. This permits lossless controls and CP437;
00 is the terminator and cannot appear inside a response. Commands are limited
to46/24 bytes and responses to15 bytes. Viewing malformed loaded fields does
not repair them; F10 focuses the first invalid field for an explicit edit.

The model keeps a baseline and a staged1264-byte image. Numeric edits touch
only their mapped bytes. String edits replace the prefix and terminator while
restoring the baseline's bytes beyond the terminator. Editing and reverting a
valid string therefore restores its complete original storage, including opaque
tail bytes. Full validation uses both existing terminal/modem decoders before
writing. Unknown fields and saved live attributes are preserved.

Save rereads the whole target and compares it with the baseline, including
unknown bytes. A missing, truncated or externally changed file prevents writing.
Unchanged staged settings return success without I/O. Changed settings use the
existing exclusive-stage/backup replacement owner with `PRMEDIT.$$$` and
`PRMEDIT.BAK`. Existing recovery files are never overwritten. If installation
succeeds but backup cleanup fails, the editor records the installed baseline,
retains the backup and locks further saves. Other retained-stage/backup errors
also lock saves. Exit and inspect recovery files before reopening.

This is failure-aware replacement, not a concurrent-writer lock or a guarantee
against power loss during FAT updates. There remains a comparison-to-replacement
race. No file-version signature is known; matching length alone does not prove
2.01 compatibility. No default constructor, automatic repair, complete schema,
path/environment precedence or live UART/parent reconfiguration is provided.
These remain parts of F02/F06 and the overall application plan.

## Verification

`standalone/check_setup_model.py` builds the actualDOS16 C model and replays its
near-cdecl APIs with DS=SS. All interrupts and IN/OUT instructions are forbidden
in this replay. Cases cover all44 lossless round trips, importer agreement,
rejected edits without any staged mutation, string capacities/caret boundaries,
all11 response slots, malformed loaded-value repair, pointer overlap, segment
wrap and output capacity. A separate DOS run checks C-runtime behavior without
rewriting its source fixture.

`standalone/test_setup_dos.py` runs real BIOS key input, video and DOS filesystem
operations in DOSBox-X against generated fixtures only. A host links the same UI
source with renamed main to independently compare every screen cell and the
cursor/shape/page after return. The exact production executable separately saves
a baud edit. The owner host checks load failure atomicity, opaque external-file
changes, read-only targets, stage/backup collisions, invalid fields, save locks
and deleted targets. A separate injected backup-delete error exercises an actual
installed file, retained backup, updated baseline and locked retry.

Generated evidence is in `build/setup{,-model}`; public hash-bound summaries are
`docs/validation/setup-{model,dos}.json`. No originals or private configurations
are test inputs. These tests establish offline mapped editing, not original
PCSETUP compatibility, physical serial behavior or complete application setup.
