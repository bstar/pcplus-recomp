# Checked ASPECT recording publication

The [publisher evidence](validation/recording-file.json) binds31 host-model
cases and16 actual DOS component sessions. The source-owned publisher writes
an unpublished sibling scratch file, closes it once, then installs the complete
ASP source. Positive DOS sessions compile that source with the maintained DOS
compiler and replay it through the production UART runner, including all256
byte values and a2048-byte payload.

This is a component checkpoint. The default terminal does not yet link the
publisher or expose its Record command. Foreground taps, owner exclusions and
code-bank integration remain required; all F01–F16 application gates remain open.

`src/recording/file.h` exposes begin, receive, transmit, flush, stop, cancel and
explicit cleanup operations. Initialize the owner to zero once. Callback and
public entries use far cdecl calls with near data arguments and DS=SS. The DOS
owner occupies326 bytes. The caller supplies valid strings/spans disjoint from
the mutable owner; this API does not validate arbitrary pointers.

`RF_NEW` refuses an existing target before recording and checks again before
publication. `RF_REPLACE` requires the caller's explicit choice. It preserves
the original throughout recording, then renames it to a free sibling backup,
installs the closed complete stage and removes the backup. A failed installation
attempts restoration. Existing scratch and backup names are skipped, with a
bounded256 attempts. Input names must be DOS8.3 paths ending in `.ASP`.

The canonical target is fixed at begin. Scratch and backup names are siblings
of that target, so changing the current directory cannot redirect publication.
The real DOS backend uses exclusive creation and kernel rename/removal. It
reserves target, prospective scratch and backup identities through the shared
[capture owner guard](CAPTURE_RESERVATION.md), preventing cooperative capture,
screen, monitor and history opens from colliding. Independent files remain usable.

Recovery is observable through phase, ownership flags and separate error fields:

| Condition | Retained state and action |
| --- | --- |
| Write failure or cancellation, certain close | Remove only the owned partial stage; release identities if cleanup succeeds. |
| Ambiguous close | Keep the handle uncertainty and claims. Never retry close or delete the stage automatically. |
| Complete stage cannot be installed | Keep the complete stage for inspection or explicit cleanup. |
| New installation and original restoration both fail | Keep the original backup, complete stage and all identities. Cleanup refuses to discard the original backup. |
| New target installed, backup removal fails | Keep the published target and original backup. Explicit cleanup can retry backup removal. |
| Reservation release fails | Keep the claim and recovery state; explicit cleanup can retry release. |

The first error stays primary. DOS errors, close/cleanup/publication/restoration
errors and reservation statuses remain separate. A counter-limit failure is
`RF_OVERFLOW`, with no fabricated DOS error. Cancellation can retain its primary
`RF_CANCELLED` return while cleanup fails; callers must inspect phase and flags.
Repeated stop after save performs no further IO.

The host cases inject short/zero/oversized writes, disk errors, ambiguous close,
rename/restoration/cleanup/release failures, reentry and the modeled32-bit
counter boundary. These are explicit models. Actual DOS sessions separately
exercise real file operations, shared owners, replacement, changed directories,
scratch collisions and deliberately raced-in targets. One fixture supplies a
real read-only DOS handle to provoke kernel write error5. The restoration race
preserves `ORIGINAL` in the backup and a complete stage alongside the raced-in
target. Each session checks DS=SS, INT0 and sampled UART/IRQ/PIC restoration.

The tests use owned synthetic media. They do not establish power-loss safety,
external-process locking, host inode identity, namespace remapping safety,
physical disk-full behavior or physical modem compatibility. Far signatures in
the component do not prove a distinct code-bank layout for the publisher.

Run fresh component campaigns with the pinned toolchain:

```sh
./tools/build test-recording-file
```

Next, place the implementation in the terminal's code banks, verify its ABI and
memory budget, bind foreground received prompts and successfully emitted user
or binding bytes, add Record UI/recovery notices, and enforce transfer, script,
child, setup, port-change and exit guards. Then test recording, DOS compilation
and replay from the actual foreground terminal before new BBS acceptance.
