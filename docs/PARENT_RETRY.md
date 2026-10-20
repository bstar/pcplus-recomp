# Script retry after retained ASPECT failure

The [same-session receipt](validation/parent-retry.json) accepts sixteen routes:
COM1/COM2 with no, software, hardware and combined flow control, using both the
keyboard terminal and the mouse-enabled terminal. Keyboard routes pass464 checks;
mouse routes pass544. No product source or normal dispatch is changed by this
checkpoint. A fresh declared-source tree reproduces34 DOS products without
original executables, prior objects or REA databases.

One executable runs both invocations. Its controlled diagnostic driver injects
the established RUN/WAIT foreground-vector fault into `LOGIN.ASX`. Actual CLI
cleanup retains the validated PSP through DOS31 and the terminal receives raw
DOS4D status030A. The observer verifies the retained MCB, separate32-paragraph
allocation and linked source-owned ISR, then invokes only that known ISR. The
first script does not continue or transmit its selected password.

Emulated keyboard input opens Alt-Z / Run Script and enters `retry.asx`. For this
designated second script, the same executable uses ordinary VM/CLI execution
without injecting a fault. It validates the selected directory name and entry,
runs the UART-mutating DOS child with NOCLEAR, transmits `RETRY-OK`, matches the
peer's `RETRY-ACK`, writes `retry-owned` to `RETRY.OUT`, and displays
`RETRY COMPLETE`. Its actual termination is DOS4C / exit0. The nested child
deliberately exits37; its real DOS4D status is preserved. WAITFOR is checked
through its native result, independently of the preceding RUN comparison.

The second process has a distinct PSP. Its nested PROGRAM holds the real
renderer lease while running; the lease is retired afterward. Exact parent
resource bytes, JFT and file-owner bytes compare equal across execution. The
source-owned diagnostic witness records closed break ownership, idle PROGRAM,
no detached serial lease, active UART and no runtime error after RUN. Serial
cursor replies and ordinary keyboard transmission continue after the retry.
Mouse routes additionally operate Write Screen through native mouse events
and restore all576 saved mouse-driver bytes at terminal shutdown.

The first process remains retained throughout. Its INT1B address, MCB owner,
paragraph count and separate allocation marker survive the second process.
The known ISR's counter changes1 to2 after the second EXEC returns. The test
does not repair a vector, fabricate a lease result or reclaim retained memory.

The observer is verified in upper memory (actual segmentCC4B in these runs),
using DOSBox-X's [LH command](https://github.com/joncampbell123/dosbox-x/wiki/DOSBox%E2%80%90X%E2%80%99s-Supported-Commands).
This removes its conventional-memory footprint from the application budget;
the application and its retained child remain ordinary DOS allocations.
Hardware UMB availability is not established. The dedicated observer also
omits unrelated admission telemetry and compares one exact pre-EXEC resource
snapshot directly with live bytes after EXEC, rather than storing two copies.

The failed pilots remain under `build/aspect-parent-exit-mouse-retry`:
`parent-retry-pilot-02` records EXEC error8 with the large observer in
conventional RAM. `parent-retry-pilot-06` captures the CRT startup message
`Not enough memory to allocate file structures`. `parent-retry-pilot-10` records
busy cleanup caused by the new observer forwarding its own cleared IF into
the DOS caller. The corrected observer forwards carry while preserving the
caller's other FLAGS bits. Raw kernel and caller FLAGS are retained separately
in the passing evidence; they differ by IF in these DOS4D observations.

```sh
./tools/build test-aspect-parent-retry
./tools/build test-aspect-parent-retry-mouse
./tools/build test-aspect-parent-retry-source
```

The proof covers one retained failure followed by one successful retry.
Repeated quarantine can still exhaust conventional memory. Physical modem,
mouse and keyboard acceptance, normal publication, application-wide ownership,
remaining native services and the full F01–F16 gates remain open. These DOS
tests do not replace stock ENiGMA/Synchronet workflow acceptance.
