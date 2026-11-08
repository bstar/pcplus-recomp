# GET native abort checkpoint

The maintained near checkpoint in `src/aspect/get_checkpoint.asm` runs the
recovered GET owner synchronously on its ordinary DS=SS stack. It rejects nested
entry, unequal DS/SS, disabled IF and set DF before entering native code. A
same-stack native abort restores SP, DS, ES and the C-preserved registers and
returns `GET_NATIVE_ABORTED` to the caller. IF/DF return to the admitted entry
state. The abandoned operand, editor or conversion frames never resume. Saved
stack coordinates are cleared on return; no destination pointer is stored in the
checkpoint. The typed runtime error belongs to its existing runtime owner.

This is an authored lifetime adapter, not recovered original bytes. With the
future `ASPECT_GET_VM` flag, the existing external abort gate delegates to GET
when no PROGRAM checkpoint is active. GET in turn delegates unmatched/inactive
or foreign-SS aborts to ALARM or the recovered dispatcher. That route remains
disabled in application builds; it is not evidence of full interpreter cleanup.

The caller must retire its display/keyboard/WHEN owners after a caught abort,
then propagate the original native abort. This checkpoint alone grants no right
to clear live deferred frames or free a typed destination. Direct dispatcher
longjmp, CPU faults, foreign-stack policy and recursive cleanup faults are not
caught by this implementation. Actual field/receive/RPC and lifetime composition
remains the next integration step.

## Evidence

[The receipt](validation/aspect-get-checkpoint.json) binds these component tests:

- All142 frozen original-observation cases pass with the actual recovered GET
  owner, typed readers, far string copy/flush, integer CRT and serviced field.
  The diagnostic now enters the real assembly checkpoint instead of host-style
  `setjmp`/`longjmp` at the error/cancel boundary. Floating service remains an
  opaque model, and UI/confirmation decisions remain authored inputs.
- Twelve additional authored faults cover three stages—inside the active field,
  after field acceptance before typed conversion, and inside confirmation—each
  with ordinary/borrowed DS and enabled/disabled IF at the abort site. The integer
  destination stays unchanged, including when accepted scratch already says42.
  A subsequent GET succeeds in the same process after every fault.
- C-preserved registers are seeded and checked around each native call. Entry
  guards, rejected nesting and delegation on an inactive checkpoint are checked.
  While GET is active, a small interrupt-disabled diagnostic foreign stack proves
  foreign-SS delegation without retiring the real owner's checkpoint. The final
  dispatcher boundary is a returning test stub, not the actual VM longjmp.
- A16-input isolated public-source export reproduces the exact8086 diagnostic
  and complete report without originals, private data, prior objects or ancestor
  Git. The field model executes in a separate code segment.
- With this checkpoint disabled, the owner diagnostic remains byte-identical to
  the earlier reviewed142-case diagnostic. The full reviewed ASPECT child also
  rebuilds byte-identically with GET disabled.

The original outcomes still distinguish cancellation paths: confirmed Escape
skips writeback; declined or KEYS-disabled Escape can convert retained scratch
and write numeric destinations. The checkpoint does not introduce a blanket
cancel rollback policy. The fault test also explicitly observes the field model
remaining ACTIVE after its frame was abandoned; releasing that resource is work
for the pending owner adapter, not an automatic effect of restoring SP.

```sh
./tools/dev --command python standalone/build_aspect_get_owner.py \
  --checkpoint --output build/my-get-checkpoint
./tools/dev --command python standalone/prove_aspect_get_owner.py \
  --build build/my-get-checkpoint --output build/my-get-checkpoint-source
```

GET remains refused by both maintained compilers and opcode49. No package,
deployment selection, physical files, live serial/BBS or SIP service changed.
