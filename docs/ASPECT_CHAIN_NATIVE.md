# Native ASPECT script replacement

OpcodeCBh replaces the current script using native exit state999. The original
source keyword is `EXECUTE`; “CHAIN” here describes the recovered dispatcher
restart path, not a newly inferred compiler keyword. It abandons the current
procedure/file rather than calling another procedure or returning to the old
file. Compiler grammar is a separate original-compiler oracle responsibility.

## Handler, filename and restart

Original tableDS4B08[CB] containsC13B, whose overlay thunk selects overlay18
E709. `src/aspect/chain_command.asm` recovers E709..E721,24 bytes:

1. Obtain an81-byte scratch slot through DFC7; save its near pointer in SI.
2. Read a string through DF04 and copy it to the saved slot using actual
   unbounded strcpy8268.
3. Set E378 to999 and return. No filename validation, cleanup, status refresh,
   FILE open or nonlocal jump occurs inside this handler.

The handler returns normally to resident4B1F. The dispatcher observes999,
sets its DI owner/context argument to0, calls per-file global-string release
C2EB→overlay02D88E, closes current FILE4B02 through8318, **then** loads SI from
E104 and jumps to4B30. It does not call the per-invocation initializer C1D7
again. The setjmp/probe9048 at4B30 is reestablished before the next open.
The filename must survive old-file cleanup and close. It is not a child-supplied
far pointer and is not an independently allocated filename object.

E104 is exactly the shared string-scratch latest-pointer field. DFC7 returns
DD88+81*E106, updates E104, and advances E106 modulo11. DF04 may itself obtain a
second scratch slot (e.g. a literal or far global copied near), retargeting
E104. For such operands, both the copied first slot and the latest operand
slot contain the filename; the dispatcher deliberately consumes the **latest**
E104 value. Per-file D88E frees far global strings, not these near scratch slots.
Successful loading consumes the filename before resetting E104/E106. Saving an
unrelated filename field, clearing scratch before open, or substituting a freed
far global-string pointer would change this ownership.

The native string/copy path has no local length guard. Valid compiler string
contracts usually provide at most80 characters plusNUL; malformed streams,
unchecked indices, missing terminators and scratch-slot aliasing remain native
hazards. A reader that nonlocally aborts before return does not reach999. There
is no local rollback of its already-advanced scratch index.

## Actual per-file owner

C21F selects overlay02D770. The new source recovers the entire **148-byte**
D770..D804 function, including RET4's immediate bytes. Its near ABI is
`file_open(owner, filename)` with owner atBP+4 and filename atBP+6; it returns
AX from the filename/open loader. DS=SS and BP/DI are preserved.

It performs these writes before calling loaderD4D0:

| Native field | Per-file action |
| --- | --- |
| E13A frame and E13C value-stack pointer | Both set toAB7Ch, computed as9062h+19C8h+52h+100h. A maintained layout must bind its own stack storage; do not use this original literal address blindly. |
| E390 expression stage, E38C operand lookahead | Zero. |
| E37A procedure depth, E320 local-record count | Zero. |
| E2F8 WHEN active count, E2FA disconnect/CWHEN armed state | Zero. |
| E378 exit state | Zero, so999 is not latched into the next file. |
| DD86 pending string writeback near pointer | Zero; no stale destination flush. |
| E2FC, E308, E314 | First word of each of three12-byte local records zeroed; remaining record bytes retained. |
| E1F4, E24A, E2A0 | Offset84 active/progress pointers of three86-byte ordinary WHEN records zeroed. Pattern/action bodies are retained but inactive. |
| 4B02 current FILE | Zero before loader call. |

It calls D4D0(owner,filename). On nonzero result it calls D850, allocating
far global strings according to the new file's header count. Regardless of a
normal zero/nonzero loader return, it subsequently sets E106=0 and E104=DD88,
calls cursor-visibility helper6DCA, and **increments the existing E382 gate**.
A nonzero owner argument increments E382 once more. It returns the original
loader result held in DI. An allocator/error nonlocal abort can bypass these
post-load steps; the component stops at that declared boundary rather than
inventing rollback.

D6EA, the per-invocation initializer, explicitly initializes E382 to0. Therefore
native first-open owner0 yields gate1 and compiled main's CF yields0. Native
first-open owner1 yields gate2 and CF yields1. CHAIN forces owner0 and preserves
the previous gate before adding1; main's CF then restores that previous value.
Pending procedure-call contributions or an explicit SET RXDATA value can thus
survive even though depth/frame and pending pattern records are reset. Replacing
this with an unconditional gate1 is a maintained policy, not these instructions.
The component tests wrap fromFFFFh as well as ordinary gate values.

D770 does **not** reinitialize FINDCASE E392, SWITCHCASE E394, WAITCASE E396,
WHENCASE E398, DISPLAY E37E, KEYS E380 or the other per-invocation settings.
It does not clear WAITFOR resultE39A, FOUNDE39C, SWITCH snapshotE322/E374/E376,
keyboard pending397A/lastCFFA, integer banksD126/D482, long bankD582, system
valuesE3C4, near string bankD13A or UART receive FIFO8E20. D88E likewise only
releases the old file's far string allocations. User far globals are newly
allocated/first-byte zeroed by D850; pointer-table entries beyond the new count
may remain stale and must not be treated as live owned strings.

The per-invocation D6EA initializes selected settings, ten wordsD126..D138 and
first bytes of ten81-byte strings beginningD13A, auxiliary FILE pointers and
auxiliary far buffers. CHAIN skips it. These are exact observed ranges; this
report does not invent a reset for every uninitialized numeric declaration.
Actual declarations/initializers in the new bytecode may independently write
banks when that code executes.

## Final owner versus per-file cleanup

C273 selects overlay02D804..D850,76 bytes, also recovered in the new source.
It closes six nonzero auxiliary FILE wordsE39E..E3A8 and frees three non-null
far pointersE108/E10C/E110. It clears current FILE4B02 and script-owner4B00,
then calls status refresh2FB8 and cursor helper6DCA. This final owner runs after
the dispatcher finishes, not between999 restarts. Auxiliary streams and buffers
therefore remain invocation-owned across script replacement.

The native final owner does not clear each released auxiliary pointer/handle.
Repeated calls can repeat closes/frees; it is not idempotent. The new component
makes that behavior explicit. A maintained ledger can safely close once, but
must distinguish that policy from recovered instructions. Likewise, cleanup of
maintained C near-heap FIND temporary allocations and abandoned C frame records
is the maintained owner's responsibility; native D88E does not implement it.
No pending WHEN call may keep a continuation into the old closed FILE. Native
D770 abandons its depth, local records and WHEN registration pointers as above.

## Filename loader boundary

The complete saved overlay02 D4D0..D6E8 listing establishes these rules; it is
not duplicated as a new production filename/compiler implementation here:

- Null near pointer or an empty string returns0 silently.
- It copies to an82-byte local filename buffer using unbounded strcpy, then
  ASCII-uppercases the copy. This is not a universal input-length check.
- It scans backward for the last backslash or colon. A period in a parent
  component is irrelevant to leaf extension recognition. A forward slash is
  not recognized as a separator by this code.
- The leaf must have1..8 characters before its first dot/NUL. At that boundary,
  only NUL, `.ASP` or `.ASX` is accepted; the comparison covers the whole suffix.
  A ninth leaf character, an initial dot, trailing dot or another extension
  gives native error102. No extension appends `.ASX` without capacity checking;
  an80-character whole path can overflow the82-byte buffer when extended.
- `.ASX` is searched through shared353D and tested with3673. The shared locator
  first tries the supplied path, then its PCPLUS environment fallback. A missing
  compiled file changes the extension to `.ASP`. Explicit `.ASP` also enters
  compilation. Missing source uses UI427F and returns0.
- Compilation invokes `ASPCOMP.EXE` with format `PCPLUS %d %s`; owner0 includes
  compile-window UI. A successful compile switches to `.ASX` and opens `rb`.
  A compiler failure produces103 for owner0,110 otherwise. An open failure
  produces104 for owner0,110 otherwise. Nonlocal native error policy is external.
- The successful open also calls94A2 on FILE byte+7. That helper returns1 when
  the descriptor is below word7B29 and byte7B2B[index] has bit40h; loader rejects
  result1. This narrow CRT-flag check is not general malformed-file validation.
- On accepted open, it copies the uppercase **leaf plus extension** to current
  labelD464 for owner0. Nonzero owner gets literal `REMOTE COMMAND` from4A60.
  It then calls actual status refresh2FB8 and returns1. D770's later6DCA changes
  cursor visibility, not the filename/status label.

A maintained bounded resolver may deliberately reject unsafe normalized lengths
or unsupported path forms. It must state those limits instead of presenting them
as native validation. This proof does not implement the original compiler spawn,
DOS current-directory/drive semantics, private environment or full error UI.

## Evidence and verification

The public fixture `standalone/fixtures/aspect_chain_native_units.json` pins
248 bytes in three source units to original SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The source-only builder emits flat units and `chain_command.obj`, plus existing
actual scratch, strcpy and dispatcher helper instructions. No original data
image, executable, private PRM or generated REA database is a normal input.

Retained REA procedures:

- E709 handler: `ev_f491d40dc8b87a86c12af6c78060155d7d202f7899eb08cdb5992d5ce3f262cf`.
- D770 per-file open: `ev_8ff21649bd3d277b6ca23c7d15e7906e380bcad2d87b3318ecb71c9c666c3e01`.
- D804 final cleanup: `ev_b30359ddd225aedf9c5c6b0528ab423016250f590530ac366e6b029d835306f6`.
- D6EA invocation initializer: `ev_1a8ebd32e68e9c0e4af323aa3f4804802726fe74c5042b463243fe7c9917212d`.
- D4D0 filename loader: `ev_d7b6d1b1b0cda4408eed7653c42dd6ec108171417055a031f680b4d6f171cee5`.

```sh
./tools/dev --command python3 standalone/build_aspect_chain_native.py
./tools/dev --command python3 standalone/check_aspect_chain_native.py
# Optional ignored original; never part of the normal build:
./tools/dev --command python3 standalone/check_aspect_chain_native.py \
  --original analysis/pcplus-install/PCPLUS.EXE
```

The208 CPU cases execute all93 instructions of the248-byte new owners. They
exercise all11 scratch indices, direct and scratch-producing operand callbacks,
length0..80 boundaries, reader abort, per-file reset/retention, gate wrap and
owner arguments, successful/failed opens, allocation stop, all64 auxiliary FILE
occupancy masks, repeated native release and actual dispatcher999 restart.
The composed dispatcher uses the real recovered open/command/final owners;
initialization, full filename loader, operand, global allocation/release,
FILE and UI services remain explicit callbacks. This is not actual DOS, a full
native loader/compiler, production longjmp, physical UART or arbitrary-bytecode
safety evidence. Native filename algorithm observations above come from the
retained full assembly, not a self-generated host resolver.
