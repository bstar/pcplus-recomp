# Key Mapping Help

Alt-Z in the mapper now opens the authored Key Mapping topic, context17,
with the full source Help viewer: navigation, Topics, Search and Continue.
Previously action84 was mislabeled About and displayed a version notice.
Recovered original dispatch routes2C00 to CS:0E4D's PCHELP producer; the
descriptor reads the context word at DS:10C8. REA observes17 at linear14FD8.
[The receipt](validation/keymap-help.json) binds the native Evidence IDs and
all accepted application tests. No proprietary HLP content is used.

The maintained mapper links the same viewer code used by PCHELP.RTE. An
additional Help process does not fit in the tested conventional-memory parent:
a smaller76176-byte source control using the native descriptor/EXEC interface
gets actual DOS error8 for PCHELP.RTE at both seven and33 profiles. It still
returns to editing/saving/input without losing files. The82432-byte embedded
mapper passes both complete Help interactions with the same parent/checker.
This changes placement from the original's external process without reducing
the viewer's topic/search functionality. Existing4096-byte mapper stack,
31284-byte baseline allocation and parent/history buffers are retained.

Embedded Help reuses the mapper's immutable displayed frame for restoration;
it allocates neither another DOS process/stack nor a separate screen image.
Each entry resets viewer search/topic state. It reads only the matched sibling
PCPLUS.HLP, independent of CWD/PCPLUS environment. PCHELP.RTE is unnecessary
for this embedded entry but remains packaged for the main terminal's Help.
Missing or malformed HLP returns to the mapper with edits retained. Existing
and newly created keyboard files keep their checked-save policies.

Nine standalone DOS8086 Help cases cover clean/dirty full and shorter files,
repeat entry, actual Topics/Search captures, missing RTE, and missing/bad HLP.
Every case checks exact KBD bytes and final screen/cursor/shape restoration.
Two connected DOS8086 parent cases independently observe context17 and require
save/live-binding resumption, normal exit and UART/PIC/vector restoration.
The two source external-process controls use the identical checker and passive
observer but require actual EXEC CF/error8 and no Help frame. The bounded DOS
observer chains the real kernel, restores its INT21 vector and repairs its
saved SS:SP/BP before observing post-EXEC results. Initial unaccepted observer
runs lacked that repair; those failures do not establish application damage.

The14 full-file,19 prefix-file and15 new-file workflows, plus11 parent
regressions, also pass with the larger mapper. Its29-input isolated source
export reproduces SHA256 `c94d43ba…`. The parent `44891156…`, standalone
PCHELP `f163169f…` and authored HLP `45c6cdba…` remain byte-identical.

Actual stock Enigma and Synchronet sessions open Help inside the mapper while
the BBS editor has an unsaved draft, then save and return. A passive title
observation proves context17 appeared. Exact4000-byte BBS frames/cursors,
continued editor input, draft abort, zero exit and independent reference/size
audits pass. Synchronet's RTS pause is12.851 seconds with no BBS delivery.
Enigma uses8086; Synchronet's diagnostic TSRs use386/UMB. The lab now stages
verified global-Help resources alongside copied applications. Enigma retains
the500-character DOS limit by removing its redundant final exit and an
unnecessary synchronous return pause; the full command remains499 characters.

These are software serial/Telnet checks. They do not prove physical
Boca/SPA2102 audio/CTS/DCD, private configuration, every Help context/geometry
or complete original feature parity. Reviewed packaging is a separate
checkpoint; the selected installation and physical machine are unchanged.
