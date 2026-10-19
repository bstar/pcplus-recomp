# Owned search, index and game-details route

This fixture copies the owned board's six search/index/details and download
modules, the selected file-base/search/details/protocol-selection menu objects,
the file command prompt, selected theme settings and three ANSI assets. It overlays them in
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
Transfer success is recorded separately from navigation. The earlier batch
metadata codec accepted only DOS8.3 basenames; the wire/local filename adapter
described below now handles the generated archive's actual long name.

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

The protocol-selector checkpoint adds the exact `loc_transfer_protocol_select`
and `loc_download_ready` modules and their selected menu definitions. The former
fixture used the stock selector, which left a gap in testing the game's D action.
The terminal branch now runs through the owned selector and returns to NFO input
after a byte-exact ZMODEM download. Its selected theme settings and FPROSEL art
are checked against the owned board. Copying the HTTP module does not establish
coverage of its browser/HTTP branch.

The game-transfer command now exits unsuccessfully whenever its full protocol
audit fails, even if a valid file offer was observed. The older characterization
command could exit successfully for a failed download; its retained JSON already
marked that download as failed. The
[selector validation](../../docs/validation/enigma-protocol-selector.json)
records current navigation and transfer results separately from historical runs.

Run the [keyboard experiment](patches/enigma-key-stream/README.md) first to
create a fresh checked candidate for the owned upstream revision, then:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_search_fixture.py \
  --candidate build/bbs-lab/NEW/candidate --server-root /path/to/owned/enigma
./tools/bbs-dev --command node lab/bbs/check_enigma_search.js \
  build/bbs-lab/NEW/candidate > build/bbs-lab/NEW/search-query-checks.json
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate
./tools/dev --command python3 lab/bbs/enigma_search_dos.py \
  --candidate build/bbs-lab/NEW/candidate --server-root /path/to/owned/enigma \
  --label unique-search-label
./tools/dev --command python3 lab/bbs/enigma_game_transfer_dos.py \
  --candidate build/bbs-lab/NEW/candidate --label unique-game-transfer-label
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/NEW/candidate
./tools/bbs-dev --command python3 standalone/record_enigma_protocol.py \
  --candidate build/bbs-lab/NEW/candidate --server-root /path/to/owned/enigma \
  --search-label unique-search-label --transfer-label unique-game-transfer-label
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

`enigma_search_dos.py --script-login` additionally stages the current ASPECT and
DOS compiler, binds LOGON.ASP through the real dialing-directory record, and
leaves the keyboard recipe free of login credentials. The source-driven login
uses only the synthetic loclab account. A slot-5 data file spans its deferred
WHEN callbacks and must finish as exactly `STARTAUTHREADY`; the DOS-generated
LOGON.ASX must equal host output. The ordinary fourteen navigation checks still
apply, yielding seventeen checks in this mode. The
[ASPECT file integration](../../docs/ASPECT_SCRIPT_FILE_RUNTIME.md) records the
successful current run with this stronger compiler/runner/file-owner boundary.
It remains an isolated patched-server test with generated data.

`--file-info-login` includes source-driven login and requires native ISFILE,
GETFSIZE and RENAME on a five-byte generated probe before credentials are sent.
The normal fourteen route checks and three script checks remain required; an
additional exact-output check requires FILECHK.BIN to contain `proof` and the
old FILECHK.TMP to be absent. This mode yields eighteen checks and is bound in
[filesystem query/rename validation](../../docs/ASPECT_FILE_INFO.md).

`--enumeration-login` includes the query/rename probe, enumerates its resulting
file and writes the native builtin values as `FILECHK.BIN|FILECHK|BIN|5` before
authentication. The exact trace adds a nineteenth check to the unchanged route
checks. [Enumeration validation](../../docs/ASPECT_ENUMERATION.md) binds this
mode to the actual DOS compiler/runner and isolated patched owned modules.

`--attribute-login` includes the existing query/rename and enumeration probes,
then sets/gets RHS and clears/gets an empty far-global attribute string before
authentication. ATTR.LOG must be exactly `RHS|`, adding a twentieth check to the
same custom navigation route. [Attribute validation](../../docs/ASPECT_FILE_ATTRIBUTES.md)
binds the source-built DOS compiler/runner and independent native-wrapper control.

`--timestamp-login` includes all earlier probes, then sets/gets file date/time
through the DOS-compiled source and requires TIME.LOG to be exactly
` 3-07-93|13:45`. This adds a twenty-first check before the same custom navigation
route. [Timestamp validation](../../docs/ASPECT_FILE_TIMES.md) binds the actual
native-core control and maintained stdio/writeback/input-copy adapters separately.
