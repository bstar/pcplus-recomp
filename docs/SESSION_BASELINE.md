# Retained accepted PRM baseline

The optional session-baseline terminal retains the exact raw PRM image accepted
by startup, and replaces it after successful live-setup acknowledgement. The
bound projection API can now obtain its baseline from that store without reading
the filesystem. Unknown bytes come from the accepted image, rather than a file
that could have moved or changed since the session began.

Build with `./tools/dev --command make session-baseline`. The product is
`build/terminal-directory-keys-process-bank-session-capture-projection-bound/TERMINAL.EXE`.
`terminal_session_project_bound(output)` copies the retained image into private
stack staging, then calls the existing capture/projector. Missing or damaged
state returns8 without modifying caller output. The existing explicit-baseline
API remains available. KEY kind2 is still disabled.

## Publication and lifetime

The store occupies 1,272 initialized bytes in HOOK_CODE: a validity word,
generation, source kind, corruption seal and 1,264 image bytes. Working routines
use the caller's stack. There is no added near data, allocation, disk IO or
interrupt/port activity in the store itself. The normal build retains 702 near
code bytes free and unchanged 65,520-byte data/stack usage. HOOK_CODE now uses
3,647 bytes, including the store; CONFIG_CODE uses 63,511 bytes.

Startup preference readers invalidate the previous slot before each new import
attempt. They publish only after their applicable serial, modem, transfer,
directory and mouse validation succeeds. Invalid arguments, short reads and
decode rejection therefore cannot leave an earlier image usable as a newly
accepted session. Source kind1 records startup acceptance. The validity marker
is written last after copying all bytes and computing the seal.

Live setup has different failure semantics: the active session already exists.
Successful acknowledgement of a validated reload publishes source kind2; failed
reloads and aborted transactions retain the previous accepted image. Publication
occurs after mouse commit and before advancing setup source baselines. Unexpected
publication failure returns the existing setup state error; it is not reported
as a successful acknowledgement. A successful no-change acknowledgement may
advance the generation because it is another accepted read.

Generation advances on publication and skips zero on rollover. The 16-bit seal
binds all image words, generation and kind. Copy checks the full seal before
touching output. Tests detect one-bit damage in each image byte and malformed
headers, but the seal is not cryptographic and does not prevent intentional
tampering or all multi-bit faults. DOS helpers still share the address space.

The internal far-cdecl APIs in `session_baseline.h` require DS=SS=DGROUP, IF1,
DF0 and caller-owned nonwrapping near buffers. Argument/context rejection leaves
the previous image intact. Invalidate is separate so startup can explicitly
retire an old slot before IO. Only trusted acceptance sites publish; the store
does not validate PRM semantics independently.

## Evidence and remaining work

1,330 linked cases execute the actual store and bound projector. They cover
32 complete-image publications/copies, every image byte's single-bit damage,
header damage, generation rollover, CPU context and argument rejection, atomic
missing/damaged output, and failed startup imports. Only DOS open/read/close
interrupts are modeled for two invalid-file cases; product routines execute.

Five actual 8086 DOS startup workflows rename TEST.PRM away before calling the
bound API. Serial, MODEM, directory MODEM, directory DIRECT and invalid inactive
modem fields produce the expected projected image from the retained startup
bytes. Raw store dumps verify generation1, kind1, seal and every source byte.
Files and hardware samples remain unchanged apart from the deliberate rename.

Two additional 8086 DOS sessions each run two controlled source-built settings
children through the real live handoff. An accepted color edit advances the
image to generation2/kind2 before the second child; a rejected profile retains
generation1/kind1 and the exact original image. Post-child profile, palette,
serial continuation and hardware restoration pass. These fixture children
exercise the acknowledgement boundary, not the production editor UI.

An empty tree with 683 source files reproduces six products, including normal
and probe terminals. The legacy directory terminal and both preceding projection
products still rebuild to identical bytes. The
[independent receipt](validation/session-baseline.json) binds frozen sources,
initial store layout, callback imports, raw image/generation/seal dumps, hardware
samples and the source proof.

The retained image identifies accepted bytes within this application lifetime.
It does not assert canonical filesystem identity, authenticate an image version,
or make unknown native PRM fields accurate runtime state. Projection still covers
the supported subset. Register lifetime/ASPECT handback, remaining native fields,
guarded HOOK execution and returned settings commit remain open, along with BBS,
combined exit/trap and physical hardware acceptance.
