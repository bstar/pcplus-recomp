# WHEN compiler conformance

The maintained host compiler emits recovered WHEN, CWHEN and SET WHENCASE records. This is compiler integration only: the production runner/application does not gain WHEN runtime wiring from this change. The separate native component and its renderer/carrier/lifecycle boundaries are documented in `ASPECT_WHEN.md`.

Supported forms are `WHEN integer string TRANSMIT string`, `WHEN integer string CALL procedure`, the corresponding `WHEN DISCONNECT` actions without a pattern, `CWHEN integer`, `CWHEN DISCONNECT`, and `SET WHENCASE ON/OFF`. Operands are atomic and typed; numeric expressions or parentheses around a slot, CALL arguments/parameterized handlers, and other action commands are rejected. Optional commas after operands follow the bounded original grammar. Numeric slot values outside0..2 remain compiler-permissive, matching original emission; the native bounded reader rejects them during execution. The source compiler does not disguise a literal3 as the special DISCONNECT prefix.

WHEN CALL emits enum07h and C7/C8 with the same absolute DWORD target fixups as ordinary procedures. It emits no ordinary CALL D0 prefix: native WHEN triggering owns the shared gate increment. C8 is selected when the handler declares local storage. String literals use the existing physical-line/position-keyed codec; forty-byte native pattern/action truncation is a runtime property, so the compiler preserves accepted literals up to80 bytes.

The original corpus exposed unused-procedure lowering. Bounded compiler probes establish these distinct cases: a zero-reference worker and the third procedure it alone calls are dropped; an unreachable mutually recursive pair remains; a removed first-declared procedure still leaves the initial jump to MAIN; malformed unused bodies are still rejected. The maintained compiler validates all bodies and then repeatedly removes zero-inbound-reference procedures with MAIN protected, retaining declaration order and the initial-jump rule. This preserves the observed cycle behavior rather than applying general main-rooted reachability elimination. These examples constrain this compiler increment; they do not claim recovery of every original optimizer rule.

`standalone/fixtures/aspect_when_vectors.json` remains unchanged from its component checkpoint: 64 original compiler attempts,36 accepted28 rejected. The separate follow-up `aspect_when_compiler_vectors.json` preserves all nine new attempts: four accepted/five rejected, with authored source/ASX hashes and original probe/report provenance. Existing earlier fixture corpora are unchanged.

Run compiler checks with the pinned Nix shell:

```sh
./tools/dev --command python3 standalone/test_aspect_compiler.py
./tools/dev --command python3 standalone/test_aspect_when_compiler.py
```

The isolated WHEN suite checks all40 accepted original outcomes byte-for-byte, all33 original rejections,40 renamed/case/whitespace variants, ten independently authored invalid sources and a newly generated framed handler target above64KiB. It reads no original executable or private oracle report.

To compose compiled source with the exact source-built native components:

```sh
./tools/dev --command python3 standalone/build_aspect_when.py
./tools/dev --command python3 standalone/test_aspect_when_compiler.py --native
```

The native option checks main CF/COMGETC display, deferred plain/framed WHEN calls during WAITFOR, and two pending calls executing SECONDFIRSTAFTER. These use the actual native dispatcher, flow/frame/stack/operand/literal/receive instructions with explicit FILE/startup/platform callbacks. They do not execute or rebuild the production parent/runner, provide hardware carrier evidence, or establish full renderer/event/error integration.

The public evidence record is [validation/aspect-when-compiler.json](validation/aspect-when-compiler.json). The optional `make test-aspect-when-compiler` target builds only the native WHEN component and runs the isolated compiler suite with its four source-native compositions; it does not rebuild the application binaries.
