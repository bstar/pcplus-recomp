# ASPECT value stack and nonlocal error composition

The recovered interpreter dispatcher now runs together with the real native
abort and setjmp/longjmp instructions in a source-built8086 DOS diagnostic.
A native value-stack overflow reaches the abort path and resumes the saved
interpreter context before any rejected push writes data. This advances actual
cross-module execution; file, UI, opcode and resource callbacks remain diagnostic
substitutes, and the maintained terminal still cannot execute ASPECT scripts.

## Build and checks

```sh
./tools/build aspect-stack aspect-unwind
./tools/build test-aspect-stack test-aspect-unwind
# Explicit optional private original comparisons:
./tools/build test-aspect-stack-compat test-aspect-unwind-compat
```

| Output | SHA256 | Evidence |
| --- | --- | --- |
| `build/aspect-stack/STACK.EXE` |35afb60eb6ac3381ace5cd7b67810579ec945d7d4e23eb92707baa86f8326993 |786 CPU scenarios;2,286 actual8086 DOS assertions |
| `build/aspect-unwind/UNWIND.EXE` |df2113e8d4d89448c4e1427e1923a1a84ae91b1c8ffd27b37be3497b37234456 |72 actual8086 DOS cases;1,968 assertions |

`standalone/record_aspect_execution.py` reconciles current source hashes,
source-only/native reports and retained REA observations into
`validation/aspect-execution.json`. Optional original comparisons match197 stack
bytes plus72 reused copy bytes, and all618 native bytes in the linked unwind
composition. The latter is an exact byte comparison; it does not run the
original application. All original inputs remain private and optional.

Both diagnostics join a69-output fresh source rebuild without original
executables, install, REA databases or previous build outputs. The current
interactive terminal binary remains731418bd…; its runtime code has not changed.
The new tests therefore do not require repeating the unchanged80-command
terminal regression, and do not claim new live-terminal behavior.

## Typed value stack

`src/aspect/value_stack.asm` recovers197 contiguous bytes at original overlay16
D0D0..D194, source file109184..109380 inclusive. Its seven entries reserve space,
push word/DWORD/eight bytes/81-byte string, and pop word/DWORD. Eight-byte and
string pushes call the already recovered72-byte native memory-copy routine at
85B4, which executes directly in both CPU and linked DOS checks. Overlapping
copy fixtures exercise actual native direction handling and its DF=0 result.

The ABI is near DS=SS. Reserve and pushes consume their arguments with RET2 or
RET4; pops return normally. BP/SI/DI are preserved. ES and general scratch
registers/flags are volatile. This is a byte stack: eight bytes are copied
without claiming floating evaluation, and81 bytes are copied without validation
of string contents.

CPU scenarios cover selected capacity boundaries, integer values, overlap,
randomized valid operations,16-bit arithmetic/pointer wrapping and unchecked pop
underflow. Native memory is mapped for those isolated observations; DOS unsafe
edge cases use explicit fixture padding. The optional native comparison repeats
all786 scenarios with original bytes. These tests preserve and expose native
limitations rather than establish a safe standalone stack API.

Native reservation adds the request to the current16-bit pointer, ignores carry,
and compares against arena+3ACAh without a lower-bound check. A wrapped result
can pass. Pops never check underflow. Error105 is invoked when the upper test
fails; if the error callback returns, the push continues. The stack-only
component deliberately separates stop-at-error and returning-error models.
Production ownership, validated bounds and complete error policy remain open.

## Actual nonlocal unwind

`src/aspect/abort.asm` adds the exact63 bytes at resident4EBC..4EFA. It optionally
passes the current32-bit script position to format/display callbacks, sets exit
state FFFF, then calls native9065 longjmp with the dispatcher's context. Its
position-format string and display/file services are source-owned diagnostic
substitutes; original error text/resources are not included.

The composition links the actual224-byte dispatcher,63-byte abort,29-byte
setjmp,33-byte longjmp,197-byte stack and72-byte memory copy. The10-byte native
context stores BP/DI/SI/SP/return-IP. It requires DS=SS and the same live CS;
it does not save segment registers or support returning to an expired frame.
No callback simulates longjmp by setting the instruction pointer or resetting
the stack in this diagnostic: the recovered instructions perform the transfer.

The72 cases combine nine scenarios with two owners, direct/chained scripts,
and position display off/on. They include normal completion, faults originating
in modeled open/service/read/handler/error/invalid-command/wait callbacks, and
a real native reserve overflow. Nested frames deliberately poison SI/DI before
calling abort. Assertions verify stack/register restoration, context guards,
absence of return/fallthrough after abort, correct script argument on restart,
and exactly-once cleanup/close/final callbacks.

For native overflow, a valid first push is exercised in the chained case. The
failing push requests two bytes with only one left. The reserve routine invokes
the declared error105 adapter, which calls the real abort routine through nested
frames. The context restores correctly and the destination and boundary canary
remain unchanged. This proves the composition through that adapter; the complete
native4EFB error UI and production resource cleanup are not implemented by it.

The display branch passes position00012345h through DX:AX and the caller's
format arguments, verifying the upper word. It does not establish real file
positioning or arbitrary format/UI correctness. The lifecycle callbacks count
calls against owned fixtures; they do not close actual ASX files or free real
loader resources.

## Provenance and next work

Abort static assembly evidence:
`ev_e3343dc7c28d2af17088266c32b0b0e42810f994bf180056d7668b977ae6e3ec`.
All seven value-stack retained assembly Evidence IDs and input hashes are in the
frozen report. Static observations are distinguished from the linked execution
above; existing setjmp/longjmp provenance remains in
`reconstruction/transfer_session/provenance.json`.

Next work must connect real DWORD file reads/seeks, call/frame/return handlers,
expression operands and a checked resource owner. The recovered native globals
still retain freed pointers and have no count cap; the recovered value stack
still has unchecked arithmetic/pop semantics. Full compiler grammar/passes,
VM commands, recorder, floating runtime, application invocation and physical
hardware validation remain open. No F01–F16 whole-application gate closes here.

The following [file/control composition](ASPECT_FILE_FLOW.md) connects native
readers and calls/frames/returns to actual maintained DOS stdio, including
positions beyond64KiB and real abort on short operands/failed positions. It
extends the source rebuild to71 outputs while leaving complete script execution
and ownership open.
