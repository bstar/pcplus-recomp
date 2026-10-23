# Terminal-linked helper transaction

The optional `--hook-execute` product links the existing DOS exchange owner,
live session projection, accepted register snapshot and returned-PRM validator
into one transaction. It directly executes a source-built helper, validates its
return and retires the allocation before publishing a private proposal. It
does not adopt registers/settings or enable interactive KEY kind2 routing.

## Lifetime and boundaries

`terminal_hook_execute(path, context, result)` is a far cdecl entry. The near
path64 and result20 must be disjoint and nonwrapping; path text is 1–63 bytes
without CR/LF and context is signed16. DS=SS must identify the actual terminal
group, with IF=1 and DF=0. The caller must already quiesce UART/IRQ, mouse,
screen, input and file owners, and set complete retained process bounds.
The entry does not itself acquire those external owners.

An idle transaction projects the current session over the retained baseline
without reading a PRM file, then snapshots all 830 accepted register bytes.
HOOK uses this bank directly: it does not run ASPECT's per-script reset.
The existing owned exchange passes the three packed native pointers to the
helper. Successful DOS EXEC is insufficient: child termination/exit must be
zero, returned strings must terminate, and the returned PRM must validate.

Close runs after every acquired exchange, including failures. A close failure
retains the owner for explicit recovery and blocks another execution. The
proposal is replaced only after successful validation and release. Pending
proposals block another execution until discard or future adoption.

The result has status/owner-status words, the eight-byte process result and
eight-byte PRM validation result. Transaction statuses 0–8 mean success,
argument, busy, projection, register snapshot, owner, child exit, validation
and release failure. Pointer/context rejection leaves the result untouched;
later rejection records details. No active configuration, accepted registers,
baseline or user file is committed by this API.

The retained far bank stores an 84-byte owner, two-byte phase, 2,584-byte
proposal and 1,264-byte private before-image. The proposal contains 20 integer
bytes, 810 string bytes, the 1,264-byte raw returned PRM and 490-byte decoded
settings. Phase0 is idle, 1 executing and 2 proposal-ready. Discard releases
the proposal state only when execution/allocation ownership has retired.

## Stack correction

The first combined diagnostic kept projection and execution staging frames
alive together. Although returned proposals and registers compared correctly,
stack overflow corrupted printer/mouse shutdown state. That run was rejected.
Projection now runs in a separate phase with its private before-image held in
far storage, so its nested PRM frames have unwound before EXEC staging begins.
Accepted DOS runs preserve a 256-byte A5 guard at the bottom of the real8KiB
stack, including the diagnostic caller's own roughly1.1KiB frame. This covers
the tested call chain; future foreground callers must retain adequate headroom.

The normal product adds 9,447 HOOK_CODE bytes relative to the validation-only
product, including 3,934 bytes of far transaction storage. Resident code remains
64,904 bytes and DGROUP remains 65,520 bytes. The previous validation-only
executable reproduces exactly. The diagnostic probe adds its own gated code;
the normal product contains no probe call or artifact filenames.

## Accepted evidence

[The receipt](validation/hook-transaction.json) binds:

- 152 linked admission/discard cases with interrupts/port IO prohibited.
- The existing 1,995 linked returned-PRM cases on this new executable.
- Five real8086 terminal startup workflows, each making ten helper attempts.
  These cover supported mutations, malformed string, opaque mutation, bad
  mouse, nonzero exit, unchanged return, nonzero sound representation, malformed
  response, invalid profile and missing helper. Full proposals, failure
  retention, pending/busy/discard, accepted register tails/epoch, baseline,
  source PRM, stack guard and hardware snapshots are checked.
- Fourteen normal/failure/retry COM1/COM2 ASPECT register recovery workflows.
- Six products reproduced from700 source files in an empty tree, with no
  original executable, installation, analysis database or previous objects.

The DOS helper tests run after genuine terminal startup and before mouse/UART
acquisition. They establish real helper EXEC in the terminal's memory layout;
they do not establish online UART continuity or interactive helper routing.
There is no new live BBS, settings adoption or physical hardware acceptance.

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff --session-controls --hook-return \
  --hook-execute
./tools/dev --command python3 standalone/check_hook_transaction.py \
  --output build/hook-transaction-linked-next
```

Add `--hook-probe` to build the diagnostic variant, then run
`standalone/test_hook_transaction_dos.py --output build/hook-transaction-DOS-next`
through the same Nix wrapper. Source reproduction and register recovery tests
accept `--hook-execute` in addition to the existing return/controls options.

Next is foreground integration with the existing PROGRAM safe point, checked
resource staging and atomic settings/register adoption. The setup editor's
partial/deferred application policy cannot be substituted for that transaction.
All remaining full application, ENiGMA and physical modem gates stay open.
