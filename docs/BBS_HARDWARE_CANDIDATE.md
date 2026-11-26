# BBS hardware candidate (roadmap G1)

This candidate is the qualified connection package with the BBS terminal opt-ins
turned on. It installs **beside** the current `C:\PCPLUS` in `C:\PCPLUSBB`, so
the known-good install is untouched and stays the fallback.

## What changes compared with the known-good package

| File | Known-good | Candidate | Why |
| --- | --- | --- | --- |
| TERMINAL.EXE | `7f5b3b03…` | `d59221a3…` | adds `--ansi-profiles --dec-graphics --bbs-csi --vt52` |
| PRMEDIT.EXE | `1c4ad063…` | `21dc7dc2…` | adds `--ansi-profiles` (profile IDs 2..11 in SETUP) |
| PCLINE.OVL, PCMETA.OVL, PCCOMP.OVL | — | rebuilt | linked against the new parent's map; must match it |
| README.TXT, START.BAT, SETUP.BAT, VERSION.TXT | — | changed | `C:\PCPLUSBB` paths, a BBS options paragraph and the new source identity |

ASPECT.EXE, ASPCOMP.EXE, XLTEDIT.EXE, PCKEYMAP.EXE, PCCHAT.OVL, PCHELP.RTE,
PCPLUS.HLP and LOCHELP.HLP are byte-identical to the known-good package.

What the opt-ins do:

- **SETUP terminal profile** accepts the ANSI-family IDs 2 through 11 ([details](ANSI_FAMILY_PROFILES.md)).
- **DEC line drawing:** `ESC(0` draws box characters.
- **VT52 mode:** `ESC[?2l` switches to VT52, and `ESC <` returns ([details](VT52.md)).
- **Modern CSI:** unknown CSI sequences are consumed instead of printed, for example SyncTERM's `ESC[=255h`. HPA, HPR, VPA and VPR are supported ([details](BBS_CSI.md)).

## Build

One command rebuilds every product from source and stages the package. It
reads no original executable, install or private configuration.

```sh
./tools/dev --command python3 standalone/build_bbs_candidate.py --output build/<new>
# payload: build/<new>/package/PCPLUSBB/
```

`--control` rebuilds the known-good package instead. It fails unless all 17
staged files match `docs/validation/aspect-screen-package.json` byte for byte.

## Install (the user does this; Claude never writes to the DOS machine)

1. Copy the `PCPLUSBB` folder to `C:\PCPLUSBB`.
2. **Copy** (do not move) your working `PCPLUS.PRM`, `PCPLUS.DIR`, `PCPLUS.KEY`,
   `PCPLUS.KBD`, `PCPLUS.XLT` and `PCPLUS.FON` from `C:\PCPLUS` into
   `C:\PCPLUSBB`.
3. Run `CD \PCPLUSBB` and then `START`. To edit settings, use `SETUP` or Alt-S.

**Fallback:** `CD \PCPLUS`, then `START`. Nothing in `C:\PCPLUS` changed.

Caution: if you change the terminal profile to anything other than 4 or 6 in
the candidate's SETUP, that PRM is refused by the known-good install. That
applies only to the copy in `C:\PCPLUSBB`; keep the two directories' PRMs
separate.

## Hardware checks to report back

For the Boca 14.4 on COM3/IRQ5, through the SPA2102 and SynthModem to your
board:

1. The call connects and the board's login and ANSI art look the same as with
   the known-good install.
2. Esc, arrows, Home/End and Delete in the board's editor behave the same.
3. A ZMODEM download completes (note the file size and whether the SHA-256
   matches).
4. *Optional:* in SETUP set the terminal profile to 2 (VT100). Redial and
   check that the board still renders, then set it back to 6.

## Software evidence (2026-11-25)

All runs are in DOSBox-X with no physical modem.

- **Package DOS workflows:** START splash, SETUP, Alt-P line, Alt-M meta,
  keymap editor and Chat/Help on COM3/IRQ5 with an 8086 all pass.
- **ENiGMA stock lab:** login, last callers, who's online and onelinerz with
  Escape, then Alt-X hangup and exit, pass on both the candidate and the
  known-good parent. Both produce the identical final screen and send the
  identical key bytes.
- **Opt-in harnesses:** `test_bbs_csi_dos.py` (profiles 6 and 4),
  `test_ansi_profiles_dos.py` (2, 9, 11, and the refusal of 12) and
  `test_vt52_dos.py` all pass on the candidate parent.
- **Known-good control:** `build_bbs_candidate.py --control` reproduces all 17
  files.

Lab harness notes:

- `lab/bbs/test_dos.py` needs `--config-fixture --full-parent-words
  --guarded-hangup-ms 500 --startup-keys 'enter p5000'` for a full packaged
  parent.
- Its ADDKEY token for Escape is `escape`, not `esc`. An unknown token
  silently drops the rest of the key script.

Not yet verified:

- the Synchronet lab session. Its pinned upstream development archive changed,
  and re-pinning waits for review;
- physical acceptance on the Boca/SPA2102/SynthModem path.
