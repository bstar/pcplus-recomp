# Full interpreter GET checkpoint

The opt-in `get_vm=True` process build links ordinary opcode49 GET into the
actual source-built ASPECT interpreter. It calls the recovered GET owner through
maintained typed readers, the serviced editor, capability22 parent metadata,
WHEN confirmation and the native checkpoint/dispatcher error path. This is a
full interpreter composition, beyond the earlier controlled-owner diagnostics.
Both maintained compilers still refuse GET. Tests insert explicitly authored
GET bytes at a unique, linear PAUSE0 instruction; this is not compiler support.
The default application, selected package and installed machine are unchanged.
F13 remains open.

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
The audited layout is65389 resident code bytes (147 spare),4079 GET code bytes,
1544 pure editor bytes and44096 DGROUP bytes. The MZ minimum including PSP is
139152 bytes; this is not the total dynamic-memory requirement.

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

[The validation receipt](validation/aspect-get-vm.json) binds current evidence.
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

Two capacity failures remain explicit. The larger keymap candidate cannot start
this GET child normally with the passive observer present. The installed-profile
pair can edit fields, but opening an additional real owned stream before GET
returns heap error7/ENOMEM5 before field admission. Reducing heap growth from512
to128 bytes does not cure it. Neither failure is a successful scratch-lifetime or
application-capacity result. The attempted FOPEN→GET test remains available as
`--stream-probe`; successful standalone file operations do not close that gate.

Pending work includes full attached-memory admission, shared FOPEN→GET scratch
lifetime, repeated/EXECUTE GET, actual native WHEN action composition, optional
width/masking/origin policies in the full VM, floating support, both compiler
frontends, package admission and connected physical acceptance. Existing
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
