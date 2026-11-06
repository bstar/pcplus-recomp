# Partial recovery of Chat echo memory cost

The optional echo parent now recovers480 bytes of conventional-memory
allocation from the [unfunded scope build](CHAT_ECHO_OWNER.md), while retaining
the same stack, data, buffers, streams and feature capacities. **This is partial
funding: actual nested ASPECT still fails, and foreground TEXT remains unbound.**

`src/chat/echo_size.json` selects33 measured per-source C compiler choices.
Each choice pins its source hash and before/after object code/data counts.
Together they save423 object-code bytes with unchanged object data. Only
`--chat-echo` applies this additional profile. Source changes invalidate the
profile before the affected build can link/publish an executable.

The echo admission code now uses a near helper with two nearby refusal exits.
The checks and their order are retained; shorter conditional branches reduce
the echo bank from895 to831 bytes. The callback's existing saved-register
frame and admitted scope cleanup remain intact. This is layout/size work,
not removal of admission checks or a change to native parser semantics.

The linked result is:

| Measurement | Unfunded control | Current experiment |
| --- | ---: | ---: |
| Minimum allocation | 480368 | 479888 |
| Near DS=SS | 65504 | 65504 |
| Resident CS | 65464 | 65464 |
| Echo bank | 895 | 831 |
| Declared application stack | 8192 | 8192 |

Linker alignment accounts for the difference between object savings and the
480-byte allocation reduction. Current parent SHA:
`067cfdf53a6f8a4e3e0cb1a57733d7a7a9acb885597468101906eab6962e405c`.
The API0103 module remains exactly5b6892e7…d45622. The current experiment still
uses496 more bytes than the timing parent, and480 more than the earlier
foreground baseline. Those comparisons do not establish a precise threshold
or complete diagnosis for the child allocation failures.

## Verification

The size checker validates all33 source hashes, actual control/current objects,
selected compiler options, unchanged data and capacities, stack sizes and module
identity. Its success means **partial recovery**, not complete memory acceptance.
The historical control is tied to its exact977d1f55…69f70c executable/object
counts; its old producer manifest is not reclassified as current source.

Six actual-parent CPU groups continue to pass echo/wrap/interleaving, CSI/C1,
owned IRQ input, bounded waits, cancellation/modem-phase revocation, nested
original CSI-M cancellation and admission refusal. Additional refusal cases
exercise changed BIOS mode/columns/page/rows and a non-plain line flag, preserving
the moved checks' observable refusal behavior. Hardware/kernel remain modeled;
actual busy-key scheduling and foreground TEXT are not accepted by these checks.

Ordinary DOS8086 main passes Chat entry, BIOS typing, RX, Escape, pending-prefix
restoration and ordinary CPR return. Echo/TEXT are inactive in that main test.
A fresh3645-file public-source export without analysis, originals, private
configuration, prior objects or ancestor Git reproduces the exact parent,
module and header and repeats the six CPU groups. A separate source export
with a comment-only edit to recording/file.c is rejected by its new profile
hash before publishing an executable. Echo disabled reproduces the exact
prior5ecf8774…092846 executable.

Actual DOS8086 nested-ASPECT with current-source cbdee194 still fails the
child/six-stream/file/viewport checks. Missing-file recovery, controlled hangup,
hardware restoration and fixture PRM preservation continue to pass. Earlier
compiler-only testing also failed that gate; the compacted version has its own
retained failing report. No new BBS or physical acceptance is claimed.

The measurements also bounded alternatives:110 parent/module C objects were
probed with several size/inlining choices. Three display-bank sources were
excluded from the final profile because that separate builder does not apply
the parent C profile. Unchanged-source interpreter no-inline experiments
reproduced cbdee194; separate interpreter C probes found only118 potential
object bytes. None is represented as an accepted new interpreter. A simple
usage-text back-reference estimate was too small to fund the remaining cost.

Next recover the remaining memory cost with source/layout work, retain the
full nested-child/stream acceptance gate, then complete busy-key/cancellation,
local cursor/presentation synchronization and foreground TEXT scheduling.
The full feature inventory and hardware/package/BBS gates remain open. Selected
and installed packages, private settings/call history and the production bridge
are unchanged. See the [receipt](validation/chat-echo-size.json).
