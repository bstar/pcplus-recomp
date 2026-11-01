# Saved call-log startup policy

`phone_log_startup_configure` now connects the accepted PRM enable word to the
checked queue's fixed absolute destination. It is a source-built DOS service;
it is **not yet called by the terminal application**. Parent banking/startup,
connection events, foreground polling and visible error/retry handling remain
required before this becomes a working application call log.

The service consumes the already accepted1264-byte image, without reopening
its filename. Any nonzero WORD at01E6 enables logging; zero requests disable.
Disabled logging ignores the environment and log-file paths. An active or
pending queue may refuse disable or retarget; startup never drops its events.

Enabled selection follows an explicit maintained policy:

1. An existing current-directory `PCPLUS.FON` wins, even with an invalid or
   unavailable environment. A read-only or nonregular current object refuses
   rather than silently selecting another file.
2. Only file-not-found permits inspecting the inherited `PCPLUS` directory.
   Missing/empty means current-directory creation later; a valid value selects
   that directory. Malformed/oversized values refuse. This reuses the existing
   bounded PSP/environment resolver and its first-match rules.
3. DOS canonicalization must produce an absolute, bounded DOS83 path. The
   selected parent directory is also checked explicitly, so a filesystem
   reporting the same error for a missing leaf and parent cannot admit a
   nonexistent destination directory.
4. The checked queue retains that absolute identity. No log file is opened,
   created or written during configuration; later explicit events and polls
   perform persistence. Changing CWD afterward cannot redirect accepted data.

This is deliberately stricter than the original resolver's fallback after any
failed open. Metadata checks do not guarantee a later write will succeed;
the existing checked append/retry/recovery policy remains necessary. Drive
remapping and concurrent external namespace replacement are outside this
startup policy. The service returns bounded path/resource/filesystem statuses
or `PLS_QUEUE_BASE + PLQ_*`, preserving the queue's refusal category.

## Native evidence

Both near and far-data queue builds pass16 actual8086 DOS cases each:
1,150 assertions across32 workflows. They cover disabled logging, current-file
precedence over malformed/valid environments, current and environment-selected
creation, nonzero enable values256/65535, read-only/directory objects, missing
parents, invalid/oversized environment values and truncated/wrapping inputs.
Active-call cases refuse retarget, disable, invalid environment and truncated
settings without changing the queue; its original records still commit to
the original file afterward.

The tests compare exact log bytes and all selected/unselected DOS-visible
paths, preserve the PRM image and20 JFT entries, require DS=SS, and restore the
independently sampled42-byte UART/PIC/vector state. They change CWD before
events/polls and verify no log appears there. Emulator attribute sidecars are
excluded from the DOS-visible filename comparison but remain hash-bound
artifacts. No original executable, installation or REA database is an input.

A clean export of24 public source files reproduces both executables and all
sixteen normalized objects byte-for-byte, then repeats all32 DOS workflows.
Two queue files in the working tree contain a separate pending reservation
guard. The proof explicitly exports their committed public versions instead;
its optional source-difference allowance applies only to those two files and
does **not** relax any executable/object equality. The tested default build
does not enable that guard. This checkpoint neither stages that separate work
nor establishes capture-reservation integration.

```sh
./tools/dev --command python3 standalone/build_phone_log_startup.py \
  --output build/YOUR-STARTUP-BUILD
./tools/dev --command python3 standalone/test_phone_log_startup_dos.py \
  --build build/YOUR-STARTUP-BUILD --output build/YOUR-STARTUP-TEST
./tools/dev --command python3 standalone/prove_phone_log_startup.py \
  --build build/YOUR-STARTUP-BUILD --output build/YOUR-STARTUP-PROOF \
  --commit e6f5a77 --allow-queue-reservation-source-difference
```

Use fresh output directories. The [receipt](validation/phone-log-startup.json)
binds source, objects, executable, native and clean-export evidence. Earlier
failed builds/tests remain local: a diagnostic pointer conditional triggered a
strict compiler warning, initial path-validation polarity was corrected, and
the initial batch failure marker was created by conditional redirection even
on successful cases. The accepted final run and public export include those
corrections.

The application, its package and card are unchanged. This closes the selected
startup service's component checks, not F07/F10 or whole-application acceptance.
Next place the service in the logger bank and call it from the real startup
owner using the accepted image; then integrate complete connection lifetimes,
UART-aware polls and user-visible failures before physical/card deployment.
