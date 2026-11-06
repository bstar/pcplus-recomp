# Deferred stream storage: recovery and package checkpoint

The normal parent `61757956` and ASPECT `cbdee194` now have refreshed recovery
coverage and a reproducible connection package. This extends
[the deferred-storage checkpoint](DEFERRED_SCRIPT_BUFFERS.md); it does not
establish physical acceptance or full original PCPlus parity.

## Recovery evidence

Twenty-four DOS386/UMB runs exercise six active screen-lease phases
(17,5,6,8,10,22) with owned-DS divide, foreign-DS divide, typed abort and direct
dispatcher unwind. Six stream buffers and six exact saved copies are live
before each fault. A passive exit observer reads the actual twelve pointer
fields at each of four interpreter exits: all 48 words are zero. Subsequent
scripts, six held files, complete viewport, keyboard, hardware and ownership
checks pass. The observer does not call product cleanup or alter its fields.
Diagnostic builds assert the native owner/snapshot structure sizes (14/22)
and pointer offsets (12/20). Normal diagnostic-disabled ASPECT remains exact
`cbdee194`.

Four representative diagnostics reproduce from clean 1706-source exports.
Whole-image comparisons show only the two phase-immediate bytes change across
the six variants in each group. This is four source exports, not twenty-four.
The assembled passive hook passes 36 ABI/filter cases. An independent audit
rereads raw exit and pointer captures and rejects six copied negative controls:
wrong pointer, phase, live count, error and either omitted mandatory check.

The harness refresh found that detailed fault assertions had become nested
under an incompatible WAIT option. They are now unconditional for fault runs,
with mandatory-check assertions in both producer and independent audit. Earlier
accepted original fault reports predate that indentation error; these new runs
provide fresh dynamic-storage evidence.

Four normal runs hold six streams across WAIT, using Space and Escape on
unobserved8086 and separate observed386/UMB configurations. Files remain exact.
Escape continues WAIT here; this does not claim general script cancellation.

## Reproducible package

`standalone/deferred_connection_candidate_recipe.json` pins the tested parent,
deferred ASPECT and all ten public package files. The parent explicitly uses
the tested128-pair dictionary. An initial inherited64-pair recipe produced a
different parent and was correctly rejected by the hash gate; that failed
build remains local and is not the accepted package.

The canonical Nix build and a separate clean2293-source export reproduce five
executables, ten package files and ZIP SHA256
`3c99eface0963806d233ab1e3bd5240918f0ae46980ac367d98ed761a0df81d4`.
The export contains no original executables, prior objects, private settings or
ancestor Git metadata. Packaging also refuses diagnostic application builds.

Actual DOS8086 splash, setup and precompiled-script launcher tests pass with
COM3/IRQ5 and an omitted BIOS UART listing. Both applicable launchers capture
the magenta splash and LoC annotation; all three restore hardware/environment,
preserve private PRM/DIR/XLT fixtures and leave package bytes unchanged.

Exact report hashes are recorded in
[the checkpoint receipt](validation/deferred-buffer-faults.json).
Earlier Enigma carrier-loss/redial/exact retry and Synchronet editor receipts
already use these exact normal parent/child bytes. They retain their original
test scope; diagnostic variants are not deployed as application builds.

## Deployment and remaining work

The reviewed package is
`build/deferred-connection-candidate-final-20261106/package`, with public payload
under `PCPLUS` and archive under the sibling `archive` directory. The selected
physical release remains RBC96FB9. The deployment doctor returned unreachable
(`No route to host`); no physical files, selector or production SynthModem
service were changed at this checkpoint.

Next: regain the management connection, verify fresh machine/configuration
identity, select this package and perform reversible application-only deployment
with independent readback. Then obtain physical Boca/SPA2102/LoC rendering,
flow-control and transfer observations after rebooting out of network mode.
Broader commands, ASPECT, emulations/protocols, Chat and Host parity remain open.
