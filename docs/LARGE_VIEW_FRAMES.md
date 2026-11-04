# Full-height shared view frames

The optional `--large-view-frames` build now saves and restores the full physical
text screen at 25, 28, 43 and 50 rows for the shared menu, history, clipboard and
elapsed-time owner. Incoming data reaches the real live screen beneath a view;
closing it restores all rows and the cursor. The full 63,000-byte live history
ring and separate frozen snapshot remain available.

This is a maintained UI integration step, not original pixel equivalence or a
complete application geometry implementation. It requires the canonical row
owner. It does not enable Ctrl--, apply startup display preferences, change
reference availability or install a new payload. The candidate still has 12
unavailable reference commands.

## Frame ownership and memory

The two shared far buffers each grow from 4,000 to 8,000 bytes. The synchronous
editor retains its 4,000-byte prefix lease of the live buffer; the editor/viewer
exclusion remains in force. Memory inspection verifies that exact prefix, all
other non-overlap rules, relocated segment pointers, retained endpoints and
capacity within a segment. Physical far UI storage grows from 12,000 to 20,000
bytes in this overlaid variant. There is no heap allocation or history reduction.

Four bytes of initialized near frame geometry and compiler alignment increase
ordinary data/stack allocation from 65,088 to 65,104 bytes. Resident CS remains
65,418 bytes, with 118 bytes spare. The diagnostic sibling uses 65,168 near bytes
and 65,428 resident CS bytes. This is not a zero-memory-cost change.

Admission checks BIOS mode3, 80 columns/page0, supported physical rows, agreeing
canonical physical height, and coherent larger-screen status/parser geometry.
Both caller frame identities and their full linked capacities must agree before
forming pointers or writing a frame. Unknown/incoherent geometry and forged
frame identities refuse. The legacy absent BIOS row byte is interpreted as25;
it cannot admit a canonical50-row view.

Frame height is captured for the lifetime of the owner. Existing geometry owner
exclusion prevents a competing internal row change. This does not guarantee
recovery if unrelated software changes VGA mode behind the owner.

History rendering, page movement and footer/search/export rows use the accepted
height. Other panels keep their existing25-row layouts. Their exposed lower
background is copied from the updated live underlay during reacquisition. A
nested clipboard can retain its history background; the live screen is still
restored in full on exit. Full original clipboard selection across larger text
areas and redesigned panel layouts are not established by this work.

## Verification

[Bound receipt](validation/large-view-frames.json) records exact build flags,
images, source identities, results and memory layout:

- 108 new linked inputs cover all four heights, both status states and four
  views; full updated underlays and guards; 64 sustained receive/repaint/query
  cycles; eight incoherent geometry/frame refusals; and full-height history
  pagination. Actual selector, BIOS-key dispatcher, UART ISR, parser, far frame
  and rendering instructions execute. BIOS, UART, date/time and DOS boundaries
  are modeled. Split-query continuation is delivered through the pending UART
  IRQ while the actual parser waits; its algorithm is not replaced.
- 943 existing control/display/reference/local-command inputs pass on the same
  ordinary image. The combined count is 1,051. No test count establishes complete
  ASPECT, binary-transfer, BBS or physical compatibility.
- Actual DOSBox-X8086 diagnostics record 32 view/restore observations: four views
  at four heights, repeated for normal and exclusive-output workflows. The real
  far key owner receives explicitly supplied normalized keys; these are not BIOS
  keystrokes. Independent Python checks validate every 8,000-byte captured return
  image and guard tail, lower panel backgrounds and the history footer location.
  Existing row/selector/video/shadow, PRM/image, zero-serial and 42-byte sampled
  UART/PIC/vector restoration checks pass. The diagnostic is rejected as a package.
- Ordinary, diagnostic and disabled images reproduce exactly from567/569/567
  public source files in empty trees without original artifacts or ancestor Git.
  The disabled image is byte-identical to the preceding status-control checkpoint,
  SHA256 `ee0bd6cd00295643f9500aed5ca4dd8b8552a102574f5d09a45affe739d7308f`.

The ordinary internal image is
`build/large-view-accepted-20261104/ordinary/TERMINAL.EXE`, SHA256
`ecc0c92ff7c6faa3e6a7794fc64a8bfde78485107a6a9220b84aa8777af7af90`.
The diagnostic is
`7f27e6a79828da17d84e5ea184cc764ea402be5db5b33630d21041eed3b1546d`.
Never package or install that diagnostic. Raw evidence remains under
`build/large-view-regress-20261104/`, `build/large-view-dos-20261104/` and the
three `build/large-view-proof-*-20261104/` directories.

## Remaining integration

Before exposing normal line changes, complete or explicitly guard the remaining
25-row modal contracts. In particular, the PROGRAM owner currently checks mode3,
80 columns/page0 but saves/restores only2,000 cells; that check does not verify
physical row count. Its DOS-child display/font restoration must be reconciled
with a larger canonical parent. The synchronous directory editor still owns a
25-row prefix. This component does not establish those paths at larger heights.

Then integrate normal Ctrl-- and startup preferences, test owned Enigma and
Synchronet layouts/editor/modal return at accepted dimensions, and verify the
bridge/session and physical Boca/SPA2102 route. Online resize requires separate
synchronization. [The Linux menu-size handoff](MENU_SIZE_BRIDGE.md) remains a staged
pre-session candidate. No installed source/config/service, package selection,
physical card or private configuration changed here.
