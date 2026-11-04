# Full-height PROGRAM display restoration

The optional `--program-display-owner` component now saves and restores the
parent's full text frame and cursor around ordinary DOS children at25/28/43/50
physical rows. It restores and independently verifies the original row height
before replaying the saved frame. Parent parser, margins, attributes, shadow,
RIS defaults and advertised text dimensions remain unchanged by this owner.

This closes the ordinary PROGRAM frame/font gap identified by the
[larger shared views](LARGE_VIEW_FRAMES.md). It does not enable Ctrl--, apply
startup preferences, install a package or establish every larger-screen modal
workflow. Reference availability remains12 unavailable commands in this variant.

## Owned return transaction

The component requires the larger shared-frame/canonical-row variant. The
PROGRAM save boundary validates mode3,80 columns/page0, supported physical rows,
canonical physical height, larger-screen status/parser layout and an8,000-byte
linked frame. The existing25-row logical-wide admission is retained; broader
logical-wide/larger-profile composition is not claimed by this work.

A successful save takes an exclusive lease, retains the visible frame and
captures the hardware cursor/shape in existing PROGRAM storage. The PROGRAM
initializer explicitly clears readiness, independently of BSS contents. A second
save refuses without overwriting the leased frame. The caller retains its existing
mouse pause and UART handoff sequence.

After a child returns, the new variant uses the existing resource-owner UART
quiet policy: restore parent DS/SS/SP with IF0, quiet the child UART, then resume
trap ownership. The memory inspector verifies the actual far calls and
relocations in that order. The DOS backend's existing context and result handling
remain responsible for the parent ABI and DOS child exit word.

Return forces the supported color text baseline and calls the recovered BIOS row
service to restore the saved height. Mode, page, columns, segment, stride and
actual row count must agree before any saved cell is replayed. Then the saved
frame, cursor and cursor shape return. New inline BIOS calls protect BP so a
cursor-shape service cannot corrupt the C stack frame. No parser/RIS reset is
inserted simply because a child used another display mode.

A failed/unverified restoration requests the existing fatal shutdown path with
exit2/service6EF7. It does not replay a larger frame over a verified25-row fallback.
Profile work, mouse resume and flow resume are skipped on this failure path.
The existing main loop checks quit immediately after PROGRAM polling, before
status work or parsing. Ordinary UART cleanup still completes. This is not a
promise to restore arbitrary downloaded fonts, VGA registers or palette state.

Inline adopted ASPECT views intentionally bypass old-frame restoration and
release the saved lease at the common return boundary. Their existing rendering
contract remains separate; larger-row ASPECT/profile adoption acceptance is open.

## Retained storage

PROGRAM's frame grows from4,000 to8,000 bytes. In this variant it still aliases
the mutually exclusive startup browser reservation. That reservation grows with
it; the browser's own copy policy remains25 rows. The memory inspector verifies
capacity, non-overlap, segment relocation and retained endpoints. Native-reset
and ASPECT rollback keep their existing4,000-byte prefix contract; a larger frame
does not by itself enlarge those transactions' supported geometry.

Far UI storage becomes24,000 bytes,4,000 above the preceding view-frame component.
Ordinary data/stack allocation remains65,104 bytes with the new scalar state. Resident CS shrinks from65,418 to65,372 bytes, leaving
164 bytes spare; the display owner itself resides in DISPLAY_CODE. No heap is
introduced. The diagnostic uses65,200 near bytes and65,414 resident CS bytes.
These are retained-memory measurements, not a claim of zero-cost code growth.

## Evidence

[Bound validation](validation/program-display-owner.json) records the exact flags,
images, source/input hashes, result identities and memory layout:

- 57 new linked inputs cover all heights/both status states; actual PROGRAM,
  COMSPEC policy, EXEC, trap suspension/resumption and context restoration;
  successful children, EXEC/resize/environment failures; pending UART input;
  tracked-online ownership; failed geometry recovery; exclusive leases; readiness
  initialization; child direction flags; and a BIOS cursor-shape BP clobber.
  Actual product instructions execute with declared BIOS/UART/DOS boundaries.
- The modeled return byte arrives at the explicit IF0 boundary after parent
  DS/SS/SP restoration. The actual IRQ receives it after UART reacquisition;
  the real parser consumes it after the full frame returns. Earlier child-owned
  IRQ activity is outside this test. Tracked-connected fixtures retain their
  connection state but are not real BBS sessions.
- 1,051 existing display/control/view/reference inputs pass on the same ordinary
  image, for1,108 combined linked inputs.
- Actual DOSBox-X8086 diagnostics perform eight real PROGRAM/COMSPEC/EXEC child
  launches, covering four heights in normal/exclusive-output runs. The owned
  source-built child selects graphics13 and appends an execution marker. BIOS
  return keys dismiss the real PROGRAM prompt. Independent captures verify parent
  physical/canonical rows and every visible frame cell; PROGRAM status4 and DOS
  child exit0 are recorded separately. The32 shared-view observations, synthetic
  PRM/image preservation, zero-serial output,42-byte sampled UART/PIC/vector
  restoration and diagnostic-package rejection also pass.
- Ordinary, diagnostic and disabled variants reproduce exactly from569/571/567
  declared public sources in empty trees without originals or ancestor Git.
  Disabling this component retains the preceding exact image
  `ecc0c92ff7c6faa3e6a7794fc64a8bfde78485107a6a9220b84aa8777af7af90`.

The ordinary internal image is
`build/program-display-final-bios-20261104/ordinary/TERMINAL.EXE`, SHA256
`e05186fee47c9ae0273dbe692d337d9cf7500202694709209a577e69d9faf59b`.
The diagnostic is
`687d37dc1027578b29d807d80b12689169461b63937d6ac40d44df96f355621f`;
never package/install it. Raw evidence is under
`build/program-display-verified-20261104/`,
`build/program-display-dos-accepted-20261104/` and the corresponding source-proof
directories named in the receipt. The diagnostic queues PROGRAM explicitly;
it does not exercise a normal command-launch hotkey or the normal main loop.
PROGRAM reacquires the UART inside that diagnostic, and its peer sends no data.

## Remaining work

The [large profile return checks](LARGE_PROFILE_RETURN.md) now cover confirmed
SETUP profile4/6 round trips with default/explicit keyboards and subsequent RIS.
Complete XLT/ASPECT composition, broader profile coverage and the other fixed
modal contracts before enabling normal Ctrl-- and startup preference application.
Then exercise owned Enigma/Synchronet layout/editor/modal return and the physical
Boca→SPA2102→SynthModem route. Online resize, transfer/carrier-loss routes and
complete original feature parity remain separate gates.

No physical machine/card, private configuration/call history, package selection,
installed SynthModem source/config/service or deployed PCPlus image changed.
