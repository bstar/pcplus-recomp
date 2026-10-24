# Current IRQ upload through framed ENiGMA

The current full IRQ terminal and register interpreter pass an actual DOS8086
upload session on COM2/19200/HARD/IRQ7. DOS compiles and runs the login script,
the client uploads a 65,539-byte binary and an empty file, the detail forms
complete, and the same connection returns through file search to the NFO view.
The [receipt](validation/irq-upload.json) binds the current products, input
sources, wire captures, official catalog records and retained failed attempts.
There are no application binary changes in this checkpoint.

The terminal SHA256 is
`31303aa66e1154848363e1b29a4353915e99b0a2bbb74444b03c0e0d288132db`.
Independent replay verifies binary and empty-file offers, payload CRCs, ZEOF,
the opposite receiver's ZFIN and final OO. Both installed files match exactly;
official FileEntry records have the expected size, hash, description, area and
synthetic uploader. Unknown source timestamps are explicit on the wire; received
creation times fall inside the observed run. Source files remain unchanged,
the 42 sampled hardware bytes restore, and no editor post is saved.

## Observer and evidence corrections

The original upload observer reserved 2,560 resident bytes for a maximum of
twelve eight-byte events. With the current larger parent, the first attempt
created no compiled login script and scheduled upload keys reached the login
prompt. It was deliberately interrupted after that failure; it cannot prove
hardware restoration. A separate short diagnostic exited normally and restored
hardware but likewise produced no compiled script or authenticated session.
Both results remain failed, with the exact original producer sources retained.

An explicit `--compact-observer` retains exactly 96 event bytes and collects a
102-byte report. Its event handler is identical to the original; report decoding
pads only the unused tail before applying the existing form checks. SNAP.COM
shrinks from 6,087 to 1,159 bytes. The same application products then compile the
login script and complete the upload workflow. This establishes sensitivity to
the test observer's conventional-memory footprint, rather than general freedom
from DOS memory limits. Cancellation retains its separate observer layout.

The first corruption-audit invocation also remains recorded. It changed only
the last NFO heading, leaving another valid post-upload heading in the capture.
The corrected missing-NFO test changes every copy; the replay verifier itself is
unchanged. All fourteen corruptions now reject, covering wire data, empty-file
boundaries, completion timing, NFO response, catalog data and unknown dates.

## Server boundary and reproduction

The initial preparation correctly refused to mix the old lab revision with the
newer LAN board revision. A separate clean checkout of
`237cd9743d6978a940dd66db0e78f6ab8ccd3e37` was exported and passed fresh decoder
checks using explicit revision/client pins. The relevant client/upload files
match the older lab byte for byte. Installed dependencies were reused; this is
not a clean dependency build. Only selected menu/module/art inputs were read
from the LAN board; synthetic fixture accounts, files and databases remain
isolated. The temporary server is stopped and port 23234 was verified free.

Follow the [upload fixture workflow](../lab/bbs/enigma-upload.md), using a fresh
checked candidate at the same explicit revision as the selected source board.
The upload command now accepts `--terminal`, `--runner`, `--compiler`, `--cpu`,
`--irq`, `--mouse-scales` and `--compact-observer`. The recorded run uses the full
guarded custom-IRQ terminal, `build/aspect-register-parent-custom-irq/ASPECT.EXE`,
`build/aspect-compiler-dos/ASPCOMP.EXE`, `--cpu 8086 --irq 7 --mouse-scales 8 4`,
`--upload-bytes 65539` and the compact observer. Run
`check_enigma_upload_audit.py` afterward; the receipt script verifies the retained
lab layout after stopping the fixture.

This covers one successful upload session with the incremental server decoder.
Reconnects, cancellation with this exact composed build, sustained load,
unmodified-stock fragmented input, LAN deployment, physical modem/ATA behavior
and the full native application remain open. The disconnected card is unchanged.
