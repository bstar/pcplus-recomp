# ASPECT WHEN native component

`src/aspect/when.asm` recovers 602 native instruction bytes for WHEN/CWHEN registration, slot selection, receive pattern monitoring, action triggering and the resident disconnect/keyboard service. This is a component, not an integrated WHEN implementation in the maintained compiler/application. No existing compiler, runtime or application builder is changed by this work.

## Build and validation

```sh
./tools/dev --command python3 standalone/build_aspect_when.py
./tools/dev --command python3 standalone/check_aspect_when.py
```

The source-only builder produces four flat units and `when.obj` in `build/aspect-when`. The checker links `WHEN.EXE` and runs DOSBox-X with the 8086 CPU setting. Normal build/check inputs contain no original executable, installed configuration, REA database or private directory record.

Validation comprises 23 controlled CPU cases covering all 246 native component instruction addresses, 10,606 actual 8086 DOS assertions, and four source-only CPU compositions with the existing native dispatcher, flow/frame/value stack, operands, literal/string readers, WAITFOR and receive policy. DOS checks cover all three ordinary slots at lengths 1..80, all nonzero byte values, control/caret patterns, case folding, rearm/cancellation, deferred call requests, and all resident service keyboard/disconnect branches. The four compositions execute actual procedure bodies and return/frame handling, while modeling FILE buffering/position, startup/open and platform I/O. The separate DOS diagnostic captures call requests; it does not claim execution of an entire DOS bytecode VM or real UART/renderer.

Optional private comparison:

```sh
./tools/dev --command python3 standalone/check_aspect_when.py \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

The original must hash to `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`. Optional checks compare every component unit, reused pure helper and source composition unit at its original coordinate. Normal `checks.json` and optional `checks-native.json` remain separate.

## Native interfaces and ownership

DS must equal SS; DF must be clear. Near exports:

| Symbol | Native entry | Stack arguments | Return |
|---|---:|---|---|
| `aspect_when_register` | overlay17 E8FC | none | RET |
| `aspect_when_cancel` | overlay17 E8C9 | none | RET |
| `aspect_when_slot` | overlay17 E9DF | none | AX slot, RET |
| `aspect_when_monitor` | resident 534E | translated lead word | RET2 |
| `aspect_when_trigger` | resident 53C2 | slot word | RET2 |
| `aspect_when_service` | resident 4DE9 | none | AX abort indicator, RET |

The owner supplies four contiguous 86-byte `aspect_when_records`, word `aspect_when_active_count`, `aspect_when_disconnect_armed`, `aspect_when_case_sensitive`, shared `aspect_flow_wait_gate`, and keyboard state words named in the source. Ordinary slots are 0..2; internal disconnect slot is 3. Before a new script, native loader behavior resets active count, disconnect armed and the three match cursors, and native startup sets case insensitive. This module does not substitute an invented full-record reset for that lifecycle.

Record offsets relative to each slot:

| Offset | Meaning |
|---:|---|
| 0 | action byte: 32h transmit, C7/C8 call |
| 1..40 | pattern copy |
| 41 | forced NUL |
| 42..81 | transmit copy or DWORD procedure target at42 |
| 82 | forced NUL |
| 83 | unused by inspected handlers |
| 84..85 | current match pointer; zero means inactive |

Imported services preserve the recovered calling conventions. In particular `aspect_string_read` is caller-clean: registration's pushed 40 belongs to the later `erase_move_bytes(dest,src,40)` call and must remain on the stack. Uppercase/caret/copy/send-formatted are caller-clean. Bounded integer consumes upper/lower words (RET4); flow call consumes the DWORD target (RET4). Monitor and trigger consume their single word. Host poll, carrier test and keyboard/UI services are explicit device boundaries.

## Proved grammar and encoding

The authored public corpus `standalone/fixtures/aspect_when_vectors.json` contains 64 original compiler attempts: 36 accepted, 28 rejected. Sources, original compiler output hashes and bytecode are public authored data; installed binaries and oracle outputs remain ignored. Accepted source forms include:

```text
WHEN 0 "READY" TRANSMIT "HELLO^M"
WHEN index pattern CALL worker
WHEN DISCONNECT TRANSMIT "BYE"
WHEN DISCONNECT CALL worker
CWHEN 0
CWHEN DISCONNECT
SET WHENCASE ON
SET WHENCASE OFF
```

WHEN is opcode D6; CWHEN is 1C. Ordinary slot prefix is 01 followed by an integer operand; DISCONNECT prefix is 00. TRANSMIT action is enum32h; CALL action is enum07h followed by C7/C8 plus an absolute DWORD procedure offset. Procedures with local frames use C8. SET WHENCASE is SET9E/subcommand56h with boolean1/0; its shared SET handler is outside this component.

The original compiler accepts numeric slots outside0..2, but native E9DF routes ordinary slots through the bounded integer reader with lower0/upper2. Compilation alone is not runtime acceptance. GOSUB/GOTO/MESSAGE/EXIT actions, CALL WITH parameters and long/float slot operands are rejected in the bounded corpus; no claim of complete language grammar is made.

## Matching and action semantics

Registration reads strings through existing native readers, copies exactly 40 bytes, forces terminators and caret-decodes the pattern in place. Source strings up to80 compile; source81 hits the compiler token cap. The original runtime truncates40 rather than rejecting strings longer40. With default insensitive mode the reader-returned near pattern buffer is uppercased in place; ownership and aliasing matter. Only ASCII letters fold, and high bytes retain identity.

Active slots run in ascending order for each translated lead. A match rearms its cursor, so handlers repeat. Replacement resets partial progress and increments the active count only if previously inactive; cancellation is idempotent. Fallback only retries the first pattern character; it is not KMP and misses ABAAB in ABABAAB. Full matches reset without overlapping consumption. Changing WHENCASE does not rewrite an existing stored pattern.

Empty patterns depend on backing bytes: an empty **zero-backed** pattern fires on a received NUL. The native 40-byte copy includes bytes after the first NUL, and after a NUL match the monitor tests the following byte. A diagnostic initially reused a stale source buffer and correctly failed its zero-backing expectation; the retained failure and corrected explicit zero-backed fixture are under ignored `build/aspect-when/failures`. No blanket empty-pattern behavior is claimed. A caret at the truncation boundary can read beyond the intended pattern; no new safety guarantee is added here.

The monitor takes an already translated byte exactly once. Raw parser continuation bytes bypass this monitor. The special disconnect action is one-shot and is cleared by trigger; ordinary matching remains armed. The service checks the explicit carrier callback and keyboard/UI callbacks. Simulated carrier state is not proof of modem DCD behavior.

## Shared suppression and deferred procedure execution

Original E382 is one physical word shared by flow CF/D0, dispatcher suppression, WHEN CALL and COMGETC display selection. Startup/open establishes E382=1, but compiled main begins with CF, which decrements it to0 before source commands. The composed source `integer value; proc main; comgetc value; endproc` therefore calls the display boundary with A and stores65. Treating post-open suppression1 as permanent would be incorrect.

WHEN CALL increments E382 and immediately uses the actual flow owner to save the bytecode FILE continuation, seek the procedure and optionally establish a frame. It does not synchronously execute the body or nonlocally abort an active WAITFOR. In the independently predicted four-case corpus:

* Main COMGETC reads/displays A and stores65 after its CF.
* A CALL worker during WAITFOR END consumes all AEND, then transmits EVENT followed by main AFTER.
* A worker with an integer local follows native C8/frame setup and95/frame restoration, producing the same EVENTAFTER and restoring the original frame/stack.
* A and B CALL events during the same WAITFOR create nested saved positions. The second body runs before the first, producing SECONDFIRSTAFTER.

All compositions end with depth0, gate0, original frame6800 and VM stack7000. WAITFOR's native4C3C display selection remains independent of E382 after these events. Request-only callback tests cannot establish this procedure behavior; the source compositions execute the actual native dispatcher and flow/frame/return instructions.

## Provenance and remaining work

Native evidence: registration `ev_2655c976f9495aeb77f30f95468db58ba4e652743a7959afa9d3f6e924f9d059`, cancellation `ev_5dbc34cf4b5cb30176730e799279b5f606fdb39b21d9168f3072edb582ead612`, slot `ev_1642a990dd84d27e2feb9f1c652461e9a9061f7b33474f4b6446458030a1dae6`, monitor `ev_ecf427221dda369399a0b942379ff7decf9928213296f2c904836bee01c029e9`, trigger `ev_5b047fe51704da0fc1e29d7595425c9cb5d81b0816ac153008bbedb5eb738035`. The private frozen compiler/full-flow ledgers are `analysis/aspect-when/ledger.json` and `flow-ledger-01.json`. Public corpus provenance records their report/probe hashes. Earlier failed ABI replay is retained privately, rather than silently discarded.

The maintained compiler has not been extended for WHEN, CWHEN or SET WHENCASE by this component. Runtime ownership, startup/reset, native carrier policy, renderer/event recursion, timeout/cancel while calls are pending, error unwinding, frame exhaustion, source-buffer aliasing and production lifecycle require explicit integration and composed tests. Source/component completion does not close the full ASPECT or whole-application reconstruction gate.
