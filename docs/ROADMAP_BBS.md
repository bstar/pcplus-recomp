# BBS calling roadmap: Boca 14.4 → SPA2102 → SynthModem → BBS (2026-11-25)

This is the working plan for long autonomous sessions. It sets priorities; it
does not replace the evidence documents it links. `PLAN.md` remains the history
log and `docs/FEATURES.md` remains the parity matrix.

## North star

The user's own DOS PC runs the source-built PCPlus. It dials through the Boca
14.4 ISA modem (COM3, `3E8h`, IRQ5) and the SPA2102 ATA to SynthModem, reaches a
BBS from `CONNECT>`, and then:

- logs in;
- reads ANSI menus and messages;
- edits a message;
- downloads and uploads files with ZMODEM (and the other protocols BBSes still
  offer);
- hangs up and redials, repeatedly, without restarting.

The menus, setup and dialing directory a caller uses for this must behave like
PCPlus 2.01. Everything else (Host mode, rare emulations, remaining ASPECT
builtins) ranks below this experience.

**Done for the whole roadmap** means every row of
[the hardware acceptance record](HARDWARE_CONNECTION_TEST.md) reads **pass**,
filled from real observations on the user's hardware, using a package that
reproduces from committed sources.

## Where things stand

| Area | State | Evidence |
| --- | --- | --- |
| Physical connect + reach ENiGMA | User-confirmed with the source-built package | `HARDWARE_CONNECTION_TEST.md` |
| Line rate on hardware | 2400 (V.22bis, native fallback); the high-rate backend times out in negotiation | `BOCA_COMMISSIONING.md` |
| ANSI / CP437 rendering | Strong in emulation; ids 2..11, DEC graphics, VT52 and modern CSI are opt-in and **not yet in any package** | `ANSI_FAMILY_PROFILES.md`, `VT52.md`, `BBS_CSI.md` |
| ZMODEM / X / YMODEM | Pass in DOSBox against independent peers. One automatic ENiGMA download passed over software audio at 1200. | `TRANSFER_RELEASE_READINESS.md`, `LIVE_ZMODEM.md`, `ANALOG_MODEM_INTEGRATION.md` |
| Uploads, cancel, >64 KiB over audio | Open | same |
| Editor keys over audio | Counterexample: the caller sent 114 bytes and the guest received 126 | `lab/bbs/synthmodem-audio-dos.md` |
| Result codes | 11-slot matcher; no 14400/57600/115200 slots; generic CONNECT can win | `ANALOG_MODEM_INTEGRATION.md` |
| Alt-Z commands | 39 listed; several still dim in the qualified build (Dialing Directory live, Meta Keys, Host, Kermit server; Chat to verify) | `COMMAND_REFERENCE.md`, `src/redisplay/command_reference.c` |
| Dialing directory | Startup browser/editor and dialing; no live Alt-D directory during a session | `DIRECTORY*.md` |
| Setup | Mapped-field editor with staged replacement; not every original Setup screen and field | `SETUP_EDITOR.md`, `CONFIGURATION.md` |

## Priority order

Work the lowest-numbered goal that is not blocked. A goal that waits on a
hardware observation is **blocked**; prepare its hardware kit (see below), then
move to the next goal.

### P0 — hardware session readiness

**G1. Hardware candidate with the BBS-facing opt-ins.**
- **Work:** build the qualified flag set plus `--ansi-profiles --dec-graphics
  --bbs-csi` (and `--vt52` if it costs nothing measurable), then package it
  with `standalone/package_connection_test.py`.
- **Done when all of these hold:**
  - the package reproduces from committed sources;
  - the existing packaged DOS workflows and Enigma/Synchronet checks pass on
    it;
  - the default `e25e0bd7…` and qualified `7f5b3b03…` controls are unchanged;
  - an install note lists the exact files to copy and how to fall back to the
    current `C:\PCPLUS`.
- **Do not** write to the DOS card or the installed copy; the user installs.

**G2. Connect-result robustness for a real 14.4 modem.**
- **Work:**
  - add result slots and parsing for `CONNECT 14400`, `CONNECT 12000`,
    `CONNECT 9600`, numeric results and suffixes such as `/ARQ`, `/V42BIS`,
    `/LAPM` and `/REL`;
  - never let a generic `CONNECT` preempt a speed-specific match;
  - keep the fixed DTE rate when autobaud is off.
- **Done when:** emulated fixtures that replay the Boca's **actual** captured
  responses (from H1) pass. Each change is behind a flag or explicitly
  documented as an intended difference from the original.
- **Blocked on:** H1 for the real strings. Until then, build the parser change
  against the documented Hayes/Rockwell forms.

**G3. Login and editor fidelity over the real path.**
- **Work:**
  - reproduce the ENiGMA "unfocused login" report in emulation (or rule it
    out);
  - resolve the audio editor counterexample (114 bytes sent, 126 received) far
    enough to know whether PCPlus, the bridge or the DSP adds bytes.
- **Done when** the login and editor rows can be handed to the user with a
  specific expected result, and the cause of any software-side failure is
  fixed with a regression test.

**G4. ZMODEM over the real path.**
- **Bridge audit:**
  - SynthModem's `TelnetProxy.js` is documented as lacking an inbound IAC
    parser, BINARY negotiation and IAC escaping;
  - its single-byte `1D`/`1C` interception can eat transfer payload.
  - Confirm what the lab's patched bridge already fixes, then close the rest
    in the lab bridge, not in PCPlus.
- **PCPlus side:** download, upload, files over 64 KiB, an all-256-byte-values
  file, local and remote cancel, auto-download, and resuming after cancel.
- **Done when** every case passes over the software audio lab (DOS → DSP →
  bridge → real BBS), with exact SHA-256 matches, and a hardware kit for the
  transfer rows is ready.

**G5. Hangup, carrier loss and redial cycles.**
- **Work:** cover DTR drop, `+++ATH`, remote logout, bridge and SIP failure,
  and three back-to-back dial/login/logout cycles in one PCPlus process.
- **Done when** these pass in the audio lab, and the DCD caveats in
  `ANALOG_MODEM_INTEGRATION.md` (forced-high DCD, a DCD that never rises) have
  explicit tests and a documented recommended `AT&C1&D2`-style setup for the
  Boca, taken from its manual rather than assumed.

### P1 — menus, configuration and calling features

**G6. Live Alt-D dialing directory.**
- **Work:** open the directory mid-session, then:
  - select one or more entries (up to 15, as in the original);
  - dial with retry and cancel;
  - apply per-entry line, emulation, protocol, script and key settings;
  - update call accounting;
  - return to the terminal with the screen restored.
- **Done when** actual DOS tests cover queue, retry, busy/no-carrier and
  cancel, and Alt-D is no longer dim.

**G7. Setup facility completeness for calling.**
- **Work:**
  - inventory every original Setup screen and field (E2 Setup `0x46ae`,
    `CONFIGURATION.md`) against the maintained editor;
  - implement the missing fields that affect calling: modem command and
    result strings (including the G2 slots), the default protocol, download
    and upload paths, auto-download, the terminal profile (now 2..11), DTE
    rate and flow.
- **Done when** each field round-trips through the PRM, takes effect live or
  at next start as the original does, and has a test.

**G8. Dim commands that matter while online.**
- **Work:** cover Meta Keys (Alt-M), and Chat (Alt-O; verify it is reachable
  in the packaged flag set). Kermit server (Alt-K) follows G9.
- **Done when** each command works, has help, and passes an actual DOS test
  with a BBS screen behind it.

**G9. Transfer protocol inventory and the protocols BBSes still use.**
- **Work:**
  - list every protocol in the original's menus (E1 `0x26d8a..0x27119`);
  - mark which ones Synchronet, Mystic and ENiGMA offer today;
  - implement in order of BBS use. Likely 1K-XMODEM(-G), YMODEM-G and Kermit
    before the rest; confirm the order from the inventory.
- **Done when** each protocol passes the same independent-peer matrix as
  X/Y/ZMODEM.

### P2 — terminal polish seen on modern boards

- **G10.** REP (`CSI b`), SU/SD (`CSI S`/`T`), and iCE colours (blink bit as
  bright background, optional). See `BBS_CSI.md`.
- **G11.** TTY (id 0) as a configurable profile, and the VT52 keyboard table.
- **G12.** Long-session sustained display: five minutes or more of scrolling
  under receive load with no overruns. Use the UART counters.

### P3 — 14.4 line rate (bridge track, parallel)

**G13. V.32bis between the Boca and SynthModem.**
- **Work:** the native backend has no V.32/V.32bis, and the VM backend times
  out with this modem today. Steps:
  1. Collect H1 and H2.
  2. Decide from the Boca's documented V.8 / V.32bis support.
  3. Try the VM backend's direct V.32bis entry.
  4. Measure.
- PCPlus changes here are limited to G2. This is SynthModem, SPA2102 and lab
  work.
- **Done when** a real `CONNECT 14400` carrier holds long enough to pass G4 at
  14.4, or the reason it cannot is documented with evidence.

### Last

Host mode (F14) and the non-calling remainder of F01–F16, as in `PLAN.md`.

## Hardware loop (user + Claude)

Only the user can run the hardware. Claude prepares a **hardware kit** for each
blocked goal:

- the package path and SHA-256;
- the install and fallback steps;
- the exact settings to use;
- a numbered checklist of what to type;
- the expected observation for each step.

The user reports results in plain words, with photos, logs or `ATI` output
where asked.

After a report, Claude:

1. records the observations in `HARDWARE_CONNECTION_TEST.md`, keeping accounts
   and passwords out;
2. turns every failure into an emulated reproduction (DOSBox fixture, audio
   lab, or bridge unit test) before changing code;
3. fixes the failure, adds the regression test and prepares the next kit.

**Hardware facts still needed:**

| Id | Ask the user for |
| --- | --- |
| H1 | Boca identification: `ATI0`..`ATI7` (whatever the modem accepts), `AT&V`, the working init string, and the exact CONNECT line seen at 2400 |
| H2 | SynthModem log of one call (backend, modulation attempts, timeouts) and its revision/config, with addresses redacted |
| H3 | The DTE rate and flow setting in the working PRM, and whether the Boca has a 16550 UART |
| H4 | Results of each `HARDWARE_CONNECTION_TEST.md` row on the G1 package |

## How to run a goal (autonomous loop)

1. **Pick.** Choose the top unblocked goal. Write its acceptance checks down
   in the goal's doc before coding.
2. **Locate.** Read the linked docs, then the source. Recovered original code
   lives in `reconstruction/`; maintained code in `src/`. Behaviour changes go
   behind a build flag unless the goal says otherwise.
3. **Build.** Use `./tools/dev --command python3 standalone/build_terminal.py
   … --output-dir build/<new-dir>`.
4. **Test.** Use real DOS in DOSBox-X, 8086, with actual COM and a synthetic
   or audio peer. The relevant harnesses:
   - `standalone/test_connection_dos.py`;
   - `test_ansi_profiles_dos.py`, `test_bbs_csi_dos.py`, `test_vt52_dos.py`;
   - the transfer release harness;
   - `lab/bbs/*` for the audio path (`./tools/modem-dev --command`).
5. **Check controls** after every source change. The default minimal
   `e25e0bd7…` and qualified `7f5b3b03…` must rebuild byte-identically unless
   the goal intends a change. Refresh size-profile hashes when the build asks.
   **The known-good package is protected.** It is the
   `docs/validation/aspect-screen-package.json` set: TERMINAL `7f5b3b03…`,
   PRMEDIT `1c4ad063…` (`build_setup.py --custom-irq --chat-mode --mouse
   --notice-sound`), ASPECT `1a036988…` and the other members. Every member must
   still rebuild byte-identically from the working tree. New behaviour ships
   only as a separate candidate package, never as a change to that one.
6. **Document.** Each goal gets its own doc, a `FEATURES.md` row and an
   updated status line in this file.
7. **Report.** Give a short summary to the user. Move to the next goal without
   waiting unless a stop condition applies.

**Known traps** are recorded in Claude's project memory
(`pcplus-full-parent-test-gotchas`):

- new flags must reach the bank builders;
- full-parent fixtures need the PRM display words;
- near `_TEXT` and DGROUP are full, so new code goes in far segments with
  trampolines and strings keep their byte lengths;
- always run DOSBox under a timeout;
- keep `build/` small and delete scratch build directories.

## Stop and ask the user before

- committing, pushing, or opening a PR, unless the user grants a standing
  authorization below;
- installing anything, writing to the DOS card or `C:\PCPLUS`, or changing the
  live SynthModem service, SPA2102 or BBS configuration;
- any AUR package. Use official packages, then Nixpkgs (`AGENTS.md`);
- deleting anything Claude did not create;
- spending a long multi-agent workflow.

Also stop when a goal can only progress with a hardware fact (H1..H4).

**Standing authorizations** (the user edits this list):

- [ ] Commit completed goals to a local branch (no push).
- [ ] Restart the lab-only SynthModem VM (never the live service).

## Status log

| Date | Goal | Result |
| --- | --- | --- |
| 2026-11-25 | (pre-roadmap) | Ids 8..11, VT52 and `--bbs-csi` added as opt-ins; none packaged yet. Next: G1. |
| 2026-11-25 | regression check | Known-good package reproduces: TERMINAL `7f5b3b03` and PRMEDIT `1c4ad063` rebuild byte-identical; ASPECT sources unchanged; the other edits are flag-gated or expand to the original test. |
