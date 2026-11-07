# ASPECT EMULATE recovery and compiler

Both maintained compilers now emit the original `EMULATE` instruction for all
33 original terminal names. The exact native command owner is recovered as a
separate component. **The interpreter does not execute this opcode yet.** This
checkpoint expands compiler fidelity without changing the installed connection
package or claiming support for 33 runtime emulations.

```text
proc main
emulate ansi
endproc
```

The bytecode is `2F <one-byte selector>`. Names are case insensitive. Numeric,
variable, string, parenthesized and compound operands reject, as do extra
operands and commas. The compiler also rejects local declarations that reuse
any of these reserved terminal names. Comments after a valid operand compile.

| Selectors | Names in selector order |
| --- | --- |
| 0–7 | TTY, VT52, VT100, VT102, VT220, VT320, ANSI, IBMPC |
| 8–15 | WYSE75, ATT605, ATT4410, TV922, H19, IBM3101, IBM3161, DGD100 |
| 16–23 | DGD200, DGD210, ADDS60, ADDS90, ADM3, ADM5, ADM31, ESPRIT3 |
| 24–32 | IBM3270, TV910, TV912, TV920, TV925, TV950, TV955, WYSE50, WYSE100 |

## Original owner and boundaries

REA identifies overlay18 E6F1..E700 as the 15-byte command owner. It calls the
resident byte reader at4CB4, writes the returned word to selector DS1D18, and
calls the full terminal reset at20A4 with caller-cleaned argument1. It performs
no selector bounds check and has no local rollback path. The reader normally
zero extends a byte; the compiler supplies only selectors0–32.

The maintained assembly reproduces all15 original bytes exactly, SHA-256
`e6d7360b2eaabb705a1e28786e80cd5d3c4e5729e5eb7e27e1387087e30536d2`.
The reset implementation already has separate recovered source under
`reconstruction/terminal_reset/`; recognizing that dependency does not bind it
to the script child or establish connected-session adoption.

REA handler dossier:
`ev_a09dd96f2669f8f35eb275cbfa9595e312e172ae161d1fa52515da514dc20702`;
assembly view:
`ev_80cbf47cb2f8e5ad7bac90445c4b9121c98b1b2191e93711d1b012138564fffb`.
The byte-reader and reset dossiers are
`ev_5e47dae02f6a6e2c1391b8172278de2615c75fce4d865361bcce1b130b4124cc`
and `ev_7076d99808f1047c371aa4d6071423b46e4437aca0ff5c5de911835dfe5a478d`.
The private export is `analysis/aspect-emulate-native-20261107.rea.json`.
The synthetic overlay was analyzed only, never executed. Normal builds consume
maintained source, not originals or analysis databases.

## Verification

The [receipt](validation/aspect-emulate.json) binds sources and results:

- The original DOS compiler supplies98 authored outcomes:36 accepted and62
  rejected. They cover all33 named selectors, reserved local names and malformed
  arguments. Both maintained compilers match those outcomes and98 presentation
  variants, including exact accepted ASX bytes. Rejected DOS compilations retain
  existing output and leave no publication temporary files.
- The complete DOS compiler regression passes2,323 cases and1,693 API checks.
  The checked-stack run passes2,341 cases, including18 CLI cases, with a16KiB API
  stack and24KiB CLI stack. A deliberate overflow control verifies the guard.
- A clean25-public-file export rebuilds compiler `ac58a8a1` exactly and repeats
  all196 compiler cases without originals, prior objects, private files or Git
  ancestry. It does not repeat the complete corpus or checked-stack suite.
- The exact native owner passes768 CPU cases: all256 byte selectors with normal
  return, a stopped reader and a stopped reset. These verify write-before-reset
  order, argument/stack handling, callee-saved registers and adjacent state. The
  reader and reset are modeled callbacks; stopped callbacks do not prove native
  fault recovery or actual rendering. A separate optional pass compares the
 15 source-built bytes directly with the verified original range.

```sh
./tools/dev --command python standalone/build_aspect_compiler_dos.py
./tools/dev --command python standalone/test_aspect_emulate_compiler.py \
  --compiler-dir build/aspect-compiler-dos --output build/my-emulate-compiler
./tools/dev --command python standalone/check_aspect_emulate.py \
  --output build/my-emulate-native
```

The subsequent [parent transaction](ASPECT_EMULATE_PARENT.md) executes keyboard
staging/reset in linked tests. Its initial memory failure is resolved by the
[later funding proof](ASPECT_EMULATE_FUNDING.md). The child request and opcode
remain unbound.

## Runtime integration still needed

The parent owns emulation, parser/reset state and keyboard behavior. The script
child cannot implement a profile change by updating its own selector alone.
Recover and bind the supported-profile admission and parent/child handoff;
coordinate the child's rendering state and native reset, including full screen
clear, cursor, attributes, tab stops and keyboard selection. Preserve ownership
when a WHEN action or modal operation is active and distinguish deliberate
safety policy from native behavior.

Then test ANSI↔VT220 transitions under receive traffic, unsupported selectors,
reset failures, subsequent script invocations, parent return and keyboard
sequences. Repeat capacity, modern BBS and source/package gates before selecting
an integrated product. Other named emulations require their own recovered
implementations and fixtures. Installed release R59A85A8 still contains compiler
`c26199a3`, parent `689bdce9` and interpreter `b4f0aecc`; this compiler/component
checkpoint is not deployed. Physical acceptance and the full F01–F16 inventory
remain open.
