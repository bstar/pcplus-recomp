# Native reset in a separate data and stack context

The recovered native width/soft-reset code now executes with its own DS=SS
image and stack while the real UART receive interrupt continues writing to the
root data segment. The [receipt](validation/reset-bank.json) binds the component
to actual DOS8086 binary traffic, exact source reproduction and the unchanged
ordinary reset controls. It is not yet linked into the interactive application.

`src/ui/reset_bank_context.asm` supplies the register interface: AX carries the
body request and returns its status. The bridge preserves the other registers
and caller FLAGS, rejects unsupported entry context, and retains one caller
frame in code-segment-owned words. It switches SS/SP/DS/ES with interrupts
briefly disabled, then enables interrupts for the native body. Return restores
the root stack and registers. A body-owned typed error can discard its private
frames and return a status; no root data image or UART state is restored.

The private image and stack occupy one physical DATA segment. An earlier split
DATA/STACK link interleaved the root group and exceeded the64KB limit. The
accepted layout is disjoint and measured from exported linker symbols:

| Extent | Size or offset |
| --- | --- |
| Private reset group | 59,136 bytes |
| Native data-image origin | 0100h |
| Native image length | D600h /54,784 bytes |
| Private stack | D700h..E700h /4,096 bytes |
| Root UART diagnostic group | 9,856 bytes |
| Diagnostic static far shadow | 6,336 bytes |

The DOS loader's initial stack is also checked against the real root stack.
These are the paired diagnostic's extents, not the full application's future
memory budget. The context control words add no root near data.

## Actual interrupt and context checks

The source-built driver configures COM1/IRQ4 at38400,8N1 with flow disabled. A
marker sent from inside the private context tells the loopback peer when to
send every binary byte value twice. The real recovered UART ISR reloads the
root data segment, stores all512 bytes while SS still belongs to the private
bank, and returns to the native body. The observed root RX count rises from0
to512 during that interval. After return, the root reader validates and echoes
the complete sequence independently.

Twenty checked body calls verify BX/CX/DX/SI/DI/BP/ES, root DS=SS and full caller
FLAGS. They include repeated narrow/wide requests, typed private-frame
abandonment followed by reuse, and an attempted reentry from the private body
that must refuse without replacing the outer owner. Each native body starts
from a fresh diagnostic image; this is repeated context entry, not preservation
of a live terminal's width state across requests. Separate IF-disabled, DF-set
and mismatched DS/SS entries refuse. Root canaries, ring drain/drop invariants,
the original interrupt vector and all42 sampled hardware bytes verify.

The native body executes the actual2A6E width adapter,20A4 soft reset and their
recovered geometry/video/viewport dependencies on the selected24-row,
hidden-status profile6 path. A static owned shadow satisfies the native far
allocation ABI; there is no DOS heap allocation or free in this fixture.
Unsupported full-profile services remain diagnostic boundaries. The typed
abandonment case is a deliberate body fault, not arbitrary asynchronous recovery
or a rollback after a partially completed native reset.

The final component SHA256 is
`9551b816d1f6a6fe921205236324ff4f4dae3bb42ef704dfe71750e24c690557`.
76 declared source/test/toolchain files reproduce it exactly in an empty tree
and repeat the actual DOS IRQ workflow. The ordinary reset remains
`8bdd8c62707ef4c1761c734a9481cad18be991aeed3cadd6194c527f14408e32`;
the viewport reset remains
`066101b9dd744d9dec029ac2160decd0a3c6505c3d4f1c787e651d4c45fa5e92`.
No original executable, existing object or REA database is a build input.

Two failed observations remain recorded. The first DOS pilot passed its driver
and IRQ workflow but its verifier assumed the private stack ended atE600h,
ignoring the image's100h prefix. It remains a failed report; the accepted repeat
uses the actual map bounds. The first clean build also exposed an undeclared
UART `layout.inc` dependency. The corrected closure includes that input and
passes fresh reproduction and execution.

```sh
./tools/build test-reset-bank
```

This builds the component and both controls, then performs a fresh source build
and DOS replay in a new directory. To retain an explicitly named run, use
`standalone/test_reset_bank_dos.py --output build/UNIQUE_DOS` and
`standalone/prove_reset_bank_source.py --output build/UNIQUE_SOURCE` through
`./tools/dev --command`. Seal matching results with
`standalone/record_reset_bank.py --dos ... --proof ... --output ...`.

## Remaining application integration

The [experimental parent checkpoint](NATIVE_RESET_PARENT.md) supplies the
namespace and exclusive borrowed workspace. Its cold-call and DOS retention
checks pass, but nested source compilation still fails memory admission. The
following projection/transaction and broader handler gates remain open.

The bank still needs production typed callback bindings alongside the live
application, an explicit renderer/profile projection and commit schema, and
display/shadow rollback for failed native operations. Copying the root data
image remains prohibited: receive queues, flow state, handles, parser/owner
state and the root stack must stay outside rollback. Existing foreground C and
DOS owners must regain their expected context before they run.

The native bank's extra memory must be included in retained-parent extents and
DOS child/ASPECT/compiler admission. Current data/stack space in the parent is
already tight; this component alone does not prove a full packaged parent plus
child fits conventional memory. Modal UI, break/critical traps, other handlers,
profile paths, general allocation/error presentation and full width/reset/BBS
workflows also remain open. IRQ evidence here covers the selected UART ISR,
not every installed handler or physical machine. The ordinary application,
Special Edition package, staged card payload and card are unchanged.
