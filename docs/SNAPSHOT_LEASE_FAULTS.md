# Tagged snapshot replies and active-lease divide recovery

Capability18 supersedes the staged capability17 lease. The matched source-built
pair is TERMINAL `61757956` and ASPECT `b61f3a03`. The physical machine's selected
capability16 package remains unchanged. The
[receipt](validation/snapshot-lease-faults.json) records application and diagnostic
identities, source reproduction and the exact validation boundaries.

## Pointer reply guard

Capability17 returned a pointer byte as an untagged word. A typed error such as7
or10 could therefore be mistaken for pointer data if an intermediate request
failed. The earlier synchronous success tests did not establish this failure
case. Capability18 returns `F000h OR byte`; the child requires the exact high-byte
tag before accepting any of the four pointer bytes. Small typed errors and the
reserved bridge errors cannot become a storage pointer. This is a deliberate
service-version change; the existing descriptor/version guard rejects mismatches.

Forty-eight linked ownership cases include rejected byte replies0,7,10,14,255,
256,EFFFh andFFFFh, plus null/wrapping pointers, failed-release quarantine/retry,
MCB/extent/caller bounds and competing UI ownership. Normal byte0 is accepted
only as taggedF000h. Actual capability16/18 mismatch controls create none of the
script outputs while preserving hardware, settings, inputs, the final viewport
and subsequent keyboard/hangup behavior.

## Actual divide cases

Small, explicitly marked diagnostic interpreters execute a real CPU DIV by zero
only when the owned `FAULT.ASX` fixture arms them. Production builds contain
neither the trigger nor its arming code. The test performs the failed invocation,
six-stream work, missing-file recovery, then normal `FIRST.ASX` in the same
terminal. The final normal invocation must run another nested child successfully.

| Phase | Live resource boundary |
| --- | --- |
|17 | Parent storage acquired; snapshot pointer pending publication |
|5 | Full saved snapshot captured |
|6 | UART paused for external execution |
|8 | Near process/environment allocation registered |
|10 | DOS child returned, before final process/display retirement |
|22 | Snapshot free/release path entered |

Each phase runs twice: DS=SS and DS deliberately changed toB800h with the same
owned stack. Before the exception, the diagnostic makes a read-only tagged-byte
request to verify the parent lease is still live. It records the actual DS/SS
through SS-relative stores, then executes DIV. The existing checkpoint and native
dispatcher perform recovery; no successful cleanup return or retirement is
injected. The one-shot trigger cannot fire recursively during cleanup.

All twelve actual386/XMS/UMB cases pass:

- The selected fault marker and measured DS/SS are present; the parent lease
  was authenticated as live immediately before DIV.
- The failed invocation reports arithmetic error12 at opcode9Bh. Cleanup error,
  external scope and display/program/process ownership words are zero at exit.
- The next three invocations exit0. Six simultaneous streams, missing-file
  recovery, a normal nested child, fresh keyboard output and hangup all complete.
- Child-output counts distinguish faults before child entry from faults after
  child return. A stale or leaked frame cannot pass the later normal SAVE call.
- Private settings/staged inputs and the42-byte UART/PIC/vector snapshot remain
  unchanged. The final1920-cell viewport matches the exact expected arithmetic
  fault text and parent error notice, including attributes and all blank cells.

The initial fault matrix failed a no-error screenshot expectation. Inspection
showed the specified visible error reports rather than lost snapshot contents.
The final test expects those exact reports; it does not ignore differing cells.
Earlier attempts are retained and excluded from acceptance.

In a fault record, probe stage`100h+phase` distinguishes it from a returned
controller result. Its status word holds the live-lease boolean, and the next
two words hold measured DS/SS. Stage2 in the final normal invocation is the
ordinary returned controller result. Do not interpret the aborted record's
DS/SS words as native display/serial status codes.

## Source and normal controls

A clean2032-source parent export reproduces61757956 and feature-disabled
867cb827. Three clean1702-source child exports reproduce the normal18 pair versus
default16, and representative own/foreign-DS phase17 diagnostics versus the
normal18 child. The default16 interpreter remains exact23caac93. No originals,
existing objects, private configuration or ancestor Git are available in the
exports. These are not twelve independent diagnostic exports.

The complete executable images for each of the six phases differ from their
own/foreign phase17 reference at exactly two phase-immediate bytes. The checker
locates both expected instruction patterns inside the linked phase helper and
compares every executable byte, including headers/relocations. Repeat with a
fresh output directory:

```sh
./tools/dev --command python standalone/check_lease_fault_variants.py \
  --pattern 'build/aspect-lease18-{kind}-{phase}-final-20261106/ASPECT.EXE' \
  --output build/lease-variants-new
```

The normal18 pair also passes ordinary unobserved8086 SAVE, the separate full
inner screen/cursor comparison, and seven register/recovery workflows with43
paired830-byte snapshots. All fault hooks are absent from that normal pair.

The fault harness requires an explicit matching phase, diagnostic admission and
passive high observer; `--lease-fault-foreign-ds` must match the selected image.
It rejects accidental use of another marked variant. `prove_program_result_probe.py`
accepts the same phase/foreign selectors for the diagnostic source comparisons.

## Remaining boundaries

This closes the six active-lease own-stack DIV boundaries for two DS selections
in the declared emulator profile. It is not typed-abort, direct-dispatcher
longjmp, WAIT/cancellation, arbitrary kernel/allocator corruption or physical
fault acceptance. Actual larger-row leases and Enigma/Synchronet/transfer/
carrier-loss regressions remain open for this exact capability18 pair. Re-run
those gates and package/source/deployment checks before changing the selected
physical installation. Broader original application parity remains open.
