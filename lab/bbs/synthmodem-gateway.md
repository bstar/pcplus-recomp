# Full software gateway over the trained DSP link

Actual external and internal SIP legs, SipServer, CallSession, the modem pool,
normal VM answering DSP, the originating native candidate and the Telnet proxy
now run together. The accepted `synthmodem-gateway-01` cohort passes24 checks.
No session constructor, setup, activation, pool, SIP or DSP method is stubbed.
The remote TCP application is a deterministic Telnet peer rather than BBS
software. DOS and physical modem/ATA hardware are outside this checkpoint.

## Run

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_gateway.py \
  --runtime build/bbs-lab/synthmodem-training-v22-05/runtime \
  --output build/bbs-lab/synthmodem-gateway-new
```

Use a fresh output directory. First prepare the accepted
[trained runtime](synthmodem-training.md). The runner verifies its exact source
and boot inputs, copies them into a new directory, then applies only the
[RTP bind-address candidate](patches/synthmodem-bind/README.md). Node/QEMU use
the pinned Nix shell. Original source/runtime images, installed services and
the DOS executable are unchanged. Free upstream tunnel UDP ports5062/10002/10003
and the configured external RTP range42000..42100 before running; listeners
bind loopback. The SIP and Telnet peer ports are chosen dynamically.

## Exercised path

1. The actual modem pool boots a warm VM with the rebuilt helper and waits for
   d-modem registration. A real loopback SIP UAC INVITEs SipServer. CallSession's
   constructor/setup answers that external leg; ACK triggers pool checkout and
   real internal INVITE/RING/init/ATA activation.
2. Both real DSPs train at V.22/1200. CallSession retains the configured6000ms
   hold,500ms quiescence and15000ms attachment cap. Its rendered banner and
   `CONNECT>` must arrive over the audio/data path before the caller writes the
   online destination. Neither connected flag nor the decoded destination is
   supplied by the harness.
3. The independent peer negotiates BINARY both ways, requests TTYPE and receives
   ANSI plus80x25 NAWS. Caller and peer exchange534 upstream/538 downstream
   bytes, each containing two cycles of every byte value and directional
   markers. Telnet IAC is independently escaped/decoded at the peer boundary.
4. The remote peer closes. The caller must receive `CONNECT>` while SIP, session
   and modem carrier remain up. It enters the address again, negotiates a new
   TCP connection and receives `RECONNECTED`. Exactly one modem CONNECT is
   allowed across both TCP sessions.
5. After the second remote close, the caller enters QUIT at the bridge menu.
   Actual external SIP BYE and internal BYE responses are audited. Session
   teardown retires the writer/drain owner and closes RTP. The pool boots a
   distinct fresh VM, waits for registration and then shuts down. Both owned
   QEMU process handles must have exited.

The runner follows the application's SIP event wiring with the real classes.
The loopback UAC uses the existing SipUacInternal implementation; it is not an
emulated SPA2102. The software modem AT profile remains ATE0/AT&K0,
AT+MS=22,0,1200,1200, AT\N0 and AT%C0. These commands configure the VM, not Boca.
The originating candidate uses immediate RTP playout for this measured wired
loopback path. No network loss/jitter tolerance follows from this pass.

## Independent evidence and limits

The [receipt](../../docs/validation/synthmodem-gateway.json) binds both runtime
generations, harness/source/patch hashes, settings, SIP negotiation, pool
cleanup and capture hashes. Python decodes both peer wire streams without the
candidate codec, requires exact payloads, verifies TTYPE/NAWS, reconstructs
guest DATA_RX as destination + payload + destination + QUIT, and requires one
guest CONNECT status. It checks captured PCMU RTP sequence/timestamp/SSRC
continuity and both SIP legs' teardown. Binary values include the old in-band
menu-escape bytes; none are consumed in proxy mode.

Observed upstream details remain explicit: displayed status lines use CRCRLF
because string normalization processes an existing CRLF; binary payloads remain
exact. The pool's successful warmup leaves its timeout timer referenced, so
Node can remain alive after functional teardown until that timer expires. The
harness waits for the same owned process instead of killing/restarting it.
Neither behavior is repaired by this bind-address patch.

Next connect the actual DOS terminal to an originating-modem serial adapter
over this DSP gateway and run owned ENiGMA/Synchronet workflows. Real BBS
interaction, transfers, sustained pressure/error recovery, other protocols,
native flow credit, serial-to-BBS TCP pressure and physical Boca/SPA2102
acceptance remain open. V32bis direct datapump entry is still separate from a
negotiated14400-bps connection.
