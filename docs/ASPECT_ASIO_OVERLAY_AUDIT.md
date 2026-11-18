# ASIO overlay capacity audit

## Saved experimental checkpoint

Work paused at the user's request. The audit below describes the original
source-only proposal; subsequent opt-in implementation changes `serial.c`,
`serial_bank.asm` and the three ASPECT builders. It is not release-qualified.

`serial_overlay_ready` defaults to false; `--serial` requires the split-ready
build. The four directory/translation getters stay resident, with the existing
DATA fields exported only under this option. The remaining ASIO code and all
register APIs share one sibling section. No connection runtime opcode is enabled.

Disabled controls reproduce both previous child executables exactly; receipt
`build/asio-overlay-v1-20261119/disabled-controls.json`. The experimental child
`build/asio-shared-overlay-v1-20261119/ASPECT.EXE` has SHA256
`47a3a7f961a67b0fda1e916e1e63c35e65a5d984b56cabb267e309f156f07004`.
Its exact minimum including PSP is121600 (saving5040 bytes), page minimum121760
(saving5088), near code65492/spare44, DGROUP40640 and stack8192 unchanged.
These are build/layout measurements; application heap headroom remains unproved.

The focused DOS8086 probe is `standalone/test_aspect_serial_hot_dos.py`.
Its v2 run passed four cases, each comparing327680 C/ASM WORD calls and327695
resident hot reads after sibling eviction. Its overlay-read counter lacks an
independent positive control, so this remains provisional. The current v3
source adds counter controls/register canaries but fails assembly before DOS:
generated `read-root.asm:32` uses PUSH immediate, which is unavailable on8086.
Do not report the current probe as passing. Preserve v1/v2 logs and the v3
failure; fix that instruction and rerun before expanding validation.

The full five-case screen/source suite has not started. Help, RPC refusal/reuse,
wide screen, nested preload, loader failures, abort/close/register publication
and package/cold/DOS/BBS qualification remain required. Use the current GET
compiler `build/connection-compiler-v1-20261118` for current-source preflight.
No owned build/test/DOS processes remain; nothing was installed or selected.

## Original source audit

The source supports an opt-in sibling ASIO overlay with resident public and
callback gates. No mandatory asynchronous entry into `ASIO_CODE` was found.
This is an implementation proposal, not an executed overlay qualification.
It does not enable connection commands or establish additional heap headroom.

The audit uses commit `e619ed0ab3c254c374e4d76e3c044edf935f46f0` and the
qualified `build/screen-child-overlay-v4-20261119` map, manifest and executable
(`1a0369887a08084365cbd04dc3f41daa2545088b5a01382f22d3ee9179519fa4`).
Concurrent connection/compiler work is outside this measured image. Only this
new document was written; no product, builder, checker or installed profile was
changed. No original application input or physical/private service was used.

## Measured capacity

The linked resident `ASIO_CODE` is **5,060 bytes**, at `1127:0000`, partitioned
by adjacent module boundaries as follows:

| Contribution | Offset range | Bytes |
| --- | --- | ---: |
| `serial.o` | `0000..0edf` | 3,808 |
| ASIO half of `serial_bank.obj` | `0ee0..0f9c` | 189 |
| `register_handoff.o` including static codec helpers | `0f9d..13c3` | 1,063 |

The existing shared arena already accommodates Help's 6,561 bytes. GET plus
its editor occupies 5,623 bytes; Notice 6,466; PROGRAM 1,463; SCREEN 1,016.
ASIO therefore fits below the existing maximum bank size. Moving this code
should reduce the root allocation by approximately five kilobytes, less new
loader vectors, section metadata and alignment. A relink must measure the actual
saving; it cannot be inferred as exactly 5,060 bytes.

The measured child retains near code65,508 (28 bytes spare), DGROUP40,640 and
stack8,192. Its manifest records exact minimum126,640 and page minimum126,848
bytes including PSP. Root image78,913 bytes and separate overlay trailer47,935
bytes are identity bounds, not a claim about runtime free heap. Moving ASIO does
not itself enlarge near-code spare. New gates must not consume that28-byte
budget; the existing gates can be retained byte for byte.

## Entrypoints and ownership

[`serial_bank.inc`](../src/aspect/serial_bank.inc:4) enumerates all nine public
entries: directory entry/record, preload, translate, translation policy, open,
close, compiler pause and compiler resume. Their existing resident near-cdecl
gates call symbolic FAR bank targets. The resident part is319 bytes at
`0001:c09b..c1d9`, including fourteen callback gates.

[`serial_bank.asm`](../src/aspect/serial_bank.asm:19) copies callback arguments
from `BP+8`, because a bank-local near wrapper precedes the FAR resident call.
The public FAR entry copies its caller's argument from `BP+6`. The custom IRQ
backend callback copies five words; ordinary backend open copies four. Retain
those ABIs, register behavior and cdecl cleanup exactly.

The fourteen callback targets are PSP, renderer active/prepare/attach, pure
directory-accounting patch, backend open/close, BREAK release, flow-alive, ticks,
poll, TX-empty, compile hold and compile release. The targets and the callback
gates stay resident. The accounting routine is a bounded in-memory patch, not
directory-file I/O ([implementation](../reconstruction/directory_accounting/patch.asm:1)).

All four register APIs are explicitly FAR-cdecl
([declarations](../src/aspect/register_handoff.h:13)). Validate, attach and
publish are called inside ASIO. Start is called from resident invocation reset
([runtime](../src/aspect/runtime.c:180)), so it needs a real overlay vector.
Keep `serial.o`, the bank half and `register_handoff.o` in the **same section**:
the qualified C bytes optimize an internal FAR register call to a pushed-CS
near call (`0e 3e e8`). It is safe within one section, not a general cross-bank
call convention.

All persistent state remains DATA/BSS: handoff/exchange pointers and tokens,
translation table/mode, directory entry/record, preload fields, compile-pause
ownership, UART ring, flow/carrier fields and interpreter registers. The only
pointer returned by a public ASIO API is the DATA directory-record pointer.
The exchanged FAR pointers address validated parent data. None is an ASIO code
pointer ([serial](../src/aspect/serial.c:32),
[register lifecycle](../src/aspect/register_handoff.c:6)).

## Asynchronous and nested paths

The actual UART ISR is resident `_TEXT`
([core](../reconstruction/uart/core.asm:333)). It handles ring and flow state
without entering serial C, the overlay loader or renderer callbacks. Resident
backend read/write/poll/ticks and process detach/restore also remain resident
([backend](../src/aspect/serial_backend.asm:432),
[process owner](../src/aspect/process_serial.asm:1)). The optional terminal
gateway flow hook in `src/uart/api.asm` belongs to a different profile and must
not accidentally join this overlay.

The published renderer callback address comes from resident assembly; it is
not an ASIO function ([client](../src/aspect/resident_render_client.asm:11)).
Its C dispatch is resident and defers WHEN execution for the callback duration
([dispatch](../src/aspect/resident_render.c:484)). Raw receive, send and transport
poll callbacks call resident paths. `runtime_receive_reset` reads the ASIO
translation table through256 foreground calls during invocation initialization;
the first can load ASIO, and subsequent calls should reuse it.

The important nested startup path is:

`resident open gate → ASIO open → ASIO backend callback → resident backend open
→ resident preload gate → ASIO preload → return to backend → return to ASIO open`.

The qualified linked bytes establish these are real symbolic FAR/near calls:
open gate `0001:c0df` has `9a 1a 0f 27 11`; backend callback `1127:0f61` has
`9a 5d c1 01 00`; preload gate `0001:c0b5` has `9a f6 0e 27 11`; preload FAR
entry calls its local implementation. This is **not** proof of future overlay
veneer placement. Inspect the newly linked bytes and map as a separate gate.
Backend masks the UART and clears IER before preload; ISR installation and
hardware RX enable occur afterward
([backend order](../src/aspect/serial_backend.asm:104)). Preload must not cause
a second disk read or manager reentry while ASIO is already being loaded.

Renderer prepare runs before backend acquisition. Renderer attach runs after
successful backend open; on failure, ASIO invokes its local close implementation
before returning ([open tail](../src/aspect/serial.c:252)). All renderer code and
its actual FAR callback stay resident; no current ASIO callback calls GET,
Help, Notice, PROGRAM or SCREEN directly.

## Compilation, external execution and shutdown

Source compilation calls ASIO pause, returns to resident code, starts its
compiler/parent lease, executes the compiler, retires the lease and re-enters
ASIO resume ([source owner](../src/aspect/source_compile.c:104)). No ASIO frame
spans the compiler EXEC. The external-process serial wrapper similarly pauses
before resident detach and re-enters ASIO after restoration
([process wrapper](../src/aspect/process_serial.c:9)). Active2 and pause-token
refusals must retain their existing behavior. PROGRAM/GET/Help can displace ASIO
between these calls without losing its DATA state.

Normal runtime finish first crosses the GET lifecycle gate
([runtime](../src/aspect/runtime.c:344)); ASIO close therefore must work when
another bank is currently loaded. Close releases BREAK, drains bounded flow,
restores child hardware/IRQ ownership, publishes registers, copies unread raw
bytes and status, then writes `returned=1` last
([close](../src/aspect/serial.c:273)). Register publication happens after backend
close and before ASIO handback publication. Those orderings must survive reload.

There is no direct near-longjmp call in ASIO or the audited resident serial
callbacks. Native interpreter abort restores only a near context, however
([abort](../src/aspect/abort.asm:1)). Existing screen/GET proofs do not establish
new close/publication behavior after abandoned bank frames. The pinned standard
manager has a256-byte private bank stack and patches FAR returns; its
`ovlret.asm` supports sibling reload on return. The recovered near-longjmp does
not call the CRT overlay-stack restoration hook. A fresh fault test must check
that an abandoned bank entry cannot corrupt subsequent ASIO entry/return,
register publication or the manager stack. Do not add an aborting ASIO callback
without a deliberate resident unwind protocol.

Loader I/O failure remains fatal255, not a typed serial error. Existing parent
revocation contains tested loader failures
([prior scope](ASPECT_OVERLAY_IO.md:49)); those tests do not prove failure while
loading ASIO close/resume or register start. In particular, failure to reload
close may prevent child publication entirely. Parent revoke, UART/vector
restoration and absence of a falsely published `returned` flag need direct
evidence; raw UART-only CLI cleanup is not implied by attached-parent proof.

## Proposed integration and proof gates

1. Add guarded root-only/overlay-only assembly modes following GET's pattern.
   Keep the current combined path and compilation order for the disabled
   profile; compare the complete disabled executable byte for byte. Root-only
   declares external FAR entries; bank-only declares external resident
   callbacks. Preserve the custom IRQ five-word branch.
2. Add an optional serial sibling section to the standard-overlay builder,
   containing `serial.o`, the split bank object and `register_handoff.o`.
   Keep the root object, backend, IRQ/core/API, process owner, renderer/client,
   all DATA/BSS and stacks resident/preloaded. Retain checked loader I/O.
3. Require map/OMF/linked-byte evidence for all nine public FAR calls and
   external register start, resident callback targets, same-section internal
   near calls, resident vector tables, all DATA bounds and unchanged buffer
   sizes. Measure root/MZ/exact/page minima and near-code spare. Reject
   duplicate combined and split bank objects or missing expected objects.
4. Run actual8086 DOS nested open/preload with preload0/4096, translation modes,
   metadata/accounting and v7 register handoff. Observe no disk request on
   same-bank preload reentry, exact arguments/DS=SS/stack restoration, and no
   ISR execution in replaceable code while RX arrives during bank switches.
5. Re-run source startup and source EXECUTE compilation, GET/WHEN, Help/Notice,
   PROGRAM/detach/restore and all seven screen commands with held FILEs and
   unchanged environment/buffers/stacks. Force sibling displacement before
   pause/resume, register start and final close; check full WORD/register/string
   state and raw queue/flow/DCD handback, publication ordering and parent input.
6. Exercise typed errors and native abort while each sibling is active, then
   ASIO close/publication. Inspect manager bank-stack balance/high-water and
   canaries. Inject loader open/read/short-read failure on ASIO start/resume/
   close and nested startup; retain incomplete-publication evidence, verify
   parent revoke/vector/UART/resource recovery, and relaunch a script in the
   same parent. No synthetic successful handback or waived fatal exit.

No source-level blocker requires leaving all5,060 bytes resident. The remaining
gates are specific linked-call, loader-lifetime and failure-recovery questions;
the existing generic nested-overlay probe is only a prerequisite. New products
still require ordinary package/cold/DOS/BBS qualification before promotion.
