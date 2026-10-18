# Live DOS directory selection

The source-built terminal can now read an explicitly selected2.01 PCPLUS.DIR,
browse and edit its entries in DOS, and connect using a selected record. The PRM
remains read-only. Accepted record edits use staged directory replacement;
successful-call date/count updates are saved after UART restoration at exit.
See [editing and recovery](DIRECTORY_EDITING.md). Complete original directory/
settings menus, selection cycles and script/key/transfer subsystems remain open.

```text
TERMINAL @PCPLUS.PRM /E:PCPLUS.DIR
TERMINAL @PCPLUS.PRM /E:PCPLUS.DIR /N:17
TERMINAL @PCPLUS.PRM /E:PCPLUS.DIR /N:17 /C:LEGACY
```

Both files are explicit and externally identified as2.01; length is not a
version signature. `/N` selects entry1..200 directly; without it the native
browser opens before UART acquisition. `/D:target` and `/E` are mutually
exclusive. `/N` and `/C` require `/E`, and directory operation requires a PRM.
Invalid selector combinations fail before browser/file/hardware activity.

## Native browser

The browser displays ten records per page. Up/Down, Home/End and Page Up/Down
move within1..200; Enter commits the highlighted entry and Escape cancels with
normal DOS exit. File errors also leave the browser through its cleanup path.
Only bounded name and number fields are rendered. Control bytes become spaces;
passwords, scripts and other raw record bytes are never printed.

Recovered screen save/restore services preserve the active text page. BIOS cursor
position/shape, selected video segment and caller registers restore on selection,
cancellation or error. Supported80-column text modes are2,3,7; active-page video
offset comes from BIOS data. The browser updates its page with one strict,
streamed file read, rather than allocating the entire directory in near memory.
Press E to edit the highlighted record. F10 validates and attempts a staged save;
Escape discards the edit. Save failures and installed-but-cleanup warnings appear
in the browser. This is a startup browser; it does not open over an active BBS
session. `/C` selects the interpretation before browsing; its footer shows the
current mode. The editor's storage ranges can exceed the live supported subset.

## Target interpretation

Literal mode is the maintained default for network modems. It preserves case,
does not use dialing-code slots, and accepts the same network-target alphabet
as `/D`. A stored number is limited to20 content bytes by the original record
format; `/D` remains available for longer targets up to63 bytes.

Explicit `/C:LEGACY` uppercases ASCII number bytes and substitutes A..J from
the ten header code slots. Inserted code text retains its case and is not
recursively expanded. It validates all header slots and rejects expansion beyond
the original60-byte content bound instead of truncating. Caret commands pass
through the bounded modem expansion before sending. See
[original quickdial evidence](DIRECTORY_DIAL.md).

These modes must stay distinct: the original rule changes `bbs.example` to
`S.XMPL` when its referenced code slots are empty. Original quickdial token
prefix/suffix syntax and permissive16-bit integer quirks are not offered by
`/N`, whose decimal bounds are checked at every digit.

## Selected settings and supported bindings

The combined loader reads one PRM and one exact23,050-byte directory, stages the
serial/display, modem and selected-entry plans, and commits only after validation.
The directory reader accepts no suffix and requires successful close. Errors do
not partially commit the three plans. Loading itself does not change either
file; explicit edits and deferred accounting can subsequently update the DIR.

Selected port0 means retain the PRM port;1..4 choose standard COM1..4. All other
entry serial fields apply regardless of DEFAULT port: baud, parity, data bits,
stop bits and terminal profile. Selected port base/IRQ must be supported and
agree with the BIOS before UART use. Profiles4 VT220 and6 ANSI are accepted.
Explicit serial CLI categories then override the imported entry settings, just
as in PRM-only startup. The underlying known PRM subset and selected record are
validated even when a CLI category overrides them.

MODEM0 initializes/dials the expanded selected number and uses the existing
bounded connection controller. DIRECT1 applies the entry serial/profile settings
and enters online mode without AT commands, result waiting or a required modem
command subset. An empty number is valid for DIRECT. Direct disconnect returns
to raw mode without sending modem hang-up commands or pulsing DTR.

Nonblank SCRIPT/KEY/META bindings currently fail explicitly before UART access,
as does HALF duplex. They must not be silently dropped on selection.
Blank follows the observed original first-byte NUL/space test, with bounded
termination still required. Protocol index is retained as metadata until transfer
selection is implemented; it is never used as an unchecked table index. A stored
password remains metadata: it is preserved, masked in the editor and never
automatically sent. The original script password accessor is documented in
[accounting evidence](DIRECTORY_ACCOUNTING.md), without claiming script support.
Notes, padding and opaque storage are preserved. Successful calls update only
the selected date/count through exit-time staged replacement; errorlevel9 reports
an accounting-save problem unless an earlier application error already exists.
Recovery files can remain even when a replacement was installed. See
[save/recovery behavior](DIRECTORY_EDITING.md).

## DOS APIs and verification

`src/directory/directory_dos.c` provides near-C read-only APIs:

* `directory_dos_read(path,entry,selection,result)` returns a366-byte selection:
  word entry0, header250 at2, record114 at252.
* `directory_dos_page(path,first,page,result)` returns a1,394-byte page: words
  first0/count2, header250 at4 and up to ten114-byte records at254. Unused slots
  on a short final page are zero.

Both preserve raw storage and commit after exact EOF and close. They stream
through bounded buffers under the existing8-KiB stack, validate near extents
and disjoint buffers, and report primary/secondary DOS errors separately.
`directory_live_read` additionally stages the validated36-byte serial plan,
366-byte modem plan and214-byte selected plan, including the raw114-byte record
at offset100 for metadata and expected-record comparison. Its10-byte result includes semantic
status and underlying I/O error detail; byte counts describe failed I/O paths.
Headers and NASM includes enforce16-bit offsets with C compile-time assertions.

Validation includes all200 selected entries and page starts under actual DOS,
short/suffix files, fragmented reads, failed reads/closes, pointer guards and
unchanged destinations. Independent actual-linked integration tests cover
serial/profile combinations, all16 CLI overrides, literal/legacy
targets, DIRECT and atomic semantic failures. The standalone browser has four CPU
groups and five DOS paths with exact4,000-byte screen/cursor restoration.

`standalone/test_directory_terminal.py` exercises actual DOS startup paths,
including browser editing/save/cancel/conflict, entry200, CLI overrides,
literal/legacy dialing, DIRECT, deferred accounting and unsupported bindings.
Synthetic PRM hashes stay unchanged; directory changes must match exact expected
record/date/count patches. Independent42-byte hardware snapshots restore.
Real local Synchronet, ENiGMA½ and Mystic tests additionally choose entry3 through
the browser before modem dialing and full message/file menu navigation.

```sh
./tools/build test-directory-dos test-directory-browser test-directory_dial
./tools/build test-terminal
```

The public evidence is in `docs/validation`; large runtime files stay under
ignored `build/`. No installed directory, password or private modem profile is
needed by these tests. Physical UART/modem behavior, complete original menus,
settings UI, automatic restart recovery, retry cycles, transfers, keyboard/META,
ASPECT and Host integration remain in the full [plan](../PLAN.md).
