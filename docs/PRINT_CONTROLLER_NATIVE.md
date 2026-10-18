# Native dedicated-print controller

`reconstruction/print_controller/controller.asm` reauthors the entire native
PCPlus2.01 overlay12:D0D0..D26F body:416 exact bytes, flat SHA256
`c8e18c7c00f75067a2838d14af665b1ec8c1ba40a218cd949e41697ab250e17e`.
The original verified EXE SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`;
this overlay region starts at original file offset89472. Retained REA assembly
is `analysis/pcplus-overlay-anchored-12/functions/0x1d0d0.asm`, Evidence
`ev_e54a45172d907f37b39b7223686bad0d0a773def52c44fa869371b05450501dc`.
`provenance.json` retains addresses, hashes, symbolic state and service boundaries.
No new REA session was needed. The explicit analyst-only `recover.py` uses the
verified original; normal builds/checks read source and stored hashes only.

This is the native controller reached by **unprefixed CSI5i**. Private CSI?5i
instead opens continuous printer copying through1A76. The new controller is a
standalone diagnostic; it does not resolve the live application's D0D0 boundary.
It reuses existing recovered36FC byte/flush instructions, excluded from the416
new-byte count. CRT, UART, keyboard, cursor and UI dependencies remain explicit
memory fixtures, not substitute live implementations.

## ABI and state ownership

`print_controller_original()` is near, no arguments, preserving BP/SI/DI and
restoring SP. AX/BX/CX/DX/ES/flags are scratch. DS=SS and ordinary8086 small-model
callee conventions apply. The routine reserves304 stack bytes; its local escape
buffer has no checked input limit. Original state addresses are symbolic in OMF
mode (`-DPRINT_CONTROLLER_OMF`) and fixed in exact flat mode.

| State | Role |
| --- | --- |
|1D18|Terminal profile ID; ID1Fh(31 decimal) treats received14h as exit|
|8FE8|DEC-family capability; parser recognizes digits,`[`, final`i`|
|9004|Other-family capability; parser recognizes lowercase`a` exit|
|8E20|Actual native queued receive count; diagnostic owns a finite queue fixture|
|8FF0|Shared near FILE pointer overwritten by this invocation|
|7A72,7A82|Arguments to cursor/display save and restore helpers|
|333E|Cursor-shape argument restored at exit|
|1D50,7500,2B6C|Reauthored short resources`PRN`, `wb`, `DEDICATED PRINT`|

The three short resources were checked in SHA-verified initialized original DS;
no original/private data blob is distributed. Profile initialization separately
sets8FE8=1 for IDs2..11, including live ANSI6/VT2204, and9004=1 for IDs22..30.
See exact reset module and STARTUP_CONFIGURATION.md. These are runtime
capabilities, not direct private PRM values to copy blindly.

| Dependency | Original address | Argument/cleanup |
| --- | --- | --- |
|Hide cursor|6E5A|No arguments|
|Save/restore display/cursor state|765C/7682|Three words; **callee RET6**|
|Status|3226|One word, caller cleanup2|
|Open|841A|Filename,mode; caller cleanup4|
|Keyboard available/read|6530/64FE|No arguments|
|Break action|0401|No arguments|
|Transmit ordinary key|AB0B|One word; **callee RET2**|
|Dequeue/wait escape byte|AA65/5CA0|No arguments|
|Printer byte|36FC|One word, caller cleanup2; actual reused putc/flush wrapper|
|Restore cursor shape|2F78|One word, caller cleanup2|
|Close|8318|One word, caller cleanup2|

The diagnostic does not claim full internal semantics of765C/7682,6530 or0401.
Its fixtures verify invocation/cleanup; the native caller's service use is proved.

## Exact loop and termination grammar

Entry hides the cursor, invokes765C, displays its status and opensPRN in`wb`,
storing the unchecked result at8FF0. It polls keyboard before each outer RX
iteration. Two consecutive **keyboard** words001Bh exit; the first is sent
throughAB0B. Other keyboard words are sent too, including high-word011Bh; exact
3000h additionally invokes0401. Received bytes between the two Escape keys do
not reset the previous-key variable. Keyboard Escape is not serviced inside
5CA0's escape-reading loop by this body; any such service belongs to that callee.

Outside a buffered escape, dequeued0000h and007Fh are discarded. All other
received values pass to36FC, except ESC begins buffering. Received14h exits
without output for profile1Fh. For every other profile it calls36FC twice,
once atD160 and again by falling throughD23D;28 source/original cases preserve
this observed double-print bug, not an intended maintained policy.

With8FE8 nonzero, `ESC [ 4 i` exits without printing the terminator. The native
parser tracks *whether any digit4 was seen*, rather than parsing a numeric
parameter: `ESC[14i` and `ESC[4;5i` also exit. Other decimal digits and semicolons
are accumulated/ignored while looking for a terminal character. `ESC[5i` and
`ESC[0i` with`[` present are discarded and return to the outer loop. A final`i`
without the`[` marker keeps waiting. `ESC X` exits only when profileID=1.
`ESC a` exits only when9004 is nonzero; the actual lowercase byte is61h,
**not backslash5Ch** (the chained subtract constants total61h).

Unknown terminal bytes replay the entire buffered sequence through36FC and
reset the two parser flags. A nested ESC does not restart parsing. In the
corroborated case `ESC4iX ESC[4i`, `X` is a recognized-but-inapplicable profile1
candidate and keeps waiting; the secondESC is unknown and replays the accumulated
buffer, leaving following`[4i` as ordinary bytes. Thus the apparent final
terminator does not terminate this malformed sequence; the fixture exits with
two keyboard Escapes. `checks.json` retains matching source/original branch
traces (`saw4`, `saw[`, `replay_buffer`, `reset_flags`, `exit`) for this case.
Initial simpler expectations were corrected from these actual instruction
paths, not by dropping the composed-sequence regression.

Buffered NUL/DEL are ignored. A5CA0 returnFFFFh is not an EOF check: native
code stores/replays its low byteFFh as an unknown terminator. A diagnostic
fixture explicitly returningFFFF corroborates that behavior; this does not
assert that every real5CA0 invocation returns that sentinel. An empty UART and
empty keyboard queue leaves the native outer loop running; a10000-instruction
characterization verifies no close/restore/return occurs. There is no local
idle timeout, carrier/quit admission, overflow accounting or bounded cancellation
policy in this controller body.

Exit restores cursor shape and display/cursor state, closes8FF0 and returns.
Open failure leaves a nullFILE passed to printer/close boundaries; native code
ignores putc, flush and close errors. Previous8FF0 ownership is overwritten.
The diagnostic proves these calls and results are ignored; it does not invoke
an actual CRT with null/stale pointers or claim that doing so is safe.

## Verification and remaining work

```
./tools/dev --command python3 standalone/build_print_controller.py
./tools/dev --command python3 standalone/check_print_controller.py
./tools/dev --command python3 standalone/test_print_controller_dos.py
# Optional analyst-only instruction comparison:
./tools/dev --command python3 standalone/check_print_controller.py --original
```

`PRINTCTL.EXE` uses Watcom8086/small model with8192-byte stack. Its near-C
`print_controller_dos_test()` calls the actual native controller on synthetic
`A ESC[4i`, checks the single captured byte/close/restore, returns0 and prints
`PRINTCTL PASS`. Actual DOSBox-X `cputype=8086` passed all six independent runner
checks, including exit0/hash stability/no unexpected files; retained results
are under `build/print-controller-dos/`. The public summary is recorded by
`./tools/dev --command python3 standalone/record_print_controller.py` in
`docs/validation/print-controller-native.json` (the recorder verifies current
artifact hashes before publishing). This is a smaller subset than the CPU
matrix, which covers28 linked plus28 opt-in original instruction comparisons,
including all256 dequeued byte values, profile-specific grammar, key handoff,
null-open/ignored errors, pendingRX on exit, stack/BP/SI/DI/DS=SS and nonreturn.

The416-byte native body is completely reauthored and flat-verified. That does
not mean all reachable callee bodies or all native states have been recovered
or every instruction branch was covered. Escape-buffer overflow, unbounded
native wait behavior under real hardware, UI-help side effects, physical
printer failure and arbitrary nested application operations are not exercised
as safe functionality. A live maintained owner still needs checked exclusive
FILE ownership, explicit bounded grammar, hardware servicing/cancellation and
error propagation before replacing its honest D0D0 unsupported boundary. No
original application, analysis executable, private configuration, physical
printer or media was executed or modified.
