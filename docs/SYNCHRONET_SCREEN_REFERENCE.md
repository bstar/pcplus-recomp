# Stock Synchronet editor screen reference

The unchanged `c41df22f...` DOS candidate now has an independent whole-cell
comparison against the owned stock Synchronet3.22a snapshot, in addition to
[ENiGMA](ENIGMA_SCREEN_REFERENCE.md). The final Synchronet editor frame matches
all1920 character/attribute pairs and CPR5;8 after21028 delivered bytes.
This accepts one measured frame and workflow, not every screen or emulation.

The initial fixed-delay keyboard attempts never reached the editor. Actual
wire/display artifacts show navigation drifting into other menus. An attempted
prompt script then exposed a stale prerequisite: this configuration goes
directly to Main after answering No to the new-message scan; it does not emit
the pause expected by the older audio recipe. Those failures remain preserved
and excluded from acceptance; they are not relabelled as rendering failures.

The accepted workflow uses the source-built ASPECT interpreter and compiler:

- An automatic synthetic directory script waits for the real proxy, login,
  password, welcome, bulletin, scan, Main, General, subject and editor tokens.
  It answers No, selects Local General explicitly, and writes stage markers
  and `SCRIPT.OK` only after actual matcher success.
- A source-built BIOS keyboard helper requires both `KEYTEST` and `Insert
  Mode` on the native screen before entering the measured body/key sequence.
  It supplies real BIOS input; no parser replies, application RAM or returns
  are fabricated. Ctrl-Y first clears a stale owned draft line.
- The ordinary helper's default output remains byte-identical480 bytes.
  Only the explicit reference variant omits its final visible-Main wait:
  downstream output is intentionally held in this fixture. A bounded keyboard
  watchdog still exits through the application's real Alt-X path.
- The held continuation independently contains stock FSEditor's Ctrl-Q abort
  and return to Main. Static server inputs, message bodies and official total
  posts/email/feedback/upload/download counters remain unchanged.

The owned serial adapter now also consumes the real reply to its own final
CPR query. It must not forward that test-generated response into a BBS editor.
Every other application-transmitted byte is retained in order and must exactly
equal the bytes presented to the real SynthModem proxy. Timeout/overflow
refuses acceptance; no reply is synthesized. The fresh ENiGMA regression also
passes with this change:48638 delivered bytes, CPR9;8 and zero differing cells.

Synchronet's initial `CSI ! _` is identified as a RIP capability query by the
[pinned server source](https://github.com/SynchronetBBS/sbbs/blob/9de2c48d0265b07e1a8406d8a55d31df4fad7ee8/src/sbbs3/answer.cpp).
It passes to pyte unchanged. The complete Synchronet reference input is
byte-identical to the delivered prefix: no font or other controls are projected
out. ENiGMA retains its one explicit default-CP437 font projection. The reference
adapter still refuses other unknown intermediate controls/font choices; RIP
graphics and font pixels are not accepted by this cell comparison.

Both fresh captures pass seven copied-artifact controls: unchanged, character,
attribute, cursor, truncated downstream prefix, unsupported font and truncated
proxy input. The source-only package is unchanged; earlier exact ten-file
reproduction remains applicable to those exact bytes. See
[the receipt](validation/synchronet-screen-reference.json) for identities,
source hashes, actual stage trace, preservation checks and controls.

With the owned Synchronet fixture already running, use a fresh label:

```sh
./tools/dev --command python3 lab/bbs/test_synchronet_screen_reference_dos.py \
  --runtime /home/bstar/projects/synthmodem \
  --terminal build/terminal-directory-adopt-334c0b8bd7e1/TERMINAL.EXE \
  --label YOUR-LABEL
./tools/dev --command python3 lab/bbs/audit_screen_reference.py \
  --output build/bbs-lab/results/synchronet/YOUR-LABEL \
  --bridge build/bbs-lab/YOUR-LABEL-proxy
```

This uses real DOS8086 COM3/IRQ5 code, a modeled19200-baud UART, the installed
proxy and stock loopback server, with250ms key framing/20ms input pacing. The
screen boundary uses150ms quiet time and a real CPR. Page keys cover one-line
document boundaries, not multiline editing. It does not establish unframed,
SIP/DSP/analog, physical CTS, sustained transfer, font-pixel or complete
application acceptance. No live BBS, bridge service, ATA, host network or card
was changed; only owned loopback fixtures and ignored test storage were used.

The later [ENiGMA multiline checkpoint](ENIGMA_MULTILINE_EDITOR.md) exercises
a24-line draft, real page navigation and preserved edits with two additional
whole-cell/cursor comparisons. The one-line scopes in this earlier checkpoint
remain historical; broader rendering and application gates remain open.
