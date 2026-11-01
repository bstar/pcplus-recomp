# Frozen settings context selection handoff

The terminal and settings owner retain separate copies of the current directory
selection. Publishing only terminal globals would leave subsequent settings
reloads comparing against the old board. `live_setup_select` updates the frozen
settings context through an exact expected-old comparison and re-decodes the
new selection's source baud and clipboard baseline from the accepted PRM.
Negotiated UART speed and session separator remain separate active state.

This is a component prerequisite behind `DIRECTORY_RESOURCE_ADOPTION` and
`TERMINAL_DIRECTORY_RETIREMENT`. The live directory UI does not call it yet.
The caller must still own the foreground selection/UART/resource transaction,
validate accepted-image and proposal freshness, and publish terminal globals.
The API performs no file IO, serial operation, script execution or dialing.

Arguments are disjoint near allocations with DS=SS: expected context496 (NULL
only before a first directory selection), next context496 and accepted PRM1264.
Action0 validates without publication; action1 repeats checks before committing.
The expected context must match every retained byte, including dates/counts.
The next PRM request must match the bound request spelling; the frozen canonical
PRM and next directory identity must fit absolute uppercase DOS83 names. New
entry numbers, code policy, global settings, selected record and transfer path
are validated before mutation. The caller remains responsible for file/page
provenance; canonical spellings are not filesystem locks or authentication.

Actual `directory_pending` or `directory_pending_count` refuses the handoff,
even when only one is set. Pending setup transactions and unacknowledged offers
also refuse. This API does not save old statistics; the foreground owner must
retire them successfully first. Reconciliation changes the exact expected-old
context: an older copy must fail after accounting has updated its date/count.
Every refusal preserves the existing settings binding and pending offers.

After publication, a settings reload uses the new frozen selected record and
the existing frozen canonical PRM. The source rate is decoded without CLI
transport overrides. It must not be confused with the negotiated current rate:
an unrelated settings reload must preserve that negotiated speed and the
session separator when their saved source values have not changed.

The [receipt](validation/setup-selection-handoff.json) binds 11 DOS8086 workflows
covering first/replacement selection, a read-only check, stale/reconciled
accounting contexts, both pending-statistic indicators, pending settings/offers,
invalid extents/aliases/identities/data, and a 63-byte directory identity. Every
selection invocation checks that IO counters are unchanged. The 11 workflows
pass 309 native assertions. Subsequent settings
finishes read the real PRM and verify new entry, negotiated speed and separator.
The synthetic PRM and directory files remain byte-identical. The component uses production decoders,
setup owner, the recovered command expander through its bounded wrapper and actual DOS filesystem;
wrappers only count DOS calls and preserve their real pointer/return ABI.
An isolated 36-file committed-source export reproduces SELECT.EXE and 16 objects
and repeats all 11 workflows. The 776-source application control reproduces all
ten package files; all five executables and nine files match the prior package,
with only the source-base commit line in VERSION.TXT updated.

```sh
./tools/dev --command python3 standalone/build_setup_selection.py
./tools/dev --command python3 standalone/test_setup_selection_dos.py \
  --output build/setup-selection-NEW
```

The application selection/resource/UART commit, script execution and dialing
remain open. Full F01–F16, independent complete BBS rendering comparison and
physical Boca/SPA2102/card acceptance remain open. No live BBS, bridge, ATA,
network interface or card is modified by this component test.
