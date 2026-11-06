# Carrier recovery key ownership diagnostic

The timed Enigma carrier workflow previously missed one redial, then passed an
identical-input repeat. No cause was established. The optional
`--guard-observer-check` records owner state when the parent reads keys after a
carrier-loss notice, without changing the parent, keyboard recipe or producer.
It is diagnostic evidence, not a fix or a connection-reliability acceptance.

## Footprint and behavior

The observer replaces diagnostic video capacity 16 with 8 and adds 16 bounded
key records. This changes no product capacity. Its resident end is padded to
the exact original 3,215-byte end, or 201 DOS paragraphs including its PSP.
This matters because the source-built parent and ASPECT admission margin is
tight. The `.COM` file also contains nonresident collector/metadata code;
its file length is not the retained-memory measurement.

INT1C still samples video notices. A passive INT16 wrapper recognizes the
parent's live IRQ5 vector, checks its recovered UART-entry opcode signature,
derives its data segment from the exact source-built map, and accepts only
matching parent-DS reads with AH0/10h and a nonempty ordinary BIOS key buffer.
It peeks that buffer, records the original interrupt return address and owner
words, restores registers/flags, and chains the original BIOS handler. It calls
no DOS/BIOS from either callback, reads no UART registers and consumes no key.
Normal interrupt stack saves are the only writes to the interrupted stack.

The record is taken **before** BIOS delivery, normalization and dispatch. It
is not a direct trace of the eventual modal-admission branch. Other callers,
private data contexts, empty reads and keys before the carrier notice are not
recorded. Full-buffer overflow counts read attempts, including foreign callers;
do not interpret it as a count of lost parent keys. Only the first 16 accepted
records are retained. Unused label-file tail bytes are diagnostic code/padding,
not additional video frames or records.

Ten actual assembled-handler CPU cases check standard/enhanced reads, peek,
producer, disabled/foreign/empty/full cases and carrier enabling. They verify
registers, entry flags, the original interrupt frame, BIOS data and parent
non-stack memory are preserved and no callback invokes an interrupt. The old
vector endpoint is modeled in these cases. The real DOS collector additionally
checks it still owns INT16, restores it, independently reads it back and records
successful restoration; original hardware/INT1C restoration remains audited.

## Use and interpretation

```sh
./tools/dev --command python lab/bbs/check_carrier_key_observer.py \
  --terminal build/PARENT/TERMINAL.EXE --output build/NEW-observer-check
```

The normal carrier command accepts
`--guard-observer-check build/NEW-observer-check/result.json`. It requires a
current passing check with the exact parent and observer bytes. Default runs
retain the original observer. The capture records its diagnostic variant,
source identities, exact footprint and bounded trace. The independent carrier
auditor regenerates and checks that specific observer before performing the
unchanged raw-proxy, authentication, CRC/finish/control and hardware checks.

```sh
./tools/dev --command python lab/bbs/analyze_carrier_key_owners.py \
  --capture build/bbs-lab/results/enigma/LABEL --output build/NEW-key-analysis
```

The analyzer verifies the captured source-built identity and actual INT16
opcode at each browser read. It reports captured sufficient admission blockers
and can replay them through the linked guard with modeled BIOS/UART. It does
not assume missing fields are idle or infer an earlier unobserved failure's
cause. Nominal recipe tick counts and socket-relay times have different origins
and must not be directly subtracted.

The first observed run passes carrier loss, redial and the exact 65,539-byte
retry. At its browser read the captured parser, transfer, PROGRAM, ANSI-wait,
view/menu and pending-request words are zero; connection state is offline.
The call site matches the native linked keyboard read. Tab and D follow with
the ordinary menu active. This demonstrates an admissible request in that run,
not why the earlier run missed it. A separately labeled repetition also passes
with zero captured owner blockers at the native browser read. Both complete
65,539-byte retries and their independent audits pass. The
[diagnostic receipt](validation/carrier-key-owners.json) binds the eight reports
and retains the original failed capture as unresolved.

No application, selected package, physical machine or production bridge is
changed. Chat foreground integration, connection reliability and physical
Boca/SPA2102/SIP/audio acceptance remain open.
