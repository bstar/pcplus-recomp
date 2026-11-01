# A bounded stock ENiGMA screen comparison

The [independent ANSI matrix](ANSI_REFERENCE_GEOMETRY.md) now has an additional
stock-BBS checkpoint: one complete ENiGMA editor frame matches all1920
character/attribute pairs and the actual cursor response after48092 delivered
bytes. The DOS application remains the unchanged `c41df22f...` candidate.
This is one final-frame comparison, not acceptance of every BBS screen or
every intermediate editing state.

Two problems in the older fixture prevented an honest whole-frame comparison.
Its proxy adapter advertised25 rows even when the binary had24 terminal rows.
Its downstream capture also included text produced during hangup, after the
terminal stopped rendering. Replaying all of that output against the final
screen compared different boundaries. Those older navigation results retain
their narrower scopes; they are not relabelled as rendering failures or passes.

The Python proxy orchestrator now reads the initial geometry words directly
from the validated source-built MZ and its link map. It requires coherent
columns, row count, last row, margins, erase extent and status ownership before
advertising the dimensions. The current application yields80x24; the older
directory-script control still yields80x25. Both binary/map hashes and file
offsets are recorded. No application code is executed by this geometry read.

The optional `--screen-reference` mode is specific to the existing unsaved
editor workflow:

1. The owned proxy forwards the real login/menu/editor interaction, with the
   existing250ms key framing and20ms input-byte pacing.
2. After actual input `UNSAVED` reaches the proxy, it waits750ms without new
   downstream output, holds later output, and sends one actual CSI6n query.
3. DOS must return a real CPR. That proves its ordered parser consumed the
   complete delivered prefix through the non-rendering query.
4. The ordinary queued Alt-X ends the application. The DOS sampler captures
   the screen; held later output cannot change it. The held bytes are retained
   separately, not silently removed from an accepted stream.
5. The audit requires exact equality between the prefix, proxy serial output
   and modem's delivered bytes, and verifies the prefix hash, producer proof,
   raw CPR, snapshot hash and hardware restoration before cell comparison.

The reference uses the same pinned pyte/wcwidth modules as the ANSI matrix.
One exception is explicitly projected out: `CSI 0;0 SP D`, ENiGMA's default
CP437 font probe. [ECMA-48 §8.3.53](https://ecma-international.org/wp-content/uploads/ECMA-48_5th_edition_june_1991.pdf)
defines FNT separately from cursor movement. The pinned server's
`core/ansi_term.js` maps CP437 to font0, and `core/connect.js` emits this probe.
Pyte0.8.2 incorrectly dispatches it as cursor-back with two parameters. The
audit records its original offset491 and exact seven bytes; no other bytes
are removed or rewritten. Other intermediate controls and other font choices
refuse this reference path. Font glyph pixels remain unverified.

The accepted capture reports CPR9;8, zero differing cells, one declared font
projection and919 held later bytes. Six copied-capture controls accept the
unchanged frame and reject character, attribute, cursor, prefix and unsupported
font mutations. The character/attribute controls each produce exactly one
differing cell; the cursor control retains matching cells but fails CPR.
Controls modify declared copies of artifacts; they never execute or alter DOS
binaries, the original positive capture or a BBS session.

The fixture uses one synthetic account and a shared server log. A kernel file
lock now prevents overlapping sessions through this orchestrator. A second
attempt during the accepted run fails before creating a proxy; a subsequent
ordinary run verifies release. Initial overlapping attempts are preserved and
excluded from acceptance. The ordinary run keeps output unfrozen and retains
the authentication/editor/directory-preview checks.

Commands, using a fresh label and the already-running owned stock fixture:

```sh
./tools/dev --command python3 lab/bbs/test_synthmodem_proxy_dos.py \
  --runtime /home/bstar/projects/synthmodem \
  --terminal build/terminal-directory-adopt-334c0b8bd7e1/TERMINAL.EXE \
  --label YOUR-LABEL --byte-delay-ms 20 --framing-ms 250 \
  --directory-preview-overlay --screen-reference
./tools/dev --command python3 lab/bbs/audit_screen_reference.py \
  --output build/bbs-lab/results/enigma/YOUR-LABEL \
  --bridge build/bbs-lab/YOUR-LABEL-proxy
```

See [the receipt](validation/enigma-screen-reference.json) for source and
capture hashes. Source-only package reproduction is inherited only for the
unchanged exact ten-file package recorded by the geometry checkpoint. No live
BBS, SynthModem service, ATA, host network or removable card was changed.
Full rendering across peers/profiles/screens, font pixels, sustained traffic,
transfers, unframed/SIP/DSP paths and physical Boca/SPA2102/card acceptance
remain open.
