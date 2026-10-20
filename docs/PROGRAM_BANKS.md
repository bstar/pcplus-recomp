# PROGRAM code banks

The experimental full ASPECT fault diagnostic now runs the guarded Ctrl-Break
owner and PROGRAM controller in separate code banks. The previous near-only
fault diagnostic was almost at64KiB; adding the guarded controller overflowed
`_TEXT` by277 bytes. The banked version leaves1019 bytes free in `_TEXT` while
retaining the existing fault families and script/renderer/serial checks.

`BRKCODE` contains the owner, raw native install/restore/IRET instructions and
its DOS vector/break adapters. Public C calls are explicitly far cdecl; internal
C helpers remain near within the bank. Far assembly adapters use BP+6 for the
first argument and RETF, while the raw recovered routines keep their original
near, callee-cleaned ABI. The installer uses its own CS for the IRET vector, so
all three raw routines must share a CS. A forced separate-segment test caught
the handler initially remaining in `_TEXT`:77 diagnostic assertions failed and
the owner quarantined the mismatched vectors. The corrected build asserts their
placement and tests an actual CS boundary. Flat builds still reproduce all117
original instruction bytes.

`PROGRAMCODE` holds `native_program.c`. Its public execute/recover functions and
WAIT callback use far entries. The platform adapters in
`src/process/program_bank.c` remain in `_TEXT`, where they can call the near CRT,
native UI, UART and process services. Their parameters retain near pointers into
the shared DGROUP; DS must still equal SS. The native WAIT trampoline calls the
far callback and then returns through the original near UI stack. These are
resident MZ code segments, not dynamically unloaded overlays.

The object audit decodes every near call/jump in both C banks and requires its
target to be defined inside that object. External transfers must use the
declared far bank/owner families. The linked map independently verifies bank
placement, native-handler colocation and near-space bounds. The linker may pack
both banks into one CS when they fit, but that CS differs from the near CRT.
The dedicated component diagnostics disable code packing to test real crossings.

```sh
./tools/build test-break-owner-far
./tools/build test-break-owner-far-source
./tools/build test-native-program-far
./tools/build test-native-program-far-source
./tools/build test-aspect-banked
./tools/build test-aspect-banked-source
```

The [banked validation record](validation/program-banks.json) binds the source,
products, layout audit and DOS evidence. The owner passes132 actual DOS checks
with four real children. Both near and far linked owners reject18 invalid
admissions, recover after195 modeled DOS-service abandonments and pass two
quarantine cases. The near owner binary retains its prior hash.

The forced-bank PROGRAM component passes47771 assertions on each of eight
COM1/COM2 flow-control routes. This covers successful WAIT return/reentry,
mutated UART/vector/break state, queued binary input, saved/NOCLEAR views,
standard text geometries, failed launches, allocation failures and SYSTEM.
Its fresh source tree reproduces22 products. A separate fresh tree reproduces24
products including the full fault VM and attached terminal, without originals,
existing objects or REA databases.

The actual full-VM suite passes93 routes and3451 checks:22 existing ownership
boundaries crossed with real divide faults, typed aborts, foreign-DS divide
faults and direct native longjmp, plus a genuine child-divide control and four
cross-port/flow cases. It verifies the original error, clean recovery, same-VM
reuse for a second script, private streams/handles, exact arena recovery,
parent view/lease restoration and continued serial operation. The diagnostic
now also requires INT1B, the original DOS vectors and break0 to be restored and
the break owner CLOSED after both VM invocations. The test child deliberately
changes INT1B and enables extended checking. Cross-port cases cover combined,
software and no flow control, including a fault inside WAIT.

Normal terminal/ASPECT publication remains unchanged. Application-wide parent
ownership, quarantine-to-process-exit retention, faults during individual native
instructions/DOS kernel operations, remaining window/macro/error services and
physical modem/keyboard acceptance remain open. The modeled service cuts do
not prove those asynchronous cases. No full application gate closes here.
