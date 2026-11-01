# DOS call-log access and repair

The later [delayed-write checkpoint](PHONE_LOG_SLOW_IO.md) adds selected
IRQ-friendly stalls with paced serial traffic. This page retains its real
read-only access and repair boundary.

The optional call-log controls image now has four real DOS read-only workflows:
two at startup and two after startup. These use actual DOS attributes and a
real DOS child, rather than an invented filesystem error return. The application
image remains unchanged; full logging, transport and physical acceptance remain
open.

## Startup access

`test_phone_log_startup_terminal.py --readonly` installs an owned helper that
sets and verifies the existing synthetic log's read-only attribute before the
application starts. With logging enabled, startup fails with its existing
setup notice and exit code 7, before acquiring UART ownership or sending modem
commands. File bytes remain unchanged.

With logging disabled, the same read-only file and an invalid PCPLUS environment
are ignored. The application connects, replies and exits normally without
changing the log. The passive observer verifies the disabled queue and released
claim; the native hardware snapshot remains exact.

## Access changes during a call

`test_phone_log_events_terminal.py --permissions` starts with a writable existing
log. The attribute fixture observes the actual relative startup query, then
sets real read-only access at the first absolute query before START append.
The backend receives the genuine DOS attribute result and refuses the write.
It retains START and END, latches retry and leaves the original file unchanged.

One case opens the call-log pane, requests retry and cancels. It confirms one
failed append attempt, zero acknowledgements, the visible retry/confirmation/
cancellation messages and exit code 12 with retained data. There is no automatic
retry at shutdown.

The other case invokes a real DOS helper through the existing PROGRAM key.
That child reads the attributes, clears only read-only through DOS, reads them
again and records the before/after values. It returns to the same serial
session. An owned serial callback independently checks the physical log bytes
before R/Y acknowledgement. Closing the pane lets the foreground scheduler save
the original START and subsequent END exactly once. Passive pre-acknowledgement
samples bind the original producer timestamp and retained START to the saved
row. The three attempts are one refused append and two successful records.
Local menu keys stay off the serial wire; final hardware restoration is exact.

## Fixture and evidence boundary

`phone_log_attributes.asm` tracks only the exact owned absolute filename and
its current-directory spelling. It uses real DOS get/set attribute services;
application queries continue into DOS and get its actual result. The collector
records final attributes, restores the original test-file metadata and restores
and checks its interrupt vector after the passive observer is removed. Neither
fixture writes product variables or patches the executable.

The first probes incorrectly assumed startup used the absolute filename and
changed access too late. Those runs are excluded. The accepted final fixtures
recognize both spellings and change access before the first data append.
The separate `phone_log_clear_attributes.asm` is the actual child used for repair.

The [receipt](validation/phone-log-permissions.json) binds the four final native
cases and a public-source exact rebuild. That export repeats these four plus
32 earlier menu, existing-file, startup and failure workflows: 36 DOS cases.
The previous short-write and disabled-variant receipts keep their own scope.
No original executable, installation, previous object or REA database is a build
input.

Image: `build/terminal-phone-log-bank-3d164fda0202/TERMINAL.EXE`.
SHA256: `2c5f5fc4dd4b9948b897db6499e920f694f30fbbbcdf3d1fb0596cbc921027f7`.

```sh
./tools/dev --command python3 standalone/test_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --label readonly-check-01 --readonly
./tools/dev --command python3 standalone/test_phone_log_events_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --label permissions-check-01 --permissions
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --output build/phone-log-permissions-public-repeat-01 \
  --commit 2f1259c --extended --permissions
```

Use fresh lowercase labels and output directories. This is DOS read-only access
coverage, not network sharing, all filesystem permissions or concurrent external
writer/replacement acceptance. Slow I/O, sustained traffic/protocols,
carrier/child/ASPECT and exception composition, all rendering frames/profiles,
full F01–F16 behavior, physical Boca/SPA2102 and card deployment remain open.
Uncertain files still require external inspection. No published package, card,
live BBS, installed bridge, ATA or host network setting changed.
