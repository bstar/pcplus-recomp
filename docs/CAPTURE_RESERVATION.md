# Shared file identities for the recorder

The [reservation checkpoint](validation/capture-reservation.json) adds one stable
external file owner to the canonical identity checks shared by capture, screen,
monitor and history output. The recorder's eventual destination, scratch and
backup identities can use this interface. The actual recorder publisher and
Record UI remain unimplemented; this checkpoint does not accept those features.

The API accepts a pure far probe and a near context. The probe returns nonzero
for an absolute DOS identity it owns. Registration first checks all currently
open or uncertain binary sinks; a conflicting owner rejects registration
without changing either sink. Every later sink begin checks the external probe
before opening or truncating anything. Different paths remain usable alongside
the reservation. Release requires the same function/context pair. A different
caller cannot replace or release the registered owner.

The owner keeps its context/path state valid until release, including after an
ambiguous close or unresolved publication. Callbacks perform no DOS IO. While
a probe runs, mutating capture/snapshot/monitor/history and reservation calls
reject reentry. Validation and protected input spans include the reservation
descriptor. This is cooperative foreground ownership over DOS canonical names;
external processes, host mount aliases/inodes and concurrent namespace changes
remain outside this guarantee.

The existing four96-byte snapshots and four134-byte descriptors retain their
layout. The new reservation needs eight bytes, making the file-owner state928
bytes before application alignment. Its zeroed descriptor is serialized in the
loaded DOS image; it does not rely on the assembly host clearing BSS. Reservation
operations occupy CONFIG_CODE, with a resident far helper scanning the private
sink descriptors. Static verification checks both compiled far call targets and
their MZ relocations, the code/data segments and all eight initialized bytes.

| Evidence | Result |
| --- | --- |
| Near-code DOS campaign |119 assertions: existing-target preservation, target/scratch aliases, all four sinks, wrong-owner release, existing open owners, independent files and probe reentry |
| Separate-bank DOS campaign |The same119 assertions with an explicit OMF code group and distinct segment bases for reservation operations and resident scan/callbacks |
| Compiled ambiguous-close models |Four16-assertion processes: target and scratch uncertainty in each layout; reservation does not retry close, write or discard ownership |
| Existing file suites |Capture file, canonical owners, capture session and monitor checks pass with the new guard |
| Linked current terminal |24 capture and27 history inputs, plus78 ZMODEM workflows, pass; hardware/filesystem boundaries in these linked checks are modeled |
| Actual current DOS terminal |Five capture/UI/UART cases pass: default filename, pause/resume, shutdown flush, read-only rejection and XMODEM coexistence |
| ABI verifier |409 damaged call targets, relocations, descriptors and layouts reject; includes eleven new reservation cases plus four initialized-state fields |

The terminal SHA256 is
`46b2ed00c197d202451ef1515c14b793d733dabda1cdd112bab5135e4b085486`.
Its369 source inputs are bound separately. DS=SS occupies64912 bytes, leaving624;
resident code occupies65336 bytes, leaving200. The eight new data bytes incur
sixteen bytes of application alignment. The recorder adapter/UI must respect
those limits and use far code for substantial implementation.

The first terminal rebuild exceeded near code by28 bytes. Moving the new
reservation operations to the existing configuration bank resolves that limit.
An initial component linker layout merged the far class into the resident code
group: its functional tests passed, but the explicit different-segment gate
failed. That receipt remains retained. The accepted rerun declares an OMF group
and proves distinct segment bases. No failed observation is rewritten as a pass.

The configuration ABI check also exposed a stale129 aggregate count. The
existing four transfer-UI entries and three callbacks make the aggregate136;
the80 configuration entries/callbacks remain unchanged. The two new compiled
reservation calls are recorded separately. New mutations reject wrong targets,
segments, missing relocations and non-idle initialized fields.

```sh
./tools/build test-capture-reservation
```

The next implementation step is a production recorder file adapter: exclusive
sibling scratch creation, certain close before publication, explicit replacement
consent, preserved originals and checked backup/restore cleanup. Its private
probe must remain installed while any handle or recovery path is unresolved.
Then connect Record start/cancel/stop and foreground RX/successful user TX to
the existing recorder core, with explicit transfer/script/child/setup/port/exit
guards and actual DOS compiler/replay tests. Current-binary BBS/audio and physical
acceptance, the full recorder and all F01–F16 application gates remain open.
