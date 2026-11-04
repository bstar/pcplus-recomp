# Isolated SynthModem window-size candidate

This GPL-2.0-or-later patch targets the maintained Telnet codec in
[synexo/synthmodem](https://github.com/synexo/synthmodem), baseline SHA256
`732b57d3134a1941e0f78f9c281d76f7b4d775ce11cf1c2cf1912804fb868f5e`.
It preserves the existing source/license attribution and does not change the
installed bridge or its configuration. The checker copies that exact module
into ignored storage, applies this patch there and runs the actual result.

`TelnetCodec.resize(cols, rows)` validates both dimensions before changing them.
The existing positive1..65535 policy is retained (the RFC's unknown/zero size
is not exposed by this bridge API). Before NAWS agreement or after withdrawal,
the latest size is cached without a subnegotiation. With agreement, a change
submits one escaped width/height message; duplicate values submit nothing.
The return is `{changed, advertised}`. `advertised` means a local Telnet write,
not remote delivery or acknowledgment of an applied BBS layout.

[RFC1073](https://www.rfc-editor.org/rfc/rfc1073) permits subsequent size
subnegotiations after agreement, requires16-bit network order and doubled IAC
bytes, and lets the peer withdraw permission. It also makes the information
advisory. The candidate therefore cannot promise that an active BBS editor
reflows merely because a size message was submitted.

No serial byte is scanned for a resize command. The API is for a future trusted
Linux-side control owner. This preserves arbitrary transfer payload, including
bytes resembling terminal reports or a menu escape. The DOS client continues
to be a serial terminal; Telnet and SIP remain in Linux.

The10 Node test groups cover unchanged default startup/data against the installed
baseline, pending agreement, duplicate updates,48 dimension-boundary combinations,
48 invalid updates without partial commit, peer withdrawal/reagreement, IAC
receive continuation, NVT CR-NUL state, and all256 binary values with interleaved
metadata. The separate owned Enigma probe observes24→25→24 size updates in one
real loopback Telnet session before login. It neither logs in nor posts a draft.

```sh
./tools/dev --command python lab/bbs/check_telnet_resize.py \
  --runtime /path/to/synthmodem --output build/NEW-resize
./tools/dev --command python lab/bbs/test_telnet_resize_enigma.py \
  --codec build/NEW-resize/src/telnet/TelnetCodec.js --output build/NEW-enigma
```

See [bound evidence](../../../../docs/validation/telnet-window-resize.json).
This is not installed integration: PCPlus-to-bridge control/framing, quiescence,
rollback across both endpoints, negotiation refusal and disconnect recovery,
active-editor behavior, binary transfers through the full route and actual
modem/SIP/physical acceptance remain open. No in-band command recognizer should
be added to the opaque proxied data stream as a shortcut around those gates.

A separate [authenticated editor comparison](../../../../docs/TELNET_EDITOR_RESIZE.md)
now preserves a30-line unsaved draft, focus, paging and discard across24→25→24
updates against a fixed24 control. The active editor retains its existing
14-line page behavior and emits no immediate redraw in the measured windows.
This is scoped editor continuity, not evidence of dynamic reflow or DOS/bridge
geometry integration; all other integration limits above still apply.
