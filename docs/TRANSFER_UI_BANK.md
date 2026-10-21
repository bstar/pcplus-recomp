# Banked transfer UI

The transfer filename prompt, running display, progress counter and restore
body now execute in CONFIG_CODE. Their four resident entry names and no-argument
calling convention remain unchanged. Three resident callbacks provide the
existing transfer service, BIOS keyboard poll and key read. Data and the saved
bottom two screen rows retain their existing near ownership.

The pre-change source at `c154f20` reproduces the accepted `3b0deeeb` plain
executable but fails both mouse builds with resident code 146 bytes over 64 KB.
Moving the UI body frees 622 resident bytes. The
[validation receipt](validation/transfer-ui-bank.json) records these builds:

| Build | Executable SHA prefix | Resident bytes free | DS=SS bytes |
| --- | --- | ---: | ---: |
| Plain | `25701409` | 624 | 64,832 |
| Mouse | `e7f89723` | 474 | 64,880 |
| Mouse/process | `56e4072d` | 474 | 64,880 |
| Mouse/traps | `9d6ac931` | 944 | 64,912 |

The ordinary build verifier now checks all four far entry targets, their MZ
segment relocations and near returns, plus the three resident callback targets
and far returns. Eighteen corrupted bridge images reject for each build; those
invalid images are never executed. All far code and shared buffers remain
within the parent's checked retained memory before child EXEC.

Validation on the final binaries covers 284 linked startup/XMODEM/YMODEM/ZMODEM
and cancellation cases, 31 linked mouse-policy cases, three actual DOS startup
transfers and three actual DOS mouse/menu/PROGRAM scenarios. Source, file,
parser/keyboard and hardware restoration gates remain mandatory in those
scenarios. Recovered ordinary sender/cancel flat instructions are unchanged.

```sh
./tools/dev --command python3 standalone/check_transfer_ui_bank.py
./tools/dev --command python3 standalone/check_transfer_ui_bank.py \
  --binary build/terminal-mouse/TERMINAL.EXE
```

The prior audio result remains bound to `3b0deeeb`; it is not silently applied
to these new binaries. Physical Boca/SPA2102 and whole-application acceptance
remain open. A separate ANSI-startup ESC-restart counterexample is captured for
follow-up; it concerns handshake filtering, not UI relocation.
