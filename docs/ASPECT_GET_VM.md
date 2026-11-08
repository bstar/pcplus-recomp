# Full interpreter GET checkpoint

The opt-in `get_vm=True` process build links ordinary opcode49 GET into the
actual source-built ASPECT interpreter. It calls the recovered GET owner through
maintained typed readers, the serviced editor, capability22 parent metadata,
WHEN confirmation and the native checkpoint/dispatcher error path. This is a
full interpreter composition, beyond the earlier controlled-owner diagnostics.
Default compilers still refuse GET. The optional
[GET compiler profile](ASPECT_GET_COMPILER.md) now passes five actual compiled
scripts through this interpreter and the larger parent. Raw-mode tests still
insert authored GET bytes at a unique PAUSE0 boundary; the malformed EOF case
always uses authored bytes.
The default application, selected package and installed machine are unchanged.
[Storage tests](ASPECT_GET_STORAGE.md) add seven local/parameter/S0 cases with
exact writeback, frame guards and normal procedure return. F13 remains open.

## Code and data ownership

The resident dispatcher enters `GET_VM_CODE` through explicit near-cdecl/far
bridges. Every callback returns to resident CS before calling resident code;
abort and ALARM bridges also switch CS before native near stack recovery.
DS=SS remains intact. Pure editor functions retain explicit far calls in
`GET_FIELD_CODE`; the206-byte field owner precedes DGROUP in FAR_DATA. A missing
pre-operand anchor refuses instead of creating a replacement lease late.
Copies within the bank use bounded local loops rather than near CRT calls.

The linker orders CODE, FARCODE, FAR_DATA, BEGDATA, DATA, BSS and STACK and
turns off code packing. BEGDATA ordering is essential: omitting it placed the
initialized null region after the stack and inflated the loaded image. The
builder now checks all public bridge, implementation and callback segments,
abort targets, field storage, CRT ordering and the unchanged8192-byte stack.
The current audited layout is62751 resident code bytes (2785 spare),4079 GET code bytes,
1544 pure editor bytes and43712 DGROUP bytes. The aligned MZ page minimum including PSP is
136128 bytes; environment/EXEC overhead and dynamic memory are additional.
The [MZ layout checkpoint](ASPECT_MZ_LAYOUT.md) corrects the earlier file-length
accounting and records the separate startup failure.

`near_globals=True` is a separate opt-in allocator experiment.81-byte global
strings first receive stable far pointers into ordinary near heap blocks with
an ownership cookie. This avoids allocating an early DOS far block and eagerly
materializing every deferred numeric group for one string. Near allocation
failure retains the previous numeric-prepare/far-allocation fallback. Cleanup
checks the cookie before `_nfree`; other allocations retain `_ffree`. No string,
variable, file-buffer or stack limit is reduced. Near-exhaustion/far-fallback
acceptance remains open.

Only ordinary mode0 string, integer and long GET are admitted. Float requests
explicitly return4; missing operands return5. Positioned/sibling modes have no
admitted grammar. The string-filter binding is an identity tag for the maintained
editor, not recovered original resident3F9C filter behavior. Normal field
retirement already adopts the parent cursor; the final owner repeat validates
the position instead of applying the viewport origin twice.

## Execution and limits

[The original checkpoint receipt](validation/aspect-get-vm.json) remains historical.
[The owned read-window receipt](validation/aspect-get-owned-window.json) binds
the current build and corrects the earlier stream-failure classification.
The full DOS parent/child matrix covers string input, integer input, long input,
confirmed cancellation, floating refusal and truncated operands. BIOS keys are
injected only after actual field admission. A passive DOS observer records child
exit and parent file/history ownership; return keys are conditioned on actual
EXEC completion and terminal restoration. The initial space dismisses the
ordinary startup splash. Tests verify exact edited values on the serial wire,
post-GET cursor reports, resumed terminal keys, clean hangup and typed errors.
The modem is an owned synthetic serial peer, not SynthModem or a live BBS.

The paired parent preserves the installed recipe's complete feature set and
adds capability22 field support. It does not include the separately reviewed,
unpromoted keymap-editor addition. DOSBox uses386/UMB for the observer and640KB
conventional memory. This is not8086 parent/child capacity acceptance.
Standalone full-interpreter DOS8086 tests cover healthy execution,128 strings,
80-character values, mixed integer/long/string/file ownership, divide recovery,
unattached GET refusal and missing-file errors.

The larger keymap candidate now passes the six attached cases after the
[qualified compiler executor](ASPECT_COMPILER_EXEC.md) removes duplicate runtime
code. Full memory/feature co-residency remains a separate gate. The installed-profile pair now passes the real
FOPEN→GET sequence, retaining its stream and exact `BEFORE|LoC42` bytes. The
[owned read-window change](ASPECT_READ_WINDOW.md) removes duplicate ASX stdio
buffering while retaining the native256-byte window and full512-byte buffers
for each script stream. It is enabled only in the opt-in GET build.

The preceding report incorrectly called runtime7 a heap error. It is an operand
error raised by the later FPUTS after FOPEN failed. A passive exit probe now
shows that the first failure was the512-byte script-buffer allocation: no
backend open attempt occurred, and subsequent lookup raised native error4.
With duplicate buffering removed, the backend open count is1, the stream
retires normally, and native/runtime errors are0. The old failed reports stay
historical; neither errno alone nor the old error label establishes a cause.

Pending work includes full variable/stream/help co-residency admission,
broader repeated/EXECUTE/error coverage beyond the two
[lifetime scenarios](ASPECT_GET_LIFETIME.md), broader WHEN/error coverage beyond the
[plain/framed action cases](ASPECT_GET_WHEN.md) and
[divide/cancel cases](ASPECT_GET_WHEN_ERRORS.md), optional
width/masking/origin policies in the full VM, floating support, broader compiler
coverage, package admission and connected physical acceptance. Existing
component tests retain their narrower scope. No physical FTP, card, SIP, modem
or BBS operation is part of this checkpoint.

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD --output build/FRESH
./tools/dev --command python standalone/test_get_vm_cli.py \
  --child build/GET_CHILD --output build/FRESH_CLI
./tools/dev --command python standalone/prove_get_vm_source.py \
  --parent build/PARENT --child build/GET_CHILD \
  --checks build/FRESH/checks.json --output build/FRESH_SOURCE
```
