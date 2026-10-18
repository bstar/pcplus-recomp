# Static far code and the resident DOS ABI

The dedicated printer controller now runs in a separate `PRINT_GROUP` code
segment. Its seven public entry points retain the existing near-call interface,
so the resident parser, keyboard router, shutdown path and other modules do not
need a different calling convention. The source remains8086-compatible and the
shared near C data/stack invariant remains DS=SS.

The first far-code checkpoint, bdeb347c, reduced resident code from63,836 to
62,604 bytes and placed1,449 controller bytes in the new segment. The later
[UI far-storage migration](UI_FAR_STORAGE.md) adds224 resident helper bytes:
current resident code is62,828 bytes, with2,708 bytes available. The controller
segment remains1,449 bytes. Near data/stack now occupies52,368 bytes, leaving
13,168 available after moving three private UI frames. These changes free
segmented address space; they do not eliminate the application's total memory
requirements or complete its memory architecture.

## Explicit bridge contracts

`src/terminal/controller_abi.inc` lists seven entries and fifteen services.
Both assembly sides consume this list. Resident entry wrappers issue a relocated
far CALL; far entries make a local near call to the implementation and return
with RETF. Calls back to resident services use the reverse path. The ordinary
bridges accept register arguments or no arguments and preserve the target's
register/flag results. They do not forward arbitrary C stack arguments or RET N
interfaces. The controller's raw PRN byte service has an explicit adapter:
AX is pushed as the target's near-stack argument, then popped after its call.

`far_bridge.inc` is reusable assembly machinery, not a medium-model conversion
of every C/assembly module. New modules need their own audited ABI lists and
service adapters. IRQ entry points remain resident. Shared state and strings
remain in DGROUP. No native reconstruction instructions or diagnostic fixtures
were converted into overlays.

The linker explicitly places CODE, FARCODE, DATA, BSS and STACK in that order.
The [Open Watcom linker ORDER directive](https://open-watcom.github.io/open-watcom-v2-wikidocs/lguide.html)
provides class ordering. A separate OMF `PRINT_GROUP` prevents automatic grouping
from collapsing the controller back into the resident CS. Paragraph alignment
makes its offset zero. Keeping initialized code before BSS/STACK avoids
serializing their otherwise unnecessary zero padding into the DOS executable.

## Build and ownership checks

`terminal_memory.py`, called by the actual terminal builder, checks the MZ and
linker map before reporting a successful build. It requires:

- Separate, bounded code and shared-data segments, with controller CS distinct
  from resident CS and a paragraph-aligned entry extent.
- All22 bridge pairs targeting the declared symbols, with exact near/far return
  instructions and the PRN argument adapter.
- An MZ relocation at each far CALL's segment word, rather than a coincidentally
  correct address before the DOS loader moves the application.
- Executable bytes inside the loaded image and inside the static extent retained
  by PROGRAM. Existing shadow/history/snapshot, stack and pointer checks remain.

PROGRAM retains all static segments. The actual DOS child test locates its
parent through PSP/MCB data, checks the retained allocation, samples the full
relocated controller byte sum, allocates and fills16KB elsewhere, then checks
code and screen-buffer samples again. The parent resumes actual far controller
polling after the child returns. This tests retained static code; it does not
implement dynamic overlay loading or reclaim code segments.

## Verification and failures caught

`check_far_code_live.py` executes all seven far entry paths through the linked
controller and checked PRN code. It observes the actual CS transition, DS=SS,
stack use and return to the resident caller. A hardware FIFO byte is offered
while controller code is executing; the real UART ISR and IRET must return to
the interrupted far CS and preserve both foreground and received bytes. Only
hardware and DOS kernel boundaries are modeled. The inspector separately rejects
six corrupted images/maps, covering targets, return form, adapter, relocation,
segment overflow and a merged resident CS.

Development exposed a real argument bug before this checkpoint: an ordinary
register bridge was insufficient for the stack-based raw PRN service, and the
all256-byte oracle observed repeated A0 instead of the payload. The explicit
adapter fixes it. The linked harness also had a caller fixture beyond STACK
which overwrote new code there. Caller fixture data now occupies a guarded,
unused part of the real test stack. A different internal DOS EXEC stack remains
valid. Replay termination uses a CS-qualified return sentinel and an instruction
bound, rather than stopping at the end of the first64KB of code.

The current results are hash-bound in
[the far-code validation record](validation/terminal-far-code.json),
[dedicated-print evidence](validation/terminal-print-controller-live.json), and
[the isolated source rebuild](validation/terminal-source-build.json). BBS results
are recorded separately in [the compatibility checkpoint](../lab/bbs/modern-compatibility.md).
These records distinguish linked hardware/kernel models from actual DOS runs.

```sh
./tools/build terminal
./tools/dev --command python3 standalone/check_far_code_live.py
./tools/dev --command python3 standalone/test_far_storage_dos.py
./tools/build test-terminal
```

This is one static segmented module. Full application startup/resources,
additional emulations and protocols, settings/UI, ASPECT, Host, original overlay
coverage and physical modem/386 validation remain open in `FEATURES.md`.

## Modem service extension

[MODEM_FAR_CODE.md](MODEM_FAR_CODE.md) extends this mechanism with a separate
modem CS, namespaced register services and four explicitly declared caller-cleaned
word-argument adapters. The current build verifies44 bridge pairs across the
printer and modem modules; the original22-pair controller checkpoint above
remains historical evidence. The DOS child now records56 bytes and verifies
both code sums before/after allocation. General C callbacks and dynamic overlays
remain outside the implemented ABI.
