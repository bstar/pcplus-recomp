# GET foreground confirmation and final abort

The experimental command API now joins the native GET checkpoint, editor and
context to foreground confirmation and final recovered abort/longjmp. It remains
a diagnostic integration, with application GET/opcode49 and compiler support
disabled. Full interpreter cleanup guards are still required before enabling it.

GET asks for confirmation after retiring its field and keyboard lease. The new
WHEN entry admits that ordinary foreground state without pretending it is an
ordinary WHEN service callback. It binds confirmation ownership to the native
GET generation, then runs the actual recovered yes/no instructions through the
existing parent confirmation client. Declining leaves FAILURE and retained-text
conversion to the recovered owner. Confirming sets the typed cancellation cause
and reaches the native abort checkpoint before typed writeback.

A restored checkpoint can retire an abandoned GET prompt, then discard its
abandoned monitor/deferred/service records. A live scope or different generation
cannot authorize that cleanup. Reset/file-reset/finish refuse to erase a retained
GET confirmation. Failed close or client validation preserves ownership for
retry, and the original runtime error retains priority. Context policy cannot be
changed while the prompt is owned.

The child client also reserves confirmation ownership before BEGIN crosses to
the parent, quarantines failed post-checks, and blocks nested requests/callbacks
while a confirmation request is in flight. A trusted rejected BEGIN clears the
reservation. Ordinary capability20 behavior remains unchanged.

`runtime_get_command_run(wrap)` supplies checked policy and returns typed status
after normal execution or recovered cleanup. `recover` retries retained GET
scopes; callers must separately check `ready`. Readiness excludes a live native
checkpoint, field or uncommitted value, confirmation, window or PROGRAM owner.
The dispatcher-facing `execute` jumps to recovered `aspect_abort_recovered` only
when ready. Otherwise it returns with the error sticky, leaving ownership intact.
Retry after cleanup propagates that error without executing GET a second time.
The caller must supply an actual native dispatcher environment for `execute`.

## Evidence and diagnostic corrections

[The receipt](validation/aspect-get-command.json) binds DOS8086/FPU-off results:

- Actual recovered GET, typed readers/integer CRT, native field ABI, editor,
  WHEN/client, yes/no, final abort and ten-byte setjmp/longjmp execute. Of142
  frozen cases,137 match original observations; one clips to the captured
  24-row view and four refuse protected spans. Native-error mapping and float
  conversion remain explicit modeled/opaque boundaries.
- Three added faults enter the actual prompt: a native service abort cleans up
  automatically; a refused close retains the prompt; a failed post-BEGIN check
  retains possible ownership. The latter two block reset/finish and new command
  execution until repaired cleanup. All then reach native longjmp with the
  destination unchanged and without rereading operands or consuming another
  field key. Generation checks prove no second GET execution.
- A45-source isolated rebuild reproduces the exact executable and full report
  without originals, private data, prior objects or ancestor Git.
- 307 actual DOS client checks include confirmation reservation, post-check
  quarantine, nested request/callback refusal and retirement after modeled serial return.
  Its ten-source rebuild reproduces the exact client executable/report.
- The independent editor suite still passes759 checks and its20-source rebuild.
  The GET-disabled full reviewed ASPECT interpreter and the earlier36-case
  wire-tested UART diagnostic remain byte-identical. No new wire acceptance is
  claimed by those comparisons.

The initial dispatcher test adapter added a return frame beyond the original
10-byte environment; longjmp resumed at the wrong continuation. The corrected
adapter tail-calls native setjmp with the caller-supplied context argument. An
initial register test also demanded checkpoint-specific BX/ES preservation from
an ordinary C command wrapper; those registers are volatile at that boundary.
BP/SI/DI, stack return and DS=SS remain checked. A fault injection initially ran
in field polling; it was corrected to trigger only in the confirmation scope.
Failed diagnostics are not accepted evidence. The cold client builder also now
creates its absent build parent directory.

The parent display/authentication, BIOS keys, serial and native WHEN action
bodies are controlled peers. This is not the complete native dispatcher or its
FILE/global/frame cleanup. Original abort and longjmp are real, while the test
owns a standalone native environment. Parent pixels/parser, child handoff,
real UART/BBS, application memory/package and physical acceptance remain open.

**Do not enable opcode49 yet.** Full `runtime_cleanup`/`runtime_finish` paths must
honor retained command ownership before freeing script strings/files/frames.
Also required: full interpreter linkage and budget, real parent policy/scratch
backend lifetime, parent parser/receive and actual WHEN actions, FLOAT.RTE,
both compiler grammars, raw console support, connected scripts and hardware.
No installed files, selected package, card, FTP, modem, SIP or live BBS changed.

```sh
./tools/dev --command python standalone/build_aspect_get_owner.py \
  --checkpoint --serviced --context --command --output build/my-get-command
./tools/dev --command python standalone/prove_aspect_get_owner.py \
  --build build/my-get-command --output build/my-get-command-source
./tools/dev --command python standalone/prove_get_runtime.py --client \
  --build build/my-field-client --output build/my-field-client-source
```
