# New keyboard files

The source helper now opens an absent KBD leaf as an unsaved blank33-profile
table. Alt-S, or Yes at the dirty-exit prompt, creates it through the checked
staged-save backend. Exit without changes and edit/discard create nothing.
Existing short files retain their original length. No factory bindings are
imported or invented.

This behavior follows recovered original evidence rather than an assumption
that the helper supplies factory mappings. Original SHA256 `f079418f…` load
routine CS:0714 clears the first byte of each79-slot/33-profile binding after
an unsuccessful open. Save CS:0970 writes31284 bytes after conversion. Four
actual original DOS8086 observations confirm absent-file exit, blank explicit
save, edit/discard and exact edited save. Originals and full REA exports remain
outside public Git. The [receipt](validation/keymap-newfile.json) binds addresses,
Evidence IDs and observations.

The maintained extension admits only DOS error2 for a missing leaf. A missing
parent directory, malformed/truncated/empty existing file, read error or close
uncertainty does not become a blank replacement. Explicit creation uses the
existing absent-target checks and exclusive staging; existing recovery files
remain untouched. After a successful creation, subsequent saves compare the
saved baseline as they do for existing files. The original's broader failure
and replacement behavior is not adopted where it would discard existing data.

Alt-O can open a new basename, discard an unsaved new table, or return to an
existing shorter file. The new-file footer identifies that Save creates the
file. Existing-file ready screens retain their previous rendering. Under the
parent, creating the selected default PCPLUS.KBD publishes its new binding on
return. Creating a different file in the helper does not redirect the frozen
parent selection. Discarding a missing selected file leaves the file absent;
the existing reload-error acknowledgement preserves the live mapping.

Helper `5a917b93…` passes15 new-file workflows,14 existing full-file workflows,
19 prefix workflows,11 parent regressions and three connected parent creation/
discard/frozen-selection sessions. All use owned files and check exact bytes,
screen/cursor restoration or actual UART/hardware restoration as applicable.
The18-input clean-source export reproduces the helper. Linker memory is70112
bytes,192 more than contract2; the4096-byte stack and peak-image strategy remain.

Actual stock Enigma and Synchronet edit/save/return sessions with existing
seven-profile files pass with the new helper. Independent editor-cell/cursor
and size audits show zero different cells, and Synchronet's measured RTS pause
is8.897 seconds without BBS delivery. Enigma uses DOS8086; Synchronet's
diagnostic TSRs use386/UMB. These are software serial/Telnet tests, not a
physical Boca/SPA2102/SIP/audio call or a test of new-file creation inside a BBS
editor. Reviewed package promotion, private configuration and physical
acceptance remain separate. The installed payload and selector are unchanged.
