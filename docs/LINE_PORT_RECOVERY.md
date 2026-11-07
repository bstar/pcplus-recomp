# Original Alt-P Line/Port recovery

The optional [live Alt-P candidate](LINE_PORT_LIVE.md) now composes these components
and passes the named application gates. The installed/default release is unchanged;
this document retains the separate component checkpoint and its limits.

The native 2.01 key selector is now recovered as assembly and independently
builds without the original executable. It is a component checkpoint: the default
terminal still opens the general saved-settings editor for Alt-P. This work
changes neither that behavior nor the installed RBADE091 package.

## Native evidence

The authentic PCPLUS.EXE SHA-256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Its Alt-P keyboard-table entry reaches resident `134C`, then the overlay-loader
stub at `B9DF`, selecting overlay 20 entry `EFDE`. REA analyzed the existing
synthetic overlay 20 container (SHA-256
`6bf3e7502a80735ba544174a7b19fb291288d908b826ce3e90ba25977cd03a64`).
That analysis container was never executed. The recovered selector independently
matches all 414 bytes at original file offset 127292 (`F05C..F1FA`), SHA-256
`bf5ee58e858643a8d3076b2f4a9d30c49f75055e00ed561f457e666d9170551b`.

Retained REA observations:

| Routine | Evidence | Observed static behavior |
| --- | --- | --- |
| Popup EFDE | `ev_fa051b50c21b78d453b383b0aed32c34dacdaac5468804f8c93c2ea749f26519` | Saves window, draws popup, reads keys, refreshes fields. Escape applies session settings and restores window. Alt-S takes the save path before applying/restoring. |
| Selector F05C | `ev_394c7be3e6e48c412d327c081c2588fb78c243c68f1ec47359b8a96b56c5c89b` | Updates five adjacent words and invokes bell or port-quiesce boundaries. |
| Selector assembly | `ev_c0d69340f77c15c75b08ec130b186bfc7478b2f47d575591fedb5914b1c152ca` | 135 instructions; maintained instruction assembly reproduces every byte. |
| Refresh F1FA | `ev_e18dd84a91a8b94683044f3192fc0d0e3c1ba01a95dc76211fa78896ff0effd9` | Displays baud selection, N/O/E/M/S parity, bits, stops and one-based port. Baud-label pointers resolve to 300 through 115200 in the original data. |
| Save F260 | `ev_629b21d05031dec974bf7ce423600c150ebd02a169f4e50ec4f121c0245483b0` | Opens a file and writes the ten-byte settings prefix, then closes. The default filename is PCPLUS.PRM; a later data read resolves it. Does not visibly check write/close results. |
| Apply 03A7 | `ev_019df849b434c3f7bf7437778876466852b4c08741eb8ea7a1f5d4c97e282850` | Calls serial helpers and updates port state; full hardware semantics remain untraced. |
| Quiesce ADBA | `ev_cf4c84bd7f5642c585597129585d3f7a5d72a35cf9e948836f74e1d895ec6738` | Calls ADD6, masks an I/O register with7F and clears two I/O registers; exact register identities are not yet established. |

The five words are port, baud index, parity, stop bits and data bits, at native
DS offsets1B84..1B8C. The independently authored test oracle covers:

| Keys | Selector effect |
| --- | --- |
| 1 through 9 | Baud index 0 through 8 |
| N/O/E/M/S, either case | Parity 0/1/2/3/4; other fields unchanged |
| Alt-1 / Alt-2 | One / two stop bits |
| Alt-7 / Alt-8 | Seven / eight data bits |
| Alt-E | 7E1 |
| Alt-N | 8N1 |
| F1 through F8 | Invoke old-port quiesce, then select zero-based port 0 through 7 |
| All other 16-bit keys | Bell once, no settings mutation |

Even reselecting the current port invokes quiesce before writing its index.
Escape and Alt-S are handled by the popup wrapper; passing either directly to
this selector correctly produces the invalid-key bell. Do not copy generic
editor cancellation semantics into the native popup.

## Build and checks

```sh
./tools/dev --command python standalone/build_line_port.py
./tools/dev --command python standalone/check_line_port.py
./tools/dev --command python standalone/test_line_port_dos.py
./tools/dev --command python standalone/prove_line_port_source.py
```

The final command requires a fresh `build/line-port/source-proof` destination.
The explicit analyst-only `reconstruction/line_port/recover.py` reads an ignored
original and analysis manifest to regenerate assembly/provenance; it is never
an ordinary build dependency. Flat builds use original addresses; OMF builds
use explicit DGROUP-relative external data references and linker-owned services.

Accepted checks, bound by [the receipt](validation/line-port-recovery.json):

- All 65536 keys from two distinct initial states, including sentinel values,
  in both flat and actual linked OMF bodies:262144 cases. Checks include all
  five words, callback ordering with pre-mutation state, cdecl stack cleanup,
  DS=SS and preserved BP/BX/SI/DI/ES. Bell/quiesce are declared boundaries;
  linked callbacks execute the authored recording bodies.
- Actual DOSBox-X 8086 execution of the source-built EXE: 40 targeted vectors.
  A 128-byte pad precedes data within DGROUP to exercise external data fixups.
  All UARTs are disabled; no settings file is opened.
- An isolated export of six declared public files reproduces both flat bytes
  and EXE exactly and repeats all 40 DOS vectors. No original, analysis database,
  earlier object, private configuration or Git metadata is in the export. The
  outer pinned Nix environment supplies the compiler/linker/emulator.

The initial diagnostic caught invalid NASM EQU framing and an out-of-range
8086 LOOP in authored host code; the initial exhaustive oracle required a guard
for Python byte membership above 255. Those harness issues were corrected before
these accepted runs. No product behavior was changed to make tests pass.

## Remaining integration work

The [popup view checkpoint](LINE_PORT_VIEW.md) now corroborates default-color
80x25 rendering and Escape/session persistence against the authentic executable.
The [staged transaction and serial plan](LINE_PORT_SESSION.md) now combine
this selector and view in a separate code bank. The optional live candidate
now composes the maintained saved-screen, foreground, serviced-input and UART
owners; native apply-helper recovery and full hardware parity remain separate. Original
COM1..8 choices exceed the maintained COM1..4 scope; unsupported ports need
explicit handling rather than silent remapping. Trace application of baud,
parity, bits, stops and IRQ to hardware before claiming native serial parity.

No physical observation follows from the static analysis, CPU model or DOS
emulator results. The exact released parent/interpreter/compiler and pending
SynthModem/LoC physical acceptance remain separate. Full F01–F16 parity remains
open.
