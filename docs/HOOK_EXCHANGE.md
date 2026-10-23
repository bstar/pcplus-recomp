# HOOK register exchange

Native KEY kind2 calls the external helper with a generated command tail:

```text
 PCPLUS <integer-bank packed pointer> <string-bank packed pointer> <PRM packed pointer> 3
```

Each pointer is unsigned decimal of `(segment <<16) | offset`, rather than a
linear address or a value read from that address. The more general original
builder can use other signed16 contexts and a different mode0 argument shape;
this new codec covers the KEY mode1 shape only. Native process-result storage
at DS:D124 remains separate from the codec's validation status.

## Recovered data contract

| Original pointer | Shape | Evidence |
| --- | --- | --- |
| DS:D126 | Ten16-bit ASPECT integer-bank words,20 bytes | Fresh REA `ev_c4dfed9da35890d213145769f511bf4b86f145491e38a9ad0e02828c27f2a1bd` observes index*2+D126. |
| DS:D13A | Ten81-byte ASPECT string-bank slots,810 bytes | Fresh REA `ev_05db164d5a5d051f96140f6dff4a7378cea3995ed79134200ab57ba22cbc6455` observes index*81+D13A. |
| DS:1B84 | Original1,264-byte PRM image | Existing PRM format recovery and native414C pointer construction. |

The overlay2 initializer advances the integer pointer from D126 to D13A by2
and the string pointer by81 per iteration, setting each word and first string
byte to zero. This establishes ten slots. Retained Evidence
`ev_1a8ebd32e68e9c0e4af323aa3f4804802726fe74c5042b463243fe7c9917212d`
and the trampoline manifest map resident C1D7 to that initializer. Resident4B1F
calls C1D7 before interpreting a script. Thus persistence/handback must account
for per-invocation initialization; the banks are not arbitrary transport structs.
The maintained interpreter already has matching10-word and10x81-byte banks.

Fresh analysis used the existing derived overlay16 analysis image, SHA256
`e14871502dba5f55646eb6184cf488c216381e6eda2ca47227a06934592b8302`, whose
source target is2.01 SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Complete REA Evidence remains in ignored `analysis/hook-registers-16.rea.json`.
This is static derived-image inspection; that synthetic image was never executed.

## Source-owned component

`src/process/hook_exchange.c` supplies a pure bounded KEY-tail formatter/parser,
far-span geometry checks, and pack/unpack of a maintained staging layout:
20 raw integer bytes,810 string bytes, then1,264 opaque PRM bytes. This contiguous
2,094-byte layout is an authored internal staging choice, not a recovered file
format or a claim that native helpers require contiguous buffers.

Formatting retains the leading space, uppercase PCPLUS marker, pointer order
and signed context. Its largest tail is47 bytes plus NUL. Decimal conversion
uses bounded doubling so a far code bank needs no near CRT long-division call.
The parser consumes an explicit byte count, bounds numeric values to32 bits and
context to signed16, and never dereferences parsed pointers. Its strict spacing,
marker and bounds are maintained validation; it is not a recovered helper parser.

Geometry checking rejects offset+extent overflow,20-bit physical wrap and mutual
physical overlap, including differently spelled segment aliases. This proves
geometry only. It does not establish PSP ownership, conventional-memory
admission, or permission to read foreign memory.

Pack/unpack require disjoint bounded near regions and a NUL within each81-byte
string slot. All integer/PRM bits and opaque bytes after string terminators are
preserved. Invalid input leaves destination bytes unchanged. PRM bytes are
opaque: this component neither validates their settings nor applies them to UART,
UI, files or the terminal's active state.

## Validation

Run `./tools/build test-hook-exchange`. A four-source empty-tree build produces
an actual8086 DOS diagnostic in HOOK_CODE, with8KiB stack.325 checks exercise
formatter/parser bounds, all32 pointer bits, signed endpoints, malformed tails,
physical aliases, CP437/80-character strings, every malformed slot, source/output
overlap and atomic publication. Seven near-segment wrap checks run specifically
in DOS; the host supplies count placeholders for that DOS-only geometry.

Host and DOS output match exactly. Their2,094-byte frame and command-tail files
match independent Python fixtures. A second fresh compilation/link reproduces
the DOS executable. OMF import inspection finds only `_small_code_`, with no near
CRT calls from HOOK_CODE. The first warning-as-error attempts caught compressed
statement indentation and always-true32-bit comparisons; both were corrected
before the accepted run.

Separate explicit optional checks replay the genuine original KEY instructions
at declared resolver/EXEC/UI recording boundaries. All297 existing cases pass.
Five additional cases compare this new codec directly against original414C
command construction for contexts3,0,-1,32767,-32768. No helper process is
spawned. The new host codec is compiled before the original is opened; originals
are never normal build inputs. These comparisons are available through
`standalone/compare_hook_exchange_native.py --original --output build/...` in
`./tools/dev --command python3`.

The [independent receipt](validation/hook-exchange.json) preserves the selected
raw outputs, sources, compiler object/imports, native comparisons and static
Evidence under ignored build storage. Public Git contains source and receipts,
with no original executable or generated analysis database.

## Integration remaining

KEY kind2 is still unsupported in the running terminal. This component does not
close HOOK, F05, F09 or the whole application gate. The next work must:

1. Add an owned far-memory exchange allocation and bounded EXEC admission at the
   foreground safe point, preserving the existing serial/output/interrupt owner.
2. Define register-bank lifetime and child handback across ASPECT invocations,
   normal return, missing/malformed helpers, abort and retained ownership.
3. Construct an accurate active PRM image, including directory/session overrides.
   The saved setup-owner image alone does not establish current runtime settings.
4. Stage and validate returned PRM changes before applying supported settings;
   unresolved fields and native helper semantics must remain explicit.
5. Exercise real DOS helpers that read/mutate each bank, error/cancel paths,
   screen/serial continuation and current ENiGMA/Synchronet sessions.

The terminal's tight near-code/DGROUP budgets still require far-bank placement.
Real DOS kernels, physical modem/mouse/audio and the complete application remain
separate acceptance requirements.
