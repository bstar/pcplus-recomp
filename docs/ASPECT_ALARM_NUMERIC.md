# ALARM with deferred numeric banks

The opt-in ALARM interpreter now passes five full-parent cases with actual
native WHEN TRANSMIT, CALL, framed CALL, multiple CALL ordering and plain
receive/render servicing. The release remains unaccepted because the larger
held-stream/nested-child capacity gate fails four of27 checks.

The [record](validation/aspect-alarm-numeric.json) distinguishes these results
and binds source, products, captures, prior control and cold reproduction.
The current source-built parent is689bdce9 and interpreter221e407c. No installed
files, release selector, modem profile, BBS or bridge were changed.

## Memory and compatibility

The system bank holds native expression temporaries, not merely unused builtin
values. The opt-in build therefore preserves all256 system slots and128 float
slots, each eight bytes, through stable near allocations. Native integer/long
reads and integer/long/float address adapters route through checked allocation;
ordinary flat recovery still retains its exact instruction bodies.

Banks initialize to zero, remain contiguous and keep their near identity until
invocation finish. They are not freed by ordinary string cleanup. An outstanding
owner rejects a new invocation. Reset clears existing data without changing
addresses. Allocation failure retains another bank's owner and reports heap
failure; finish releases only owned storage. Invalid indices report operand
failure in this maintained adapter. Original unchecked malformed-bytecode
behavior is not claimed for the new allocation boundary.

Global far strings revealed a DOS near-heap ordering constraint: a far heap
block can prevent later DGROUP growth. Before the first far global allocation,
the adapter therefore prepares both complete numeric banks. Scripts without far
globals materialize only banks they actually use. No stack, stream count,
512-byte stream/snapshot buffer or CRT growth policy is reduced.

The paragraph-rounded launch minimum including PSP decreases from133680 to
130880 bytes:2800 bytes. This is not a universal peak-memory saving. Scripts
with far globals reserve the full3KB before their first far allocation, and
live buffers and snapshots still need their original capacities. The failed
parent capacity gate remains a release blocker.

The new parent also fixes an admission mismatch: its assembly published
capability19 while its C validator still selected18. Both now select19 under
the opt-in parent policy flag. Ordinary interpreter output remains exactly
91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b.

## Validation

- Real DOS8086 bank API:33115 checks,214 allocation attempts,210 releases and
  four deliberate allocation failures. All system/float slots, all eight bytes,
  stable pointers, isolation, resets, cleanup,100 reuse cycles and a foreign
  allocation are checked.
- Actual linked production VM:512 integer/long system-slot cases without far
  global strings and512 with them. They cover all256 indices, zero initialization,
  native address/read/write and conditional/conversion paths. The no-string
  vectors match512 cases on the preceding static-bank interpreter exactly.
  Float arithmetic remains unsupported;128-float-slot storage is tested at
  the bank API rather than through floating VM operations.
- Original-free flat operand regression:4599 CPU scenarios pass. Default
  interpreter rebuild remains byte-identical.
- Five actual parent/ALARM cases pass explicit quiet `ALARM 4` with standard
  BIOS input and the native ANSI renderer. Live text and cursor queries arrive
  while the alert runs. Observed replies take3.9–5.5ms in this emulator, before
  command return; the child exits zero and the parent resumes keys and rendering.
  The recovered controller counts observed DOS-second changes; a four-count
  alert spans about3.05–3.11s in these runs. This is not PAUSE's full-second
  scheduling or a physical timing guarantee.
- A5393-file cold public-source export reproduces both executables exactly,
  repeats the full bank API/1024 VM cases and one parent ALARM case. It records
  its Git base, declared overlay, complete source inventory hash and excludes
  original binaries, private files, previous objects and Git metadata. It does
  not repeat the entire five-case matrix, capacity gate or BBS tests.

The parent matrix places its passive observer in UMB and enables that DOS memory
configuration. No key is injected during ALARM. The earlier schedule typed
`done` while the alert could still own keys; it consumed the first letter and
the peer waited forever for the complete word. The corrected peer releases END
on the script's completion marker, independently of the alert's key policy.
A mistaken initial alias test also overlapped system slot0 with the compiler's
own expression temporary. The preceding static interpreter failed that vector
too. Final vectors test one native type at a time or use direct conversion,
so they no longer mistake intentional temporary reuse for bank corruption.

## Remaining release gate

The no-TSR parent capacity run passes23 of27 checks. It reports invalid runtime
state10 at RUN opcode9B, step26 around six held streams. The six-stream files,
third nested child and final viewport checks fail. Earlier FIRST and missing-
file recovery markers still return. The immediate cause needs further tracing;
do not label it solely a DOS memory shortage or remove buffers to make it pass.

Default-duration restoration, explicit operand errors, sound and early-key
completion through the full VM remain additional tests. Repeat carrier/error
recovery, Enigma/Synchronet/editor/transfer tests after the capacity fix. Physical
Boca/SPA2102/SynthModem acceptance, full ASPECT coverage and other original
emulations/protocols/Host mode remain open.

## Reproduction

Use the pinned Nix environment and fresh output directories:

```sh
./tools/dev --command python standalone/test_numeric_banks_dos.py \
  --output build/my-numeric-banks
./tools/dev --command python standalone/test_numeric_bank_vm_dos.py \
  --runner build/aspect-alarm-vm-numeric-final-20261106/ASPECT.EXE \
  --output build/my-numeric-vm --strings
./tools/dev --command python standalone/prove_alarm_numeric_source.py \
  --parent build/terminal-alarm-policy-admission-20261106 \
  --child build/aspect-alarm-vm-numeric-final-20261106 \
  --output build/my-alarm-cold
```

The last command exports the exact declared source into an empty tree and
replays parent/child builds and selected tests. Its products remain staging artifacts until the remaining gates pass.
