# Editing the selected input table

**Alt-F8**, or **Alt-Z → Setup → Edit input table**, opens the source-built
XLTEDIT application for the table currently selected by the terminal. Table
mode 1 with the normal FFh input mask is required. Modes 0/2 have no selected
table to edit; XLTEDIT remains available as an offline command for an explicit
file.

The child receives the exact absolute table path remembered by startup or a
confirmed translation-mode change. It does not select a different current-folder
file with the same name. F1 saves in XLTEDIT and Escape returns. The terminal
then reads a fresh, exact 256-byte snapshot and asks whether to apply it. Y
accepts that snapshot; other answers retain the current mapping. Saving the file
and accepting it into the terminal are separate actions. Failed execution,
nonzero child exit, failed reads and changed ownership retain the active table.
The PRM mode, enabled flag and input mask are unchanged.

## Executable selection and connection ownership

The terminal executes XLTEDIT.EXE beside its own executable, using the DOS 3+
PSP environment trailer. This location remains independent of a later CWD change
and the PCPLUS resource-directory value. There is no PATH or command-processor
search for this action. The filename trailer follows the environment's second
NUL and count word, as documented in Microsoft's
[MS-DOS EXEC description](https://www.pcjs.org/documents/books/mspl13/msdos/encyclopedia/section5/).
The maintained reader requires one absolute program-name string within the
validated environment allocation. Missing or malformed trailers and a resulting
helper path exceeding 63 bytes fail without executing another program.

Pure command preparation leaves its outputs unchanged on failure and does not
consume an unrelated settings stage. The table argument is quoted and bounded;
CP437 filename bytes are passed directly to DOS. No shell expands the argument.
The offline editor accepts an 8.3 leaf or an absolute drive-rooted path up to
63 bytes. Directory components remain DOS8.3 names, with device and recovery
names rejected before opening them. Relative parent paths are not accepted by
the document API.

The existing PROGRAM owner drains queued and physical output, pauses configured
flow, preserves DTR, lowers RTS and releases the UART interrupt before EXEC.
Capture closes according to that owner's established policy. After the child
returns, the owner quiets its UART/vector state before showing a text-mode
confirmation. It restores the original screen, cursor, UART and receive flow
before terminal input resumes. NONE flow cannot prevent incoming bytes while a
child owns the machine; physical Wi-Fi modem behavior remains unverified.

Local parser, macro, transfer, monitor, printer-controller, snapshot and view
ownership are checked before scheduling and again during the handoff. Pending
cancellation performs no EXEC or table read. Late ownership changes prevent
adoption, and local confirmations use the foreground FIFO before BIOS input.

## Replacement and recovery

XLTEDIT retains separate baseline and staged 256-byte tables. Save compares the
current file with the baseline before replacement. It creates XLTEDIT.$$$
exclusively beside the target, checks writing and closing, renames the old file
to sibling XLTEDIT.BAK, then installs without overwriting another file. Failures
retain the established cleanup/rollback behavior and lock retries when recovery
remnants remain. A successful install with failed backup cleanup adopts the
installed baseline and reports the retained recovery files.

Both recovery names are built from the target's parent. Current-folder files
with those names are not touched when the target is elsewhere. A short target
leaf at the 63-byte target limit can require a 73-byte recovery pathname; those
paths have separate bounded buffers. This does not change the on-disk headerless
256-byte format or provide namespace locking or power-loss atomicity.

## Verification

```sh
./tools/build test-translation-edit
./tools/build test-xlt-editor
```

The linked terminal suite executes actual command preparation, declared far
entry frames, dispatch, DOS EXEC backend, UART handoff and confirmation logic.
Only DOS, BIOS, hardware and child execution boundaries are modeled. It includes
selected default/environment/explicit paths after CWD changes; acceptance and
decline; missing child, resize, exit and read failures; ownership guards;
connection retention; preserved settings staging and invalid output spans.
Eight actual production-editor DOS workflows verify resulting files, unchanged
PRMs and effective mapping separately from these CPU tests. The current
[validation record](validation/translation-edit.json) binds these observations
to both executable hashes,276 rejected call frames/layouts, the77-command
regression and64 independently reproduced outputs.

The offline DOS suite includes actual filesystem ownership, deterministic file
faults, independent screen/cursor restoration checks, quoted absolute paths,
short-name aliases, CP437 names, maximum-length targets and synthetic bounded
PSP trailer cases. Emulated DOS evidence does not establish every physical DOS,
BIOS, video or modem configuration. This command advances the application plan;
full settings/key editing, other emulations, ASPECT, Host and the remaining
whole-application gates stay open.

The same application build also repeats the existing DOS menu, clipboard-transfer
and explicit-reload workflows successfully. Selected stock BBS downloads pass
on Synchronet and ENiGMA, including ENiGMA's post-download search. Synchronet's
editor passes; immediate ENiGMA Home/Insert remain failed, and the separate30ms
buffering experiment passes. These stock runs are regressions of existing
workflows; they do not claim a live XLTEDIT session on a physical modem.
