# Synchronet width changes during ASPECT execution

This campaign composes the source-built DOS terminal, ASPECT interpreter and
optional DOS compiler with the official Synchronet lab runtime. The server
uses a private copy of the synthetic LABUSER account and a test shell on
`127.0.0.1:23240`. It waits for A from the actual ASPECT child before making
its first width request. The existing lab and other boards remain unchanged.

The script drives five width/navigation states:132/selection0,132/1,132/0,
80/0,132/0. Native Synchronet `console.getxy()` receives the actual DOS cursor
replies, and `console.inkey()` handles the script's arrow sequences. The script
then returns to the stock shell, dismisses its normal pause and finishes.
A subsequent manual T command must open the real File Transfer menu.

The reused [read-only observer](enigma-aspect-width.md) verifies genuine
ASPECT renderer/bridge ownership, the actual window state, separate parent and
child DS=SS images, normal child exit and idle parser/PROGRAM/native-bank
owners after return. Its hooks are removed before the independent42-byte
UART/PIC/vector restoration snapshot. No application instruction, return value,
serial byte or cursor reply is supplied by the observer.

The four-case matrix requires precompiled/source scripts with the cooperative
window open/closed. Source cases must publish an ASX identical to the host
compiler's output. Every script writes the exact progress marker
`START|0|1|2|3|4|RETURN|` in DOS. A generic successful application exit alone is
insufficient. All cases use8086, COM2/IRQ5,19200/8N1/HARD and immediate modem
forwarding; no ENiGMA decoder patch or packet timer is involved.

For fresh output names:

```sh
./tools/bbs-dev --command python3 lab/bbs/synchronet_aspect_width_fixture.py setup \
  --candidate build/bbs-lab/synchronet-aspect-width-NEW
./tools/bbs-dev --command python3 lab/bbs/synchronet_aspect_width_fixture.py start \
  --candidate build/bbs-lab/synchronet-aspect-width-NEW
./tools/dev --command python3 lab/bbs/synchronet_aspect_width_dos.py \
  --candidate build/bbs-lab/synchronet-aspect-width-NEW \
  --terminal build/SELECTED-SOURCE-PRODUCT/TERMINAL.EXE \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --compiler build/aspect-compiler-dos/ASPCOMP.EXE \
  --window --label YOUR-FRESH-LABEL
./tools/bbs-dev --command python3 lab/bbs/synchronet_aspect_width_fixture.py stop \
  --candidate build/bbs-lab/synchronet-aspect-width-NEW
```

Omit `--compiler` for precompiled ASX and `--window` for a closed script window.
The fixture composes a separate delayed-start module without changing the
earlier main-loop fixture or its accepted evidence. Its metadata binds both
composition sources and all immutable runtime/configuration inputs. Node/PID/
statistics/recycle state remains private and mutable.

This verifies a synthetic width shell followed by the stock menu. It does not
establish stock132-column artwork adaptation, wide file transfers, arbitrary
carrier/OS interruption, unsupported application families or physical modem/
card acceptance. The earlier stock ENiGMA immediate-fragmentation failure
retains its scope.

All four cases pass56 producer checks and the independent audit. The
[sealed receipt](../../docs/validation/synchronet-aspect-width.json) binds136
artifacts. Accepted labels are `synchronet-aspect-width-window-01`,
`synchronet-aspect-width-source-window-01`, `synchronet-aspect-width-plain-01`
and `synchronet-aspect-width-source-plain-01`. The temporary server was stopped.
Application, interpreter and compiler binaries are unchanged from the SUB source
checkpoint. This validation change does not require repeating its177 DOS tests.

```sh
./tools/dev --command python3 lab/bbs/record_synchronet_aspect_width.py \
  --label synchronet-aspect-width-window-01 \
  --label synchronet-aspect-width-source-window-01 \
  --label synchronet-aspect-width-plain-01 \
  --label synchronet-aspect-width-source-plain-01 \
  --output docs/validation/synchronet-aspect-width.json
```
