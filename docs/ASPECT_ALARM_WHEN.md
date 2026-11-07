# ALARM foreground key ownership

An opt-in `ASPECT_ALARM_SERVICE` path now gives ALARM exclusive BIOS key
ownership while the actual WHEN C transport and foreground gates run. It
prevents the ordinary Escape-abort path and native key-ready adapter from
consuming the alert's completion key. This is a prerequisite for VM binding,
not a claim that the interpreter now executes ALARM.

The guarded begin rejects nested ownership, existing errors, deferred/parser
service, native monitor work, confirmation or an active parent window. End
rejects release from borrowed service/monitor contexts. Reset cannot silently
clear an outstanding lease. The owner must release explicitly after alert
cleanup, including after speaker-owner quarantine and recovery.

`runtime_when_alarm_poll` services the ordinary native WHEN safe point before
bounded receive work: at most64 receive leads or one BIOS tick per invocation.
Raw ASIO retains its unread bytes unless an active WHEN pattern consumes them;
the attached path admits the existing WHEN-before-display entry. Transport
continues polling the UART but leaves every key queued for ALARM. Error status
is retained; the service path does not fabricate a key to end the alert.

## Evidence and limits

The [receipt](validation/aspect-alarm-when.json) binds50 real-I/O emulator cases,
35 declared cold-source files and an exact reconstructed diagnostic. The cold
proof repeats normal completion, enhanced-key/software flow and speaker-owner
recovery; it does not repeat all50 cases.

The diagnostic executes actual `when_runtime.c` admission/key-ready/transport/
foreground gates around the [real DOS platform](ASPECT_ALARM_DOS.md), including
actual BIOS keyboard, DOS clock, banked PIT speaker and UART ISR. All508 payload
bytes arrive exactly per case across COM1/2 and four flow modes. Escape ends
normally, the following F1 remains queued, reentrant lease changes reject on
native-service callbacks, and failed speaker cleanup retains the lease until
explicit recovery. Deferred/monitor admission and unmatched release reject.

Native WHEN action bodies and the receive/renderer entry are modeled.41 cases
exercise raw gate preservation;9 enhanced-key cases use a modeled attached
receive entry that reads actual UART data, checks key ownership and the receive
burst bound. The original diagnostic consumer can read remaining bytes too.
This does not prove all508 bytes traverse the real translation/WHEN/parser path,
actual CALL/TRANSMIT/DISCONNECT action ordering, or full parent/VM integration.
Observed receive bursts need not reach the64-lead limit.

The emulator is muted. CTS stays ready and RTS is not enforced by nullmodem;
software XOFF/XON remains explicit. There is no acoustic, physical modem/SIP or
BBS acceptance claim. A rebuild of the ordinary interpreter remains byte-for-
byte identical because the feature flag is not enabled in its build. No package
or installed files were changed.

## Reproduction

Use new output directories in the pinned Nix environment:

```sh
./tools/dev --command python standalone/build_alarm_when_uart.py \
  --output build/my-alarm-when
./tools/dev --command python standalone/test_alarm_when_uart.py \
  --build build/my-alarm-when --output build/my-alarm-when-matrix
./tools/dev --command python standalone/prove_alarm_when_source.py \
  --build build/my-alarm-when --output build/my-alarm-when-cold
```

`make test-aspect-alarm-when[-source]` supplies the same diagnostic workflow.
The [compiler emission](ASPECT_ALARM_COMPILER.md) is already implemented.
Next bind the recovered operand wrapper and current parent sound/duration
settings, run actual WHEN actions/translation/receive rendering through the VM,
fund code without reducing capacities, and repeat parent memory and connection
gates. Physical acceptance and full parity remain open.
