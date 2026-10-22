# Clean modem command mode after carrier loss

[Independent validation](validation/modem-reconnect.json) accepts parent6075bc18
and runnera84dd21d for SOFT/BOTH reconnect after a remote drop under XOFF. The
previous pair also reconnects, but its trace contains XOFF+XON before the second
ATZ, which receives ERROR. It proceeds to dial despite that initialization error.
The corrected pair sends clean ATZ and receives OK. Both actual BBS byte streams
remain exact and unchanged. Reconnect success alone would miss this defect.

The owned TCP board drops its first carrier after KEYREADY and XOFF. Native
DISCONNECT TRANSMIT attempts its action, remains flow-blocked and returns child14.
Alt-D redials the same synthetic entry. A second automatic script sends SECONDOK
and writes SECOND.OK; manual input gets its exact cursor reply. Both selected
directory accounting updates occur, then the second peer closes after the reply.
The passive observer sees disconnected and reconnected parent states. It checks
the first child JFT/file-owner return; it does not capture the second child frame.
Overall42-byte hardware snapshots and actual second socket/script/file/stream
supply the separate reconnect evidence.

The initial fixture expected a stuck peer pause and one connection. Those
assumptions were contradicted: parent pause was observed clear and reconnect
succeeded. That attempt is retained as unaccepted. The accepted baseline checks
the observed command contamination and requires both connections, exact streams,
accounting and final peer close. Neither a stuck-pause counterexample nor a
physical modem defect is claimed.

## ASIOv6 carrier policy

ASIOv6 retains the50-byte v5 layout and gives the existing last word a second bit:

| Bit at offset48 | Input | Output |
| --- | --- | --- |
| 0 | Current peer TX pause | Final peer TX pause |
| 1 | MODEM session whose parent already observed DCD high | Same bound policy |
| 2..15 | Rejected | Rejected |

All input bits participate in the guard. The returned policy bit remains bound
while the peer-pause bit may change. A paused input still requires software flow.
Direct links, disabled connection control and never-observed-high DCD retain the
previous policy. Legacy ASIOv1..v5 remain accepted; renderer capabilities12/13 are
unchanged. An earlier source-built child rejects v6 before UART acquisition.

For an admitted carrier policy, the child checks actual MSR DCD before servicing
queued flow. Once DCD is low it discards pending XOFF/XON; close does not introduce
a final XOFF. It preserves the normal native action/error path and peer-pause
semantics while the application unwinds. This prevents teardown control bytes
from entering the modem's command interpreter.

The parent retains its matching conservative carrier policy. PROGRAM return
retires its introduced pause without sending XON after the known modem carrier
falls. The controller also retires old peer-pause/flow state on detected carrier
loss and releases driver-owned lowered RTS, preserving DTR and other MCR bits.
Live/untracked links continue their normal flow behavior. The new far helper
uses the existing DS=SS group with no borrowed child pointer, allocation or wait.

The42 linked cases execute actual parent/child code, native ISR and near/far
frames with modeled UART/kernel inputs. They cover context staging, control
suppression, live/direct/untracked policies, flag rejection, register/IF/DF
preservation, old-queue discard and clean subsequent initialization. An earlier
checker attempted an unsupported far-call convenience API; its corrected run
uses a real checked far frame. The failed fixture/log remains retained.

## Regression scope

Two reconnect cases, two normal flow-resume cases, two inherited-pause cases,
four timeout/cancel cases, two emulated CTS cases, four modem-drop cases and a
separate parent-state capture pass. Ten confirmation workflows,56 COM/flow/process
cases and13 attached PROGRAM cases pass. Fresh original-free source trees
reproduce26 application and23 diagnostic products. Pure result assertions move
into PROCESSDIAG; all checks remain and96 near-code bytes are available there.
Normal/mouse parent data spare is112/64 bytes and near-code spare164/14.

[Eight corrupted-evidence controls](validation/modem-reconnect-audit-guards.json)
keep producer booleans green and recompute capture hashes. The independent
auditor still rejects dirty modem commands, an erased baseline ERROR, incorrect
child exit/hardware/script/accounting/socket evidence and a wrong manual reply.

[Four recorder/replay sessions](validation/bbs-modem-carrier-compat.json) and
[two stock-window sessions](validation/bbs-modem-carrier-window.json) pass on owned
stock Synchronet/ENiGMA. [Fresh normal software audio](validation/recording-modem-carrier-audio.json)
passes26 producer,34 independent and12 serial checks, with60,929 display bytes
plus187 bridge bytes exact,77 independently waveform-decoded online bytes and
normal hardware/timer/SIP/VM cleanup. [Admission](validation/recording-modem-carrier-audio-preparation.json)
retains seven BIOS probes/56 checks and13 DOS/Telnet controls. This is one normal
ENiGMA V22/1200 route; it does not exercise fault/reconnect over audio.

~~~sh
./tools/build test-modem-carrier-flow test-modem-reconnect-dos
~~~

This uses DOSBox-X's virtual modem and owned localhost endpoints. Its ATD
Internet target is an emulator fixture, not a command prescribed for the Boca
modem. Actual Boca/SPA2102/SynthModem integration and14.4 negotiation remain
unverified. Initially-low or transient DCD, manual hangup/cancel reconnect and offline launch paths,
longer/configurable stalls, RTS/sustained RX, software-audio fault/reconnect and
every full F01–F16 application gate remain open.
