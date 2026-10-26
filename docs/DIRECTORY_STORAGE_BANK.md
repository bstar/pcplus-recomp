# Banked directory persistence — 2.01-LoC.6

The explicit `--directory-storage` candidate routes the terminal's actual saved
record and deferred accounting entry points through the shared canonical
[directory owner](DIRECTORY_STORAGE.md). Startup editing and post-UART accounting
use the admitted absolute target and recovery names. An open/uncertain binary
owner or existing external registration refuses conflicting writes.

The facade preserves original backend statuses 0–13 and adds OWNER 14 and
RECOVERY 15. A refused retry returns a fresh result with installed/recovery flags
zero. It cannot reuse a previous installed-warning flag to consume a new pending
count. Actual installation still updates the accounting baseline even when
backup cleanup or claim release fails. Canonical DOS errors remain visible.

The common DOS EXEC boundary now checks the directory owner before resize or
child execution. Unused/idle/resolved owners permit children. Active, held or
damaged state refuses without resetting ownership or changing the caller's
result. PROGRAM, ASPECT, setup, translation and HOOK use this same boundary;
filename claims alone cannot protect inherited handles after a failed close.

This is persistence and child-admission integration, not completed live
selection adoption. Alt-D still stages and previews; it does not change the
active selection or dial it. The full application plan remains open.

## Code and memory

The action facade and guard execute in CONFIG_CODE. Existing resident callers
retain their near-cdecl interfaces through 5/8-word entry adapters. Three
separately declared resident callbacks forward exactly 3/6/7 words to path
derivation, date/count patching and replacement. The older 1–4-word callback
family is unchanged. The validator checks all 99 configuration bridge pairs,
bank locations, far-call relocations and the EXEC zero-result refusal branch.
Damaged argument words, relocations and reversed admission reject.

The first integrated parent retained 407,312 bytes and failed nested ASPECT source
compilation with DOS error 8. The failed screen remains at
`build/directory-storage-start-final-20261026/drive/SCREEN.BIN`; it is not an
accepted result. Size optimization alone did not recover sufficient headroom.

The final parent lends the last 2,000 bytes of the inactive frozen history buffer
to Alt-G's complete character image. Snapshot refuses an active viewer/command
owner; the viewer already refuses an active snapshot. The separate live history
ring keeps its full 63,000-byte capacity, and every viewer opening rebuilds the
frozen image from that ring. The ASPECT window's separate full-screen buffer
remains independent. No stack, queue, history or screen capacity is reduced.

| Resource | LoC.5 | LoC.6 |
| --- | ---: | ---: |
| Near data and stack | 64,272 | 64,496 |
| Resident code | 65,506 | 65,142 |
| Resident spare bytes | 30 | 394 |
| Physical full-screen storage | 12,000 | 12,000 |
| Minimum retained module bytes | 405,520 | 405,312 |
| Live history / frozen image / Alt-G image | 63,000 / 63,000 / 2,000 | 63,000 / 63,000 / 2,000 |

## Acceptance

The [receipt](validation/directory-storage-bank.json) binds the final candidate:

- 36 linked accounting/controller inputs include actual bank adapters, deferred
 count/date handling, installed-warning consumption, a subsequent held retry
 with all old installed flags cleared, and EXEC refusal before DOS memory or
 child calls. Only calendar/canonicalization/replacement kernel boundaries are
 modeled; guard and shared registration logic execute normally.
- 45 directory inputs, 35 snapshot inputs, 84 reference inputs, 29 keyboard inputs
 and existing shared-screen restore/refusal cycles pass. Reciprocal snapshot/
 history lease refusals preserve all 63,000 frozen bytes; successful Alt-G followed
 by redisplay preserves and rebuilds the complete wrapped live ring.
- Real DOS8086 COM3/IRQ5 tests connect, persist exact accounting, edit/save in the
 startup browser, connect afterward and successfully run a small DOS child.
 Native file/registration diagnostics add 44 workflows/1,612 assertions across
 the core and terminal-facing facade, including close/rollback/cleanup/release
 faults and protection against duplicate installed accounting.
- Three actual DOS8086 Alt-G workflows check exact CP437 bytes, repeated append
 preserving an existing 1Ah prefix and simultaneous independent text capture.
 They verify cursor/status replies, subsequent keyboard input, screen colors,
 file bytes, private PRM and hardware restoration. The capture recipe explicitly
 declares its visible owned status row, ` Alt-Z FOR HELP`, from the maintained
 status label in `src/status/status_state.inc`; it does not silently omit that
 row from the byte oracle. Earlier blank-row/IRQ fixtures remain recorded.
- Packaged START performs nested source compilation and exact script replay;
 SETUP returns from the editor and captures the original magenta logo with
 the LoC.6 version note. Both preserve private fixtures and restore hardware.
- The stock ENiGMA editor route opens the directory preview, resumes Home/Insert
 editing and discards the draft with no post saved through the actual proxy at
 20ms input-byte pacing. This excludes SIP/DSP, analog and physical CTS/DCD.
- A clean 760-source export reproduces all ten package files. Six older ordinary/
 LoC.1–5 application controls retain their prior executable bytes. The same
 package and both component proofs pass from committed sources at `f6a86e8`,
 excluding pending telephone-log worktree changes.

The first parent fixture omitted the required mouse 8/4 settings and was rejected
by both LoC.5 and this candidate; the corrected fixture passes. The native serial
snapshot fixture takes the custom COM/IRQ from its PRM. An extra COM override
bypassed that saved IRQ in the first fixture; the corrected fixture preserves
the saved port. The independent IRQ/port UI and CLI policy remain separate work.

## Reproduce

```sh
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --custom-irq --directory-storage --output build/storage-NEW
./tools/dev --command python3 standalone/check_directory_actions.py \
  --binary build/terminal-directory-storage-276a15011380/TERMINAL.EXE \
  --map build/terminal-directory-storage-276a15011380/terminal.map
./tools/build test-directory-storage-actions
```

Use a new output/label for each retained run. The receipt identifies the accepted
staged package and executable. No removable card or live service is changed.

Next implement the quiesced selection owner: stage and claim profile/key/meta/
translation/script resources, verify baseline freshness, retire old accounting,
publish the new context and restore confirmed UART/profile ownership before
dialing. Original interface services, complete F01–F16, full ENiGMA workflows
and real Boca/SPA2102/card acceptance remain open.
