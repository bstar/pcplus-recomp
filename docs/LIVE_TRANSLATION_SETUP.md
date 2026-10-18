# Confirmed input-mode changes from setup

Alt-F10 now applies a saved input translation mode during the running session.
In PRMEDIT, select **Input translation** on the Terminal page, save with F10 and
exit the editor. A separate Y/N prompt offers to apply the new mode. Y accepts;
other keys retain the current mode. The saved PRM remains available for next
startup even when the live change is declined or cannot be applied.

| Mode | Applied receive behavior |
| --- | --- |
| 0 | Identity, FFh driver mask |
| 1 | Checked 256-byte default XLT table, FFh driver mask |
| 2 | No table mapping, 7Fh mask at UART dequeue |

An explicit `/X:FILE.XLT` keeps its active table/mode override. A saved PRM mode
edit cannot replace that override, and invalid raw PRM settings still reject the
whole candidate. Serial and supported-profile questions remain independent of
the translation question. Mode changes do not alter physical UART data bits.

## Staging and ownership

The existing PROGRAM/setup owner drains output, pauses configured flow and
releases parent UART interrupt ownership before launching the editor. Before
that child runs, `xlt_live_bind` captures absolute current-directory and optional
PCPLUS-directory table paths. Relative environment paths are resolved in that
same namespace. Paths must fit the checked reader's 63-byte limit. A child that
changes the shared DOS current directory or modifies environment bytes cannot
redirect adoption to another table.

After the PRM is reread and fully validated, the translation owner stages the
proposed mode. Mode 1 reads exactly 256 arbitrary binary bytes and checks EOF
and close into private storage. It tries the bound current table first and only
uses the bound fallback after file/path-not-found. A damaged or inaccessible
current table is never hidden by fallback. Modes 0/2 need no table read. An
unusable fallback does not block a valid current table or modes that need none.

Confirmation occurs after successful staging. The final commit rechecks that no
parser, transfer, monitor or dedicated print-controller owner is active. It
copies the staged table, then installs the mode/enabled/mask state while input
is still handed off. No second file read occurs after confirmation. Only then
does the existing owner restore the view/profile, UART and receive flow.

Queued raw receive bytes are retained. Bytes dequeued after return use the newly
accepted mode; the prompt states this explicitly. RIS retains the accepted
mode/table/mask. Binary transfers continue to reject a non-FFh receive mask.
Output, terminal replies and protocol bytes keep their existing raw contracts.

Decline, namespace/read/size/close failure or unsafe ownership keeps the active
mode/table/mask. Independent valid display/pacing/modem edits can still apply.
A later modem-preparation failure prevents the accepted table from being
installed as part of that failed settings transaction. Failure/busy notices
require acknowledgement even if another independent change was accepted.

This is maintained staging around source-owned PRMEDIT, not the original
PCSETUP shared-memory child interface. Same-mode table reload and opening
XLTEDIT as a dedicated terminal command remain open. Editing a table on disk
does not silently replace the active in-memory table. The lookup is not a
concurrent-writer lock or a physical modem flow-control guarantee.

## Build and validation

```sh
./tools/build test-live-translation
./tools/build test-terminal
```

[Live mode validation](validation/live-translation.json) binds 331 linked inputs,
10 actual DOS workflows, all 147 damaged configuration-frame/layout cases,
the 66-command terminal regression and a 63-output fresh public-source rebuild.
The linked tests run the actual owner, parser/driver, namespace resolver, DOS
reader and cdecl/far adapters; only DOS/BIOS/UART boundaries are modeled.
Declared fault cases mutate input state at child return or commit without
skipping a product function. They cover all mode pairs, declines, all 256 table
outputs, fragmented reads, stale namespace changes, queued high-bit input/RIS,
late ownership changes, mixed profile choices, native prepare rollback and an
unbound backend with deliberately poisoned DOS BSS.

The DOS workflows use production PRMEDIT for table and 7-bit enable/disable,
decline, failed table loads, environment fallback and explicit `/X`. Fresh peer
bytes and cursor replies verify the effective receive transform, alongside
unchanged fixtures and independent UART/PIC/IRQ snapshots. A separate
source-built diagnostic child edits the same PRM field and changes CWD to prove
that the old table/PRM namespace remains selected. Its executable is also
rebuilt independently from public source. No original or synthetic analysis
executable is an input. Physical UART/modem timing remains unverified.
