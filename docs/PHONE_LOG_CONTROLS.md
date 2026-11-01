# Call-log status and confirmed retry

The optional `--phone-log-controls` terminal adds **Alt-Z → File → L: Call log
status / retry**. It implies the disk, event, lifecycle, startup and claim
options. This checkpoint adds selected application controls; full F07/F10,
whole-application and physical acceptance remain open.

## Using the pane

The pane shows the fixed destination, queued and committed record counts,
call generation, retained END state, and scheduler/file/DOS/close/rollback
errors. F5 refreshes the display; Esc returns through the existing menu.
Alt-X uses the existing protected exit path.

Press R to request a retry, then Y to acknowledge it. N or Esc cancels the
confirmation. An acknowledgement changes retained RAM state only: the pane
never writes a file or polls the disk scheduler. Close the pane to let eligible
foreground polls resume. The fixed destination, generation, queued payloads
and original event timestamps survive. A still-broken destination produces
one new failed attempt and latches again; it does not start automatic retries.
Healthy and disabled logging refuse unnecessary retries.

An uncertain close displays **Recovery required: exit and inspect the log.**
It preserves records and file ownership, refuses retry and prevents generic
PROGRAM execution from inheriting that ownership. There is no reset or
reconciliation command. A sticky event clock/input fault also cannot be
cleared by retrying a disk write: a missing event cannot be reconstructed by
inventing its timestamp.

## Image and memory boundary

Source commit: `3eb0b033247b677fe7353b3a84fd8c0082e7cfe4`.

Image: `build/terminal-phone-log-bank-3d164fda0202/TERMINAL.EXE`.
SHA256: `2c5f5fc4dd4b9948b897db6499e920f694f30fbbbcdf3d1fb0596cbc921027f7`.

This optional native-reset bank combination retains 64,752 near data/stack
bytes (784 spare), 65,530 resident code bytes (six spare), a 13,244-byte logger
bank and 65,029 CONFIG_CODE bytes. Both 63KB histories, the 8KB application
stack, 666-byte far queue and compiler/VM limits are unchanged. The four-word
far pane entry and all four relocated menu calls are inspected in the linked
image. Private scheduler/acknowledgement and pane state have complete
initialized DATA, with no nonempty BSS dependency.

The menu row follows every existing optional row. A source-table audit covers
all four directory/controls conditions, preserves every previous item index
and rejects the earlier incorrect insertion order. This is a source-table
check, not runtime acceptance of every reference-menu variant.

## Native DOS evidence

The [validation receipt](validation/phone-log-controls.json) binds 19 actual
8086 DOS cases in `controls-final-02` and 19 public-source repeats. The previous
13 disk cases remain covered: successful calls, hangup, failed dial/timeout,
redial, disabled logging, DIRECT, three-call reuse, flow settings, namespace
failure and healthy PROGRAM handoff. Six additional paths exercise:

- Healthy status inspection and refusal of an unnecessary retry.
- Repair of the owned test namespace, R/Y confirmation, then successful saving.
- R/N cancellation without an acknowledgement or disk retry.
- R/Y with the namespace still broken: one new failure, then a fresh latch.
- Uncertain close: refusal of retry and generic PROGRAM handoff.
- Disabled logging: no retry acknowledgement and no log file.

Actual video-memory frames witness the title, confirmation, acknowledgement,
cancellation and protected-recovery messages. The serial oracle requires exact
init/dial, terminal replies, the deliberate test input and hangup bytes; pane
keys do not leak to the BBS. Passive pre-acknowledgement samples independently
bind the retained original START payload and producer timestamp to the final
saved row in both accepted retry runs.

Uncertain-close coverage uses a separate, explicitly active DOS-return fixture:
it performs the real close of the exact owned test file, then reports error 6
with carry set to the application. It does not patch the executable or product
variables. The resulting file contains only the heading and START, while the
application retains START and pending END and refuses duplication. This is a
controlled kernel-return model, not a physical failing-media test. The passive
observer separately reads state/video and verifies restored interrupt vectors.

## Public reproduction

A clean export of 1,743 committed public files reproduces the exact executable
and repeats all 19 cases without original executables, installations, previous
objects or a REA database. Another 67 scoped regressions pass: 13 controls-off
disk cases, eight RAM-event cases, seven startup cases, three capture cases,
15 queue-claim cases and 21 producer cases/1,041 assertions.

Four disabled variants are byte-exact against baseline `fecd404`: disk without
controls, RAM events without disk, lifecycle without events and bank-only.
The receipt binds all eight current/baseline images. These controls establish
preservation of those variants, not acceptance of every feature combination.

```sh
./tools/dev --command python3 standalone/test_phone_log_events_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 --label controls-check-01
./tools/dev --command python3 standalone/prove_phone_log_startup_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --output build/phone-log-controls-public-repeat-01 \
  --commit 3eb0b03 --baseline-commit fecd404
```

Use fresh lowercase labels and output directories. Earlier pointer-type,
based-string and DOS-create-hook attempts are excluded; the accepted receipt
names the final image and both final runs explicitly.

## Remaining work

Existing-file application coverage, slow/error-I/O and rollback composition,
sustained traffic/protocols, carrier/child/ASPECT/exception paths and broader
menu/feature composition remain open. Uncertain files require external
inspection; automated reconciliation is not implemented. Every-frame BBS
rendering across profiles, full F01–F16 behavior and physical Boca/SPA2102
acceptance still require their own evidence.

The published BBS package remains the separate `c41df22f...` image. The card,
live BBS, installed bridge, ATA and host network were not changed.
