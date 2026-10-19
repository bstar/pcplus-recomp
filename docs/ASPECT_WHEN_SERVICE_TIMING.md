# Native WHEN service and receive-queue timing

This independent investigation constrains production integration. It does not establish that the maintained application has completed WHEN support. No compiler/runtime/application builder was edited for this investigation.

Fifteen controlled original-native cases pass across1,166 distinct instruction addresses. Owned original compiler probes add five service/dispatcher sources and one COMGETC/COMDATA source. The original executable SHA256 is `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`; the compiler SHA256 is `5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`. Private source/evidence hashes and scope are frozen in `analysis/aspect-when/service-timing-ledger-01.json`. Original files and generated oracle output remain excluded from public builds/Git.

## Where disconnect actions run

Native4E34 clears the last-key word CFFA and calls native4DE9 at4E3A. Native4DE9 performs host/carrier bookkeeping0DDE, checks disconnect armed E2FA, reads the carrier flag through AA5C, and invokes53C2 with slot3 when carrier is absent. Thus4E34 is a script service poll, not merely a keyboard predicate.

| Active operation | Native service timing established here |
|---|---|
| Dispatcher | 4DE9 before fetching the next opcode |
| WAITFOR | 4E34 at52B6 after its receive burst and timeout/match checks; a completed match or expired timeout can exit before this poll |
| RGET | 4E34 at5113 before each receive/time iteration |
| Raw dequeue AA65 | No script-service call: dequeue/mask/count/flow-control operations |
| TRANSMIT48CC | No direct4E34/4DE9 call; local echo, send-byte and delay services are separate dependencies |
| Native6B72/6B98 delays | Busy calibrated/tick waits; no script-service calls in those recovered bodies |
| Inspected AB0B flow-block paths | Generic3F4B keyboard Escape poll, not script4E34 |

The original WAITFOR/RGET dynamic cases start with no queued input, drop the controlled carrier at an actual4E34 entry, then inject END or A/CR after the service poll. The actual53C2/C7 flow owner schedules the handler inside the active wait. The wait completes its input first, then dispatcher runs EVENT followed by main AFTER. This is EVENTAFTER in both cases, with depth/gate/stack restored. It is neither an immediate synchronous handler body nor deferral of all disconnect detection until the next opcode.

An independent TRANSMIT case drops the controlled carrier at the first send-byte boundary while transmitting SEND. It finishes all four bytes; the next dispatcher service detects the drop and runs EVENT before AFTER. The observed sequence is SENDEVENTAFTER. This proves the bounded positive unblocked sender path with local echo disabled. It does not prove that every indirect renderer/menu/interrupt or exceptional blocked-hardware path can never introduce additional work.

AA5C reads the hardware modem-status DCD bit. The replay supplies controlled carrier values, not actual modem hardware. Host poll0DDE updates carrier cache3974, status UI and optional overlay4 E2A9 connection-accounting work; its inspected body has no direct53C2 call. That accounting path is distinct from the explicit armed-disconnect check in4DE9. No exhaustive negative claim about every application callback is made.

## Actual receive count and prefetched opcode

Original8E20 is the real queued receive count. Original E2F8 is simultaneously the ordinary WHEN active count and dispatcher seek-enabled predicate; those names describe one shared word, not independent state. It is also the dispatcher's paused/pending-input word, not a separate Boolean. At4B59, after fetching the opcode into SI:

1. With queued input, opcode belowC7, and shared E382=0, dispatcher enters the receive-drain path.
2. If ordinary WHEN active count E2F8 is nonzero, it first seeks the script FILE back one byte, to the fetched opcode's start.
3. It consumes queued leads through4C3C/4C74 until8E20 reaches zero, allowing the actual monitor to change FILE position and call/frame state.
4. With ordinary slots still active, it returns to the dispatch loop and fetches from the resulting FILE position. Without ordinary slots it executes the previously fetched SI opcode without rewinding it.

The controlled original QUEUED source has WHEN A CALL worker followed by TRANSMIT AFTER. Input A arrives immediately before the low-opcode gate. Dispatcher rewinds to BF at offset16; the handler call saves16, seeks worker26 and later returns16. The opcode is fetched again and AFTER executes: EVENTAFTER. With nonmatching XY, the same rewind/re-fetch produces AFTER. Two prequeued events A/B save positions30 then40 and run the second and first handlers before main continuation: SECONDFIRSTAFTER.

The same real-count alias changes full-script COMDATA observations. These are original full-dispatcher traces, not component-only RGET expectations:

| Authored source/input | Native command result | Following numeric assignments |
|---|---|---|
| RG0: RGET global buffer; HELLO/CR/TAIL | buffer HELLO, queued tail4 immediately after RGET | failure0, success1, COMDATA0 |
| RG1: RGET global buffer1; AB/CR | buffer A, queued tail2 immediately after RGET | failure0, success1, COMDATA0 |
| RGGLOB: buffer=OLD before RGET buffer5/timeout1; prequeued NEW/CR | NEW/CR drains before initial AC assignment, RGET then has no input | with advancing DOS seconds, empty buffer, failure1, success0, COMDATA0 |
| GCLEFT: COMGETC value; then remaining=COMDATA; queued AB | value65, queued B immediately after COMGETC | remaining0 |

The next assignment opcode5B is belowC7, so dispatcher drains those remaining bytes before evaluating COMDATA. Its destination selector8D is an operand within that record, not the opcode tested at the dispatch gate. Consecutive C9 COMGETC opcodes are above the threshold and can still consume consecutive queued bytes normally.

The RGGLOB full-dispatcher trace uses controlled DOS seconds0,1,2. With a frozen diagnostic seconds value and no queued input after the initial drain, this source cannot reach its timeout; that is a fixture-clock configuration issue, not evidence of a production-clock failure.

The existing public receive corpus preserves command/component expectations4 and2. A composed runtime must distinguish those outcomes from the full dispatcher observations0 and0 rather than changing or disguising the earlier component evidence. No public receive fixtures were edited here.

## Keyboard/UI contract

Native4DE9 resets pending-key word397A toFFFF. With keyboard enabled (E380=0), it checks651A and reads a ready key through64FE into CFFA. A non-Escape key enters the full terminal dispatcher1604. The ordinary ASCII path194E optionally echoes through0610 and sends the character through AB0B at1966. The actual native ASCII path is executed in the new replay: A transmits41. Function-key tables, line editing and modal commands are broader terminal UI services; these are not equivalent to discarding ordinary keys.

Escape calls4E6B, which snapshots a UI rectangle via3FC7, prints the prompt, runs yes/no6DDE with defaultNo, and restores the rectangle through4015. Enter retains the default; Escape/N declines; Y confirms. A confirmed answer calls4EBC, which sets E378=FFFF and nonlocally restores the saved dispatcher context via9065. This is an abort/longjmp contract, not an ordinary returning callback. The existing `src/aspect/abort.asm` owns this recovered abort body.

If Escape is declined,4DE9 returns zero but CFFA remains1B;4E34 still returns1 because it tests that last key. Therefore the current WAITFOR/RGET can end while the script itself continues. The new controlled replay selects the explicit modal-No boundary and proves this path; it does not execute an entire original modal UI or confirmed nonlocal abort.

With keyboard disabled (E380 nonzero),4DE9 skips terminal key handling.4E34 peeks through651A, normalizes the key with77D2, returns1 for Escape without consuming it, and consumes/discards a non-Escape ready key. Five replay cases cover enabled ordinary ASCII, declined Escape, disabled ordinary consumption, disabled Escape preservation, and no key.

## Integration boundaries and reproducibility

A backend cooperative UART/flow/ESC check must not silently become native4E34 everywhere. The inspected maintained platform callbacks also poll cancellation in raw dequeue, parser continuation, TX and delays, where the bounded original bodies do not call script service. Connecting WHEN to all those calls would introduce additional detection points and possible FILE/frame changes during raw parser continuation. The integration should distinguish actual native4E34 imports from low-level cooperative transport cancellation, while retaining whatever safety policy is explicitly chosen for the maintained child.

The maintained `when_runtime.c` foreground owner deliberately retains immediate Escape cancellation instead of the original modal confirmation/decline behavior. Other terminal UI keys stop with typed unsupported status rather than pretending to execute1604 menus or transmit them. Deferred renderer/raw callback scopes also postpone native service until a safe VM stack is active. These are explicit maintained platform/safety policies; exact recovered WHEN machine code does not establish full original UI or reentry fidelity. The owner separates low-level transport cancellation from the native4E34 import, avoiding accidental disconnect dispatch at every raw/TX/parser safepoint. Full integration verification remains the owner's separate gate.

Initial composed diagnostic timeouts are retained privately by the integration owner. One earlier receive wall-clock timeout is preserved under `build/aspect-runtime/receive-wallclock-timeout-01` with a hashed reason ledger. The current RGGLOB frozen-clock issue was identified before its explicit runtime-only clock/expectation override; the canonical component fixture stays unchanged. The public `standalone/fixtures/aspect_receive_runtime_overrides.json` records that separation. This investigation directly traces RG0, RG1, RGGLOB and the new GCLEFT source; it does not label every other derived override as a separately executed original probe.

Replay FILE/open/global allocation, raw UART/TX, carrier/key hardware, renderer0610 capture, modal-No and DOS seconds are modeled. All new traces use DS:8800 CPU stack, disjoint from original CFFA. An initial keyboard attempt inherited a D000 stack that collided with CFFA during a native push; its failure/source are retained, and all original14 cases were repeated with the corrected stack. An initial missing-register import failure is also retained. Neither was a product failure.

Primary retained native evidence: WAITFOR `ev_54ab2f40f6d6628581b4d811b2b7e426d136da6d39c7cc9c78a53597699792d5`, RGET `ev_82b85e5c2064a515b7e01d43f9c5f052c6b05ee214947c95c1d0f3fb96a651b8`, host poll `ev_57d88c51754ddc8de7e4b604519e330dff1f8a88d9e986b68e516ee86b7a944d`, modal wrapper `ev_a394eb82c8850f72011e2f9477f3c165b2241bc9f89906aafd237c0a7cc25842`, terminal dispatcher `ev_b21291abf4490cc6ecbcbe1f8b3a97938d5a9915fa4cc5c5213f0ec2a523534e`.4E34..4E6B is additionally bound by exact file coordinates and byte hash in the private ledger. No REA active session was opened during this timing follow-up.

Remaining gates include real DCD transitions, full keyboard/modal/renderer reentry, parser continuation behavior, pending-call cancellation/abort cleanup, selected record/accounting work and production UART lifetime. These native observations do not close the full application gate.

## Frozen probe and report identities

| Private authored artifact | SHA256 |
|---|---|
| `compiler-06/report.json` | `edcdf13c8dc20831eee853af92d80685f40d2bf49ee7357b628abc1b86b5d526` |
| `compiler-07/report.json` | `9a758ef0ffc564b3baa99f5e6d7463ae5304ae39157cf6fd4a3ebaa674cc65d1` |
| `service-probe.py` | `6d2ffe25f20710cacf61b7ce940eb3d8af0dc622782dbfd94b68deb0bd5e69b9` |
| `comdata-probe.py` | `40864e80bd9b3e0ad45318dbc684b32fdac7c4e8153ba2f6bd9582308fe453cf` |
| `service-replay-01.json` | `66ad0327223abfa077a56c8590c5a4a9c0e8d8327fe63742a15a073d3253c5cd` |
| `queue-accounting-replay-01.json` | `364959c98768f3ff4bbcc418c4fa5664d82475a7558a03042c9163b0a54db6fa` |
| `keyboard-replay-01.json` | `fc35b2b7b7e3d525ad213efbbcdfafc40ae011278523b68d079de988cde1f2f9` |
| `global-initializer-replay-01.json` | `47effa1182cd55eea9e1b381a56f1729b8b27e3ab19d31e55683d681c6662815` |
