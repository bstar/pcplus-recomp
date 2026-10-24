# Current IRQ carrier recovery

The current IRQ terminal and register interpreter pass a complete DOS8086
carrier-loss/redial/retry workflow on COM2, 19200 baud, hardware flow control
and IRQ5. The [receipt](validation/irq-carrier.json) records sixteen producer
checks, thirteen independent capture-corruption checks and five loopback relay
checks. There are no application binary changes in this checkpoint.

One DOS process authenticates, begins a generated ZIP download and writes an
actual 4,096-byte source-matching partial. The relay aborts that connection;
DOSBox-X's built-in modem drops emulated DCD. PCPlus reports carrier loss and
removes `PCRX.$$$` before the second login. It redials, authenticates again,
downloads all 34,169 bytes, confirms ZMODEM completion and opens the NFO page.
Both directory connection updates and all 42 sampled hardware bytes verify.

The terminal SHA256 is
`31303aa66e1154848363e1b29a4353915e99b0a2bbb74444b03c0e0d288132db`.
The current custom-IRQ register interpreter and DOS compiler are selected
explicitly and checked against their manifests and source closures. The login
script is compiled in DOS before starting the terminal; this test does not
exercise compilation beneath the resident parent.

Independent replay validates the interrupted source offer/data, partial-prefix
hash, absence of staging before reconnect, the retry's payload/CRC/offsets,
actual receiver completion controls and subsequent NFO response. Recorded video
notices, both authenticated sessions, directory accounting, PRM IRQ and actual
emulator configuration are checked separately. Each connection has a fresh
Telnet codec; all captured decoded bytes occupy positive contiguous trace ranges.
The negative checks remove every qualifying NFO title/body copy, preserving the
stronger redraw handling from the earlier carrier acceptance work.

The isolated ENiGMA instance uses the declared incremental input decoder at
upstream revision `237cd9743d6978a940dd66db0e78f6ab8ccd3e37`, with fresh decoder
checks and reused installed dependencies. Accounts, archives and databases are
synthetic. The fixture is stopped and port 23234 was verified free. Existing
stock services, the LAN board and the disconnected card were unchanged.

## Reproduction and remaining scope

Prepare a fresh checked decoder export at the same revision as the selected
source board, then use `enigma_search_fixture.py --transfer-bytes 32768` as in
[the carrier workflow](../lab/bbs/enigma-carrier.md). The carrier harness now
accepts explicit `--terminal`, `--runner`, `--compiler`, `--cpu`, `--irq` and
`--mouse-scales` options. This run uses the full guarded custom-IRQ terminal,
`build/aspect-register-parent-custom-irq/ASPECT.EXE`,
`build/aspect-compiler-dos/ASPCOMP.EXE` and
`--cpu 8086 --irq 5 --mouse-scales 8 4`. After the run, use
`check_enigma_carrier_current_audit.py`, stop the owned fixture and run
`standalone/record_irq_carrier.py` against the retained labels and relay check.
Use fresh result labels to preserve earlier captures.

The network-dial syntax and `AT&K3` initialization belong to the emulated modem
fixture. They are not a Boca hardware profile. Physical DCD/RTS/CTS behavior,
Boca/SPA2102/SynthModem carrier recovery, SIP/audio loss, repeated-cycle/load
testing, wider server compatibility and full native application parity remain
open. This proves one emulated interrupted-download recovery, rather than all
disconnect conditions or physical modem acceptance.
