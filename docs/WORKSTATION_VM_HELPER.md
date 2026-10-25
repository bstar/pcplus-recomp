# Workstation VM helper update

The 2026-10-25 workstation update now includes the Nix-built control helper,
alongside the earlier [stock ENiGMA proxy fixes](STOCK_ENIGMA_PROXY.md).
The original helper's single nonblocking writes could lose an unsent tail or
leave a truncated control frame after a short write/EAGAIN. The maintained
patch retains ordered output and advances only by bytes actually written.
It is built by the existing pinned `synthmodem-control-i386` Nix target.

The fresh actual-VM pressure test passes all 14 checks. Both directions move
16,777,219 bytes exactly, exercise real backpressure and continue reverse service
during a forward stall and forward service during a reverse stall. Workers and
the guest terminate cleanly. This uses virtio modem/control stand-ins; it does
not establish analog modem data integrity.

A separate production image changes only `usr/local/bin/modemd-ctrl` in the
original installed archive. The kernel, init, DSP binaries and every other
archive entry retain their contents. No diagnostic `lab-init` is included.
The image boots with the actual updated backend on separate loopback tunnel
ports. Eight real SmartLink AT queries/settings succeed, including readback of
`132,0,4800,14400` after the existing `AT&E0` setting.

The existing runtime test, adapted only to isolate host tunnel ports and use
the exact workstation initialization commands, also passes all 14 checks:
normal startup/registration, actual SIP INVITE/RING/answer, accepted modem
initialization, bidirectional PCMU RTP and non-silent real DSP output, followed
by BYE and complete cleanup. The caller supplies silence; no carrier is claimed.

The adapter was on-hook/idle before installation. The original archive was
backed up, only SynthModem restarted, and the updated service's own VM and SIP
listener reached ready. The 14.4 profile, LOC shortcuts, 250ms key framing,
adapter, workstation network and live BBS were preserved.

The [receipt](validation/workstation-vm-helper.json) records exact source/media,
helper and installed archive identities, VM pressure results, real-modem AT and
SIP/audio checks, the generated isolated harness identity and deployment guard.
The diagnostic VM and production VM image are distinct and their hashes are
recorded separately.

Remaining acceptance requires a real Boca/SPA2102 call, sustained serial/audio
byte integrity, flow control, transfers and repeated disconnect/reconnect. The
unit/VM/proxy checks do not establish a perfect analog path or complete PCPlus
application parity. No DOS card was written.
