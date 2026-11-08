# Serviced GET editor lifetime

The subsequent [native-owner checkpoint](ASPECT_GET_NATIVE_FIELD.md) connects the
recovered owner to this editor in a diagnostic. It also adds cached cursor
coordinates and corrects far-heap placement: the current202-byte record must
precede DGROUP, and the lifecycle suite now passes759 checks with a heap probe.
The676-check/200-byte evidence below describes the earlier checkpoint.

`get_runtime.c` composes the existing field model, capability21 child client,
WHEN keyboard/service lease and native abort checkpoint. It is an explicit
attached-terminal prototype. The maintained application still refuses GET;
its recovered command operands, typed destinations and cursor bindings are not
yet connected to this owner. Raw-ASIO console entry returns unsupported until
its separate platform path is implemented.

The owner acquires the keyboard lease before beginning the parent field. It
copies initial text into private state and retains no source, destination or
borrowed stack pointer. Normal poll services WHEN and bounded receive before
reading one field key. The native field result distinguishes accepted string
length/numeric0 from canceledFFFF. Normal end retires the display before the
keyboard lease. Commit is permitted only after successful accepted retirement,
inside the same native invocation. Failed target validation retains the accepted
value for retry. Error end discards it.

A caught native abort restores the caller before recovery touches abandoned
frames. The checkpoint now issues a nonzero generation on each admitted entry;
rejected nesting retains the generation. WHEN and editor ownership bind to it.
Only an inactive, aborted, matching generation can use the new WHEN unwind
entry, and only after display retirement has been acknowledged. It then drops
the abandoned service/monitor/deferred records belonging to that synchronous
call. Normal end cannot clear those records. Failed client validation or a
refused close retains ownership for retry; even a tagged cleanup error can prove
that the display retired and allow the remaining lease to retire. Original
runtime errors retain priority over cleanup reporting.

The child reserves local BEGIN ownership before crossing into the parent. A
failed post-request identity check therefore quarantines the possible field
owner, rather than incorrectly releasing the keyboard lease. A repaired tagged
error-close is required before reuse. A trusted rejected BEGIN clears the local
reservation normally.

Parent EMIT marks the field dirty. The owner repaints after a field key or that
display activity, keeping idle polls free of field RPCs. Each repaint explicitly
configures the frame before ordered cell staging; the actual controller requires
that reset before another full frame. This is a scheduling choice, not a claim
about the original editor's repaint timing.

The200-byte private record is an assembly-owned far segment outside DGROUP;
C accesses it through a far external. C size and diagnostic linker-map assertions
bind this layout. The pure field code runs in a separate bank. An initial named
C data segment still joined DGROUP despite a far declaration/class; that layout
was rejected and replaced, not accepted as memory isolation.

## Evidence and limits

[The receipt](validation/aspect-get-runtime.json) records:

- 676 DOS8086/FPU-off checks over11 authored scenarios. The actual assembly
  checkpoint, field kernel, session owner, WHEN C gates and renderer client run.
  The command body, native WHEN actions, BIOS keys, serial peer and parent
  display are controlled services. This is not the recovered command or a real
  child EXE-to-parent parser/UART connection.
- Accept, Escape, numeric rejection/bell, masked non-ASCII text with raw
  writeback, deferred commit and invalid-target retry; ordinary service errors,
  normal-close refusal/retry and client failure during repaint/BEGIN.
- A native abort abandons actual busy/service/monitor/deferred C frames. Refused
  retirement and client-check failure retain them. A repaired tagged cleanup
  error retires display and keyboard ownership while preserving the original
  runtime error. Recovery without an active owner is idempotent. The diagnostic
  tests live-owner refusal; the source also requires a matching generation, but
  the test does not force a later generation over a retained owner.
- Twenty idle polls cause no field RPC or new frame. Three modeled receive
  leads enter actual WHEN receive scheduling and the child EMIT client, then
  cause one full repaint. This is not a throughput benchmark or actual ANSI
  parser/video acceptance.
- A clean20-source export reproduces the exact executable and complete report
  without originals, private data, previous objects or ancestor Git metadata.
- 292 child-client checks include dirty-state tracking and post-BEGIN quarantine.
  The generation-enabled native checkpoint still passes142 original-observation
  cases plus12 injected faults/retries, with its own16-source exact rebuild.
- GET-VM-disabled UART diagnostic remains byte-identical to its earlier36-case
  wire-tested binary. The reviewed GET-disabled ASPECT interpreter also rebuilds
  byte-identically. These comparisons preserve earlier coverage; no additional
  physical or wire acceptance is claimed.

The parent display model was corrected to retain completed staging until the
next configure, matching the actual controller. Earlier prototype reports used
a model that reset staging on present and do not establish that protocol detail.
The cold-source builder also needed to create its absent build parent directory;
the final source reproduction includes that fix.

Still required: actual recovered GET command/runtime aliases and cursor/geometry
composition, typed/scratch lifetime and abort propagation into the full native
dispatcher, real parent parser/receive tests, FLOAT.RTE, both compiler grammars
and opcode49, raw console behavior, whole-application memory/package admission,
connected scripts/BBS and physical acceptance. The current session module is
not included in a released application build. Installed files and the selected
connection payload are unchanged; no FTP, modem, SIP or live BBS was probed.

```sh
./tools/dev --command python standalone/build_get_runtime.py \
  --output build/my-get-session
./tools/dev --command python standalone/prove_get_runtime.py \
  --build build/my-get-session --output build/my-get-session-source
```
