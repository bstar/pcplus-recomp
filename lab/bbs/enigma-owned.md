# Owned ENiGMA compatibility

The user's running board is `~/projects/black-flag-bbs`, revision
`237cd9743d6978a940dd66db0e78f6ab8ccd3e37`, with a custom file index and game
details module. The separately named `~/projects/enigma` directory was empty.
Its live service listens on LAN port2323. Testing must cover that board as
well as the older isolated stock fixture; a laboratory editor pass alone does
not establish compatibility with its custom menus.

`enigma_owned_dos.py` runs the current source-built DOS terminal through the
existing immediate modem/UART harness and a byte-transparent loopback-to-LAN
relay. Explicit server-root, private address and account-file arguments are
required. It uses only the regular `PCPlusProbe` validation account, verifies
the saved account ID against the live database before dialing, and leaves
credentials, wire captures and server-session records in ignored `build/`.
No source or configuration in the running board is changed. Editor tests type
an unsaved draft and disconnect; no editor action-menu Enter is submitted.

```sh
./tools/dev --command python3 lab/bbs/enigma_owned_dos.py \
  --server-root /path/to/owned/enigma \
  --account-json /private/path/to/probe-account.json \
  --host YOUR_LAN_IP --port 2323 --mode files --label unique-files-run
```

Use `--mode editor` for Home/Insert checks; `--profile enigma-editor` selects
the explicit control-key experiment instead of the ordinary network bindings.
The account JSON contains `userId` and `password`; its regular account must be
named `PCPlusProbe`. A test-account password must be alphanumeric for ADDKEY.
Do not substitute a sysop account or check the account file into Git.

The current live client's SHA-256 is identical to the older pinned client's:
`d66207f46af13ae4acb0ac430b1d0f2572a03722c79f4bcb7125dcd01e98e788`.
An actual Client/editor replay on this revision reproduced74 fragmented-key
differences and9 editor differences. Those are counterexamples to chunk-safe
decoding, not74 failed network sessions. TCP cannot preserve keyboard-sequence
boundaries for a DOS UART or guarantee how a remote server groups bytes.

The isolated [keyboard stream experiment](patches/enigma-key-stream/README.md)
also applies to this newer revision. With explicit commit/client pins, it
passes1638 framing checks,112 actual Client/editor checks with no fragmented
differences, and123 upstream regressions. It preserves unfragmented behavior
and has a bounded100ms incomplete-key deadline; binary transfer owners bypass
the key decoder. That is a tested candidate, not an installed live-server fix.

Initial live runs `owned-files-01` and `owned-editor-01` did not authenticate:
an existing ArchiveProbe credential file referred to a deleted account. The
dedicated identity now has a database preflight. `owned-files-02` authenticated
but its borrowed login schedule left an extra N in the main command field.
The fixture now explicitly clears that field before executing its recipe.
These attempts remain retained; none count as game-browser or editor passes.

The first isolated DOS run reached the editor, but its auditor encountered
both the startup readiness connection and the authenticated connection.
`check_editor_dos.py` now requires exactly one connected, authenticated
`loclab` session and audits only that session. The original failed wrapper
and a separately named posthoc audit are retained. New runs use the corrected
auditor from the beginning.

The prompt-driven `owned-files-05` run authenticates through DOS-compiled ASPECT,
enters the custom game search/details module and displays actual FILE_ID.DIZ
and NFO pages. It does **not** pass scrolling: the24-line NFO remains at
lines1–15 after correctly emitted Down and PageDown sequences. A separate
`scroll-audit.json` preserves that failure instead of treating successful page
entry as complete navigation. The fixed source login matches stable text
fragments between ANSI style changes and services deferred WHEN calls through
short WAITFOR intervals. Timed login attempts and the first incorrect raw-text
prompt match remain retained.

On an isolated copy of this revision with the decoder patch,
`owned-revision-framed-editor-02` passes all audited editor checks with immediate
forwarding. `owned-revision-framed-transfer-01` subsequently enters the editor,
discards its unsaved draft, downloads the11,521-byte synthetic PCXTEST.BIN by
ZMODEM with exact length/hash and completes actual file-list interaction after
the transfer in the same connection. The live custom-board decoder is still
unmodified. These isolated passes do not erase the live navigation failure.

The unmodified-board `owned-editor-04` run explicitly selects the conference's
default writable area through the real UI. It reaches the editor and retains
normal DOS exit, device restoration and no-post behavior, but fails Home
positioning and Insert/overtype. Earlier attempts with the newly created
validation identity had no current message area and are retained as editor
prerequisite failures. The [published evaluation](../../docs/validation/enigma-owned.json)
keeps live failures separate from isolated patched successes and excludes
private credentials, configuration contents and transcripts.

The optional control-key profile run `owned-editor-control-01` also failed its
editor checks, and is excluded from controlled comparison because the live
file-menu configuration/module changed during its capture. Its failed outcome
and changed-input guard are retained in the evaluation. The control-key profile
is not recommended as a verified fallback for this newer board.

Before claiming the requested compatibility, require actual DOS login, custom
search/list/details/DIZ/NFO navigation, unsaved editor behavior, and byte-exact
transfers on this board. Repeat after any installed decoder change. Physical
RS-232 Wi-Fi modem timing/flow-control testing remains separate.

The [isolated owned game-details fixture](enigma-notes.md) now copies the exact
details/helper source but supplies only synthetic notes/files and a dedicated
menu route. Actual Client/module replay reproduces fragmented navigation and
accidental exits with the original decoder, while the staged decoder preserves
all180 checks. The patched DOS run reaches DIZ/NFO and passes the complete
nine-page navigation sequence, including leaving and reopening the module.
This strengthens the candidate evidence without modifying the live board or
claiming its custom search/list route is fixed.

The next [search/index route fixture](enigma-search.md) copies the selected
owned menus, ANSI assets, theme settings and all four modules around a30-ZIP
generated catalog. It passes11 real SQLite/FTS query checks and the DOS
F/S search → paged index → selected game → DIZ/NFO → empty-search/return route.
This covers the actual selected routing in isolation; the live catalog and
service remain unchanged, and game-download results are evaluated separately.

The native [ZMODEM name adapter](../../docs/ZMODEM_NAMES.md) now handles the
generated catalog's actual long ZIP filename through that custom D action.
DOS saves the byte-exact archive under its checked deterministic alias and
returns to usable NFO input. Existing targets retain the checked skip policy;
the host and8086 DOS tests include an actual CRC32 alias collision. This adds
client-side transfer evidence without changing the live board's decoder.
