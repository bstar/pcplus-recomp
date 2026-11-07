# Line/Port transaction and serial plan

The optional [live Alt-P candidate](LINE_PORT_LIVE.md) now composes these components
and passes the named application gates. The installed/default release is unchanged;
this document retains the separate component checkpoint and its limits.

The recovered selector, maintained renderer and a new staged transaction now run
together in a separate 16-bit code bank. These standalone checks exclude the terminal's routes and actual IO; the
optional live candidate now binds them.
The installed RBADE091 package is unchanged. No physical acceptance is implied.

## Transaction contract

`src/line_port/session.c` owns a caller-provided 28-byte near transaction. Begin
accepts only a zeroed or completed owner and valid native indices for supported
COM1..4. Editing invokes the exact recovered selector through the far-cdecl
`select.asm` adapter. The adapter records native bell/quiesce requests; it does
not touch a UART. In particular, reselecting the current port still records
quiesce. Applying that request immediately to a connected UART would bypass the
maintained drain/handoff protocol, so hardware execution remains a separate step.

Escape requests application of session edits. Alt-S requests persistence first,
then application. The owner refuses application before a requested save has
succeeded. A normal save failure returns to editing. An uncertain save locks the
owner, and begin cannot clear that lock. A successful save followed by an apply
failure retains the saved state; requesting a retry returns save0, preventing
an implicit second disk write. Apply success retires the owner. Unsupported
COM5..8 selections preserve the staged values and return an explicit refusal.

This records the native wrapper's save/apply distinction while leaving checked
IO and resource ownership to the maintained foreground. Save/apply results in
this checkpoint's diagnostic are **authored inputs**, not actual file or UART
operations. An uncertain-save lock must eventually integrate with retained
recovery details and explicit application recovery before deployment.

## Actual serial values and saved indices

`plan.c` converts the actual effective transport into the native five-word
selection, including negotiated baud. It supports all nine recovered baud
indices through 115200, preserving the high word of the maintained baud value.
A proposed selection produces a 44-byte serial plan, 10-byte little-endian saved
prefix, and change mask for port/baud/framing. Flow, emulation, translation,
clipboard, display and other serial preferences remain as in the active plan.

For the same port, live base/IRQ choices survive; a stale saved table cannot
replace an explicit current `/U` or `/I` choice. For a different port, the
candidate uses that port's base and IRQ from the supplied accepted PRM. It
validates the standard COM base and allowed maintained IRQ before publishing
any output. It never guesses that COM3 must use IRQ4. This is a pure proposal:
the existing UART handoff still must check BIOS conflicts, carrier, pending
traffic and exclusive hardware ownership before committing it.

## Verification

The [receipt](validation/line-port-session.json) binds:

- **71 actual DOSBox-X8086 checks** for selection, Escape/Alt-S ordering,
  normal and uncertain save failure, save/apply retry, completed ownership,
  unsupported port refusal, output alias rejection, current IRQ preservation,
  PRM-derived different-port IRQ, high-word baud and saved-prefix encoding.
- The combined code bank is separated from ordinary DOS/runtime code by a
  diagnostic-only 64KiB code segment. The map places LINE_PORT_CODE beyond the
  first 64KiB; its far calls and native near calls execute in DOS. The padding is
  never an application/package input.
- Its 1142-cell popup/footer footprint matches the previously established native
  initial-state digest. The prior [native view comparison](LINE_PORT_VIEW.md)
  covers the broader three-state/reopen observations independently.
- An isolated export of 16 declared public files reproduces the EXE and popup
  exactly and repeats all 71 DOS checks. No original, private configuration,
  analysis database, earlier object or Git metadata is exported. The outer
  pinned Nix environment supplies tools. An initial export revealed two missing
  header declarations; those were added before the accepted proof.
- Selecting the optional far bank changes no flat recovery bytes. The original
  414-byte hash, 262144 exhaustive key/state cases and 40 DOS selector vectors pass
  again, as does the refreshed six-file selector reproduction.

```sh
./tools/dev --command python standalone/build_line_port_session.py
./tools/dev --command python standalone/test_line_port_session_dos.py
./tools/dev --command python standalone/prove_line_port_session_source.py
./tools/dev --command python standalone/record_line_port_session.py
```

The source-proof destination must be fresh. Existing proofs are retained under
ignored build storage rather than silently used as build inputs.

## Remaining live work

Add the optional terminal build wiring and direct/browser/reference Alt-P
routing. Begin from an actual session snapshot, use configured popup colors and
supported display geometry, and preserve live-screen/cursor ownership while
serial input and replies continue. The [checked prefix storage component](LINE_PORT_PERSISTENCE.md) now passes
real DOS and fault checks. Bind it and the staged proposal to the existing
foreground drain and port handoff, including canonical PRM identity, file claims
and recovery reporting. Do not synthesize a child PRMEDIT invocation or change
unrelated settings to stand in for native Alt-P.

Then validate all routes, no-op/reselect, Escape/Alt-S, invalid ports/settings,
file/close/rollback failures, connected traffic, carrier loss, busy/refusal and
modal return against the exact new application. Package/source proofs and
Enigma/Synchronet checks follow an actual application change. Physical
Boca/SPA2102/SynthModem acceptance remains separate and pending.
