# ALARM numeric storage and capacity recovery

The opt-in ALARM interpreter now passes the previously failing held-stream and
nested-child capacity test. Both the 386 test (27 checks) and the 8086 test
(26 checks) pass with the original six stream slots, buffers and stacks.
Synchronet editor/display return and Enigma carrier-loss/redial/transfer
regressions also pass. This is a development checkpoint, not an accepted release
or a claim of full original feature parity.

The [validation record](validation/aspect-alarm-groups.json) binds the sources,
products, captures and cold rebuild. The parent is `689bdce9`; the interpreter
is `9d44b523`. The installed RCC859D7 package and release selector are unchanged.

## Failure and correction

The preceding dense deferred-bank interpreter passed simple ALARM cases but
failed four capacity checks. A diagnostic build observed a failed DOS allocation
of 608 bytes with error 8 and only 112 bytes in the largest free block. Native
PROGRAM then reported errno 12/DOS error 8. These are diagnostic-build readings,
not measurements of the production interpreter's free memory.

Numeric storage now allocates groups of sixteen eight-byte slots (128 bytes)
as needed. Sixteen system groups and eight float groups retain all 256 system
slots and 128 float slots. Newly allocated values are zero; acquired per-slot
near addresses remain stable until finish. Reset preserves addresses and clears
values; finish frees only owned storage. Bounds and allocation failures retain
typed errors and existing owners.

Current recovered consumers borrow a single two-, four- or eight-byte value:
numeric operands and stores, expression addresses, string integer destinations,
conversion destinations, disk-free queries and file sizes. They do not traverse
a whole bank. Contiguity is preserved within each group, not across groups.
Future raw bank walkers require a separate review. Integer and long views of
the same slot retain their original byte aliasing. Float arithmetic remains
unsupported; allocating its storage does not implement it.

Before the first far global, all groups are materialized to preserve the DOS
near/far allocation ordering constraint. That path can use more allocation
metadata than dense storage; this is not a universal peak-memory saving. The
paragraph-rounded child launch minimum including PSP is 130944 bytes, 64 bytes
above the preceding dense deferred build. The parent minimum is 479680 bytes.
The capacity gain comes from allocating smaller groups during ordinary
expression work, not reducing the supported slot count or stream capacities.

The corresponding diagnostic workflow now completes all four child invocations
with zero exit/cleanup errors and successful PROGRAM results. No failed DOS
allocation is recorded. It does not imply that the old 608-byte allocation
request occurs in the corrected path.

## Verification

- 33341 bank API checks, including five injected allocation failures, all slot
  bytes, stable addresses, group boundaries, reset and ownership cleanup.
- 1024 native VM slot cases and four deep-expression cases cross group
  boundaries, with and without far strings. The preceding static-bank clock
  interpreter produces the same results. Ten mixed integer/long alias cases
  cover boundary and high slots against that control.
- The full maintained VM diagnostic passes 1123 cases and 26986 checks across
  107 base slots. Only its numeric storage changes; inherited serial/clock/
  carrier models are not full-product or hardware acceptance.
- Five actual-parent ALARM cases pass with native WHEN actions and receive
  rendering: TRANSMIT, CALL, framed CALL, ordered multiple CALL and plain
  receive. These cover explicit quiet four-count alerts with standard BIOS/ANSI
  and an observer in UMB.
- A 5397-file public-source cold export reproduces both products and repeats
  the bank API, 1024 slot/four deep cases and one real-parent ALARM case. It does
  not repeat the alias, full VM, capacity or BBS suites.
- The normal products pass no-TSR capacity tests on 8086 and 386, retaining the
  three nested children, clock queries and stream checks. The 386 test also
  holds streams open through child execution.
- Stock Synchronet passes all 25 checks, including script login, its editor,
  an external COM viewer's graphics return and subsequent editing. Enigma
  passes two script logins, carrier loss, redial, retained partial transfer and
  exact 65539-byte retry. The independent journal-aware capture audit passes.

The BBS tests use isolated loopback laboratories and staged SynthModem Telnet
code. They do not test the physical SPA2102, SIP/audio/DSP, analog carrier or a
real RTS/CTS stall. Enigma uses the established 150-second transfer allowance;
the initial 60-second cutoff, wrong Nix environment and unsupported display
fixture attempts are retained as failed attempts, not accepted gates.

## Remaining acceptance

Expand full-VM ALARM coverage for default and invalid operands, temporary policy
restoration, early keys, sound, long-duration service budgets and carrier/error
cleanup. Packaging, physical tests and the remaining feature inventory are
still open. No private configuration/history, live BBS, bridge, network or
machine files were changed at this checkpoint.
