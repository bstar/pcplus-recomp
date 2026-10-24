# Composed parent IRQ configuration

The optional `TERMINAL_CUSTOM_IRQ` terminal/editor now accept IRQ3/4/5/7 for
BIOS-listed standard-base COM1..4 and pass the selected IRQ to the matching
`ASPECT_CUSTOM_IRQ` interpreter. The ordinary products keep their exact previous
executable hashes. This build is not installed on the card or in the staged
Special Edition package.

## Configuration and ownership

The existing selected-port PRM IRQ word is used; no file format or ASIO version
was changed. Setup validates the same policy as startup, live settings and
returned helper settings. Selecting a COM retains that port's valid saved IRQ;
an invalid inactive value receives its standard default. Editing the IRQ changes
only its selected table slot. Unsupported IRQs and nonstandard bases reject.

The parent checks its vector against its active IRQ slot, then appends the
explicit IRQ suffix to the child lease. Pair it with the custom-IRQ ASPECT build;
the ordinary child does not support this suffix. All v7 register descriptor,
seal, reset, renderer and flow rules remain in force.

Offline IRQ changes use the existing confirmation and drained PROGRAM owner.
For another UART, the old UART is restored before the target snapshot is taken.
For an IRQ-only change on the same UART, the original hardware/PIC snapshot is
retained: restoring/re-saving the original UART here would pulse DTR and replace
its exit baseline with live state. Only IRQ/vector ownership moves. The old
vector is restored, the target vector is captured, DTR stays asserted, and final
shutdown restores the original UART, all affected vectors and the original mask.
Connected/busy changes refuse; declining keeps the active link while leaving
the deliberately saved PRM available for a later attempt.

## Evidence

The [receipt](validation/parent-custom-irq.json) independently checks:

- 324 linked inputs: editor/import round trips, invalid-field atomicity, saved
  per-COM IRQ retention/default repair, all 240 directed COM/IRQ transitions,
  actual recovered ISR RX/TX, DTR continuity and original baseline restoration.
- Four production PRMEDIT workflows in DOS8086: same-COM IRQ5→7 and IRQ7→5,
  COM1/IRQ5→COM2/IRQ7, and decline. Exact saved PRM, four UART/vector/PIC samples,
  independent timer activity, selected-IRQ receive/replies, typing and video
  are checked. No peer connects until the offline settings choice is complete.
- Fourteen actual parent/ASPECT v7 workflows on COM1/IRQ5 and COM2/IRQ7: normal,
  damaged token, missing script/helper, divide, budget and confirmed abort.
  All 86 paired snapshots check every register byte, native reset/tails, token,
  epoch, seal, failed-child retention and post-child receive/parser/transmit.
- Ten guarded-helper workflows, online and offline, on the same IRQs. Thirty
  helper executions inspect accepted/returned frames; success adopts atomically,
  failure retains the accepted bank. Extended raw snapshots inspect the IRQ5/7
  vectors and actual masked UART at each helper boundary.
- Eight bare-parent DOS source-compilation workflows: explicit ASP, ASX fallback
  to source, chained source and rejected-source recovery on both IRQs. Successful
  ASX files match the host compiler exactly; rejected source emits no success
  marker. These runs have no resident observer consuming compiler memory.
- Eight products reproduce exactly in an empty 715-source tree. Five standard
  controls, including the terminal, editor, both existing interpreters and DOS
  compiler, retain their earlier hashes. No original executable/object is input.

The register tests retain explicit native integer-bank operand fixtures; they
do not establish complete compiler/native-language parity. DOS UARTs and modem
peers are emulated. This receipt does not establish physical IRQ sharing,
spurious IRQ7 handling, arbitrary source sizes, current stock BBS behavior or
full application acceptance.

## Build and reproduce

Use the pinned Nix toolchain. Build all three matching optional products:

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff --session-controls --hook-return \
  --hook-execute --hook-modem --hook-input --hook-apply --hook-lookup \
  --exit-guard --traps --custom-irq
./tools/dev --command python3 standalone/build_setup.py \
  --mouse --notice-sound --custom-irq
./tools/dev --command python3 standalone/build_aspect_process.py \
  --notice-bank --notice-sound --notice-input --notice-help --help-resource \
  --serial-bank --register-handoff --custom-irq
```

The terminal is the `-custom-irq/TERMINAL.EXE` variant of the full guarded lookup
build; its sibling products are `build/setup-mouse-notice-sound-custom-irq/PRMEDIT.EXE`
and `build/aspect-register-parent-custom-irq/ASPECT.EXE`. The DOS compiler remains
the current ordinary `build/aspect-compiler-dos/ASPCOMP.EXE`.

Use fresh output labels for actual DOS workflows:

```sh
./tools/dev --command python3 standalone/check_parent_custom_irq.py
./tools/dev --command python3 standalone/test_parent_custom_irq_dos.py \
  --output build/parent-irq-dos-next
./tools/dev --command python3 standalone/test_parent_irq_compile_dos.py \
  --output build/parent-irq-compile-next
./tools/dev --command python3 standalone/prove_parent_custom_irq_source.py \
  --output build/parent-irq-source-next
```

The last command also needs the five standard control products/manifests built
from current sources. The receipt recorder accepts the DOS, compilation and
source-proof output paths separately. [Current stock BBS checks](IRQ_BBS.md) now
cover source login, helpers and editors with recorded ENiGMA buffering limits.
BBS/transfer pressure, additional refusal races, branded packaging and real
Boca/adapter tests remain next gates.
