# Explicit child IRQ lease

The optional `ASPECT_CUSTOM_IRQ` build now accepts a selected master-PIC IRQ
instead of deriving it only from the COM number. This is the child half of the
ISA-modem configuration work. The normal terminal/importer/editor still require
IRQ4/3/4/3; no card or Special Edition package has been changed by this work.

## Interface and ownership

The existing serial option remains valid and selects the standard IRQ:

```
/S1:0003:03:H
/S1:0003:03:H:ssss:oooo
```

The separate experimental executable also accepts a final IRQ suffix:

```
/S1:0003:03:H:I5
/S2:0003:03:B:ssss:oooo:I7
```

Only3/4/5/7 are accepted. The suffix is case-insensitive. Divisor, LCR, flow,
descriptor, parent allocation and translation/renderer validation remain in
place. The parser bounds every optional byte through the final NUL, including
near-segment wrap. Invalid IRQs reject before hardware writes in both the C
parser and the assembly backend, including direct backend admission.

The maintained backend now has a conditional fifth WORD argument. Its banked
far-to-near adapter copies all five arguments; the linked receipt inspects that
actual machine code. Complete eight-word PIC mask tables prevent IRQ5/7 from
indexing into an adjacent object. The selected slot supplies both the mask and
IRQ+8 vector. Native recovered UART/ISR source is unchanged. Close restores the
saved vector, mask, framing, divisor and modem control. A legacy option following
a custom lease returns to the standard mapping instead of retaining the prior
custom IRQ.

No ASIO structure or version was changed. The existing parent descriptor and
register protocol remain separate from this command-line selection. V1/V3 raw
handback is tested with the suffix; a real parent/v7 custom-IRQ handoff is still
pending. The terminal must publish its actual selected IRQ when that integration
is implemented. An existing child without this extension cannot be paired with
a custom-IRQ parent by silently omitting the suffix.

## Evidence

The [receipt](validation/custom-irq.json) binds:

- 309 targeted linked inputs: four COMs, IRQ3/4/5/7, four flow policies and four
  initial PIC masks; binary ISR RX/TX, master EOI, unchanged unrelated vectors,
  full restoration, V1/V3 raw handback, malformed/direct-backend refusals,
  busy reopens and near-segment boundaries.
- 108 existing serial inputs in24 groups on the optional executable.
- 29 actual DOS8086 workflows: all16 COM/IRQ pairs, additional SOFT/HARD/BOTH,
  legacy forms, five executions of the current banked register interpreter and
  two deliberate physical/lease IRQ mismatches. Matching configurations return
  the exact expected serial reply; mismatches produce error23 with no reply.
  All cases compare the independent42-byte before/after UART/PIC/vector sample.
- An empty287-source tree reproduces five products. The ordinary diagnostic,
  register interpreter and ordinary interpreter retain their exact previous
  executable hashes. The optional products remain separately named.

The DOS tests configure DOSBox-X's `irq:` serial parameter, whose implementation
is visible in its [upstream serial source](https://dosbox-x.com/doxygen/html/serialport_8cpp_source.html).
The mismatch cases verify that an ignored IRQ setting cannot count as a pass.
The full interpreter cases use a real far bank adapter and real bytecode; they
are standalone child invocations, not terminal-launched v7 exchanges.

## Reproduction

Use the pinned Nix tools and fresh output labels:

```sh
./tools/dev --command python3 standalone/build_aspect_serial.py --custom-irq
./tools/dev --command python3 standalone/build_aspect_process.py \
  --notice-bank --notice-sound --notice-input --notice-help --help-resource \
  --serial-bank --register-handoff --custom-irq
./tools/dev --command python3 standalone/check_aspect_custom_irq.py
./tools/dev --command python3 standalone/test_aspect_custom_irq_dos.py \
  --output build/custom-irq-dos-next
```

Outputs are `build/aspect-serial-custom-irq/SERIAL.EXE` and
`build/aspect-register-parent-custom-irq/ASPECT.EXE`. To reproduce all five
products, first build the standard controls through the same builders without
`--custom-irq`, and build `standalone/build_aspect_runner.py`; then run:

```sh
./tools/dev --command python3 standalone/prove_custom_irq_source.py \
  --output build/custom-irq-source-next
```

## Remaining integration

1. Extend the optional PRM/import/live validators and editor together; preserve
   standard defaults when a new COM is selected.
2. Carry the parent IRQ through script publication and prove actual v7 register,
   renderer, flow, failure and return ownership on IRQ5/7.
3. Extend guarded helper admission, startup and selective returned-settings
   adoption. Confirm offline same-COM IRQ changes and different-COM changes,
   restoring the old vector/hardware baseline before capturing the target.
4. Check refusal/confirmation races, all affected PIC/vector snapshots and
   continued real UART traffic. Repeat source reproduction and current BBS
   workflows on the composed product before packaging it.
5. Identify the Boca hardware and jumpers. Test physical exclusive IRQ ownership,
   sustained load, carrier, flow and restoration. Shared IRQs, slave-PIC handling
   and physical IRQ7/spurious-interrupt behavior are not established here.

The full application, stock ENiGMA fragmentation, analog bridge and physical
acceptance gates remain open.
