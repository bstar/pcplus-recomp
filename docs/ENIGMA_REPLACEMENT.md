# ENiGMA replacement checkpoint — 2026-10-25

The later [stock-ENiGMA proxy checkpoint](STOCK_ENIGMA_PROXY.md) adds actual
stock-server editor evidence and the installed framing/output-pressure fixes.
The codec-only settings and corrected-decoder results below describe the
initial checkpoint.

The working target is a reliable DOS serial terminal for the existing Boca
COM3/0x3E8/IRQ5 → SPA2102 → SynthModem → LoSs oF CoNtRoL connection.
Rendering and interactive login/editor behavior are acceptance requirements.
The original 2.01 has also shown instability, so comparisons must separate
terminal defects from bridge defects and damaged modem data.

## Installed bridge correction

The workstation's SynthModem now uses the existing checked Telnet codec.
The previous proxy passed negotiation bytes into the serial display, failed
to quote literal FF bytes, advertised dimensions from the wrong configuration
section, and consumed some valid binary bytes as menu escapes. These defects
were reproduced in the upstream control. They can affect either DOS client;
they are not proof of the cause of every reported glitch.

The installed source retains the LOC/1/ENIGMA aliases and ANSI 80×25 settings.
The codec handles streaming negotiation, BINARY/NVT, terminal type, dimensions,
literal IAC, remote close and stale-socket isolation. The merged candidate
passes 1,220 transport assertions and the existing shortcut test. Its optional
ANSI input-sequence framer passes the component and local TCP checks, but
remains disabled in the running service. TCP write boundaries cannot guarantee
correct parsing by an arbitrary server.

The update checked PHONE1 on-hook/idle, saved rollback files under the user's
SynthModem state directory, and restarted only SynthModem. The service then
registered its warm VM and reported ready for calls. The V.32bis profile, DSP
image, adapter configuration and live BBS were not changed. This is software
validation, not a new physical-call acceptance result.

## DOS candidate and local profile

The new nine-file source-built package is staged locally at
`build/special-enigma-ready-20261025/PCPLUSSE`. It includes the original CP437
logo on magenta with the LoC edition/version annotation. START and SETUP pass
actual DOS8086 launcher checks on emulated COM3/IRQ5: normal return, environment,
UART/PIC/vector restoration, configuration preservation, compilation or splash
capture as appropriate.

`standalone/test_special_package_dos.py` now accepts `--com 1..4`; its PRM,
UART sampler and emulator all select the same port and IRQ. COM2 remains the
default for earlier reproduction commands.

Prepare private configuration separately from the public application build:

```sh
./tools/dev --command python3 standalone/prepare_boca_profile.py \
  --input /path/to/identified/PCPLUS.PRM \
  --output build/NEW-private-boca
```

The input must be an identified original-format 2.01 PRM; matching file length
alone does not establish its format. This utility creates BOCA.PRM and LOC.BAT
without changing the input. Defaults select COM3/0x3E8/IRQ5, fixed 19200 8N1,
RTS/CTS, ANSI/CP437, no translation or software flow, DTR drop on abort and a
90-second application dialing deadline. It preserves all modem commands and
opaque bytes outside the selected fields. Modem-side flow control and DCD/DTR
behavior still need confirmation on the actual Boca. It adds no presumed
AT+MS support or persistent modem settings.

Copy these two local files alongside the package under `C:\PCPLUSSE` when
deploying. Run `C:\PCPLUSSE\LOC.BAT`; after carrier and CONNECT>, enter `LOC`
or `1`. LOC.BAT uses numeric dial target 555 and a 20-second initialization
acknowledgment deadline. An error/timeout must be investigated, not suppressed.
The separate profile preserves the old PCPLUS.PRM. No card was accessed in
this checkpoint, and the staged profile is not yet a hardware-verified preset.

## Interactive and rendering evidence

The exact branded terminal (SHA256
`e096c53b802df1561ce4e9a135cd091a7ba8edb03fe24822341061e8fac91a9b`)
authenticates and enters the isolated ENiGMA full-screen editor in actual
DOS8086 on COM3/IRQ5, 19200 8N1 with hardware flow selected. The independent
semantic audit passes login/editor entry, emitted keys, Home placement,
Insert/overtype and no saved post. The actual video snapshot contains UNSAVED
and OVR 01,08. End, Delete, Tab, page keys and Ctrl-Y were exercised; the page
case is a one-line boundary test, not multiline scroll acceptance.

This instance uses the lab's corrected input decoder. It does not establish
stock/live ENiGMA decoder behavior, physical UART timing, analog byte integrity,
file transfers or perfect rendering of every ANSI feature. The loopback modem
holds CTS ready. The software receipt is
[enigma-replacement.json](validation/enigma-replacement.json).

Remaining gates include an actual Boca/SPA2102 login and editor session with
the corrected installed bridge, sustained data integrity and flow control,
repeated disconnect/reconnect, transfers, stock-server fragmentation, multiline
screen behavior, and the remaining original application/menu parity. Keep the
old executable available while these gates remain open.
