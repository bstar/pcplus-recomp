# Banked ASPECT serial controller

The current full interpreter had only 112 bytes left after `_TEXT`, too little
for the register-handback extension. The optional serial-bank build moves the
existing serial controller into ASIO_CODE and keeps its public near-cdecl ABI
through explicit adapters. It changes placement, not protocol or script behavior.
ASIO remains v1–v6; register handback is still pending.

Build with `./tools/dev --command make aspect-serial-bank`. The result is
`build/aspect-serial-bank-parent/ASPECT.EXE`, with its usual LOCHELP.HLP companion.
The preceding help-resource interpreter still rebuilds to identical bytes.

## Placement and ABI

The 3,415 compiler-emitted serial instruction bytes are identical to the
preceding object's code segment. Compiler aliases redirect its public entries
and external calls; segment/class names and relocation targets intentionally
differ. Nine public near/far entry pairs and fourteen resident callback pairs
preserve DS=SS, caller-cleaned argument slots and returned register values.
The six-word directory-accounting callback has an explicit separate adapter;
the existing generic callback family is not widened.

`_TEXT` shrinks from 65,408 to 62,304 bytes, freeing 3,104 bytes. ASIO_CODE uses
3,613 bytes including wrappers. Its linker-selected CS is shared with other
far modules and its offset is nonzero; adapters use actual mapped addresses
and relocations, rather than assuming a zero-based bank. All code fits its
real-mode segment and precedes DGROUP, so ordinary retention of the CRT data/
heap extent retains the bank across nested EXEC. Data/stack remains 53,248 bytes.
This creates room for further work; it does not close a full application gate.

## Evidence

The linked audit checks all 23 entry/callback pairs, every declared argument
copy, near target, far target and far-call relocation, as well as segment bounds,
unchanged instruction bytes and unchanged data extent.

All 28 actual DOS serial-script cases pass with the banked interpreter. They
exercise binary/control/high bytes, argument expansion, repeated operations,
matching, timeout and returned unread data. Two larger attached-terminal DOS
workflows pass on COM1 with combined flow and COM2 with software flow, totaling
112 checks. Each includes nested DOS programs, private streams and enumeration,
directory data, display restoration, command shell, actual DOS compilation,
and parent serial return.

The first two attached runs failed at the nested compiler with DOS error8
while a large passive observer occupied conventional memory. Moving only that
diagnostic observer high allows both unchanged products to complete. The accepted
configs explicitly contain `LH D:\\RENDER T`; the earlier failures remain
retained. This is an instrumented memory limit, not proof that arbitrary memory
profiles or physical machines will work.

Read-only actual DOS greetings against the existing local Synchronet and ENiGMA
servers pass through the Hayes/Telnet model. These checks send the expected dial
and one CR, with no login, menu navigation, posting or file transfer. They do
not establish full BBS or physical modem compatibility. No server was restarted
or reconfigured for these checks.

An empty-tree proof reproduces six products from 685 sources: terminal and its
projection probe, banked ASPECT, DOS compiler, help resource and settings editor.
The [independent receipt](validation/aspect-serial-bank.json) binds exact object
bytes, bridge relocations, raw DOS/BBS captures, both observer placements and
the source proof. Failed preliminary captures are not accepted as passing.
Next is the register exchange protocol: bounded parent storage, child admission,
native per-script initialization and validated handback, followed by guarded
HOOK routing and returned-setting application.
