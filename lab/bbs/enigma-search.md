# Owned search, index and game-details route

This fixture copies the owned board's four search/index/details modules,
the selected file-base/search/details menu objects, the file command prompt,
the search-specific theme settings and three ANSI assets. It overlays them in
an isolated lab checkout with the staged keyboard decoder. The other login
and system menus remain the synthetic lab defaults. No live source, settings,
databases, catalogs or service are changed.

Thirty generated ZIPs named `PCPLUS PROBE 00 (1991).ZIP` through
`PCPLUS PROBE 29 (1991).ZIP` provide real file entries and searchable FTS rows.
Each archive contains a generated README, FILE_ID.DIZ and NFO; the generated
notes database matches those documents. No game software is copied.

The actual owned `search.js` and real `FileEntry.findFiles` pass11 read-only
SQLite checks: browse, multiword/case/punctuation/Unicode-normalized queries,
anchored wildcard, full-text descriptions, no results and allowed-area
intersection. The explicit allowed-area input in these query checks is not
an assertion about a real user's permissions; the DOS run uses the real user's
area-access checks separately.

The DOS19200/HARD/immediate-modem run passes the actual route:

`File Base → Search → Indexed Files → Game Details → Indexed Files → Search →
empty Indexed Files → Search → File Base → Main Menu`.

It searches for `PCPLUS PROBE`, moves through all three result pages using
Up/Down/PgUp/PgDn/Home/End, selects game01, displays DIZ/NFO, uses all six NFO
navigation keys, returns through the original menu stack and performs a
`ZZZNOMATCH` search. Exact selected indexes, page ranges, content and server
menu history are compared. Normal DOS exit, hardware restoration, unchanged
code/config/art inputs and no saved posts are required. The direct `NFO`
probe command is removed, so this test cannot bypass the real search route.

The game transfer probe uses the selected archive's actual long filename.
Its adapter changes only the test harness's DOS83-BIN fixture-name admission;
the production DOS engine, modem and passive CRC/data audit are unchanged.
Transfer success is recorded separately from navigation. The current batch
metadata codec currently accepts only DOS8.3 basenames; long-name handling is
a separate compatibility requirement, not replaced with an easier BIN fixture.

The retained pre-fix custom download sent a CRC-valid ZFILE offer for
`PCPLUS PROBE 01 (1991).ZIP` (1301 bytes), but transfer fails and no file is
saved. DOS exits normally, restores hardware and leaves no staging file. A
separate replay sends the captured metadata through the production-linked
decoder: it returns `BH_NAME` without altering its result. Changing only the
filename to `PROBE01.ZIP` makes the same metadata return `BH_OK`. This identifies
the filename limitation separately from menu navigation and CRC framing.
The new [wire/local filename adapter](../../docs/ZMODEM_NAMES.md) now passes
this exact download as `8868026D.ZIP`, with byte-exact storage, full ZMODEM
completion and NFO input/response afterward. The historical failure record
remains unchanged; the new filename validation record binds the corrected
binary and tests separately.

Run the [keyboard experiment](patches/enigma-key-stream/README.md) first to
create a fresh checked candidate for the owned upstream revision, then:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_search_fixture.py \
  --candidate build/bbs-lab/NEW/candidate --server-root /path/to/owned/enigma
./tools/bbs-dev --command node lab/bbs/check_enigma_search.js \
  build/bbs-lab/NEW/candidate
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate
./tools/dev --command python3 lab/bbs/enigma_search_dos.py \
  --candidate build/bbs-lab/NEW/candidate --server-root /path/to/owned/enigma \
  --label unique-search-label
./tools/dev --command python3 lab/bbs/enigma_game_transfer_dos.py \
  --candidate build/bbs-lab/NEW/candidate --label unique-game-transfer-label
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/NEW/candidate
```

The first transfer driver selected a same-named standalone diagnostic because
the shared DOS harness also exposes that directory on `sys.path`. It never
connected to this BBS. The driver now selects and asserts the laboratory module
path; a fresh label retains the failed attempt separately.

The live board still needs the approved patch/restart and retesting against its
actual catalog. Physical Wi-Fi modem timing and the decoder's100ms incomplete
key deadline remain unverified. These tests close no whole-application gate.
The [validation record](../../docs/validation/enigma-search.json) distinguishes
navigation results from transfer results and the retained live failures.
