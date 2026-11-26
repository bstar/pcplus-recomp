# ASPECT HITKEY

The opt-in `aspect_hitkey=True` interpreter implements the original bare
read-only integer operand `HITKEY`, selector25. Both source compilers accept it
and reject writable targets, declarations, string use and function-call syntax.
The [native provenance](../reconstruction/aspect_hitkey/provenance.json) binds
the exact eight-byte overlay16 getter atDA1C, its callback/thunk, and the
recovered peek/normalizer dependencies. Original executable comparison remains
a separate optional check; normal application builds read no originals.

HITKEY returns a normalized BIOS **WORD**, without consuming input. For example,
raw1E41 becomes0041,4800 remains4800, and3920 becomes0020. The native normalizer
retains AL0/AL E0/AH E0, special Backspace/Delete and its signed372A comparison.
It is not an availability Boolean, a low-byte-only conversion or the second UI
normalizer. Empty BIOS status returns0000; an occupied raw0000 returns0100.
A nonempty native mouse queue reads its six-entry peek table, not the separate
dequeue table. The maintained parent refuses index≥6 before that unchecked
native lookup. The queued word, count and index remain unchanged.

The standalone interpreter uses its real owned standard/enhanced BIOS status
path followed by the original normalizer. It has no private application mouse
queue. The attached profile uses a matching `--aspect-hitkey` parent and
capability25, with all capability24 terminal-query prerequisites retained.
The recovered getter runs in resident CODE with a small FAR adapter; the
ASPECT_CODE renderer must not near-call resident RET targets.

Parent request30/payload0 captures one complete normalized word and returns
`F000|low-byte`. Request31/payload0 returns `F000|high-byte` from that capture
and retires it. A new keyboard arrival or mouse-word change between responses
cannot tear the result. Both requests authenticate the current PSP, DS, client
descriptor/version/token, MCB and callback, and recheck live admission. High
without pending, overlapping low, invalid payload, corrupt queue index and
returned-UART states refuse. With no queued mouse event, only configured BIOS
modes0/10h are admitted: adding one to an invalidFFh would select a consuming
AH00 read. A valid queued event or cached high half performs no BIOS query and
does not need this mode check. These are maintained admission checks outside
the unchanged native getter. BEGIN/END/prepare/revoke, other body operations
and body-level typed failures retire the pending observation. A mechanical
bridge rejection before entering the body leaves application state untouched;
a repaired high still must pass full current authentication. Normal C callers
return on that failure and do not retry a high half by itself.

The child publishes its word only after both exact tags and post-request
validation succeed. Failure leaves its prior value and destination unchanged.
The pair does not poll transport, invoke a child callback, enter the parser,
draw output or run a child scheduler. HITKEY permits owned field/window/
confirmation contexts because it does not consume their keys; in-flight waits,
PROGRAM and snapshot ownership still refuse. Modal-owner admission has direct
client and linked-parent model coverage. The current GET loop stages WHEN CALL
and executes its script body after field retirement, so the real WHEN test
does not establish script execution inside a live field.

The original `KEYS ON` writes the keyboard-disable word; `KEYS OFF` clears it.
Explicit HITKEY reads still work with automatic key dispatch disabled. Existing
cooperative Escape cancellation can run before an opcode reaches its operand;
this older maintained policy is unchanged. Parent mouse ownership is suspended
for PROGRAM. Reading the retained parent queue is tested independently from
physical mouse production or a child notice owner's separate event queue.

[Validation](validation/aspect-hitkey.json) binds:

- 262544 native getter calls across recovered and preserved-original code,
  including all65536 raw BIOS words in both modes, empty/occupied-zero,
  repeated peeks, new arrivals, six mouse events and exact peek-table addresses.
  Getter8/dependency86 bytes and all231 keyboard-region bytes match.
- Ten original compiler probes:6 accepted,4 rejected, exact host/DOS bytes.
  The full DOS8086 compiler suite passes3256 cases and1693 API checks.
- 139 DOS8086 client cases/1628 checks;401 linked-parent cases and ten linked
  child version handshakes. They cover tag/error precedence, delayed publication,
  ownership, captured-word consistency, authentication and retirement, including
  all254 invalid BIOS mode bytes. Admission,
  BIOS and selected DOS/broker boundaries are explicit models in the CPU test.
- 231 actual DOS VM runs/3198 checks over repeated same-process rounds, including
  signed promotion, globals/locals/parameters/string-register conversion,
  unchanged comparison, six held streams, EXECUTE and WHEN. Eleven checks use
  actual DOSBox standard/enhanced BIOS rings and restore their initial contents;
  the production standalone CLI reads real empty BIOS state. A separate
  feature-disabled bridge rejects with error3 before replacing saved1234.
- Enabled1414-case/35415-check and default-disabled1135-case/27295-check runtime
  suites. Existing capability24 client435-case/2766-check coverage still passes.
- Two full-parent source/GET workflows pass105 checks, reading empty state then
  the retained4800 word twice with native keyboard dispatch disabled, including
  source EXECUTE. Two plain/framed post-GET deferred WHEN callbacks pass96 checks
  and four repeated4800 observations. The invalid input gate that waited for a
  worker before allowing GET to finish remains a documented lifecycle fixture
  counterexample, not an application-failure claim.
- Nested-DOS/held-FILE/Help passes63 checks. A clean1074-source export reproduces
  the parent, interpreter, compiler and overlays and repeats source/GET and Help
  without originals, prior objects or ancestor Git.
- Staged capability25 packaging has45 pair/module/archive controls; preceding
  capability24/23 controls remain39/34. This is contract staging, not release,
  BBS, installation or physical qualification of the new profile.

The full interpreter is SHA256
`a117afc83c16b67664c376632cff1b2743a3f53070df0128026f439a00426f87`.
Near code65316 leaves220 bytes; DGROUP40624, stack8192 and existing buffer/stream
limits are retained. The exact DOS minimum is126320 bytes and page-rounded
minimum126352. Parent DGROUP remains65520. The matching GET-enabled compiler is
`6e978674b1983c92d4c83a486554e66f08471a59db24108a2668ca7b8cf5bdf9`.

The prepared [capability24 connection candidate](ASPECT_TERMINAL_CONNECTION.md)
retains its independent qualification and unchanged installed status. The new
profile still requires committed release/package and BBS/hardware qualification.
FROMDDIR, MONO and six Host table services remain unbound, alongside the broader
compiler/runtime, setup, emulation, transfer and F01–F16 gates. Host stays last.
