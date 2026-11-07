# ALARM speaker policy and cleanup

Six actual-parent/interpreter cases now observe the emulated speaker gate and
child exit state. All pass on the existing `689bdce9` parent and `9d44b523`
interpreter. The [validation record](validation/aspect-alarm-speaker.json)
binds product manifests, current sources, authored scripts, observer assembly,
raw reports and wire captures. No application binary or installed file changes.

The passive observer reads port61 bits0–1 at BIOS ticks while the child EXEC is
active. It never writes the PIT or speaker gate. At the child's DOS exit it also
reads the child speaker owner and ALARM duration word, verifying DS equals SS
before accepting those readings. The added fields precede the existing window
observations, preserving the existing report fields and checks.

| Case | Sound | On ticks | Gate edges | Gate/owner at exit | Duration at exit |
| --- | --- | ---: | ---: | --- | ---: |
| Native WHEN TRANSMIT, natural completion | Enabled | 24 | 16 | 0 / 0 | 4 |
| Plain receive, natural completion | Enabled | 24 | 16 | 0 / 0 | 4 |
| 32767-count alert, Escape | Enabled | 15 | 10 | 0 / 0 | 4 |
| 32767-count alert, printable x | Enabled | 15 | 10 | 0 / 0 | 4 |
| 32767-count alert, F1 | Enabled | 15 | 10 | 0 / 0 | 4 |
| 32767-count alert, Escape control | Disabled | 0 | 0 | 0 / 0 | 4 |

Each long-alert script executes a single explicit `alarm 32767`. The observed
duration at exit is four, matching the configured default. This strengthens the
preceding [policy tests](ASPECT_ALARM_POLICY.md): it observes child state after
the wrapper returns, rather than inferring restoration solely from a subsequent
command that rereads the parent policy. It does not sample every intermediate
instruction or prove malformed-operand restoration.

Natural sounding alerts complete after approximately3.27 seconds; key-completed
alerts return after approximately1.93 seconds. Actual native rendering and WHEN
TRANSMIT continue while sounding. Receive queries are answered in approximately
4–6 ms before completion, exact wire comparison excludes leaked completion keys,
and parent keyboard, JFT and sink ownership checks pass afterward.

The observed edges establish enabled output and shutdown, not an independently
measured frequency or exact tone cadence. The recovered controller's paired
880Hz requests and arguments remain covered by the separate
[native baseline](ASPECT_ALARM_NATIVE.md). Port sampling does not verify an
acoustic waveform, a physical speaker or the modem's own speaker.

The existing harness adds `--speaker` to enable the actual parent sound policy
and observe gate/exit state. `--observe-alarm` samples the same state with sound
left disabled. Both combine with `--variant when`, `policy` or `keys`, explicit
parent/child directories and hashes, a fresh label and optional case selection.
The accepted captures are under:

- `build/aspect-alarm-vm-dos/sound-natural-groups-20261106`
- `build/aspect-alarm-vm-dos/sound-keys-groups-20261106`
- `build/aspect-alarm-vm-dos/quiet-observer-groups-20261106`

Each has `checks.json`, `pause-checks.json` and `speaker-checks.json`. The recorder
independently checks raw speaker/exit words and binds every captured artifact.

Malformed operands, long-duration service budgets and carrier/error cleanup are
still open. In particular, the VM currently supplies a fixed2000000 service-call
budget regardless of requested duration. Early cancellation of32767-count
alerts does not establish that this budget supports their full duration.
This is a concrete remaining policy question, not a measured long-run failure.

These tests use standard BIOS/ANSI, a UMB observer, an emulated UART and an owned
raw peer. No physical SIP/audio/CTS test, new cold export or new modern-BBS
regression is claimed. Products remain exact to the preceding capacity/BBS
checkpoint; the installed RCC859D7 release remains unchanged.

The subsequent [operand-error checkpoint](ASPECT_ALARM_ERRORS.md) covers five
invalid operands and subsequent same-parent reuse. It supersedes that portion
of the remaining list above, without covering errors inside an active alert.
