# Ordinary upload startup

The maintained ordinary sender adapter now tolerates receiver banner text at
startup. The recovered sender and double-CAN routine remain byte-identical to
their flat instruction baselines. Only the initial timed-read call returning
to `send_at_df9a` selects this filter; block ACK and EOT reads retain their
existing behavior.

Incoming NAK and CAN remain immediate. ASCII C/G/U/W is held until two quiet
BIOS ticks, about 110 ms, distinguish a raw control from uninterrupted text.
An intervening byte discards the candidate. ANSI CSI, terminal strings and
charset selections suppress embedded control letters; their state survives
individual native read timeouts and is cleared on every transfer notice.
G retains the native non-streaming CRC policy; U/W remain explicit unsupported
protocol paths. No data-byte filter runs after handshake selection.

One native one-second startup request retains a 19-tick bound, with at most
two extra ticks to settle a candidate arriving near its end. Local Escape,
Alt-X, carrier loss, receive overflow and the existing whole-owner progress
deadline remain serviced. Noise does not count as accepted transfer progress.
Arbitrarily paused plain-text handshake letters remain ambiguous on XMODEM's
unframed startup channel; this does not claim universal banner parsing.

The filter executes in CONFIG_CODE because the resident code segment is full.
Two small far bridges enter the real UART reader and serviced transfer owner.
Fault unwinding runs with the native resident CS active. The new build retains
DS=SS at 64,832 bytes; resident code is 65,534 bytes, leaving two bytes.

[The component receipt](validation/terminal-upload-startup-fixed.json) binds
build `3b0deeeb`, a failing sixteen-case baseline using `54d53c72`, and:

- 43 linked startup cases, including CRC/checksum, ANSI sequences split across
  read timeouts, native U/W rejection, peer CAN, deadline/carrier/overflow/local
  cancellation, low-word wrap/midnight and reuse after an unfinished OSC.
- 54 ordinary upload, 37 packet-boundary cancellation and 44 receive regressions.
- Three actual DOS tests with independent receiver banners and withheld
  handshake. No packet may be emitted during banner display; subsequent exact
  data, padding, EOT NAK/ACK, parser/keyboard use and hardware restoration pass.

The retry-counter regression now freezes its synthetic BIOS clock only after
the first physical packet begins, so startup can settle before isolating the
original fifteen-attempt bound. The former frozen-clock failure is retained
under ignored build storage; it is not treated as a product compatibility fix.

Use the pinned Nix environment:

```sh
./tools/dev --command python3 standalone/check_terminal_upload_startup.py
./tools/dev --command python3 standalone/test_terminal_upload_startup_dos.py \
  --sha256 SHA256_OF_TERMINAL_EXE --label FRESH_LABEL
```

A fresh actual audio attempt is running at
`build/bbs-lab/synthmodem-synchronet-retry-startup-audio-01`. It deliberately
retains the original early second Alt-S sequence that failed with the older
binary, with fresh remote names and the same local source for both attempts.
Audio startup acceptance remains pending; the component receipt alone does
not establish it. Physical Boca/SPA2102 testing and the full application
inventory remain separate requirements.
