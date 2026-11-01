# Log startup and failed rollback in the terminal

The optional call-log controls image now has five startup workflows with
existing writable logs and three commit/rollback failure workflows. The image
is unchanged. These tests extend the earlier
[existing-file checkpoint](PHONE_LOG_EXISTING.md); they do not close full
F07/F10, transport, rendering or physical acceptance.

## Files present before startup

The `--existing --preexisting` matrix places each owned synthetic log in the
DOS working directory before launching the application. A callback at the
first dial command independently checks that startup preserved those bytes
before the peer supplies CONNECT. The tests then exercise:

- An existing empty file, which receives one heading and one call pair.
- An existing heading and prior call, preserved exactly before one new pair.
- An existing log over 64KB, with its entire prefix preserved after append.
- A real short write, successful rollback and confirmed retry.
- A real partial write followed by an explicit DOS error on the larger log,
  successful rollback across 64KB and confirmed retry.

Both retry cases compare passive samples of the original START payload and
producer timestamp with the final saved row. Startup remains read-only, and
there is one heading, no duplicate call and no invented timestamp. This is
writable regular-file coverage; read-only attributes, sharing and external
replacement/concurrent writers remain separate requirements.

## Three I/O failure workflows

`--io-failures` also seeds a log over 64KB before application startup. It uses
the exact same application, owned serial peer and real menu input:

- **Commit failure with successful rollback:** the first 64-byte START is
  physically written. The fixture returns error 5 for its commit request.
  Real seek/truncate/commit/close restore the original file. An independent
  callback verifies those bytes before R/Y acknowledgement; the original START
  and subsequent END are then saved exactly once.
- **Rollback truncation failure:** seven START bytes are physically written,
  then the fixture returns error 5 for truncation. The physical file retains
  exactly its old prefix plus those seven original START bytes. The terminal
  latches recovery, retains START and pending END, refuses R/Y retry and denies
  generic PROGRAM handoff. Shutdown performs no blind retry and exits 12.
- **Rollback commit failure:** seven START bytes are written and real
  seek/truncate restores the original length. Error5 is returned for the
  rollback commit request. Although the visible bytes equal the old file,
  durability is uncertain: recovery stays latched, records remain protected,
  R/Y and PROGRAM are refused, and shutdown exits 12 without another attempt.

The safe retry case requires three append attempts, one truncation, four
commit attempts and three closes. Each recovery case requires one append
attempt, one truncation attempt, one close and zero acknowledgements. Actual
video-memory frames witness the protected recovery text; the exact serial
oracle prevents local menu keys from leaking onto the BBS connection.

## Fixture and reproduction boundary

The separate `phone_log_write_fault.asm` fixture tracks only the exact owned
log path and relinquishes a handle number when it closes. Partial/full data
writes and successful rollback operations use real DOS. Selected failed
commit/truncate requests return error 5 without performing that operation.
This is an explicit DOS-call model, not evidence of physical failing-media
behavior. It does not patch application variables or executable bytes.
The separate passive observer checks state, video and restored vectors.

The [receipt](validation/phone-log-startup-io.json) binds the final eight native
cases and a clean public-source replay. That export rebuilds the exact image
and also repeats the five earlier existing-file cases and 19 menu/disk cases:
32 public DOS workflows altogether. No original executables, installations,
previous objects or REA database are build inputs. Earlier native probes are
excluded from the final receipt.

Image: `build/terminal-phone-log-bank-3d164fda0202/TERMINAL.EXE`.
SHA256: `2c5f5fc4dd4b9948b897db6499e920f694f30fbbbcdf3d1fb0596cbc921027f7`.

```sh
./tools/dev --command python3 standalone/test_phone_log_events_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --label preexisting-check-01 --existing --preexisting
./tools/dev --command python3 standalone/test_phone_log_events_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --label io-failures-check-01 --io-failures
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --output build/phone-log-startup-io-public-repeat-01 \
  --commit 97a4e92 --extended
```

Use fresh lowercase labels/output directories. The earlier disabled-variant
receipt keeps its own boundary; this checkpoint does not repeat all feature
combinations. No automated reconciliation of uncertain files is supplied.
Permissions, slow I/O, sustained traffic/protocols, carrier/child/ASPECT and
exception composition, all rendering frames/profiles and full F01–F16 behavior
remain open alongside physical Boca/SPA2102 and card deployment. The published
BBS package, card, live BBS, installed bridge, ATA and host network are unchanged.
