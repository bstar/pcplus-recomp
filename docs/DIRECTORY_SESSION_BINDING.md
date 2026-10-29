# Bind directory previews to the actual session

The directory resource preflight now rejects a stale preview before queueing
PROGRAM and rechecks it after serial handoff, before resource reads. The
preview retains the actual 628-byte configuration plan and 66-byte transfer
preferences used to calculate the selection. Both checks capture the actual
session again and compare all 694 bytes, rather than comparing against the
configured PRM or assuming the preview is still current.

The supported actual fields include the active COM/I/O/IRQ, DTE speed, framing,
flow, emulation profile, display policy, modem configuration, logical directory
plan and transfer preferences. The existing capture service supplies the data
under its actual-session policy. This is a snapshot of these planes; it does
not bind every mutable application object, such as key/action contents,
independent accounting ownership or translation-table bytes.

The retained session and two 16-bit seals occupy 698 bytes at inactive frozen
history offsets 5602..6300. The seals bind the proposed selection and accepted
in-memory PRM as they were at preview creation. They detect accidental damage,
not authenticity, external-file freshness or a transaction generation. The
actual-session comparison is exact and does not use these seals. Active popups,
then the admitted pending/active PROGRAM owner, preserve the far-buffer lease.

No new near data or resident code is needed: near DATA/stack remains 64,976
bytes and resident CS retains 208 spare bytes. Minimum module retention grows
from 409,872 to 410,240 bytes in the opt-in owner build. The existing 63,504-byte
inactive frozen-memory loan still permits actual nested ASPECT compilation and
subsequent history viewing. The ordinary, LoC.6 and CLI-only controls stay exact.

## Evidence

The [validation receipt](validation/directory-session-binding.json) identifies
the candidate, package and test artifacts. A clean export of committed source
`5e40947`, without ancestor Git metadata, rebuilds all ten package files exactly
from 768 declared source inputs. Eight linked admission cases cover
changes to actual baud, profile, modem settings, transfer preferences, accepted
image, proposal and retained session, plus an unchanged successful queue/cancel.
They execute the actual UI, capture and queue code. Refusals preserve the changed
session and keep the preview open, without resource DOS calls or transmitted
bytes. These tests model filesystem, BIOS and UART boundaries.

Nine DOS owner workflows retain the existing valid/malformed/default and nested
popup checks. Explicit fault builds separately alter the queued proposal, one
transfer setting or the actual DTE speed at the mouse-suspend boundary. The
worker rejects these changes before any resource DOS call. The DTE fault uses
valid 38,400 baud rather than an invalid-rate shortcut. All active bytes other
than the declared injected fault, original resource files and final hardware
baselines remain intact. Nonfault cases use a passive observer.

The far-cdecl capture adapter has an independent byte/relocation check and a
damaged caller-word control. Existing directory preview tests observe a full
owner stack high-water mark of 6,358/8,192 bytes. The unchanged memory-loan logic
passes its 14 linked cases for the new layout, and native packaged START runs
the nested compiler and reopens the frozen viewer. Stock ENiGMA login/editor,
online refusal and preview checks pass through the actual SynthModem proxy,
with 250 ms key-sequence framing and no artificial input-byte delay.

The ENiGMA `exact_screen` predicate is historical: it checks the 4,000-byte
frame size and final draft/cursor markers. It is not an independent full
character/attribute oracle or a claim of perfect BBS rendering.

## Remaining adoption work

The R action still checks resources only. It does not adopt the selected entry
or dial. Before that publication can be enabled, stage translation/scripts,
retire the previous selection's pending accounting without losing recovery
ownership, reconcile retained logical context for setup/script projection, and
apply selected UART/profile/KEY/KBD/target/transfer state with explicit failure
and rollback rules. Repeat the relevant state checks immediately before commit.
The full F01–F16 scope, physical Boca/SPA2102 acceptance and card deployment
remain open.
