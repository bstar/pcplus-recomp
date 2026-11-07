# ALARM duration policy and completion keys

Six additional actual-parent/interpreter cases pass on the grouped numeric
build (`689bdce9` parent, `9d44b523` child). The
[validation record](validation/aspect-alarm-policy.json) binds product manifests,
authored scripts, frozen expectations, serial captures, passive observations and
the maintained test sources. Application bytes and installed files are unchanged.

The duration cases cover an omitted operand, explicit zero followed by an omitted
operand, and explicit two followed by an omitted operand. The actual parent is
configured for quiet four-count alerts. Zero returns in about 6 ms; the two-count
alert returns after about 1.08 seconds. The following omitted-duration alerts
observe approximately 3.05 and 4.01 seconds respectively. These are the recovered
controller's observed DOS-second transitions, not full-second PAUSE intervals.
Both following alerts use the configured four-count default.

This verifies policy rereading from the real parent after explicit overrides.
It does not sample the child duration word between commands. The exact native
wrapper restoration remains separately established by the
[native controller tests](ASPECT_ALARM_NATIVE.md); policy rereading could mask
a wrapper restoration defect, so the timing tests alone do not prove it.

Three other cases enter `alarm 32767` and deliver Escape, printable `x`, or F1
through the actual BIOS keyboard. Each finishes after about 1.93 seconds, exits
successfully and continues the script. Exact wire comparison proves the
completion key does not leak to the BBS. Parent keyboard input resumes afterward.
These are early-key tests, not nine-hour timing or service-budget acceptance.

All six cases retain a receive-side cursor query during the alert, answered in
approximately 4–5 ms before alert completion. Full native rendering, parent
return, JFT and sink ownership checks pass. The tests use standard BIOS/ANSI,
an emulated UART, an owned raw modem peer and a passive observer in UMB.
There is no parser/reply substitute or physical SIP/audio test.

The first policy attempt incorrectly expected the zero-alert completion marker
after the receive query. Its actual wire placed that marker before the query,
and the test failed. The accepted fresh run freezes the correct order and sends
the query later, inside the subsequent default alert. The failed attempt remains
in ignored build storage; it is not counted as accepted evidence.

Run with the pinned environment and exact product hashes, for example:

```sh
./tools/dev --command python standalone/test_aspect_alarm_vm_dos.py \
  --parent-dir build/terminal-alarm-policy-admission-20261106 \
  --child-dir build/aspect-alarm-numeric-groups-final-20261106 \
  --variant policy --label my-alarm-policy \
  --terminal-sha256 689bdce91c267320b4aad9136a530ab8ce90f733f4a540197e53e6ce4074df06 \
  --runner-sha256 9d44b5237d6398b90a621f44ebf2a9ae7b2a0e140d81a4bac10c83ccaddd78cb
```

Use `--variant keys` with a new label for the three completion-key cases.
The default `when` variant retains the preceding five native WHEN/render cases.
Use a fresh label; prior captures must not be overwritten.

Sound, malformed operands, long-duration service budgets and carrier/error
cleanup remain open. No new cold export or modern BBS test is claimed here:
the application products are unchanged from the
[capacity/BBS checkpoint](ASPECT_ALARM_GROUPS.md). Packaging, physical acceptance
and the remaining full-parity inventory are still required.

The subsequent [speaker checkpoint](ASPECT_ALARM_SPEAKER.md) observes enabled
gate activity, normal/key-completion cleanup and the child duration word at
exit on these same products. It supersedes the sound/exit-state portions of
this checkpoint's remaining work, without claiming acoustic or physical tests.
