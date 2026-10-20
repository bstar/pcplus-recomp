# Native mouse primitives

The PROGRAM mouse dependencies now have source-built probe, initialization,
callback registration and event-processing primitives. Their six flat regions
match **368 original bytes**, including the callback's two-byte CS guard and a
13-byte signed-absolute helper. Relocatable objects link as `MOUSE.EXE` without
reading an original executable, installed configuration or REA database.
This is a component; live mouse support and PROGRAM integration remain open.

The [validation ledger](validation/native-mouse.json) records 117 linked cases,
one actual 8086 DOS self-check and a blank source-only rebuild. Existing normal
application products are unchanged; no full feature gate closes.

## Evidence and boundaries

The original PCPlus2.01 SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
`reconstruction/program_mouse/provenance.json` records each region's exact
end-exclusive source range, file offset, digest, REA evidence and mapping IDs.

| Original CS range | Role | Bytes |
| --- | --- | ---: |
| 76b4–76e8 | Driver-vector check and reset/probe | 52 |
| 76ea–7722 | Scale/state initialization | 56 |
| 7f92–7fa0 | Far callback registration | 14 |
| 8072–8099 | CS guard word and far callback | 39 |
| 809a–815c | Button/motion event processing | 194 |
| 9d66–9d73 | Signed absolute helper | 13 |

Retained REA exports already supplied the first three routines. Fresh REA byte
and source-mapping evidence supplies the callback/event block and absolute
helper. Ghidra did not recognize a procedure at18074; that failed dossier is
retained. The callback's entry is established by the registered CS:8074 pointer,
and its extent/event call by decoded instructions and far/near returns. No
decompiled callback function or complete static caller inventory is claimed.
The original callback DS immediate is an MZ relocation; analysis loaded bytes
are checked against the original with that declared relocation applied.

## Native behavior and ABI

`mouse_probe(reset)` is near, returns AX and removes its two-byte argument.
A missing INT33 vector returns0 without invoking it. Argument0 invokes function0
and retains its raw AX result; any nonzero argument invokes21h and admits only
AXffff with BX1..3. The result is not a general hardware inventory.

`mouse_init(y_scale,x_scale,reset)` removes six argument bytes. It publishes the
probe result; only a nonzero result sets both scale words, zeroes the16-byte event
state, calls function0Bh and installs the callback through0Ch with mask000Bh.
Its AX result is not a documented status value. The scale words are unchecked.
Either zero scale causes a real native divide fault during motion processing;
tests retain that behavior. Maintained live admission must validate settings
before enabling callbacks, while keeping the exact original baseline separate.

The callback installs its module DS and restores the driver's original DS.
It uses a CS depth word initiallyffff: outer entry reaches0, nested/busy entry
skips processing, and return balances the word. It returns far with IF cleared;
the driver owns the surrounding saved registers/interrupt return. It must not
be exposed as an ordinary foreground call that promises preserved FLAGS.
Actual linked and DOS tests demonstrate foreign DS **and a separate SS**.
The event processor and its absolute helper use BP-relative stack operands;
this native path does not intrinsically require DS=SS. Later C/VM bridges must
retain their own separately established ABI and ownership rules.

Motion divides signed16-bit counter differences by the configured scales.
Subthreshold motion retains the baseline. Pending events suppress new motion.
Horizontal movement wins a magnitude tie; signed direction selects codes0..3.
Disabled motion is still rebased after a nonzero quotient. Button events select
codes4/5, can override pending motion, and give the left press precedence when
both selected press bits arrive together. Disabled buttons retain the old event.
These are observed native event codes; complete UI/keyboard consumption is not
implemented by this component.

## Verification and reproduction

```sh
./tools/build test-native-mouse
./tools/build test-native-mouse-source
```

The linked replay executes the actual relocated instructions and declares DOS
vector/INT33 results as scalar boundaries. It covers absent/partial vectors,
reset modes, accepted/rejected button counts, state initialization and registration,
positive/negative/subthreshold/tied motion,16-bit counter wrap, pending/disabled
events, both buttons, busy entry, foreign DS/SS and both zero-scale faults.

The actual DOS executable probes and initializes DOSBox-X's INT33 driver,
registers the native callback, then calls it with source-owned motion/button
events on a separate stack and foreign DS. It checks motion, pending input,
buttons, disabled events, guard balancing and IF/segment restoration. It retires
its callback before the DOS allocation terminates and writes an exact success
marker only after completing those checks. A missing executable or ordinary
emulator exit cannot satisfy the runner. Physical clicks/motion and latency are
not represented by these directly supplied events.

The fresh-source check copies only the declared assembly, host, provenance and
builder inputs into a blank tree. It validates all six flat region hashes and
reproduces `MOUSE.EXE` exactly. The analyst-only `recover.py` explicitly requires
the ignored original and retained REA records; ordinary builds never invoke it.

Remaining work includes scale/enable configuration admission, complete event
consumption and UI mappings, owned driver/callback suspension and restoration
across real PROGRAM/ASPECT children and faults, original keyboard/window/error
services, physical mouse/modem tests and full application acceptance.
