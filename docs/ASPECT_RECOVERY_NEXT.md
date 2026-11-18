# ASPECT recovery after the state operands

The complete reconstruction remains governed by [F01–F16](FEATURES.md). Finishing
the non-Host builtin tables does not finish ASPECT: the base VM diagnostic still
explicitly rejects108 of215 original opcode slots. Optional application
profiles add bounded services beyond that base; neither count proves complete
language or application coverage. Host remains the final implementation stage.

The next coherent target is the local screen/cursor command family, through
actual compiled scripts and the admitted parent renderer. These operations
support script menus and status displays and follow the current daily-use
terminal/UI priority. The retained original dispatch inventory confirms:

| Command | Opcode | Original target |
| --- | --- | --- |
| BOX | 0C | overlay17:E6D1 |
| CLEAR | 12 | overlay17:E700 |
| HOME | 57 | resident1F56 |
| LOCATE | 6A | overlay17:E7E5 |
| SCROLL | 9C | overlay17:E847 |
| GETVATTR | 52 | overlay18:EA23 |
| PUTVATTR | 8C | overlay18:EA3C |

The current compiler command maps omit these commands; the runtime dispatch
falls through to explicit unsupported. The mappings identify entry points,
not complete grammar or semantics. The original BOX body has retained REA
evidence `ev_69adaa250b9d1ed0e04e2aef07f121858aeebafa7ead2bbe3ef41940ecb51a68`.
It calls operand readers, rectangle helper6EDC and local-window helper4056.
The private retained assembly is
`analysis/pcplus-overlay-17/functions/0x1e6d1.asm`.

Recovery needs original compiler probes for operand types, optional arguments
and refusals; native handler/dependency evidence; and execution through real
compiler, VM and parent display owners. Clipping, cursor/attribute state,
window/status geometry, owner refusal, UART/parser continuity and cleanup need
explicit checks. Sending ANSI strings to emulate a local command does not
establish the native operation. The current child has156 near-code bytes spare;
new handlers need a measured placement plan that preserves buffers and stacks.

The next two larger families remain required:

- Scripted connection control: DIAL22→resident567E, MDIAL70→5685,
  REDIAL92→568D, HANGUP55→overlay18:E759. Existing foreground modem code is
  insufficient while the child owns the UART. Recover grammar and shared
  helper5695, then implement the ownership transition, cancellation/results,
  directory/accounting behavior and return to script. The retained helper
  evidence is `ev_68a224dfa7a066c6b1d9f93fb2ff91df97d5797d06419cb4176229341e4bc34f`;
  wrapper/body closure remains incomplete.
- Scripted transfer control: GETFILE4F→resident4FF6 and
  SENDFILE9D→resident5157. Native transfer engines and foreground owners exist,
  but script grammar, protocol/path/result behavior, UART handoff, retry/cancel
  and resumption require their own recovery and end-to-end checks.

The retained tables are `analysis/aspect-vm/inventory-02.json` and
`analysis/aspect-vm-runtime/keywords-02/inventory.json`. They remain optional
analysis evidence, never application build inputs. Floating-point execution
and the rest of the original compiler/runtime, UI, emulation and protocol
requirements also remain open. This ordering advances the original scope;
none of these families alone closes F13 or whole-application parity.
