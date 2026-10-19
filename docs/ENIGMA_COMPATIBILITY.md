# ENiGMA compatibility acceptance

The target includes the user's running `~/projects/black-flag-bbs` checkout,
its configured menus and modules, and the source-built DOS client. Passing
an isolated stock BBS is insufficient. Compatibility is not complete.

The [October 19 live validation](validation/enigma-live-20261019.json) records a
fresh DOS run with the correct Classic Pillars prompt: login, menu, details,
DIZ and NFO entry pass, but complete NFO scrolling fails. Both Down and PageDown
are present on the client-to-server wire. Down advances from lines1–15 to2–16
of24; PageDown never reaches the final page. All source/configuration
fingerprints remain unchanged. A fresh replay
of the live Client reproduces74 fragmented-key and9 editor differences; the
staged candidate passes112 checks with neither difference. The candidate is
still separate from the running board.

## Evidence and remaining checks

| Workflow | Evidence | Remaining acceptance |
| --- | --- | --- |
| DOS source compilation and scripted login | Current compiler/runner execute the login before the isolated owned search route; all 21 checks pass in [timestamp validation](validation/aspect-file-times.json). Live regular-account login also succeeds. | Repeat the complete route on the current live service. |
| Classic Pillars main menu | Actual live DOS display contains the new menu. Its contiguous wire prompt is `[ LoC ]`; the decorated heading contains SGR boundaries and spaced letters. | Use the explicit prompt option below; do not report the old `Main Menu` text check as a terminal defect. |
| Search, index, game details, DIZ and NFO | [Owned route](../lab/bbs/enigma-search.md) passes all selected navigation checks with the staged decoder and generated catalog. Live DOS reaches DIZ/NFO. | Live NFO scrolling still fails; verify all six navigation keys, result paging, empty search and return to the actual main menu after correction. |
| Message editor | [Owned evaluation](validation/enigma-owned.json) retains live Home/Insert failures and isolated corrected editor passes. | Repeat unsaved draft insertion, Home/End, Insert/overtype, paging and discard on the current live board. |
| Transfers and subsequent input | [Protocol selector](validation/enigma-protocol-selector.json) covers the owned terminal selector and exact ZMODEM download. [Repeat validation](validation/enigma-repeat-download.json) covers receive, existing-file skip, second receive and usable NFO input after each. | Repeat against actual live catalog files; extend cancellation, interrupted connection/retry and upload coverage. |
| Infocom door | [Live DOS validation](validation/enigma-infocom.json) passes13 checks: real library paging, Zork I entry, LOOK/NORTH/LOOK responses, worker lifecycle and clean return through Doors to Main. Eight corrupted acceptance captures reject. Existing probe saves remain unchanged. | DOS SAVE/RESTORE and broader story/playthrough coverage remain open. |
| Other doors | Current board includes Global War and Barren Realms Elite. | Actual DOS client entry, play/input and return checks are still required. Infocom and file-browser passes do not cover these games. |
| RS-232 Wi-Fi modem | Current DOS tests use modeled UART/19200/HARD flow control. | Physical modem testing, slow/fragmented input, flow-control pressure and reconnect are required. |

## Reproduce the live file navigation check

Run from this repository through the pinned Nix environment. Use only the
existing regular `PCPlusProbe` account file; passwords and captures stay in
ignored `build/`. The test changes no live code/configuration and saves no posts.
Use a new label each time.

```sh
./tools/dev --command python3 lab/bbs/enigma_owned_dos.py \
  --server-root /home/bstar/projects/black-flag-bbs \
  --account-json build/bbs-lab/owned-account/account.json \
  --host YOUR_LAN_IP --port 2323 \
  --mode files --main-menu-text '[ LoC ]' --label NEW_LABEL
```

The main-menu option identifies a contiguous literal wire fragment for this
configured artwork. The default remains `Main Menu` for older fixtures. The
report records the selected fragment and hashes JSON layouts as well as module
source. Successful authentication or NFO entry cannot satisfy scrolling.

## Known server input defect

The current live `core/client.js` has SHA-256
`d66207f46af13ae4acb0ac430b1d0f2572a03722c79f4bcb7125dcd01e98e788`.
Its per-event key decoding interprets some fragmented escape sequences
differently from the same bytes received together. The
[isolated decoder candidate](../lab/bbs/patches/enigma-key-stream/README.md)
buffers incomplete sequences with an explicit 100 ms deadline and preserves
raw transfer ownership. It has not been installed on the live service.

Client-side batching cannot guarantee TCP receive boundaries on an arbitrary
BBS. Treat staged decoder success, live-server acceptance and physical modem
acceptance as separate results. Preserve failing captures when retesting;
whole-application gates remain open.
