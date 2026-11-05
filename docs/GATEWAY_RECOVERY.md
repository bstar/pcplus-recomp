# Original Gateway to DOS contract

The [direct COMSPEC prerequisite](GATEWAY_LOOKUP.md) now implements and tests
the bounded execution policy. Foreground Alt-F4 ownership and binding remain
open; the startup diagnostic is not an online Gateway acceptance test.

Original Alt-F4 is an interactive shell gateway. It reads uppercase `COMSPEC`,
executes that interpreter directly with an empty DOS command tail, and restores
the terminal when the child exits. It does not add `/c` or the ordinary PROGRAM
return-key prompt. A shell `CD` persists after Gateway return; final application
exit restores the original startup directory.

This is recovery evidence for the next file/DOS command, not an implemented
application feature. The [receipt](validation/gateway-recovery.json) binds
12 checks across three accepted unmodified-original DOS workflows, eight new
REA records and the existing PROGRAM recovery. The real COMMAND.COM workflow
creates an owned witness directory and returns through EXIT. A synthetic child
returns 37 without an extra wait. Full pre/post video, cursor and shape match.
Missing/absent COMSPEC failure UI was not successfully observed at runtime;
those timed-out schedules are excluded and the failure analysis is static only.

The original key dispatch is 6B00→residentBA3F→overlay 3:DC34..DC4C. Its 25-byte
body calls `getenv(COMSPEC)` and the existing executor with flags
`command_processor=0, wait=0, save_screen=1`. The direct spawn path uses the
recovered extension/PATH lookup, rather than the separate SYSTEM fallback to
command.com. Missing COMSPEC must be rejected safely in the maintained version;
the original near-pointer/null behavior is not a suitable validation policy.

## Serial ownership distinction

In the accepted offline/dummy-UART original fixture, the child sees the original
UART ISR still installed, IER 01, DTR/RTS asserted and the IRQ unmasked. The
original executor reconfigures the UART on return and includes an RBR read.
This differs from the maintained PROGRAM owner, which pauses/releases serial
ownership around a child. Original execution does not prove safe sustained
traffic, flow-pressure, carrier-loss or child-altered-port behavior.

Gateway therefore needs an explicit serial policy and its own tests. Reusing
PROGRAM must preserve empty-tail/no-extra-prompt semantics while accounting for
the UART difference. Do not silently copy the original return-time dropping
policy or claim original equivalence for an exclusive maintained handoff.

## Integration requirements

- Resolve a bounded, validated COMSPEC executable and empty tail; distinguish
  missing, invalid and failed EXEC results without an implicit SYSTEM fallback.
- Admit through foreground ownership with explicit transfer/parser/controller
  and resource-transaction conflict checks.
- Retain the parent memory floor, frame, cursor, geometry, traps and mouse;
  verify display/UART restoration before ordinary terminal service resumes.
- Test an interactive shell lifetime, queued RX, flow pressure, DCD loss and
  same-process reconnect after return under the chosen serial policy.
- Preserve canonical startup resources and permit shell directory changes until
  orderly application exit restores the path-session snapshot.
- Determine file-handle inheritance and preserve capture/log/history/printer/
  script ownership and positions. The original child had six open JFT slots;
  their attribution and busy-file combinations remain unverified.

These checks precede physical DOS/modem acceptance and a claim of complete
Gateway parity. Raw original executables, copied private configuration, analysis
databases and capture files remain outside public Git. The REA session was
closed after exporting the evidence.
