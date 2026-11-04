# Status-row notice ownership

Connection notices now validate canonical row ownership before saving, drawing,
restoring or refreshing their fifteen-cell underlay. This is a prerequisite for
[status and line controls](STATUS_LINES_RECOVERY.md), not their activation.

The previous d9eae89d candidate restored all30 saved bytes over newer bottom-row
terminal output after canonical status suppression was set. A direct replay of
that executable reproduced the overwrite. It also closed the history/browser
owner when asked to display a notice on an unavailable row.

The maintained fix in `src/terminal/connection_ui.asm` admits the existing row
only when canonical suppression is zero, status width80/base3840/coordinate1800h
match, the physical screen stride is160, columns80 and video segmentB800h. This
read-only check does not probe BIOS, change geometry or establish hardware
support. Existing callers remain responsible for their BIOS/mode admission.

A rejected notice retires its stale lease without touching video or closing the
history/browser owner. A rejected restoration discards saved cells instead of
overwriting later output. A rejected status refresh returns unsupported result3
without drawing or acquiring a new underlay. Pause and elapsed-time deferred
notices recheck ownership after their modal row is released.

A geometry transaction must still restore a valid notice **before** exposing its
row and changing canonical geometry. These checks cannot detect an unobserved
hide/show cycle that returns every field to its old value. They also do not
provide generation tracking for unrelated writes while all admitted fields stay
unchanged. Do not use them as a substitute for transition/underlay ownership.

## Validation

The full candidate retains all prior feature flags and540 declared product
inputs; only `connection_ui.asm` changes. Its resident code is65330 bytes,
leaving206 bytes before the64KiB segment boundary. New instructions add90 bytes;
no persistent data allocation is added.

[Linked checks](../standalone/check_notice_row_live.py) execute actual notice,
status, pause-flush and video-copy routines. They cover ordinary repaint and
restoration,27 unsupported ownership/layout cases,81 stale-lease retirements,
replacement notices, explicit retire-before-hide ordering, and both modal
owners' deferred draw/restore actions. The previous candidate fails these
regressions. BIOS/UART inputs remain modeled; no physical display claim follows.

Auto Answer27 inputs, Screen Pause41 cases, elapsed view22 cases and32 carrier/
status groups also pass. The carrier checker now accepts an explicit terminal,
uses the existing DOS-clock fixture when required and respects the current
four-tick modem carrier-loss qualification instead of assuming immediate loss.

Actual DOS8086 COM3/IRQ5 sessions through the installed SynthModem proxy pass
owned Enigma24-line/page-up/edit/discard and Synchronet ASPECT/editor/abort, with
actual call logs. Independent24-row cell/cursor audits find zero differences:
Enigma87171 delivered bytes/cursor22,14; Synchronet22387/cursor5,8. These do not
establish other pages, fonts, physical timing or analog/SIP/DSP compatibility.

See [validation receipt](validation/status-notice-ownership.json) for exact build,
source, regression and BBS identities. The notice patch is maintained integration
work, not a byte-identical recovery of original code. Native display routines
remain separately recovered and gated; their geometry/reset/history/bridge/NAWS
integration and physical acceptance are still open.

```sh
./tools/dev --command python standalone/check_notice_row_live.py \
  --terminal build/CANDIDATE/TERMINAL.EXE --output build/NEW-notice-checks
```
