# Directory editing, saves and call statistics

`TERMINAL.EXE` can edit a selected2.01 directory record before connecting and
save successful-call statistics after restoring the UART. These are maintained
application features built on the recovered directory layout and screen
services. Complete original menu behavior, sorting, printing, dialing cycles,
transfer and ASPECT integration remain open.

```text
TERMINAL @PCPLUS.PRM /E:PCPLUS.DIR
```

Both paths are explicit; neither file is discovered or imported implicitly.
The PRM remains read-only. The directory is read for selection and can now be
changed by accepted edits or successful-call accounting. Files must be externally
identified as2.01; matching length alone does not identify a version.

## Edit a record

Use Up/Down, Home/End or Page Up/Page Down to highlight an entry, then press
**E**. The editor opens before any UART acquisition. Tab, Enter or Down moves
to the next field; Shift-Tab or Up moves back. Left/Right and Home/End move
within a field. Insert toggles insert/overwrite; Delete and Backspace remove
characters. **Escape discards the entire staged edit** and returns to the
browser. **F10 accepts and attempts to save the complete record**; invalid
values keep the editor open at the offending field.

The standalone editor only commits its private114-byte working copy in memory
on F10. In the terminal, its browser wrapper then performs the staged file save.
The browser reports `Entry saved.`, a save error, or an installed-entry warning
when cleanup retained recovery files. A successful or installed-warning result
reloads the page. Canceling the browser afterward does not undo an already saved
edit. Enter in the browser selects an entry for connection.

The editor preserves opaque string tails, last-call date and count. Passwords
appear as asterisks; control characters in other displayed fields are sanitized.
Screen contents, active text page, cursor position/shape and selected video
segment restore when the editor closes. Supported video modes are80-column
text2,3 and7. This editor is a startup operation; it does not open during a live
BBS session.

| Field | Accepted storage value |
| --- | --- |
| Name / number | Up to24 /20 content bytes |
| Baud index |0..8:300,1200,2400,4800,9600,19200,38400,57600,115200 |
| Parity |0 NONE,1 ODD,2 EVEN,3 MARK,4 SPACE |
| Data / stop bits |7..8 /1..2 |
| Duplex |0 FULL,1 HALF |
| Script, KEY, META, note | Up to8 content bytes each |
| Password | Up to10 content bytes, masked on screen |
| Profile / protocol | Raw storage IDs0..255 |
| Dialing mode |0 MODEM,1 DIRECT |
| Port |0 DEFAULT,1..8 COM1..COM8 |

These are storage constraints. Connecting currently supports COM1..4, FULL
duplex and profiles4 VT220 or6 ANSI. Nonblank SCRIPT, KEY or META bindings are
rejected before UART access. Protocol and note remain metadata. A stored
password is preserved as metadata and is **never automatically sent**. The
original script expression engine can access that field, but that engine is not
implemented here. See [the original evidence](DIRECTORY_ACCOUNTING.md).

The maintained editor uses explicit numeric storage IDs and preserves text case;
it does not reproduce the original nested selection menus, automatic parity/data
coupling or filename uppercasing. Thus an entry may be valid to store yet require
changes before the current terminal can connect. Unsupported entry bindings are
reported rather than silently applied.

## Staged file replacement

A save streams the exact23,050-byte directory through bounded buffers. It
compares all114 bytes of the selected record against the version originally
loaded, substitutes the replacement, and preserves the header and other199
records byte for byte. A changed selected record causes a stale-data failure;
it is not overwritten. A short file, extra suffix, failed read/write/close or
read-only target also prevents installation.

The save uses same-directory `PCPSTG.$$$` and `PCPBAK.$$$` files. It requires both
names to be absent, creates the stage exclusively, and closes source and stage
successfully before renaming the target to backup and installing the stage.
After installation it removes the backup. On installation failure it attempts to
rename the backup back to the target. Existing recovery files are never replaced.

Only explicit ASCII DOS8.3 paths of at most63 characters are accepted for saves.
The parent prefix must fit53 characters so recovery names also fit. DOS device
names, dot/dotdot components and recovery-file targets are rejected. A directory
that can be read under a different path spelling may therefore be rejected for
saving. File bytes are preserved; timestamps and attributes are not retained by
this replacement operation. This is not a crash-atomic FAT transaction and does
not lock out an external writer after the source is closed.

If a save needs attention, preserve the target and any recovery files before
resolving them. `PCPBAK.$$$` can contain the prior directory; `PCPSTG.$$$` can
contain an uninstalled candidate. An installed-entry warning means the new
target was installed but cleanup left recovery material. A failed rollback can
leave the original under the backup name and no target at its usual name.
Inspect the actual files and reported result before deciding which version to
retain; do not blindly delete or overwrite recovery files. Automatic restart
recovery is not implemented.

## Successful-call accounting

A successful selected-entry MODEM connection, or entry into selected DIRECT
mode, records a pending count and DOS calendar date in RAM. Repeated successful
connections aggregate their counts modulo65536 and retain the most recent
captured date. A canceled or failed dial adds no count. Explicit `/D` dialing
without a directory does not update a directory record.

At terminal exit, IRQ/UART/PIC restoration happens **before** directory
persistence. The application applies the pending delta to the original selected
record baseline and saves through the same expected-record comparison and staged
replacement. This keeps full-file directory IO outside the live UART session.
Only date/count bytes61..71 change; the PRM and other directory bytes stay
unchanged. An external change to the selected record causes a save conflict.
Pending accounting can be lost if DOS or the program stops before this exit
flush; it is not a durable background journal.

The maintained patch writes `MM/DD/YY` with year modulo100. This intentionally
fixes the original year2000 defect: its year-minus1900 formatter emits three
digits after1999 and overwrites the counter's low byte with the date terminator.
Exact original instructions and29 replay cases preserve/prove that defect
separately; [accounting recovery](DIRECTORY_ACCOUNTING.md) describes the evidence.
The maintained date API validates Gregorian dates in1980..2099 and preserves the
original16-bit modular count behavior.

An accounting-save failure prints `Call statistics save needs attention. Check
directory recovery files.` and returns DOS **errorlevel9** when no prior
application error exists. A prior errorlevel is preserved. This status can also
mean the new directory was installed but backup cleanup failed; result flags
distinguish installation, retained backup and retained stage. The application
does not retry an already installed delta. An editor save failure remains in the
browser with a notice rather than using this exit-time errorlevel.

## Verification and remaining scope

Source-only editor CPU and DOS tests cover keyboard editing, field ranges,
cancel/accept atomicity, masked passwords, opaque-tail preservation and exact
screen/cursor restoration. Actual DOS replacement tests exercise real files and
declared read/write/close/rename/rollback/cleanup faults. Terminal integration
checks editing save/cancel/conflict, deferred accounting, retained recovery
conflicts, MODEM/DIRECT and password metadata without display/transmission.
The current terminal also passes actual local Synchronet, ENiGMA½ and Mystic
login plus read-only file/message navigation with authoritative semantic audits.
These use synthetic records and loopback BBS servers; physical modem/handshake
timing and complete application compatibility remain separate work.

```sh
./tools/dev --command python3 standalone/build_directory_editor.py
./tools/dev --command python3 standalone/check_directory_editor.py
./tools/dev --command python3 standalone/test_directory_editor_dos.py
./tools/dev --command python3 standalone/check_directory_replace.py
./tools/build terminal test-terminal
```

No installed private directory, modem profile or real password is required by
these tests. Full settings UI, original directory commands and cycles, transfer
protocols, KEY/META, ASPECT and Host remain in the [application plan](../PLAN.md).
