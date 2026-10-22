# Checked live text capture

The [external canonical reservation interface](CAPTURE_RESERVATION.md) now
protects future recorder target/scratch identities before capture or another
sink opens or truncates them. Independent paths retain concurrent foreground
use. The recorder's publisher and UI are still pending; older capture receipts
below retain their original binary and state-size scope.


The maintained DOS terminal now connects the recovered132-byte resident09b6
logger to a source-built DOS file owner. This implements processed text capture,
append, pause/resume and checked shutdown. The complete F10 gate also requires
raw monitoring, complete screen-snapshot modes, printer output and script
integration; those surfaces remain open. A maintained checked
[Alt-G screen-file path](LIVE_SNAPSHOT.md) now works alongside text capture.
[Native inventory](CAPTURE_NATIVE_INVENTORY.md) records the
REA evidence, original key routes and differences between those surfaces.

Build with `./tools/dev --command python3 standalone/build_terminal.py`, then run
`build/terminal/TERMINAL.EXE` in DOS with the desired existing serial options.

| Key | Behavior |
| --- | --- |
|Alt-F1|If closed, prompt for a DOS83 path of at most63 characters; empty Enter uses `PCPLUS.LOG` in the current directory. Escape cancels without file IO. If open or held, flush and close.|
|Alt-F2|Flush pending text and toggle hold. Inactive requests do nothing. Held bytes are omitted; resume adds no marker.|
|Alt-F3|Toggle the original CR-adds-LF option. This also changes the native terminal newline behavior.|
|Alt-X|Normal terminal exit flushes/closes capture after restoring serial hardware.|

Successful actions show `Capture open`, `Capture hold` or `Capture closed` using
the existing temporary connection-notice window. Incoming output restores that
window. A denied filename/open shows `Capture denied` and leaves the terminal
usable. There is no permanent capture dashboard or complete original status UI.
The filename prompt owns the bottom two rows and restores their cells, cursor
and shape. It services modem, flow and pending transmit work while awaiting a
local key. Receive parsing waits until the prompt closes; a full RX ring takes
the existing overflow cleanup path. Opening during another foreground owner or
an incomplete modem connection is refused.

## Bytes and file ownership

The recovered logger still selects the bytes: it skips FFh and DEL7Fh, omits CR
with CR-adds-LF disabled, and turns CR into LF when that option is enabled.
Delivered LF becomes CRLF in the maintained text layer, reproducing the
original text-mode lower writer's conversion. Consequently CRLF input with
CR-adds-LF enabled produces two CRLF pairs. ANSI commands, modem responses and
binary transfer bytes do not pass through this processed-character sink. This
is not a raw wire transcript. No timestamps or generated session headers are
added. Local capture UI does not enter the log.

`capture_file.c` uses a96-byte ownership/result record and DOS kernel IO without
native CRT FILE pointers. Existing writable regular files open write-only and
seek to end on that same handle. Missing files use exclusive creation; an
intervening creation fails without truncation. Device names, directory paths,
wildcards, traversal and invalid/overflowing near spans are rejected. Existing
bytes, including DOS1Ah EOF markers, remain byte-for-byte intact: the unresolved
native48a1/text-EOF behavior is not silently guessed. Append is nontransactional;
there is no rollback, concurrent-writer exclusion or crash-atomic guarantee.

Snapshot and raw-monitor files share this implementation through second and
third independent96-byte owners. All input guards protect all three records
and descriptors. Only the monitor owner admits explicit replacement, after its
Y warning; text capture and snapshots retain their existing append/new modes.
Checked DOS Truename admission prevents a text log and `PCPLUS.SCR` from opening
the same DOS file through different spellings; open/held and uncertain owners
retain that exclusion. The admitted absolute identity is used for open. This
requires DOS3 or newer and does not identify host mount aliases or lock out
external writers. Capture itself stays open/held during a separate screen save.

The256-byte application buffer flushes when full, after18 BIOS ticks, before a
hold/close/transfer, and at shutdown. Full BIOS day ticks handle low-word wrap
and midnight. Each write must accept the exact count. A short/error write
records the actual accepted prefix, disables capture and closes once. The native
special CR branch ignores its putc return, so the maintained sink itself must
also perform failure handling there. Ordinary native failure UI is deferred to
the next foreground notice; its paired viewport refresh is acknowledged without
enabling unrelated unrecovered viewport services.

Failure shows `Capture error`; partial output is retained. The terminal stays
connected. A genuine capture write/close failure remains sticky and normal
exit reports the existing storage-error level12, unless a prior terminal error
has precedence. This code is shared with transfer cleanup; the capture-specific
console message identifies a failed log. Rejected
opens that acquired no handle do not become shutdown write failures. A close
whose outcome is uncertain cannot be retried or reset into a new file. A resolved
failed file may be followed by a new capture, while the earlier session failure
remains observable at shutdown.

Before PROGRAM executes a child, capture flushes/closes so the child cannot
inherit or mutate its handle. An uncertain close cancels the pending child.
Capture remains closed on return; reopening is explicit. This is maintained
ownership policy, not a claim about the original PROGRAM's handle inheritance.
Binary transfers retain the processed log owner but flush it before acquiring
the serial protocol; their payload and framing never reach the text logger.

## Verification

```sh
./tools/dev --command make test-capture-file test-capture-session
./tools/dev --command python3 standalone/check_terminal_capture_live.py
# Actual UART/keyboard/DOS filesystem suite; use a fresh label each time:
./tools/dev --command python3 standalone/test_terminal_capture_dos.py \
  --sha256 SHA256_OF_TERMINAL_EXE --label MY_RUN
```

The separate suites cover actual8086 DOS file ownership, compiled kernel
faults, text buffering/state, and actual linked native logger/UI/PROGRAM code
with only hardware/kernel boundaries modeled. The independent DOSBox-X suite
uses real BIOS hotkeys, UART DSR replies, exact output files and before/after
UART/PIC/vector snapshots. Successful login, normal exit or correct wire bytes
alone cannot establish capture correctness. Public validation records retain
their binary/source hashes and narrower scopes.

The first live run exposed a rejected-readonly-open shutdown bug, subsequently
fixed by cleaning up only acquired/uncertain owners. It also showed that reading
the host file while DOS still has it open is an unreliable periodic-flush
oracle. DOSBox-X's local-file writer uses buffered `fwrite`; its
[upstream implementation](https://github.com/joncampbell123/dosbox-x/blob/dosbox-x-v2026.07.02/src/dos/drive_local.cpp)
does not necessarily expose those bytes to another host reader immediately.
The independent periodic test therefore records actual DOS write/close calls
with a source-built tracing TSR and verifies their BIOS-tick separation. The
original failed host-visibility observation is retained separately. No commit,
fsync, power-loss durability or physical CF timing is claimed.

Printer-device errors, screen/shadow snapshot formats, raw monitoring, full
capture settings/status UI, ASPECT commands and physical DOS/Wi-Fi validation
remain required work. The native inventory identifies their concrete next code
and ownership dependencies.
