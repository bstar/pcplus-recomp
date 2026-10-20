# Mouse events, keyboard consumption and driver ownership

The native mouse producer now feeds the original keyboard reader through one
shared state. A maintained foreground owner validates motion settings, retains
the caller's driver state, suspends callbacks for a DOS child and reinitializes
the mouse afterward. The separate `MOUSEKEY.EXE` diagnostic passes 76 linked
policy cases and 42 actual 8086 DOS assertions; three products reproduce from a
blank source tree. The [validation receipt](validation/mouse-keyboard.json)
keeps component evidence separate from normal application publication.

Normal terminal input is still BIOS-only. Startup/live setup activation, real
PROGRAM/ASPECT parent composition and the complete UI routing remain required.
This checkpoint closes no F01–F16 feature gate.

## The native event is the keyboard queue

The [mouse primitives](NATIVE_MOUSE.md) write DS7a60/62/64. The existing keyboard
consumer reads those same words as active/count/index. They are now aliases of
one source-owned allocation, rather than independent buffers. A motion event
provides a code0..3 and a repetition count; a button supplies code4/5 and count1.
The consumer decrements that count and clears the button-pending word. It does
not advance the index because the index identifies the repeated event.

The original startup-data overlay32 supplies the 30-byte enable/peek/read table:

| Event code | Meaning | Peek word | Read word |
| --- | --- | --- | --- |
| 0 | Up | 4800h | 4800h |
| 1 | Right | 4d00h | 4d00h |
| 2 | Down | 5000h | 5000h |
| 3 | Left | 4b00h | 4b00h |
| 4 | Left press / Enter | 1c0dh | 000dh |
| 5 | Right press / Escape | 011bh | 001bh |

All six source default enables are1. This explains the original twelve-byte
distance between the peek and read tables. The composed build validates 368
mouse code/guard bytes, 231 keyboard bytes including alignment, and these 30
data bytes against their independent recorded digests. Those existing regions
overlap earlier component coverage; they are not an additional599 unique bytes
of application recovery.

The table is absent from the initialized resident-only MZ image. The attempted
REA read correctly returned zero bytes with `complete:false`. A read-only
synthetic overlay1 context materializes the verified overlay32 data. Its REA
read is `ev_fa5e0d08d7086b2a1cb1eec1c4a703327d3f9c92df323653b3ae6e656ed84366`;
the synthetic mapping is
`ev_7b7ba9ed240073ed5b9d330f049f2ecf92f68f9256f63042aebba69efc2c13bf`.
The original source range is file2b73e..2b75b, within overlay32 at file25950;
the synthetic file coordinates are different. `defaults.json` records both
original lineage and analysis-artifact identity. No synthetic analysis image
was executed or used as a build input.

## Configuration and lifecycle

`mouse_settings_decode` reads only PRM04e4/04e6 (original DS2068/206a), leaving
other fields opaque. Setup overlay19's e798 passes signed bounds1/999 to
parent16's dd68 numeric handler, then writes those scale words. Startup overlay3
and resident PROGRAM pass them to native mouse initialization. Maintained
admission enforces1..999 before driver mutation, avoiding the baseline's actual
zero-scale divide fault. This is an explicit maintained validation policy;
original whole-image loading does not validate every word.

The lossless host codec exposes `mouse_scale_x` and `mouse_scale_y` but retains
all16-bit values for inspection/repair. Its generic edit operation does not
silently clamp values. Six enable bytes in the owner API accept canonical0/1;
the source defaults retain the original native mappings. Decode rejects wrong
size, null/wrapping extents and source/destination overlap without changing its
output. It performs no file I/O or driver operation.

| Owner state | Admitted behavior |
| --- | --- |
| Closed | Validate/open, or idempotent close. |
| Ready | Poll/read keyboard, suspend for a child, or close. |
| Suspended | Resume after a child or close; keyboard consumption rejects. |
| Quarantined | Retain the allocation and reject input; after repair, close returns the baseline. |

Open captures the driver vector and its reported storage size, allocates a far
buffer with two16-byte guards, and saves the opaque state before the first
reset/init. It also snapshots the native22-byte scale/presence/event block and
six enables. Snapshot rejection before driver mutation frees its allocation;
failures after mutation retain an explicit owner for close.

The driver-storage interface uses INT33 functions15h/16h/17h, also implemented
by [DOSBox-X's mouse handler](https://github.com/joncampbell123/dosbox-x/blob/master/src/ints/mouse.cpp).
The owner treats the saved payload as opaque. It checks guards, exact vector
identity and storage-size agreement before further admitted driver operations.
Unsupported/oversized storage and a far-pointer end crossing64KiB reject. This
depends on a driver honoring its storage API; the guards are not a proof of
arbitrary third-party driver correctness.

Suspend uses the actual native reset/probe and removes the application callback.
Resume uses actual native initialization with the retained settings, clearing
pending event repetitions and baselines as native PROGRAM does. Close restores
the original opaque driver payload and exact native state, then frees its buffer.
A changed vector/size, guard failure, invalid event index/scale or busy callback
retains quarantine rather than calling an unknown driver or advertising release.
After repair, close can reclaim it; resume is not admitted from quarantine.
The callback's owning DOS allocation must remain resident while that owner is held.

Foreground APIs require their own DGROUP, DS=SS and IF1 for driver operations.
That does not restrict the native IRQ callback: the assembly path still supports
the driver's foreign DS and SS. `mouse_owner_key` returns pending with its output
unchanged when no input exists. Otherwise the actual native poll/read path gives
mouse repetitions priority over BIOS input, then resumes BIOS normalization.
The unrelated debug UI gate stays disabled and fails visibly if reached.

## Actual execution and reproduction

```sh
./tools/build test-mouse-keyboard
./tools/build test-mouse-keyboard-source
```

The DOS diagnostic registers an independent prior callback and saves its actual
driver state. Source-owned mouse events run through the native far callback on
a separate SS with foreign DS, then through the actual keyboard consumer. Two
Right events precede a queued BIOS `k`; Enter/Escape use their actual read words,
and empty polls leave the output unchanged. The initial scale decode and invalid
admission checks are real DOS C execution.

Two actual CRT DOS children independently exchange/read back callback ownership,
change cursor/sensitivity and register/retire their own callbacks. The first
returns to working parent input. The second also replaces INT33; resume and close
reject until the diagnostic restores the saved vector. Repaired close matches
all **576 driver-state bytes** reported by this DOSBox-X build and all28 native
bytes. The prior callback is explicitly retired before the diagnostic exits.
The child launcher here is CRT `spawnl`, not a claim that the recovered PROGRAM
controller or ASPECT parent has already incorporated this owner.

The linked replay declares allocator, driver and BIOS boundaries explicitly.
It covers range/extent/overlap rejection, IF/SS admission, missing/unsupported
drivers, allocation failure/wrap, snapshot guards, real native event consumption,
driver/vector/size corruption, failed native init/suspend, reentry and repaired
close. These 76 cases complement actual DOS execution rather than replacing it.
The fresh-source proof reproduces MOUSEKEY and both children without originals,
installed settings, existing objects or REA databases.

The normal keyboard diagnostic remains byte-identical, and a fresh27-product
application proof preserves every executable from the preceding unwind receipt.
Those earlier161 DOS executions are carried by exact executable identity; they
were not rerun for assembly-comment changes. Current mouse-owner execution and
source proof have separate frozen identities.

Remaining work includes startup/live settings UI, event dispatch in actual menus
and terminal/ASPECT, ownership through the recovered PROGRAM/fault paths, fitting
the module into the application's existing code/data segments, original macro/
window/error services, broader BBS workflows, physical input and real DOS kernels.
The original diagnostic here uses its CRT far heap. The subsequent
[CRT-free banked owner](MOUSE_BANK.md) adds a DOS allocation backend, explicit
far-code adapters and an assembly-started parent with real maintained DOS EXEC.
It proves that lifetime without CRT initialization; connecting it to the
interactive terminal and ASPECT remains separate integration work.
The separate live ENiGMA decoder is unchanged.
