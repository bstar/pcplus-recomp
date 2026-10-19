# Automatic source loading in DOS

The production ASPECT interpreter now compiles an explicit `.ASP`, or the ASP
sibling of a missing ASX, using the maintained DOS ASPCOMP beside the running
interpreter. The DOS package contains both executables. For example:

```text
ASPECT HELLO.ASP
```

The terminal's existing script menu and directory-bound launcher accept the
same source extensions, under their existing ASCII8.3 admission policy. `EXECUTE "NEXT.ASP"` also compiles before replacing the current
script. Explicit ASP recompiles even when an old ASX exists; a failed compile
preserves that old file and never executes it.

## Namespace and publication

For a compiled name, the loader tries the current ASX then the bounded PCPLUS
directory. Only DOS missing-file/path results permit fallback; an existing bad
header or an unreadable/directory target does not select different source.
If neither ASX exists, it tries current ASP then the PCPLUS source. Qualified
names keep their own directory. There is no PATH search for scripts or compiler.

The source and compiler are preflighted without consuming source bytes or device
input. The compiler's executable sibling is located through the checked DOS3+
environment trailer, independently of CWD and PCPLUS. The source is its sole
argument; ASPCOMP's default ASX target keeps the native 80-byte source limit inside
DOS's 126-byte command tail. A 79-character qualified source is exercised in DOS. Native OEM/CP437 names
remain valid in the interpreter, including PCPLUS fallback for both source and
existing compiled files; the resource helper's narrower ASCII leaf grammar does
not replace the script namespace. The OEM cases create names through actual DOS
calls and dump generated ASX through an ASCII carrier for exact comparison.

ASPCOMP retains its staged publication and replacement rollback. Captured
compiler stdout/stderr use an exclusively reserved sibling LOG, with parent
handles restored on every tested outcome. Success diagnostics are suppressed;
failed-child diagnostics replay through the interpreter's existing console or
resident rendering path after the child returns. Logs are then removed. The
accepted compiled name is published through the existing capability4 label API.

## CPU, process and session ownership

The interpreter's INT0 handler can nonlocally unwind native VM state. It cannot
be inherited by a compiler whose DS/SS belong to another process. A scoped neutral
handler instead terminates the current compiler PSP with status 12 and touches no
parent data or stack. After P_WAIT returns, the interpreter restores its own
handler even if the child replaced INT0. The caller's original vector is restored
when the interpreter exits. Child PSP and inherited INT23/24 are checked.

An injected compiler explicitly changes DS and faults on DIV. Its setup records
the injected DS and child SS; this is not a debugger register snapshot at the
fault. A second child publishes the arithmetic-boundary ASX, installs its own
INT0 handler and exits directly through DOS. The interpreter restores its proper
VM trap and handles the subsequent actual native IDIV fault. Both return 12 and
preserve the outside caller's PSP/vectors. All injected executable/source hashes
are bound by the offline checker.

Unused CRT far-heap segments are released before nested EXEC; live session state
remains resident. Native EXECUTE still releases the old far strings and FILE
before loading the replacement. The compiler does not reset the interpreter's
numeric/settings banks, directory snapshot, translation policy, receive gate,
UART ring or rendering lease. The new script allocates fresh global strings.

Compilation is synchronous. Escape before EXEC cancels without compiling; Escape
queued during child execution cancels on return, after a valid ASX may already
have been published. It does not asynchronously interrupt compiler work.

## UART flow bracket

The UART IRQ remains installed throughout nested compiler execution. The
maintained IRQ queues XOFF for foreground delivery, so the compiler bracket
proactively sends XOFF, lowers RTS where configured, and waits boundedly for
control/TX completion before EXEC. It does not close/reopen the port or discard
the ring. Resume retires introduced pauses; a high queue retains backpressure
until normal consumption. Rejected nested brackets and foreign BREAK preserve
the existing owner/framing. Active-port admission rejects IF0 before mutation
so a disabled BIOS timer cannot make the foreground drain wait indefinitely.

Combined software/hardware flow previously returned from the software dequeue
without restoring a preloaded hardware pause. The maintained child wrapper now
also restores RTS at the low watermark in that mode. The recovered flat UART
bytes remain unchanged. Independent DOS preload tests cover a full 4096-byte
ring, wrapped sources, translation and7-bit mode on COM1/COM2, nested admission,
foreign BREAK and exact raw handback.

The production serial test has four direct N/S/H/B cases and three pressure
cases. The pressure cases use a declared diagnostic wrapper around the actual
compiler, holding its child process for36 BIOS ticks. An independent peer sends
3200 padding bytes plus END/TRAIL despite pause. Exact control bytes prove the
high-water pause and later low-water resume; END is consumed and TRAIL returns
unchanged to the ASIO parent. This is virtual UART evidence, not a claim that a
physical modem obeys backpressure or that unbounded input can fit the ring.

## Verification and limits

Use the pinned Nix toolchain:

```sh
./tools/build test-aspect-source-compile
./tools/build test-aspect-source-serial-dos test-aspect-compile-flow-dos
```

The 22 offline production cases perform 223 checks over real nested DOS execution,
source precedence, failed old-ASX preservation, qualified/PCPLUS paths, chain
state, compiler absence, device/directory rejection, CPU/vector faults and
cancellation. The 1146-case native-VM regression and 21-case production CLI also
pass. UART CPU and six ordinary DOS backend cases pass separately.

Actual directory-bound source compilation in the unchanged terminal authenticates
to owned loopback Synchronet and ENiGMA, resumes the parent renderer/editor, and
leaves drafts unsaved. LOGON.ASX is absent from the frozen launch inputs and its
DOS-generated bytes match the independent prediction. The passing ENiGMA network
profile uses explicit 30 ms modem buffering. An earlier source-enabled run with
immediate forwarding compiled and authenticated, then failed the existing Home
check. That evidence is retained; this checkpoint does not fix that interaction.

The fresh original-free source proof reproduces 153 normal products. Exact current
hashes, test artifacts and BBS checks are bound in
`docs/validation/aspect-source-compile.json`. The compiler still covers the
maintained host grammar; full native language/recorder/original compiler UI,
other application families, physical machines/modems and untested timing remain
required. No F01–F16 whole-application gate closes here.
