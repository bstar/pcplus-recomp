# ZMODEM replies behind a buffered modem

The first stock ENiGMA audio upload failed because the sender's three-second
reply read expired while its fixed38400 DTE had queued data behind a1200-bps
carrier. Replays accumulated before a valid ACK arrived. The
[failed-run receipt](validation/synthmodem-audio-upload-01.json) and
[linked predecessor counterexample](validation/zmodem-upload-response-counterexample.json)
remain failures; exact truncated prefixes are not accepted as whole transfers.

The maintained engine now has an explicit `zm_run_link` entry. A nonzero
minimum carrier rate enables a bounded sender reply allowance. The existing
`zm_run` entry preserves the ordinary three-second policy. Rates below300bps
are rejected before the workspace or callbacks are touched. Receive timing,
source/storage ownership, retries and what counts as confirmed progress remain
unchanged.

For connected modem mode, the terminal selects the conservative300-bps floor
already used by its receive accepted-progress watchdog. This is independent of
the UART divisor. Direct directory mode and disconnected sessions retain the
ordinary policy. No Boca-specific initialization command or negotiated14400
rate is assumed.

The sender computes the allowance from peer-unacknowledged payload, bounded by
the negotiated window. Each byte may quote to two; each frame needs at most21
header plus11 ending/quoted-CRC/XON octets. Another64 octets cover EOF and the
reply. At8N1, the read allowance in seconds is:

```text
3 + ceiling(10 × (2 × pending payload + 32 × frames + 64) / carrier floor)
```

At300bps, the first1024-byte packet allows75 seconds and an8192-byte window
allows560 seconds. Metadata uses its actual128-byte payload bound. Control-only
exchanges receive their smaller allowance. Nonblocking overlap polls still
request zero seconds and retain partial headers. Source bytes merely emitted
on the wire never become confirmed progress.

The shared UART reader caps each call at30 seconds. The live ZMODEM adapter
honors larger allowances through successive serviced reads, checking faults
between them. Its existing verified-progress watchdog stays independent:
17280 BIOS ticks in modem ZMODEM mode. Escape, carrier loss, per-byte CTS/THRE
stall limits, finite protocol retries and bounded cancellation drain continue
to apply. Unverified noise cannot refresh accepted progress. These are per-read
allowances inside that separate overall inactivity bound, not an unlimited
per-byte extension.

All arithmetic uses32-bit intermediates even in the16-bit executable. The new
modem-mode query has a declared CONFIG_CODE-to-resident zero-argument bridge.
Watcom's32-bit multiply/divide imports use the existing register bridges;
normalization changes only OMF external names, lengths and checksums. Source
instructions, data, symbol ordering and fixups remain intact. DS equals SS and
near storage remains64832 bytes.

The regression scope includes independent host wire peers, actual linked DOS
instructions with modeled hardware/kernel boundaries, and actual DOS transfer
checks. Full stock audio upload acceptance still requires a fresh complete run
and all CRC/control/finish, exact official storage, post-form search/list and
cleanup checks. Physical Boca/SPA2102, other peers, pressure/loss and all
F01–F16 application gates remain separate.
