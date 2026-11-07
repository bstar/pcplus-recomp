# Active alert and carrier-loss regression

The matched capability 20 package passes eight actual DOS alert/carrier cases:
37 checks each, 296 total. Parent `856a9c85` and interpreter `5c641ac4` are the
same files in the reproduced public package. The
[validation record](validation/emulate-carrier.json) binds product identities,
sources and raw captures.

| Profile | Disconnect handling | Observed native result |
| --- | --- | --- |
| VT220 and ANSI | No handler | Normal return |
| VT220 and ANSI | Deferred CALL | Ordered framed CALL, then main resumes |
| VT220 and ANSI | TRANSMIT | One actual modem AT action, then main resumes |
| VT220 and ANSI | XOFF/service failure | Typed error 14 and cleanup |

A real DOSBox modem changes DCD after the owned peer closes its socket. A parser
query/reply round trip is verified before the drop. The passive UMB observer
checks that the speaker was active, its gate and owner retire, temporary duration
returns to the saved value, DS=SS is retained, disconnect registration retires,
JFT and sink owners restore, and parent owners return to the command menu.
The final parent status is OFF-LINE. Peer wire and ordered file effects match
independent expectations.

These runs execute the ordinary package products rather than the same-process
diagnostic driver. The XOFF error is observed inside a sounding alert; it is not
an error substituted by the test. Speaker port activity establishes software
ownership/cleanup, not audible output on the physical computer. The observer
changes memory/timing footprint and does not write product state or synthesize
terminal replies.

This closes the named active-alert/carrier matrix for the current package.
Arbitrary asynchronous faults, broader sustained flow/headroom, physical
Boca/SPA2102/SynthModem runtime and full original feature parity remain separate.
Physical installation, private configuration and call history are managed in the
local machine record rather than published in this software receipt.
