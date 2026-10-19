# ASPECT character, line and quiet-line input

This is the receive-command checkpoint. The later
[input-policy integration](ASPECT_INPUT_POLICY.md) adds native mapping and
parent XLT/seven-bit inheritance; its validation record binds the newer products.

The receive increment adds COMGETC, COMGETCD, RGET and WAITQUIET to the
source-built interpreter, plus COMDATA and FOREVER integer operands. These
advance the scripting and serial application work; the full application and
all F01–F16 acceptance gates remain open.

## Native component

`src/aspect/receive_commands.asm` contains 435 exact bytes across nine units:
the two character-command wrappers and shared integer destination/store,
line input, quiet-line input, display selector, seconds sampler, DOS time
helper, delayed character helper and two integer builtins. The nine ranges
and 51 supporting ranges total 4,094 bytes and match the pinned original.
The independent component suite covers 696 paired CPU scenarios, all 188
instructions, and 14,500 assertions in actual 8086 DOS. Device, seconds,
cancellation and wait services remain declared component boundaries; direct
native DOS time and BIOS-delay tests are separate from those models.

COMGETC stores an immediately available byte, or FFFF when empty, in an
integer destination. COMGETCD uses the same destination/store with a delayed
read. The native helper waits for 36 observed changes of the BIOS clock's low
word, not a signed timestamp difference. Its late-arrival ordering can return
FFFF with a byte left queued on the final transition. The production platform
adapter services flow control and Escape while waiting; it is distinct from
the exact native busy loop exercised in the component diagnostic.

RGET writes a string, replacing a terminating CR with NUL. Its optional maximum
is 0–80 and defaults to 80; its optional counter is 0–32767 and defaults to 30.
It decrements the counter when the sampled DOS seconds value changes. It does
not subtract elapsed seconds, so skipped seconds and minute rollover retain
that native behavior. A zero counter skips input and reports failure. CR,
maximum length and native cancellation report success; maintained Escape
cancellation additionally unwinds with its explicit runtime error.

Native RGET checks the limit pointer rather than checking whether maximum is
zero. A zero maximum can therefore still consume input and overflow a string.
That defect is retained in the bounded native diagnostic. The maintained owner
stops with operand error7 before an 81st non-CR byte can be stored outside its
81-byte string storage. This is an intentional difference, not a claim that
arbitrary bytecode or all native pointer arithmetic is safe.

WAITQUIET defaults to 15 quiet intervals and a total of 30 intervals. Each
iteration waits, then either decrements quiet time or drains queued input and
resets quiet time. It reports success only when the quiet counter reaches zero.
The original inner drain does not poll cancellation; the maintained raw receive
adapter checks cancellation per byte so continuous input cannot starve Escape.
RGET and WAITQUIET use the recovered SUCCESS/FAILURE state, independently of
the earlier WAITFOR result builtin.

FOREVER depends on its grammar position. The ordinary integer builtin22 returns
one. RGET's options and WAITQUIET's first option use that integer operand.
WAITQUIET's second option, like WAITFOR's timeout, accepts the distinct special
FOREVER encoding1A, which disables the total deadline. Compiler fixtures
explicitly distinguish these cases rather than treating the spelling as one
universal value. COMDATA builtin20 returns the current receive count.

## Platform services and remaining gaps

Successful original script opening increments E382 after resetting E37E to
one, but the compiled main procedure's CF immediately decrements E382 to zero.
COMGETC/CD therefore display in the normal main-procedure state. E382 is the
same physical word used by flow and receive suppression; treating the opening
value as a permanent default was incorrect. The maintained runtime now aliases
those owners. [Native WHEN compositions](ASPECT_WHEN.md) execute the actual
dispatcher and main CF and independently verify that COMGETC displays A and
stores65. Native direct reads through4C3C, used by RGET/WAITQUIET and WAITFOR,
have a separate display selector.

An admitted connected child now routes mapped lead bytes through the
[actual parent renderer](ASPECT_RENDERER.md). Parser continuation reads remain
raw and bypass translation and WAITFOR matching. Standalone raw diagnostics
explicitly disable display because they have no renderer service; they do not
establish the native application's display default. [Native WHEN monitoring
and deferred calls](ASPECT_WHEN_RUNTIME.md) now run before display on translated
leads; parser continuations bypass both monitors.
E2F8 is a pattern/event-monitor count, not a file-capture flag. Native startup
uses explicit identity-table initialization and configured loading/masking;
serialized zero bytes are not evidence of an active zero translation table.
The parent translation policy is inherited. Broader terminal, event and UI
services remain application work.

The existing UART lease, ASIO unread-byte handback and serviced return-key
prompt are reused. COMGETCD's cooperative wait and every receive call keep
flow control and cancellation active. No new original executable, private
profile or REA database is required by ordinary builds.

## Test layout and use

```
./tools/build test-aspect-receive-commands test-aspect-compiler
./tools/dev --command python3 standalone/check_aspect_runtime.py
```

The optional `test-aspect-receive-commands-compat` target compares the native
component to the locally supplied pinned original. Source compilation uses
`src/aspect/compiler.py`; execution uses ASPECT.EXE with the existing Script
menu or explicit UART option described in [serial scripting](ASPECT_SERIAL.md).

The composed diagnostic loads source-generated `CASES.DAT` beside EXECUTE.EXE.
The ACV1 record file holds authored expected values and modeled device inputs;
it is not part of the production interpreter. This replaces unrolled generated
C calls that exceeded the DOS near-code limit when the full receive corpus was
added. All source-compiled fixtures and the unsupported-slot checks remain in
the suite. Its manifest binds the data-file identity and schema.

The [frozen checkpoint report](validation/aspect-receive.json) distinguishes
component proof, modeled composed
execution and independent actual DOS/UART tests. Compiler-only unsafe original
zero-limit cases and unrelated unsupported FOUND behavior remain identified;
no broader native service, full compiler or physical-modem claim follows from
these tests.
