# Existing call logs and rollback in the terminal

The later [startup and I/O checkpoint](PHONE_LOG_STARTUP_IO.md) adds existing
writable files before startup, commit retry and protected failed rollback.
This page retains its original after-startup seed boundary.

The optional call-log controls image now has application-level tests for
appending to an empty file, preserving earlier call rows, and seeking beyond
64KB. Two additional cases perform real partial DOS writes and verify rollback
before a confirmed retry. The application image is unchanged; this checkpoint
extends acceptance evidence rather than altering the logger.

## Five actual DOS workflows

`standalone/test_phone_log_events_terminal.py --existing` runs a separate
matrix with the full terminal, its real UART/main loop, menu and shutdown.
The fixtures use owned synthetic files, not a user's call history.

- An existing zero-length file gets one heading and one complete call pair.
- A file containing a heading and an older call retains every earlier byte
  and receives exactly one new pair, without a duplicate heading.
- A file with 900 older rows (over64KB) retains its entire prefix and appends
  at the full DOS EOF position.
- A short write physically appends seven of the requested64 START bytes.
  The application seeks, truncates, commits and closes the same file, then
  displays retry status. An owned serial callback verifies the physical file
  equals its original prefix before the operator acknowledges R/Y.
- An explicit write error follows a real seven-byte append to the larger
  file. Rollback across the64KB boundary restores the original file exactly;
  confirmed retry saves the original START and subsequent END once each.

These seeds are installed after startup and before CONNECT, exercising the
backend's existing-file path. Startup with a preexisting destination, file
attributes/sharing and concurrent external writers need separate coverage.
The backend does not parse or repair an earlier incomplete call row.

Both fault cases require three append attempts, one real rollback truncation,
three commit calls and three closes. Passive samples before acknowledgement
bind the retained START payload and original producer timestamp to the final
saved row. No menu keys leak onto the serial link. The same hardware snapshot
and interrupt-vector restoration checks as the earlier matrix remain active.

## Fault fixture boundary

`standalone/phone_log_write_fault.asm` installs a separate DOS interrupt fixture
before the passive observer. It matches only the exact owned `D:\PCPLUS.FON`
path, tracks its open handle, and relinquishes that number at close so later
DOS handle reuse cannot contaminate the counters. It asks DOS to write seven
bytes on the first nonzero write, then returns either the real short count or
error5 with carry set. Later writes, rollback, commit and close use real DOS.

This deliberately modifies DOS call behavior. It does not modify product
variables, patch the executable, synthesize terminal replies or simulate a
physical failing disk. The observer remains read-only; the serial callback
checks the owned host file before any retry acknowledgement.

## Reproduction and limits

The [receipt](validation/phone-log-existing.json) binds the accepted native
matrix, the unchanged image, a committed-source export, its exact rebuild and
its five repeated workflows. Nineteen prior menu/disk cases also pass both
locally and from that export. The earlier four disabled-variant controls
retain their separate [controls receipt](validation/phone-log-controls.json);
this checkpoint does not claim fresh runs of all disabled combinations.

Image: `build/terminal-phone-log-bank-3d164fda0202/TERMINAL.EXE`.
SHA256: `2c5f5fc4dd4b9948b897db6499e920f694f30fbbbcdf3d1fb0596cbc921027f7`.

```sh
./tools/dev --command python3 standalone/test_phone_log_events_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --label existing-check-01 --existing
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --output build/phone-log-existing-public-repeat-01 --commit 7179390
```

Use fresh lowercase labels and output directories. The initial short-write
fixture's reused-handle counter failure is excluded; the accepted final run
uses the corrected fixture and checks original payloads before retry.

Slow I/O, commit/rollback failures and unrecoverable media errors remain open
at application level. The existing uncertain-close case still refuses retry
and requires external inspection. Sustained data/protocols, carrier/child/
ASPECT/exception composition, broader menu and feature variants, every-frame
BBS rendering, full F01–F16 behavior and physical Boca/SPA2102 acceptance are
not closed. The published BBS package and card are unchanged; no live BBS,
installed bridge, ATA or host network settings were altered.
