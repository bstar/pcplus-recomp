# Original file-command recovery anchors

The [runtime follow-up](validation/file-tools-original.json) now adds five
unmodified-original DOS workflows, and the [private search owner](FILE_FIND_OWNER.md)
provides a source-built enumeration prerequisite. This supersedes the earlier
unknowns below only where the following observations supply direct evidence;
The later optional [File Directory frontend](FILE_DIRECTORY.md) now enables
the listing in its source candidate. View a File remains unimplemented, and
the installed release is tracked separately by the private package selector.

## Enumeration and original runtime follow-up

Fresh REA evidence traces CS:5B71 through the DOS4E/4F carry result and shared
43-byte DTA at DS:CEB4. Attributes are at DTA+21, time+22, date+24, size+26,
and name+30. A zero caller argument copies the name; the listing's nonzero
argument selects formatting. Exact attribute10h selects the directory format;
the branch is an equality comparison, rather than a test of the directory bit.
The recovered date fields are month/day/(DOS year+80), hour and minute.
The format strings use a left-justified12-character filename and either
`<DIR>` or a minimum6-character unsigned32-bit size. Month has minimum width2;
day, year, hour and minute have minimum precision2. Those are minimum widths,
not bounds: year2026 is rendered126 by the original.

The original offline runtime, on owned synthetic files, confirms:

- Alt-F prompts for a file specification; a trailing directory backslash
  selects its contents. A small listing includes `.`, `..` and the subdirectory.
- At25physical rows, the listing has15entry lines, its original heading/frame,
  and a `- MORE -` acknowledgement when the page is full. Space continues the
  next page; Escape returns to the byte-identical pre-dialog screen. The
  observed enumeration order is the DOS-returned order of these fixtures;
  no general filesystem sort-order guarantee is inferred.
- A missing specification displays `File(s) not found` and acknowledges back
  to the original terminal screen.
- Alt-V with the reference settings opens the internal viewer. Its first page
  displays lines1–24 with a footer. Page Down advances to25–48; Page Up restores
  the complete first frame. A separate workflow advances through lines49–72,
  then Home restores the exact first frame. Escape restores the terminal.

The native three-digit year also leaves a trailing digit in reused listing
rows when the next page contains shorter1993 dates. This is an observed native
presentation defect, not a requirement to introduce stale characters into the
maintained UI. The date/clearing policy needs an explicit documented correction
when the frontend is integrated.

All five accepted workflows use one frozen local producer script, the same
original executable identity, passive timer/VGA capture and a dummy UART.
Raw4000-byte screens and producer/resource identities are retained locally.
The timer's additive checksum is not an exhaustive video-event trace; the
receipt checks complete captured frame bytes and expected content. An earlier
viewer attempt used invalid ADDKEY token `pgdn` and timed out; the accepted
fresh recipes use `pgdown`. No synthetic analysis image was executed.

The subsequent [internal viewer recovery](FILE_VIEWER_RECOVERY.md) establishes
chunking, clipping, tabs/binary bytes, long-line/EOF behavior, missing-file retry
and a seek beyond64KB in eight more original workflows. Detailed DOS error paths
and configured external-viewer PRM binding still require recovery.

Fresh REA/Ghidra evidence identifies the original 2.01 Alt-F directory listing
and both Alt-V viewer paths. This is a static recovery checkpoint; it does not
enable either command in the maintained application.
[provenance.json](../reconstruction/file_tools/provenance.json) binds the original
SHA-256, byte regions, loader routing and retained Evidence IDs. Full REA bundles
remain in ignored local analysis storage. Analysis images were never executed.

## Entry routing

The original scan-code dispatch table at DS:44E0 maps Alt-F/scan21h to CS:1302
and Alt-V/scan2Fh to CS:1374. The resident wrapper bytes read by REA agree with
the original executable. Appended overlay32 provides the initialized table;
the bare resident MZ does not initialize that data for a static analyzer.

| Action | Native route | Observed contract |
| --- | --- | --- |
| Alt-F | CS:1302 → BB6B → overlay18:F08E | Calls the native screen-boundary helpers around the listing controller, passing zero for an interactive file-specification prompt. |
| Alt-V, configured command nonempty | CS:1374 → BA87 → overlay3:DE2C | Reads the command at DS:1EE1, validates its length, builds an 80-byte local command including the selected filename at DS:CE6A, then calls the existing program-launch controller. |
| Alt-V, configured command empty | CS:1374 → BB2F → overlay20:E660 | Passes zero to the internal viewer controller, which prompts for and opens a file. |

The current PRM field binding of DS:1EE1 has not been recovered here. The
original editor command at DS:1F22 is a separate resource; it must not be
substituted for the viewer merely because both can launch external programs.
The command-length validator and exact appended separator flags still need
separate review before adapting external invocation.

## File Directory controller

REA identifies a 366-byte controller at overlay18:F08E. A zero argument opens a
file-specification field with native size argument `0x40`. An empty accepted field selects `*.*`;
a trailing drive colon or backslash appends `*.*`. Escape from that prompt
returns without enumeration. A nonzero argument supplies the specification.

The controller enumerates entries through separate helpers and displays pages
of physical-row-count minus 10 lines. Escape closes the listing; another key
continues when a full page was printed. A partial final page closes after its
key acknowledgement. Whether the prompt size includes its terminator, and the exact heading, entry
formatting, ordering, attribute filtering and error presentation are not yet
recovered.

The 20-byte first-enumeration helper at CS:5B54 installs DTA DS:CEB4 with DOS 21h/1Ah
and selects DOS 4Eh; its next helper at CS:5B68 selects DOS 4Fh. They share CS:5B71.
These are instruction observations. Complete DTA preservation and continuation
semantics require tracing that shared helper and testing real DOS behavior.

The native controller callee-cleans its one-word argument. A maintained far
adapter must preserve the project's DS=SS ABI explicitly; decompiler type
inference alone does not define a safe cross-bank C interface.

## Internal View a File controller

The 408-byte controller at overlay20:E660 prompts for a filename (native prompt-size
argument `0x2B`), retries an unsuccessful open, then calls separate display/page
helpers. Escape closes the file and restores the screen. Home seeks to the
start; Page Up and Page Down route through distinct native page helpers. Other
keys loop without taking those paths. This does not establish complete text
formatting, wrapping, binary-byte treatment or page-position behavior.

The default synthetic overlay context did not expose this function to Ghidra.
The already established entry-anchor context admitted it without changing its
original code bytes. That discovery difference is not absence of a feature or
permission to execute a synthetic analysis image.

## Next implementation work

1. Trace directory enumeration/formatting and viewer page/read helpers. Preserve
   bounded failures and distinguish native observations from maintained changes.
2. Capture the original command screens and key behavior in DOS using synthetic
   files only: empty/multiple pages, wildcard, directory/drive paths and viewer
   Home/Page Up/Page Down/Escape.
3. Implement banked, serviced foreground owners using the existing frame/mouse
   interfaces. Preserve incoming UART/parser service and protect capture, printer,
   file identity and DOS DTA ownership. Do not assume a chooser or editing action
   is part of the listing's original contract.
4. Verify absent/read-only files, invalid paths, media errors, cancellation,
   child failure and normal return. Bind direct keys and Alt-Z/browser actions
   only after those owners pass; rerun BBS rendering and transfer/reconnect checks.

The original API may block in a native keyboard helper. A serviced maintained
implementation must document that adaptation rather than claiming identical
scheduling. Both commands, external-viewer configuration integration, original
runtime parity and all remaining F15/F01–F16 obligations stay open.
