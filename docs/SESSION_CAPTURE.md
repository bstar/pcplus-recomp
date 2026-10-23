# Terminal settings capture

The optional `--session-capture` terminal moves the live setup editor's capture
into a shared HOOK_CODE routine. A second policy captures current session values
for future helper projection. Both policies use the same actual transport values,
including negotiated/CLI speed, active COM base/IRQ, translation, clipboard
separator and BREAK delay. No data storage is added to the terminal.

Build it with `./tools/dev --command make session-capture`. The executable is
`build/terminal-directory-keys-process-bank-session-capture/TERMINAL.EXE`.
KEY kind2 is still disabled; this build exercises shared capture through the
existing live settings editor, not through a HOOK helper.

## Internal interface

`terminal_session_capture_far` takes AX pointing to a 628-byte live configuration
plan, DX pointing to an optional 66-byte transfer plan (zero omits it), and BX
selecting policy0 or1. It returns AX0 for success,1 for an invalid destination or
policy, and2 for invalid CPU context. It preserves BX, CX, DX, SI, DI, BP, ES,
DS and SS. DS must equal SS and the linked DGROUP; interrupts must be enabled
and the direction flag clear. The caller enters from the guarded foreground
handoff while mutable session owners are quiescent.

The plan destination can be the existing dedicated setup plan or a caller-owned
stack object above the incoming far-return frame. An optional transfer output
must also be on that live stack. Both objects must fit the terminal's 8 KiB
stack without wrapping, and must not overlap. Admission completes before any
output mutation. This is a restricted internal interface; the caller remains
responsible for allocating and retaining those stack objects.

Policy0 preserves the existing editor behavior: configured display/pacing values
plus actual transport, translation, separator and BREAK. Policy1 replaces those
configured fields with the current profile, palette, wrap/scroll modes and macro
pacing. It reads the actual modem pause character separately, rather than forcing
it to equal the macro pause character. Modem command delay remains the configured
raw unit value: the maintained sender has a separate fixed BIOS-tick pacing
policy. Directory plan bytes are copied as retained metadata and the change mask
is cleared. Transfer preferences are copied without normalization when requested.

Capture deliberately does not validate settings or claim a complete native PRM
image. The [projector](PRM_PROJECTION.md) performs supported-field validation.
In particular, serial-only startup does not initialize an active modem plan;
the observed snapshot contains zero modem fields except its current BREAK delay.
An integration caller must distinguish inactive groups from valid active groups
and choose an explicit baseline policy. Likewise, divergent macro/modem pause
values cannot be silently collapsed into the PRM's one shared field. The current
projector rejects that conflict. These remain concrete integration requirements.

## Evidence and remaining integration

144 linked cases execute the actual capture instructions: 128 complete-byte
outputs across both policies/destinations, fourteen invalid geometry/context
cases and two exact-boundary cases. Rejected calls preserve output. Register
checks and whole-DGROUP comparisons constrain writes to admitted destinations
and the call frame; interrupt/port hooks reject any IO attempt.

Three actual 8086 DOS workflows exercise live editor admission. A source-built
child reads its suspended parent's exact 628-byte captured plan and verifies a
CLI-selected 19200 rate. The production editor's cancel and color-save paths
preserve/adopt the expected PRM and resume serial IO with the expected palette.
UART/vector/PIC samples restore exactly. An empty-tree build reproduces five
products from 675 source files, including the terminal, ASPECT, DOS compiler,
help resource and settings editor. Policy1 is linked-tested separately; it has
not yet been invoked by a terminal HOOK action.

The [independent receipt](validation/session-capture.json) binds the accepted
sources, raw observer plan, serial/video/hardware captures and reproduced
products. Both preceding directory terminal variants rebuild to identical bytes.
The new build has 744 near-code bytes free and unchanged 65,520-byte data/stack
usage; its capture bank occupies 357 bytes.

An initial DOS runner completed all three workflows but failed while collecting
provenance because a fixture dependency was listed under the wrong filename.
That recording error was corrected before the accepted source-bound runs.

Next: join capture and opaque-baseline projection with explicit inactive-group
and shared-field policy; establish register lifetime/handback; route HOOK through
PROGRAM's guarded execution owner; validate and apply returned changes. Complete
native PRM coverage, combined exit/trap ownership, BBS sessions and physical
hardware acceptance remain open.
