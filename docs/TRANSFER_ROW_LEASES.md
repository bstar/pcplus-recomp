# Transfer prompts on accepted text heights

The transfer prompt and progress display now use the bottom two physical rows
of an admitted25/28/43/50-row display. Previously they always used rows23–24,
placing them in the middle of taller screens. The owner still saves only320
bytes and leaves the terminal's canonical cursor, attributes, shadow planes and
history intact. This is maintained UI policy; no protocol engine was changed.

With the composed row-geometry component selected, acquisition verifies DS=SS,
IF1/DF0, the shared canonical row/status layout, narrow80-column strides and
actual BIOS mode3/80 columns/page0/height. An unreported BIOS height retains the
existing25-row interpretation. Both visible and hidden status layouts are
admitted at the linked boundary. Without that component the legacy25-row path
remains selected.

An admitted lease retains its physical byte offset and last-row coordinate in
the existing far CONFIG code owner. Filename input, titles, progress counters and
the hardware input cursor use those captured coordinates. A second acquisition
cannot overwrite the first saved underlay. Restore rechecks current geometry
against the captured lease before replaying cells, shape or cursor. Malformed or
coherently different geometry cannot receive an old frame: restoration requests
shutdown with exit7, preserves an existing transfer fault, releases visibility
and leaves the foreign video untouched. Ordinary invalid acquisition returns
the existing view fault8 before changing video.

## Validation

The [receipt](validation/transfer-row-leases.json) binds image identities,
manifests, checkers, immutable DOS captures and five independent source rebuilds.

-257 linked cases cover both terminal profiles, all four heights, visible/hidden
 status, manual/automatic prompts, all three protocols and both directions.
 Complete8000-byte video/canaries, canonical/reset defaults and far planes/history
 remain intact outside the two-row overlay. F2/Escape, duplicate acquisition,
 invalid mode/page/stride/height/flags, stale restore, coherent foreign-height
 changes and legacy unreported25-row BIOS geometry are included.
-The existing static bank/relocation verifier passes19 checks, including18 damaged
 target/return/relocation controls. The four public UI bridges and three resident
 callbacks retain their existing ABI.
-The old ordinary image passes the existing16-workflow transfer regression. The
 new ordinary candidate independently repeats those16 workflows.
-64 new actual8086 DOS workflows run the16 frozen recipes at25/28/43/50 rows,
 with explicit COM3/IRQ5,19200,8N1,HARD flow. They cover mixed-size and full-byte
 XMODEM data, CRC/NAK retry, local Escape and peer CAN; YMODEM batches, retained
 completed files and cancel/resume/retry on the same connection; and ZMODEM
 receive/send against the pinned independent lrzsz peer. The file vectors include
 NUL,1A,FF,XON and XOFF. Unfinished scratch files must be absent.

The new DOS observer chains INT10 without replacing a product callback or
injecting product state. Three source-address symbols identify actual cursor-read,
prompt-cursor and restore calls; selected-image instruction bytes bind those
addresses. The observer captures the two physical rows and BIOS geometry/cursor/
shape before acquisition and after the real BIOS restore. It separately witnesses
the overlay at the expected bottom rows. All68 leases, including the four second
attempts after cancellation, require exact before/after bytes and metadata.
Original caller IF/DF are retained when forwarding BIOS condition flags.

The remote peer finishes the explicitly requested lower-row CPR before beginning
binary negotiation. Its protocol parser does not silently discard a terminal
reply as packet data. A separate artifact verifier checks raw BIOS samples,
placement, known binary source/destination vectors, parser/keyboard return,
scratch cleanup and the existing UART/hardware snapshots. Actual hidden-status
protocol sessions and physical BIOS/video acceptance are separate from the
linked hidden-layout cases.

The ordinary image is
`c78b77de415a10d63e42b5d99afad9108b59e2effd636cc13154248bd720001e`.
It retains65,120 near bytes and65,484 resident CS bytes; CONFIG_CODE grows from
59,105 to59,313 bytes. No resident code or saved-screen capacity was added.
Diagnostic parents retain65,510 resident bytes and cannot be packaged. Five
569-source parent rebuilds reproduce exactly without original executables or
previous object files. No original UART instruction, transfer framing/CRC policy,
keyboard shortcut, splash, private configuration or deployed file changed.

These direct nullmodem sessions do not supply modem DCD transitions, SIP/audio or
Enigma/Synchronet acceptance. Actual modem loss during X/Y/ZMODEM frames, cleanup
and same-parent redial remain next, followed by wider modal/line-control/startup
composition and physical validation. The full application-parity inventory and
overall goal remain open. The selected deployment package and installed bridge
remain unchanged.
