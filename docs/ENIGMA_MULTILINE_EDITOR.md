# Stock ENiGMA multiline editor

The owned ENiGMA fixture now has a native DOS input recipe for a draft longer
than its 14-row editor viewport. It enters 24 numbered lines, presses Page Up,
inserts `UPMARK` into document line14, and either stays on that page or presses
Page Down before typing `UNSAVED`. Disconnect leaves the draft unpublished.

This complements the earlier one-line editor-key and
[whole-cell snapshots](SYNCHRONET_SCREEN_REFERENCE.md). It exercises actual
multiline navigation rather than Page Up/Down at an empty document boundary.
The default keyboard helper still assembles to the same 480 bytes; only the
explicit `ENIGMA_MULTILINE` test variant includes the new key table.

The test retains the owned login/subject recipe, then waits for the actual
`KEYTEST` title and `INS 01,01` status before injecting BIOS keystrokes. A bounded
watchdog and normal Alt-X path restore its timer vector. No application RAM,
serial response, BBS editor state or return value is supplied by the helper.

`enigma_multiline.py` validates the actual key wire, the server's document
coordinates and the entire numbered viewport. Page Up changes `(25,1)` to
`(14,1)`. The edit advances to `(14,7)`; Page Down returns to `(25,1)`.
The final page-down viewport preserves `UPMARKR14` among lines12–24 and the
new unsaved line25. The page-up variant instead retains lines1–13 followed by
`UPMARKUNSAVEDR14`. Original login/editor/no-published-post checks remain
required; normal DOS exit alone never accepts a case.

SGR sequences can occur between `INS` and its document coordinates. The
validator accepts those exact intervening color controls, rather than joining
unrelated screen text by removing every control. The first attempt incorrectly
looked for an uninterrupted status field. Its native run completed but its
producer failed; it remains excluded from acceptance. Fresh runs use the
corrected validator.

The independent screen audit separately compares all1,920 character/attribute
pairs and the real final CPR against pyte after the complete delivered prefix.
Only the declared default-CP437 font probe is projected out; later output is
held until DOS exits. The fixture consumes its own real CPR reply, preserving
every other outgoing byte. This uses the same source-built DOS application,
80×24 terminal geometry and real installed SynthModem proxy as the earlier
checkpoint, with250ms key framing and20ms input pacing.

Both fresh runs pass: page-up compares87,181 delivered bytes at CPR`22;14`;
page-down compares88,160 bytes at CPR`22;8`. All1,920 raw character/attribute
pairs match in each frame. Both seven-case screen controls and the six-case
multiline semantic controls pass. The page-up case explicitly requires that
Page Down was not sent; its checked policy is not evidence of that key being
exercised in that run. The separate page-down case exercises both keys.

With the owned loopback fixture running, use fresh labels and run the two
sessions consecutively because they share one synthetic account:

```sh
./tools/dev --command python3 lab/bbs/test_synthmodem_proxy_dos.py \
  --runtime /home/bstar/projects/synthmodem \
  --terminal build/terminal-directory-adopt-334c0b8bd7e1/TERMINAL.EXE \
  --label YOUR-LABEL --framing-ms 250 --byte-delay-ms 20 \
  --screen-reference --multiline-editor page-down
./tools/dev --command python3 lab/bbs/audit_screen_reference.py \
  --output build/bbs-lab/results/enigma/YOUR-LABEL \
  --bridge build/bbs-lab/YOUR-LABEL-proxy
```

Repeat with `--multiline-editor page-up` and another label. The semantic-only
copied-artifact controls are repeatable with
`lab/bbs/check_enigma_multiline_controls.py --capture <page-down-result> --output <new-build-directory>`.
They accept the unchanged capture and reject missing page keys, a missing
numbered line, changed viewport content and a wrong document coordinate.
Whole-cell character/attribute/cursor/input-integrity controls remain separate.

See [the receipt](validation/enigma-multiline-editor.json) for measured
identities, assertions, capture sizes and results. Package bytes and the card
are unchanged. Two final measured windows do not establish every intermediate
frame, arbitrary-length drafts, other BBSes/emulations, all timings, font
pixels, saved posts, sustained transfers or physical Boca/SPA2102 acceptance.
The earlier [synthetic multiline reference differences](ANSI_MULTILINE_REFERENCE.md)
remain open within their own scope. No live BBS, installed bridge, ATA, host
network or removable card was changed.
