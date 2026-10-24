# Live helper returns on the owned BBSes

The helper-enabled terminal now has live directory-script, KEY kind2 helper and
unsaved editor evidence on the existing loopback Synchronet and stock ENiGMA
fixtures. This extends the synthetic modem checks in [HOOK_APPLY.md](HOOK_APPLY.md).
The exact executable is the normal
`terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply/TERMINAL.EXE`
build beneath `build/`.
The optionally branded Special Edition has separate startup evidence; its different
binary is not covered by these live runs.

All cases use actual DOS8086 execution, COM2,19200,8N1 and HARD flow. A directory
ASPECT script supplies only the existing synthetic account credentials. After it
returns, three Alt-1 KEY kind2 actions invoke a source-built helper before the
normal editor recipe. No acknowledgement keys are supplied between helpers.
Neither server is patched, reconfigured or restarted. Drafts are not submitted.

## Returned state and recovery

The first helper changes the integer/string banks, normal attribute, sound,
mouse preferences, autodownload, BREAK, mapping delay and clipboard separator.
In the reject variant it additionally changes an unsupported opaque PRM byte.
The second helper makes no changes. The third deliberately returns exit23.

Raw snapshots before each child independently establish accepted registers,
epochs, baseline and active settings after the first and second returns. Accepted
runs advance epochs1→2→3; rejected-first runs retain1 before advancing to2.
Rejected settings retain the captured supported state. Helpers read actual UART
divisor/LCR/IER/MCR, PIC mask and restored vector while the parent is quiet.
The following stock editor checks exercise RX/parser/TX and failure recovery.
There is no post-third accepted-bank snapshot, sustained transfer test or physical
modem timing claim.

Synchronet's recipe explicitly selects Local/General after logon, because the
synthetic account can retain a different sub-board from an earlier interrupted
session. The first reject attempt retained settings correctly but attempted to
post into read-only Notices; that failed editor run remains failed. An initial
fixture revision selected the wrong group; its failed artifacts are also retained.
The final fixture selects both group1 and sub-board2 before opening an unsaved
draft. No application acceptance requirement was removed.

## Compatibility boundary

Both acceptance and rejection pass on Synchronet with immediate forwarding and
on stock ENiGMA with explicit30ms byte-transparent buffering. A separate immediate
ENiGMA run authenticates, completes all helpers, emits the expected editor key
bytes and leaves no saved post, but reproduces the Home/Insert editor failure.
This remains conditional ENiGMA compatibility. Buffering is not a guarantee about
arbitrary TCP partitions; see [REGISTER_BBS.md](REGISTER_BBS.md).

The independent [receipt](validation/hook-bbs.json) checks source/product hashes,
frozen staged inputs, raw state snapshots, credential boundaries, keyboard wire,
semantic editor outcomes and draft cancellation. The [six corrupted-copy checks](validation/hook-bbs-auditor.json) reject
changed completion status, active normal attribute, accepted bank, quiet UART IER,
returned proposal and executable identity. Original artifacts are untouched.

## Source compilation follow-up

The live source-login attempts do not count as passes: no LOGON.ASX was produced
and authentication failed. A separate actual DOS control compiles the same source
exactly to the maintained host's bytes when ASPECT runs directly from DOS. A tiny
source script beneath the current retained parent reports `ASPECT: out of memory
(error 8, opcode 00, step 0)`, recorded in an actual DOSBox frame. An otherwise identical tiny-script control succeeds under the previous register
parent; the helper-enabled parent retains18,928 additional bytes and fails. Child,
compiler, source, KEY and PRM bytes are identical in that comparison. This establishes
a composed memory regression, not the precise failed allocation or a completed fix.
The raw [unresolved evidence](validation/hook-source-memory.json) binds these
attempts and the control. Nested compiler/interpreter memory is a required next
application task; precompiled-script acceptance does not close it.

## Reproduction

Use fresh labels and the existing owned services on loopback23231/23233:

```sh
./tools/dev --command python3 lab/bbs/directory_script_dos_probe.py \
  --label hook-sync-next --hook-session accept --cpu 8086 --mouse-scales 8 4 \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply/TERMINAL.EXE \
  --runner build/aspect-register-parent/ASPECT.EXE
./tools/dev --command python3 lab/bbs/enigma_directory_script_probe.py \
  --label hook-enigma-next --hook-session reject --packet-delay-ms 30 \
  --cpu 8086 --mouse-scales 8 4 \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply/TERMINAL.EXE \
  --runner build/aspect-register-parent/ASPECT.EXE
```

Select `accept` and `reject` on each board. Immediate ENiGMA is a separate
`--packet-delay-ms 0` observation and can fail its editor audit. The recorder
`standalone/record_hook_bbs.py` requires both helper modes on both boards, with
explicit labels; optional immediate observations retain their actual outcomes.
Native helper lookup/field parity, composed exit/trap ownership, compiler memory,
other application services, full BBS acceptance and physical Boca/SPA2102 testing
remain required. No full F01–F16 gate is closed.

The later [nested compiler memory checkpoint](NESTED_COMPILER_MEMORY.md) adds
a compact CLI and successful bare8086 source and observed386 BBS workflows.
It preserves the low-conventional-memory observer failures and the limits above;
the original receipt remains scoped to its precompiled scripts.
