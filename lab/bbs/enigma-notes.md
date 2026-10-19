# Owned game-details navigation

The owned board's exact `mods/loc_game_details/loc_game_details.js` and
`mods/black_flag_files/helpers.js` are exercised in a separate ENiGMA checkout.
Only these two source files are copied. The fixture uses the existing synthetic
`loclab` account and `PCXTEST.BIN`, with generated DIZ and22-line NFO text in a
new notes database. No owned configuration, catalog, game archive or user
database is copied. The live board is not changed or restarted.

The current source module hash is
`0711413e29c01f0cf3cef7f89b3dc607515381a67a23e1a58205aa6d7a20efb8`.
Its helper hash is
`e4f6c1df6dbb9d6282d0534150c9149889637d34f01665691ca3bc5d19a06235`.
They are evaluated against owned upstream revision
`237cd9743d6978a940dd66db0e78f6ab8ccd3e37`.

The actual Client-to-GameDetails replay includes180 checks. It runs every
partition of selected Up/Down/PgUp/PgDn/Home/End sequences, both numeric and
letter Home/End encodings, a combined tab/key stream, tab resets and listener
teardown. The original decoder reproduces164 fragmented differences and120
unintended previous-menu calls. The staged decoder has zero of either while
preserving unfragmented results. These are controlled replay observations,
not counts of failed BBS sessions. Synthetic notes and a previous-menu boundary
are used in this replay; actual menu ownership and SQLite loading are checked
in DOS separately.

The DOS runner dials through the maintained immediate19200/HARD modem/UART
harness. It authenticates to the synthetic board, enters an added `NFO` command,
displays overview/DIZ/NFO, scrolls using all six advertised navigation keys,
returns to overview, leaves and reopens the module, then scrolls again. It
audits the actual server session, outgoing profile bytes, full observed page
sequence, final NFO content, unchanged inputs, normal DOS/hardware restoration
and no saved posts. The patched run passes with these24-line NFO page ranges:

`1–15 → 2–16 → 10–24 → 9–23 → 1–15 → 10–24 → 1–15`, then after reentry
`1–15 → 10–24`.

The same DOS fixture with the unmodified decoder authenticates and enters both
DIZ/NFO pages, exits normally with hardware restored and emits the expected
profile key bytes. Navigation fails: both visits remain at `1–15/24`, and the
last NFO line never appears. Its failed compatibility result is retained beside
the patched pass. This reproduces the live failure in an isolated controlled
fixture; it does not assume the result from only a decoder unit test.

The new menu command deliberately isolates the actual details module; it does
not reproduce the live custom search/index route. Game downloading from this
module, browser links and physical modem behavior still require their own
validation. The standard editor/ZMODEM tests remain separate evidence.

Prepare a new checked candidate using the documented
[keyboard experiment](patches/enigma-key-stream/README.md), then run:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_notes_fixture.py \
  --candidate build/bbs-lab/NEW/candidate --server-root /path/to/owned/enigma
./tools/bbs-dev --command node \
  lab/bbs/patches/enigma-key-stream/check_game_details.js /path/to/owned/enigma \
  > build/bbs-lab/NEW/module-baseline.json
./tools/bbs-dev --command node \
  lab/bbs/patches/enigma-key-stream/check_game_details.js \
  build/bbs-lab/NEW/candidate --fixed \
  --baseline build/bbs-lab/NEW/module-baseline.json
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate
./tools/dev --command python3 lab/bbs/enigma_notes_dos.py \
  --candidate build/bbs-lab/NEW/candidate --server-root /path/to/owned/enigma \
  --label unique-notes-label
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/NEW/candidate
```

Use a separately prepared candidate with `--decoder baseline` to select the
unmodified client for comparison. A failed navigation assertion is retained as
an observed failure, not turned into a compatibility pass. Both instances use
the same loopback port and must run sequentially.

The first DOS attempt stopped before connecting because it used a new harness
name with an explicit ENiGMA server log. The runner now uses the supported
`enigma` owner and a unique output label. The original failed preparation is
retained under `build/bbs-lab/results/enigma-notes/owned-notes-framed-01`.

These tests strengthen the staged patch evidence. They do not replace the
retained live NFO/editor failures, install the patch, close F01–F16 or establish
universal/physical compatibility. See the
[validation record](../../docs/validation/enigma-notes.json).
