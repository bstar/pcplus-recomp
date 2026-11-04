# Native PROGRAM restoration at28 rows

Nested native PROGRAM now accepts the standard400-scanline/14-pixel28-row ROM
text view and restores it after graphics children. Previously admission excluded
28 rows; the restore helper would also select350 scanlines for any14-pixel font
and8-pixel ROM fonts for every non25 height. Those choices could not reproduce
80×28. The new28-row branch explicitly selects400 scanlines and BIOS1111h's
14-pixel font, then retains the existing independent mode/row/font verification
before any saved frame is replayed. Existing25/43/50-row branches keep their
scanline/font policy. Arbitrary downloadable fonts are not added.

This is a maintained platform extension around recovered display/process/UI
services; it does not relabel new C policy as recovered original instructions.
The exact recovered assembly/provenance checks still run during source builds.
No parent executable, package selection or physical installation changed.

## Evidence

The [receipt](validation/native-program-28-rows.json) binds the source-built child,
component and actual-session results, declared sources and independent rebuild.

-The native PROGRAM diagnostic now includes a28-row SAVE round trip through a
 real child that changes to graphics13h and mutates UART/PIC/vector state. It
 checks all2,240 saved cells,80×28 dimensions,14-pixel font and cursor/shape after
 return, alongside existing40/80-column, mono and25/43/50-row views and failure
 cases. The complete COM1/COM2 × NONE/SOFT/HARD/BOTH set checks exact peer bytes,
 queued binary input, serial restoration and expected flow transitions. The added
 round trip increases the expected software XOFF/XON pair count from14 to15.
-Linked rejection/ABI cases retain the previous no-IO/nonstack-write checks for
 invalid arguments, ownership, DS/SS and interrupt state.
-24 actual DOSBox-X8086 parent→ASPECT→nested-DOS-child workflows cover profiles4/6,
 all four physical heights, SAVE graphics, NOCLEAR graphics and NOCLEAR text with
 raw child status247. The child deliberately replaces UART framing/divisor,
 IER/MCR, PIC bit and IRQ vector while retaining DTR. A second, independent
 observation-only DOS child records the actual returned BIOS mode, columns,
 physical rows, font height and page. Its80×28/14-pixel record proves restoration
 outside the application policy itself. CHILD.LOG proves the intended mutating
 child ran exactly once.
-SAVE retains the full initial frame; NOCLEAR graphics intentionally leaves the
 new blank frame; raw247 NOCLEAR retains the child's visible text. All cases
 retain generated initial CPR/DA, post-parent READY/CPR/CSI18t replies, accepted
 dimensions, footer policy, parent JFT/sink ownership, expected synthetic directory
 accounting, immutable staged inputs/PRM and42-byte sampled UART/PIC/vector
 restoration. The artifact checker additionally validates child exit/cursor and
 sampled far-history content/relocation/bounds across EXEC.
-The source-built child is independently reproduced byte-for-byte from288 current
 public sources in empty trees, without originals or ancestor Git, using pinned
 Nix. The existing parent diagnostic images remain exactly those documented in
 [the larger session checkpoint](ASPECT_LARGE_SESSIONS.md).

The real ASPECT exit is distinguished from nested DOS exits by checking the
exiting PSP's parent. The observer never calls a renderer or supplies terminal
replies. Its existing literal BIOS-key scheduling and synthetic serial peer remain
explicit test boundaries. CHILD.LOG is an expected output with exact contents,
not an input-preservation exception without verification. The observation child
only reads BIOS/BDA geometry and writes GEOM.BIN; it changes no display state.

## Reproduce

Build the current public source snapshot through the child-build command recorded
in the receipt, under `./tools/dev --command`; use an empty tree to keep accepted
artifacts intact. The standard `standalone/build_native_program.py` also builds
the updated composed diagnostic. Its linked admission checker is
`standalone/check_native_program_admission.py`, and
`standalone/test_native_program_dos.py --label NEW` covers all COM/flow pairs.

Use `standalone/test_aspect_large_session_dos.py --build PARENT-BUILD --runner
ASPECT.EXE --profile 4 --rows 28 --nested save --output build/NEW` for the attached
path; repeat with profile6, other heights and `noclear-graphics`/`noclear-text`.
These use the existing non-deployable startup-height probes. Run
`standalone/check_aspect_large_session_artifacts.py --run RESULT-DIRECTORY ...
--output build/NEW` for independent capture/history verification. Exact hashes,
flags, commands and raw-result locations are in the receipt.

## Remaining work

The [dynamic-row notice component](ROW_CONNECTION_NOTICES.md) now covers normal
connection notices. Normal line switching/startup preferences remain separate. Partial CSI/errors/cancellation, carrier-loss
and reconnect, sustained in-flight data/flow stalls and transfer composition at
larger heights remain separate session gates. Broader emulations, ASPECT/Host
parity, owned Enigma/Synchronet and physical Boca/SPA2102/SynthModem acceptance
remain open. These synthetic DOS tests establish neither physical modem behavior
nor complete original feature parity. No private settings, call history, physical
card, installed bridge/service or deployed application changed.
