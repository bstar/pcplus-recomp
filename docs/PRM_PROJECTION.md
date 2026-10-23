# Supported active settings projection

`src/config/prm_projection.c` adds a pure DOS16 staging operation needed before
HOOK execution. It writes explicitly supplied active serial, modem and transfer
settings into a copy of an opaque1,264-byte PRM baseline. Reading the saved PRM
alone cannot account for CLI/directory overrides, negotiated speed or runtime
clipboard/translation changes. The caller must capture those actual values.
The [terminal session API](SESSION_PROJECTION.md) now connects capture and this
projector with explicit active/inactive modem policy. HOOK routing remains open.

The projector covers the44-byte serial plan,368-byte modem plan and66-byte
transfer plan accepted by the existing maintained importers. It writes the
selected port's base/IRQ and the native baud index, keeping other port slots
unchanged. Shared pause-character and delay fields must agree between serial
and modem plans. Raw modem byte fields cannot silently truncate16-bit inputs.
The established decoders validate the staged serial/modem representation before
publication; transfer path syntax and normalized boolean input are also checked.
No baseline validity assumption is needed for fields wholly replaced by the
active plans.

Five input/output objects must have pairwise-disjoint, nonwrapping near extents.
Failure leaves output unchanged. Unknown fields and bytes after each new string
terminator retain baseline values. A still-enabled Auto Download preserves the
original nonzero word; an empty saved download prefix stays empty when the
active plan represents current directory as `.`. These rules avoid unrelated
normalization of opaque state.

Run `./tools/dev --command make test-prm-projection`. The source-only8086 DOS
diagnostic passes2,688 checks, including the preceding2,660 and720 port/rate/parity/bits/stop
combinations, all terminator positions in six commands and eleven response
slots, invalid values, shared-field conflicts, output preservation, null/alias
and segment-wrap rejection. An independent Python fixture checks every byte of
the baseline and projected image, including untouched tails. A second fresh
compilation/link reproduces the executable.
The [original receipt](validation/prm-projection.json) binds the earlier raw output,
baseline/projected bytes, fresh executable, frozen sources and exact OMF imports.
The projector object imports only the existing validators and memory/string
services, with no DOS, file, UART or hardware entry.
The current session checkpoint adds inactive-group and explicit BREAK cases;
see [session projection](SESSION_PROJECTION.md) for current evidence and scope.

The first two diagnostic runs incorrectly compared rejected output against the
initial sentinel after successful calls had already replaced it. All23 failures
were that fixture assertion; the independent complete-image check already
passed. The accepted fixture snapshots output immediately before each rejected
call. Earlier evidence remains retained, rather than accepted as passing.

This is a partial supported-fields projection, not proof of a complete native
active PRM image. Directory metadata, current display attribute/mode state,
sound/mouse configuration and unknown native fields require their own accurate
capture/projection contracts. Terminal safe-point capture, HOOK routing,
register lifetime and validated returned-state application remain pending.
No file I/O, UART access or active setting mutation occurs in this operation.
