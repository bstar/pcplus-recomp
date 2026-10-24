# Peer-requested display width

The experimental transaction parent now routes native private mode3 set/reset
requests to the existing80/132-column display transaction. Non-transaction
parents retain the explicit2A6E unsupported boundary. The source-only and DOS
checkpoint passes; BBS/hardware and deployment acceptance remain separate.

The maintained resident bridge preserves the native one-word `RET2` ABI.
The exact recovered34-byte original adapter and its diagnostic remain separate;
the application uses its guarded live transaction rather than captured RIS.
The native mode dispatcher and flat CSI/UART sources remain unchanged.
Normal parser input applies the request synchronously, before following mode
parameters or subsequent bytes. Non-private mode3 retains native ignore behavior.

The physical display remains80 columns. Logical132-column content uses the
existing two overlapping panes. This does not select a BIOS/SVGA132-column mode.

## Script ownership

PROGRAM already owns its screen backup while ASPECT executes. A transaction
during a genuine renderer body instead borrows the separate editor/viewer live
backup. Admission requires PROGRAM active1/kind4, ASPECT active1, parser depth
1..16, attached renderer1, resident bridge busy1 and hidden script overlay.
Viewer/menu/other modal owners must remain inactive, including the byte-owned
directory editor and chooser. These checks do not grant cold native-bank calls
or ordinary PROGRAM children access to the borrowed native workspace.

The bank entry accepts the exception only for live requests100h/101h while the
transaction owner is active. The native data image, full4096-byte private stack
and projection/validation/commit/rollback policy stay intact. UART state,
parser continuation, default RIS state and child pointers remain outside the
projection. A refusal uses the established unsupported/unwind path.

The pure renderer preflight admits private mode3 only when the linked parent
declares the transaction capability and its scoped renderer state is valid.
Report-prefix and other supported/unsupported mode semantics remain unchanged.

## Evidence so far

The basic transaction parent builds with Nix. MZ/map inspection checks the
resident mode bridge, callee cleanup, relocated far destination, initial
backup pointers and capability value.

`standalone/check_peer_width_live.py` passes64 normal-parser commits over both
profiles,1/5/24/25 startup rows and both status states. It checks geometry,
cleared content and exact CPR, plus native ignore behavior for non-private3.
The controlled ownership matrix covers768 states, with exactly one admitted
combination. Eight additional cases reject invalid depth, modal backups and
cold/arbitrary bank requests. Four real UART-ISR injections on the private
stack retain all512 received bytes; two injected native metadata faults roll
back content and preserve PROGRAM's backup.

The first rollback fixture wrote the static symbol address instead of the
borrowed runtime bank. The corrected fixture targets the active bank and
observes the real validation failure and rollback; it does not patch a return.

The earlier transaction regression still passes25 commits,112 row/margin/save
cases,20 IRQ/fault rollbacks and63 refusals. Expanded pure policy checks pass
58,962 DOS assertions and48 independent CPU probes. Controlled owner bits do
not prove a real ASPECT RPC/PSP lease.

Genuine DOS8086 pilots now pass for the main receive loop, a precompiled
ASPECT child with its cooperative window, and a DOS-compiled child with hidden
status and mapped output. The source case publishes an exact ASX and compiler
exit0; its compact observer does not capture full planes. Precompiled and
main-loop cases match the normal-parser replay's complete logical screen and
both metadata planes. Wire replies include the wide127/132-column coordinates
and the subsequent narrow80-column reply (or immediate-wrap3;1 in alternate
output). Child return and subsequent keyboard input also pass.

The observer's `PEER_WIDTH` fixture stages fields but never invokes the width
API. A split incoming CSI performs all width changes. Profile4 with mapped
output also passes full-plane comparison, including repeated mode3 requests
and mixed parameter lists with mode3 first, middle and last. Pilots are under
ignored `build/peer-width-DOS-*` directories.

The [sealed receipt](validation/peer-width.json) binds865 declared source files
and2432 artifacts. The clean proof `build/peer-width-source-01` passes all101
DOS workflows. It retains all55 prior cases and adds46 peer-width cases:
32 genuine child combinations,
eight main-loop combinations and six additional mask127 cases. Both profiles,
status states, window states, source/precompiled children and ordinary/mapped
output are covered. Four parent binaries, both interpreters, the unchanged
compiler and unchanged CSI diagnostic reproduce exactly in an initially
build-free source tree. No original executable, private configuration, disk
image or REA database is a build input. Each DOS subprocess owns separate files and an ephemeral
TCP port; at most two run together after all model/build dependencies finish.
Both transaction parents repeat the linked ownership, width, field, erase,
scroll, UI and IRQ regressions. The full parent retains401440 bytes including its PSP and keeps
130 resident-code bytes spare. Compiler/VM stacks and limits are unchanged.

For the basic experimental parent and linked peer test:

```sh
./tools/dev --command python3 standalone/build_terminal.py --native-reset-bank --native-reset-transaction
./tools/dev --command python3 standalone/check_peer_width_live.py --terminal build/terminal-native-bank-transaction/TERMINAL.EXE
```

## Work still required

Later checkpoints add actual DOS [SUB/refusal/interrupted-request cases](SUBSTITUTE_CONTROL.md),
authenticated [ENiGMA](../lab/bbs/enigma-aspect-width.md) and
[Synchronet](../lab/bbs/synchronet-aspect-width.md) width sessions, and
[emulated carrier loss with same-process redial](../lab/bbs/peer-width-carrier.md).
Those receipts supersede the corresponding open software witnesses in this
historical checkpoint; they do not establish physical target acceptance.
The [wide DOS-child matrix](../lab/bbs/peer-width-process.md) separately adds16
actual RUN workflows, continued rendering and hardware restoration. It does
not establish arbitrary OS interruption or full-plane preservation around EXEC.

Verify interruptions beyond those selected cases and the controlled
ownership/fault matrix. Other terminal/video profiles,
arbitrary modal compositions, partial-width wrapped scrolling, font resources
and full application reconstruction remain open. The receipt explicitly keeps
`accepted_for_deployment: false`. The card is absent and has not received this
experimental parent.
