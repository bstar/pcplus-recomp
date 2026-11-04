# Live call-clock lifecycle

The optional `--call-timer` original-reference candidate binds the recovered
220-byte timer to confirmed connection transitions. The exact original start,
seconds conversion and elapsed update bodies live in a retained code bank.
Five explicit connection callbacks start once on MODEM or DIRECT connection
and freeze on confirmed carrier loss, completed modem retirement or DIRECT
hangup. A failed attempt never starts the clock; repeated stop is harmless.

The timer remains running when an online hangup fails and the connection owner
returns to online state. Actual disconnect freezes the duration. BUSY, timeout
and canceled attempts after that retain LAST CALL until another confirmed
connection replaces the anchor. Duplicate start while active does not reset it.
`terminal_call_timer_refresh_far` updates only a running clock; offline refresh
preserves the frozen value and performs no DOS clock read.

The live service does not depend on call-file logging. The native start routine
still captures two clock reads, and native update still applies the original
single-day rollover policy described in [timer recovery](ELAPSED_TIME_TIMER.md).
All public far lifecycle entries preserve registers and FLAGS with DS=SS.
The DOS time-structure service now uses actual AH2C. Narrow division/remainder
adapters implement the proven positive timer operands (<86400, divisor60/3600),
and the formatter implements exactly the timer's fixed HH:MM:SS contract.
These adapters are not general C-runtime replacements.

The application candidate is SHA256
`2192f454f46c6ecec0c84ea43d3714a5e2e2ab1d89b5220c6d24b7967afc4c9d`.
It has64848 near data/stack bytes,48 more than the prior candidate, and still
65176 resident code bytes with360 spare. The new retained code bank is497 bytes.
With the feature disabled, a full same-option build reproduces the prior
`501629c093d731be8f3324f185e128af76e00c2942e5ad3463c1ce7da54edb6e`
image exactly. Ordinary builds exclude all new timer objects.

## Validation and limits

The linked CPU suite executes the real native bodies, new adapters and actual
connection controller. Six groups cover logging enabled/disabled, midnight,
carrier loss, BUSY/redial, timeout/cancel before CONNECT, DIRECT disconnect,
clock rollback/carry, duplicate start, idempotent stop, and failed online hangup.
Only kernel time/date, BIOS/UART/PIC and filesystem boundaries are modeled.
No product callbacks are patched or skipped. Separate layout checks require
all five far-call segment fixups and compare all220 recovered bytes after only
declared call/data relocations and local-branch coordinates are normalized.

The native DOS regression exercises three real DOSBox modem DCD-loss/reconnect
workflows, including delayed HARD/SOFT log writes, with the new clock services
executing through DOS. Four ASPECT WAIT/WHEN/window return cases are checked
separately. These fixtures retain their exact call-log, cleanup, parser and
same-parent second-call requirements; they do not directly measure the timer
fields on physical hardware. The existing41-case Screen Pause CPU regression
also covers its key, flow, deferred notice and view-restoration behavior.

Fresh owned Enigma and Synchronet editor/proxy sessions retain independent
final-cell/cursor audits, call-log and draft-discard checks. The scoped
[receipt](validation/call-timer-live.json) binds actual results and source/input
identities. The source-only native recovery proof remains a separate scope.

At this checkpoint the Alt-T/Alt-Z window was unavailable. The later
[serviced window](ELAPSED_VIEW_LIVE.md) now enables it separately. Its owner must keep
serial/parser/flow/carrier service active, defer underlay notices, consume one
local dismissal key and restore cells/cursor before being enabled. Whole
original feature parity, physical BUSY/reboot diagnosis and Boca/SPA2102/SIP/
analog acceptance remain open. No live BBS/bridge is restarted, no candidate
package is selected for deployment, and no DOS machine file is changed.

```sh
# Add --call-timer to the original-reference candidate's existing build options.
./tools/dev --command python standalone/check_call_timer_live.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-timer-live
./tools/dev --command python standalone/check_call_timer_layout.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-timer-layout
```
