# Restarted ANSI sequences during upload startup

An ESC that interrupted an unfinished CSI, ESC or charset selection could let
the following C/G escape the ANSI filter and start a transfer before the
receiver supplied its handshake. For example, `ESC [ ESC [ 5 G` exposed G after
the second `[` incorrectly ended the old CSI state.

The filter now treats fresh ESC as the start of a new escape sequence in those
states. OSC/DCS string handling keeps ownership of ESC/ST, so an embedded CSI
does not end a string or become a handshake. NAK and CAN remain immediate;
settled ordinary C/G/U/W selection and all data-phase reads keep their policy.

The [six-case baseline](validation/upload-startup-ESC-restart-baseline.json)
binds executable `25701409` from the UI-banking source at `4c90c33`. Five cases
attempt transmission before the independent receiver's handshake at 60 modeled
ticks; the existing OSC/ST control case passes. The
[fixed receipt](validation/upload-startup-ESC-restart-fixed.json) records:

- All six linked restart cases now wait for that handshake and complete.
- Six actual DOS cases with withheld C/NAK verify no premature packet, exact
  source, CRC/checksum, EOT exchange, parser/keyboard recovery and hardware
  restoration. One OSC case spans a 1.3-second input pause.
- The existing 43 startup and 135 upload/receive/cancellation cases pass.
- All four builds retain validated UI bridges and code capacity.

The plain executable is `976ba8d0`; mouse, mouse/process and mouse/traps are
`6b7d66b0`, `4911b0ad` and `eb35c2d9`. Resident bytes free remain 624, 474, 474
and 944 respectively. DS=SS remains within 64 KB for each build.

```sh
./tools/dev --command python3 standalone/check_upload_startup_restart.py
./tools/dev --command python3 standalone/test_upload_startup_restart_dos.py \
  --sha256 SHA256_OF_TERMINAL_EXE --label FRESH_LABEL
```

The accepted audio workflow remains bound to the older `3b0deeeb` executable.
This receipt establishes the restart correction in linked and actual DOS tests,
not audio or physical hardware acceptance of the new binaries. Unframed,
arbitrarily paused plain-text handshake letters, receiver partial cleanup and
the broader application requirements remain separate.
