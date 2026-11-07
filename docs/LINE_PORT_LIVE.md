# Live Alt-P candidate

The optional `--line-port` parent now connects the recovered selector and popup
to serviced terminal input, checked prefix saving and the existing UART handoff.
The candidate SHA-256 is
`a057b35cfa1d187e0a355cee62ac3c99489c226e499fe898bf6b5a2722aef134`.
It is **not release eligible: the paired ASPECT capacity gate fails**. It is
not installed or selected for release. Physical RBADE091 remains the
previous parent 856a9c85 with its separate pending acceptance.

Direct Alt-P, the Setup browser entry and Alt-Z → Line/Port Setup reach the
native-shaped popup. Its cursor and initial 1142 character/attribute cells match
the original observed 80x25 layout. Native baud/parity/bits/stops and COM1..4
choices are staged while input, parser replies and live background rendering
continue. Escape applies session edits without saving; Alt-S saves the ten-byte
prefix before application. The original selector is unchanged; its old-port
quiesce request is deliberately executed at the drained commit rather than
immediately on a selection key. COM5..8 are explicitly refused.

## Runtime ownership

A 256-byte front state lives in LINE_PORT_CODE. Calls to the verified session and
plan APIs use bounded DS=SS stack snapshots; no persistent session/path/plan
arrays are added to DGROUP. The selector adapter retains its 12 near bytes. C
text constants have explicit code-segment placement, and far pointers are
materialized before operations that could lose their segment frame.

The accepted canonical PRM identity comes from the already-bound setup owner.
A fixed canonical file claim spans the popup and queued operation. A new internal
PROGRAM kind 12 reuses ordinary admission, drain timeout, flow, IRQ/vector,
screen and mouse restoration. It executes no child and inserts no extra return
key prompt. Independent capture/file owners stay open. Actual framing/global
publication and a different-port resource transfer occur only in that handoff.
Different ports retain their configured PRM base/IRQ values; occupied/carrier-
connected ports are refused before saving. The current port retains its live
base/IRQ choices. Unrelated profile, flow and display preferences are preserved.

The prefix writer uses bank-local near-cdecl DOS services and existing checked
path/CRT bridges in CONFIG_CODE. It never truncates the original. File errors
retain the established install/stage/backup/close/rollback results. Ordinary
failures reopen a serviced error popup after the UART resumes; a successful save
is distinguished from failed application. Uncertain ownership retains the claim
and requires DOS recovery on acknowledgement. The saved baud baseline is
acknowledged only after commit; a frozen dialing-directory record keeps its own
source baud baseline rather than being silently rewritten by a global PRM save.

## Verified application behavior

[The live receipt](validation/line-port-live.json) binds these exact binaries and
results; it does not substitute component results for application behavior.

- Ten actual DOSBox-X8086 sessions on COM3/IRQ5 cover no-op, Escape edit, Alt-S
  save, direct/reference/browser routes, incoming traffic while open, COM5
  refusal, read-only PRM, existing recovery backup and connected port-change
  refusal. All 257 checks pass. An independent synthetic modem peer sees the
  initialization/dial, ordinary keyboard bytes and real parser-generated replies.
- The passive popup observer captures native geometry, attributes and cursor.
  It latches the UART LCR after post-popup traffic: 8N1 remains 3 on unchanged or
  refused operations; successful edits produce 8E1 value 1B. It does not toggle
  DLAB, read RBR, change product memory or inject replies.
- Alt-S produces only the requested baud/parity prefix patch; Escape and refused
  operations preserve the complete PRM. Existing recovery content is retained,
  independent input/replies continue after failure acknowledgement, and before/
  after hardware snapshots match. Error visibility is tested, not inferred from
  a return code. A code-segment pointer issue found by those tests was corrected
  before the accepted run.
- A separate offline move from COM3/IRQ5 to COM1/IRQ4 passes 17 checks with actual
  selected-port traffic and four UART/PIC/vector snapshots restored on exit.
  That lab's timer observer temporarily toggles DLAB with interrupts masked to
  sample divisors and restores LCR; it never reads RBR or changes product memory.
  The production settings editor is copied by the reusable lab but never invoked.
- An isolated export of 689 public files reproduces the parent exactly and repeats
  save, serviced-input, read-only and connected-port-refusal sessions. No original,
  private configuration, analysis database, previous object or Git metadata is
  available in the export; the outer pinned Nix environment supplies tools.
- A current-source build with this flag disabled still reproduces the installed
  parent 856a9c85887312099ae92a9f47592ca8b04f6812e7e6e404ad240bad63a6f6d7
  exactly. All stacks and ring capacities remain unchanged. The new candidate
  has 65520 DGROUP bytes (16 spare), 65536 resident code bytes (zero spare), and
  488544 minimum allocated module bytes before its PSP. These limits are checked
  by the linked memory verifier, including nested configuration ABI conditions,
  far-state placement/initialization and bridge identities.

## Known capacity regression

The same ASPECT interpreter (`5c641ac4…`) was tested with both parents on DOS
8086, using profile switching, six held streams and nested child execution.
The unchanged `856a9c85…` control passes all 29 checks. The new parent switches
profiles, then the first held-stream open fails: error 7, opcode 41, step 9.
`HOLD0.BIN` is absent. The initial producer raised `FileNotFoundError` instead
of writing its final summary. The diagnostic now treats absent held files as
failed checks and writes the failure receipt before returning a failure status.
The repeated candidate still fails; the paired control still passes. The initial
log and repeated capture/results are retained and bound by the live receipt.
An expected banner-reset check in the underlying
capture is not the evidence for this failure; the missing held file and paired
control are.

The candidate adds 9,040 minimum module bytes (488,544 versus 479,504). This
establishes a capacity regression. A separate
[passive resize diagnostic](LINE_PORT_CAPACITY.md) now observes DOS refusing
AH=4A with AX=8; mapping each request to its precise CRT owner remains open.
Compiler-size experiments saved only 16–256 bytes
and were reverted to the exact reviewed candidate. No stack, ring, stream count
or file-buffer capacity was reduced. The next step is to reduce residency,
potentially loading the popup code only while needed, and repeat the identical
paired stress workload before promotion. The existing Chat overlay loader is
source guidance, not a drop-in Line/Port loader: it has a distinct identity,
API and state contract.

The next residency change must satisfy these constraints:

- Keep a small parent dispatcher and a distinct, versioned Line/Port callback
  descriptor. Loaded code must retain the parent DS=SS convention and validate
  its file/image identity before entry, as the Chat loader does.
- Acquire storage without growing the parent's minimum allocation. In the
  current redisplay source, Alt-P, Alt-Z and the browser enter as direct menus:
  their history length is zero, so the 63,000-byte frozen snapshot is not
  populated. The live/view underlays have separate storage. This makes the
  snapshot a possible transient code arena without relocating those underlays.
  Chat's existing lease still refuses an active command menu, so a distinct
  lease must prove this direct-menu state rather than bypassing its guard.
  File-viewer/path bindings must not access the borrowed region while leased.
- Keep the canonical file claim and pending plan alive through PROGRAM kind12.
  Never overwrite executing module code, unload a pending save/handoff, or let
  a child reuse storage until the operation and every callback have retired.
  Closing the visible menu does not retire a queued kind12 operation. A lease
  therefore needs its own pending/active lifetime, not only redisplay_active.
- On missing, truncated or mismatched module input, refuse the popup visibly
  and preserve UART traffic, owners and PRM bytes. Test reopening after failure.
- Repeat the unchanged 257 UI checks, 17 move checks, paired ASPECT capacity
  workload and isolated rebuild before BBS/package/deployment gates. Measure
  minimum allocation as well as near/code limits; a far bank alone saves no
  conventional memory.

## Build and remaining gates

```sh
./tools/dev --command python standalone/build_line_port_profile.py \
  --output build/NEW-line-port
./tools/dev --command python standalone/test_line_port_terminal_dos.py \
  --terminal build/NEW-line-port/TERMINAL.EXE --output build/NEW-live-save --case save
```

The profile JSON pins the composed application flags, including the matching
capability 20 parent policy. This builds the development parent, not an installed
release or a complete redistributable package. Companion ASPECT/Help/Chat files
must remain matched and verified before packaging/deployment.

The known ASPECT capacity regression must be fixed. The new application also
needs broader Enigma/Synchronet,
transfer/cancellation/reconnect and package/source/deployment gates. Other text
heights, configured-color comparison against the original, the complete port-pair
matrix, generic-setup/directory composition after session edits, and live injected
close/rollback uncertainty remain open. Storage faults have separate component
coverage; that is not proof of their full application/UI composition. Real
Boca/SPA2102/SynthModem behavior and modem signaling remain unverified for this
candidate. Full F01–F16 parity remains open.
