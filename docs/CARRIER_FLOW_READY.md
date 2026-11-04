# Flow control while DCD is being qualified

Actual DOS modem reconnect testing found a command-channel regression in the
composed application. After the BBS closed its first socket, the program returned
from its ASPECT script and correctly cleared peer XOFF. Before the next `ATZ`,
however, the modem received `11 13 11` hexadecimal as a command prefix and answered
`ERROR`. The second connection still succeeded, so checking only the final login
would have missed the regression.

A linked differential check also caught queued ordinary output leaving the UART
during that same grace interval. Against the intermediate flow-only image, the
first queued NUL was transmitted while DCD was low. The final foreground gate
holds ordinary output and its macro write grant for a logically online session
until carrier returns; confirmed loss retains the existing queue retirement.

The maintained MODEM controller intentionally qualifies four BIOS ticks of low
DCD before declaring loss. That protects the physical connection from a brief
level change around training. Its existing `terminal_connection_flow_alive`
therefore means that a session remains logically retained, including that grace
interval. It did not mean that it was safe to send flow bytes immediately.

## Change

`terminal_connection_flow_ready` adds a separate far readiness boundary. It first
uses the existing logical lifetime/retirement policy, then refuses immediate
control output while a previously observed MODEM carrier is currently low. It
does not shorten the disconnect grace interval or discard a pending resume during
a transient drop. DIRECT, disabled-controller and never-observed-DCD policies
retain their existing behavior. DS=SS and callee registers remain intact.

- The ordinary foreground poll holds queued control bytes while DCD is low.
  Returning carrier lets the existing UART flow poll send them; sustained loss
  retires them through the existing controller. Queued ordinary bytes also remain
  intact through a transient drop and resume in order; they do not reach the
  modem command interpreter while the session is still in its grace interval.
- PROGRAM pause acquisition and the call-log disk writer use immediate readiness
  before sending a new XOFF.
- PROGRAM resume and call-log release keep their logical-lifetime checks when
  queuing XON. This preserves a deferred resume for a returning carrier; the
  foreground readiness gate controls when it can physically leave the UART.
- Shutdown waits within its existing bounded deadline for readiness. It resumes
  after a transient drop or succeeds silently once sustained loss retires the
  pending flow. It retains its explicit failure when cleanup cannot complete.

No recovered UART instruction, raw receive byte, modem result parser, four-tick
qualification rule, configured initialization string or connection timeout was
changed. This is maintained application policy, not an original-binary recovery
claim. The original splash and LoC annotation selection remain unchanged.

## Evidence

The [receipt](validation/carrier-flow-ready.json) binds the failing actual DOS
capture, current source-built parents, unchanged child, immutable session captures,
independent checker and isolated source-only rebuilds.

The linked readiness model covers transient intervals of zero through three ticks,
retained XON and XOFF, both hardware-flow settings, midnight/low-word wrap,
unchanged logical connection state, sustained loss, shutdown, recovery during
shutdown and existing untracked/direct policy. Queued NUL/FF/ASCII output verifies
ordinary byte preservation and ordering alongside both control-byte classes.
All58 inputs pass. The existing
parent status/controller suite has32 passing groups; malformed-CSI recovery also
retains its20 faults followed by60 fresh queries.

The actual8086 DOS matrix runs profiles4/6 at25/28/43/50 physical rows with SOFT and
BOTH flow. Each of16 workflows uses one parent process and two real DOSBox-X modem
connections to an owned loopback TCP endpoint. The peer sends XOFF, then closes
its first socket. DOSBox-X supplies the actual emulated DCD transition and
`NO CARRIER`; no product flag or MSR value is injected by the observer. The first
script must return serial error14, and the second must exit normally and create
its expected result file. Ordinary local input and a fresh CPR must then work.

The observer reads state and supplies normal BIOS keys at observed lifecycle
boundaries. Redial uses Alt-Z, backtick, Right and D through the visible command
browser's Connection/Dial selected target entry. Alt-D retains its original
directory role. It is not replaced by a private dispatcher action in the test.
Both EXEC lifetimes have JFT and resource-owner captures. The final logical
screen, physical carrier-loss status, font/geometry, raw peer stream, modem
commands, directory accounting and hardware restoration are checked. The first
EXEC's relocated far-history bounds/content are independently verified too;
the second EXEC does not have a separate history snapshot in this observer.

Only `ATZ` and the selected dial command may reach the command interpreter, with
one optional empty line between sessions from the existing command-resync path.
No flow/data prefix or modem `ERROR` is accepted. The final terminal legitimately
shows `NO CARRIER` and `Carrier lost` after the second peer also disconnects.

These are emulator/component results, not physical Boca/SPA2102/SynthModem or
Enigma/Synchronet acceptance. The test's Internet dial string belongs exclusively
to DOSBox-X's virtual modem; it is not a command recommendation for a real modem.
In-flight binary transfers/cancellation, other modal owners and broader feature
parity remain separate. No installed bridge/service, physical DOS files, private
configuration or selected deployment package changed here. Diagnostic height
images remain internal and unpackageable. The ordinary candidate uses65,120 near
bytes and65,484 resident code bytes; the diagnostic parents use65,510 resident
bytes. All code segments stay below64 KiB. Five exact source-only parent rebuilds
pass, and the existing child retains its288-source manifest and executable hash.
