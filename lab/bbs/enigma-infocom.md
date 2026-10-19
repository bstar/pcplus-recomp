# DOS client and owned Infocom door

The live ENiGMA driver supports `--mode infocom` for the currently configured
Classic Pillars menus and Zork I catalog entry1. It uses the existing regular
PCPlusProbe validation account, actual DOS source compiler/interpreter and
terminal, and the immediate19200/HARD modeled modem. It installs no server fix.

The [recorded live run](../../docs/validation/enigma-infocom.json) passes all13
checks; its acceptance auditor rejects all eight corrupted captures. The live
decoder and application binaries remain unchanged.

The actual BIOS keyboard recipe visits:

`Main → Doors → Infocom Library → page2 → page1 → Zork I → LOOK → NORTH →
LOOK → QUIT/confirm → Infocom Library → Doors → Main`.

Acceptance requires ordered page and room responses, the actual outgoing
commands, and exactly one matching worker-ready/worker-stopped pair within
the authenticated server session. Introductory game text or a clean DOS exit
alone cannot pass. The selected catalog version and story hash are verified
before connecting; the test does not assume that Zork uses Z-Machine version3.

Source/configuration/layout/catalog/story/worker identities are checked before
and after the run. The selected probe account's existing save files must remain
byte-identical, and the recipe never requests SAVE. Creating the server's normal
per-account save namespace, login statistics and session/door logs is ordinary
server behavior; this test does not claim the complete database is unchanged.
No story files, private accounts or full transcripts are published.

```sh
./tools/dev --command python3 lab/bbs/enigma_owned_dos.py \
  --server-root /home/bstar/projects/black-flag-bbs \
  --account-json build/bbs-lab/owned-account/account.json \
  --host YOUR_LAN_IP --port 2323 \
  --mode infocom --main-menu-text '[ LoC ]' --label NEW_LABEL
./tools/dev --command python3 lab/bbs/check_enigma_infocom_audit.py \
  --label NEW_LABEL
./tools/dev --command python3 standalone/record_enigma_infocom.py \
  --label NEW_LABEL
```

Use fresh labels. The audit checker requires a successful actual run, then
independently removes paging, input responses, return-menu evidence, outgoing
quit, worker completion or story identity, and introduces a worker error or
SAVE command. All eight corrupted captures must reject. It never contacts a
server or generates replies.

An initial preflight incorrectly assumed a `.z3` filename for the installed
Zork story. It failed before connecting, and is retained separately. The driver
now uses the catalog's actual contained path, version and SHA-256.

This workflow covers one story's entry, input and clean return. It does not
establish full playthrough compatibility, SAVE/RESTORE from DOS, Global War or
Barren Realms Elite behavior, corrected NFO/editor key decoding, or physical
RS-232 modem operation. The [ENiGMA acceptance matrix](../../docs/ENIGMA_COMPATIBILITY.md)
and full application gates remain authoritative.
