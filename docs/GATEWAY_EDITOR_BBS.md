# Gateway return inside stock BBS editors

The optional Gateway frontend now has actual Enigma and Synchronet editor-return
coverage. Both owned loopback sessions use the source-built terminal from
commit `89221e9`, an 8086 DOSBox-X CPU, COM3/IRQ5 at 19200 DTE, HARD flow, and the staged
real SynthModem Telnet proxy. The application executable remains unchanged.

This closes the selected quiet-editor return check. It does not close sustained
traffic, transfer/reconnect, SIP/audio, physical modem or full-parity gates.

## What ran

Each session authenticates to the existing stock server, enters its real editor
with a synthetic KEYTEST subject, then supplies an actual BIOS Alt-F4. The
explicit test COMSPEC receives an empty tail, writes its two-byte PSP tail report,
marks an independent observer, switches to graphics mode and waits 18 BIOS ticks
with interrupts enabled before returning.

The observer watches BIOS requests and VGA memory. It neither accesses product
state nor injects serial data, terminal replies or screen cells. Its before/after
captures prove all 4,000 bytes of the editor's 80x25 frame, the cursor position,
cursor shape and video geometry were restored. Subsequent ordinary editor keys
exercise Home/End, Delete, Insert, Tab, page keys and Ctrl-Y, then type UNSAVED.
Enigma disconnects without posting; Synchronet's normal Ctrl-Q abort is checked
separately. The tests verify unchanged message bodies/no publication, hardware
restoration, source/runtime identities and unchanged generated inputs.

A real final cursor-position query bounds exactly the delivered BBS stream.
The existing independent cell interpreter matches all 1,920 logical cells and the
cursor for each peer. Only the explicitly documented default-font probe is
projected out; later BBS output is held by the fixture after that boundary.
Gateway screen restoration is independently observed before this final check.

The selected transport uses 250 ms input-sequence framing and 20 ms byte pacing.
Those are explicit tested settings, not proof that an unframed connection or
physical CTS timing works. The test interpreter is deliberately synthetic;
ordinary COMMAND.COM creation/CD/child/EXIT was covered by the separate
[frontend workflows](GATEWAY_FRONTEND.md).

## Evidence and replay

[validation/gateway-editor-bbs.json](validation/gateway-editor-bbs.json) binds the
executable, fresh ASPECT helper, proxy sources, both sessions, screen audits,
passive captures and negative controls. The ASPECT helper reproduces the existing
`23caac9350b0a4be6f5898ce4bbc52c21604a5410a5f3340feae7732e04b004f`
executable from current sources. Its actual directory-script login runs in the
Synchronet session before the Gateway test.

Use the pinned Nix shell and fresh labels. The owned stock servers must already
be running. Select the validated staged proxy runtime explicitly; the plain
SynthModem checkout is not interchangeable with the size-probe candidate.

```sh
./tools/dev --command python lab/bbs/test_synthmodem_proxy_dos.py \
  --runtime build/menu-size-accepted-20261104/candidate \
  --terminal build/gateway-front-reviewed-20261104/TERMINAL.EXE \
  --label NEW-ENIGMA-LABEL --framing-ms 250 --byte-delay-ms 20 \
  --screen-reference --size-probe --gateway-overlay

./tools/dev --command python lab/bbs/test_synchronet_screen_reference_dos.py \
  --runtime build/menu-size-accepted-20261104/candidate \
  --terminal build/gateway-front-reviewed-20261104/TERMINAL.EXE \
  --runner build/gateway-bbs-aspect-20261104/ASPECT.EXE \
  --label NEW-SYNC-LABEL --size-probe --gateway-overlay
```

Run `lab/bbs/audit_screen_reference.py` on each capture and its matching proxy
directory, then `standalone/check_gateway_bbs_evidence.py` on the untouched
capture. The latter accepts the original and rejects eight separately copied
changes: frame cell, cursor, shape, observer marker, mode, nonempty tail, absent
child and missing edit wire. It does not alter the original evidence.
`standalone/record_gateway_editor_bbs.py` binds those reports to current source
and runtime hashes. Full command arguments and artifact identities are recorded.

## Observer memory and retained failure

The first Synchronet attempt used a 16,000-byte frame-buffer observer. DOS exited
normally, but neither the scripted login nor the Gateway ran. The semantic
checks correctly rejected it. A same-parent control without the observer reached
the editor. Reducing the observer to the actual two 4,000-byte frames allowed both
the ASPECT login and Gateway test to pass. The failed attempt and control remain
bound in the receipt. This is consistent with conventional-memory pressure;
the exact DOS error was not captured, so a proven root cause is not claimed.

The observer is test-only and is not included in an application package. Its
compact variant is limited deliberately to this 25-row test. Other display row
heights retain their separate linked foreground tests.

No physical files, deployment selector, live proxy service, adapter, boot or
network configuration changed. Later [composition checks](GATEWAY_COMPOSITION.md)
cover selected Gateway capture/HOLD/PRN and enabled-image reconnect/cancel-retry
workflows. Further owner combinations, sustained traffic, broader transfer and
carrier-loss/reconnect sessions, Microsoft
DOS 6.22 and physical Boca/SPA2102/SynthModem acceptance remain required.
