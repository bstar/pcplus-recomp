# Terminal call-log startup binding

The optional `--phone-log-startup` application now invokes the checked
[startup policy](PHONE_LOG_STARTUP.md) after successful configuration loading
and setup binding, before the splash, mouse/UART acquisition or modem commands.
It copies the sealed accepted PRM image rather than reopening its filename.
With no explicit PRM, it disables logging without requiring a baseline or
reading a malformed `PCPLUS` environment value.

The new owner, policy and private bounded resource resolver execute in
`PHONE_LOG_CODE`. A zero-argument far entry is called directly from the real
startup path; there is no new resident callback trampoline. The existing
ten queue entries/eighteen callbacks and666-byte far owner are unchanged.
The memory inspector checks the new entry frame, actual near target, relocated
far call and bounded startup block. DS=SS, both63,000-byte histories and the
existing8KiB stack remain intact.

An admission failure has its own `Call-log setup failed` notice and the common
configuration exit status7. It must not report an unrelated serial/profile
error or continue to UART ownership. The detailed component status remains
available internally; no queued event or file is silently discarded.

## Actual DOS evidence

Seven full-terminal8086 workflows now cover:

- No explicit PRM and disabled logging despite a malformed environment.
- An explicit disabled setting, missing current-file creation policy,
  environment-selected destination and existing-current-file precedence.
- Malformed environment and missing parent directory, both rejected before
  UART ownership with the correct notice and no modem commands.

A separate passive INT1C observer derives the MZ load base from the actual
installed UART interrupt vector and reads the live status/queue. It performs
no DOS/UART calls, keyboard injection or product-memory writes in its handler.
It confirms the initialized cookie, enable flag, empty queue and exact absolute
path, including the value256/65535 settings. It restores its timer vector
before the independent hardware snapshot comparison. Successful runs also
exchange actual modem init/dial and ANSI replies, preserve the first banner,
leave settings/resources unchanged and create no log file. The unconfigured
case uses an actual direct serial session instead of modem commands.

The application is `build/terminal-phone-log-bank-bdfc66f3d712/TERMINAL.EXE`,
SHA256 `ed8006adb10c777737f5487853e91abbc833f5229e0721d56061364ea27dc58a`.
It retains64,560 bytes of near data/stack,976 bytes spare,22 resident-code
bytes spare and an8,331-byte logger bank. This is the existing full native-reset
bank variant, not the separately packaged directory-adoption BBS candidate.
No histories, stack or feature limits were reduced to fit it.

A source export containing 1,716 public files reproduces that exact executable and repeats
all seven native cases. It also builds the same feature-disabled terminal
from both the new and pre-feature public commits: both yield
`3fbb1acf887cb03d243dca35c758c79d05007e09a121ec602e94db9de888be15`.
The separate pending reservation source changes remain unstaged; the proof
declares their source differences and still requires exact executable equality.
It copies no original executable/install, old object or Git metadata.

```sh
./tools/dev --command python3 standalone/test_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-bdfc66f3d712 --label YOUR-LABEL
./tools/dev --command python3 standalone/prove_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-bdfc66f3d712 \
  --output build/YOUR-PUBLIC-PROOF --commit 58339e8 --baseline-commit 6c364f6
```

The terminal builder accepts `--phone-log-startup` with the existing full
baseline-enabled options; it implies `--phone-log-bank` and requires
`--session-baseline`. The proof derives those tested options from its manifest.
Use fresh result labels/directories. See
[the receipt](validation/phone-log-startup-terminal.json) for identities and
checks. The first link had a resolver object-name collision; the first native
attempt exposed incorrect error classification. Those attempts remain excluded.

This initializes the actual application's queue; it does **not** yet generate
connection events or run disk polls. The separate fixed-claim work must be
composed before live log writes, followed by full connection lifetimes,
UART-aware scheduling and visible full/retry/recovery handling. Full F07/F10,
the complete application, all feature combinations, physical Boca/SPA2102 and
card/deployment gates remain open. The published BBS package and card are
unchanged; no live BBS, bridge, ATA or host network was changed.
