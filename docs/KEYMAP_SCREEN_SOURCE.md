# Source keyboard-mapping screen and key dispatch

`src/key_mapping/keymap_screen.c` reconstructs the original helper's screen,
79 field positions, 33 terminal labels and key dispatch. The source-rendered
blank ANSI profile matches the observed original ready screen byte for byte:
all2000 characters and all2000 attributes, SHA256
`87f6aaa8025b4abe6a03d3ff0b4c197be5b04849db6a93b20dfc1d2b8f2c710f`.
This includes borders, headings, field colors, terminal name and filename footer.

[Validation](validation/keymap-screen-source.json) checks every possible16-bit
input key against an independent original-instruction dispatch trace. All65536
cases match, including all79 slots, PgUp/PgDn/Space, Alt-O/S/X/Z, Escape and the
reserved Alt-digit inputs. The fixture records195 complete action ranges and
a digest of the65536-byte expansion. The oracle runs original CS:03E0 branch
instructions, stops at the action/slot boundary and models the save prompt and
bell as no-op returns. It does not execute open/save/about/exit operations.
Profile wrapping at0/32 remains a foreground-controller integration check.

The source-only DOS8086 diagnostic repeats all65536 dispatch cases and renders
all33 terminal profiles. Each4000-byte frame is written to B800 video memory,
read back and compared with its source frame. Only the blank ANSI frame has an
independent original-screen comparison; the remaining32 frames establish source
rendering/VGA consistency, not original per-profile screen acceptance. Separate
host checks validate79 distinct binding placements and invalid-profile refusal.
An eight-file isolated source export reproduces the DOS binary byte for byte.

The renderer reads binary storage through the bounded notation converter and
never changes the binding image. Bindings whose notation exceeds ten columns
show a trailing `+`; ambiguous or unterminated storage shows `[RAW]`. These are
intentional visible differences on unsafe original inputs. They must remain
uneditable until the foreground controller can refuse the edit while retaining
all original bytes. Rendering a marked binding never truncates its storage.

REA paint Evidence `ev_bec7564cd0007302d7b0e02a68549c5e564133b01cc1450e766af4ba0875b54b`
confirms the slot-position table and attribute-based painting. Dispatch Evidence
`ev_36c92a6dbffeb28bf009a0e80b57cb2e21c2d857cb2fa286f036ce18277ef5aa`
and public range hashes bind the reconstruction to the original helper SHA256
`f079418fca6392cde318e2eb657874a1f5ee10db83616c83054d191441fb6244`.
Original binaries and full REA exports remain ignored. Factory defaults and
private keyboard-file contents were not imported.

```sh
./tools/dev --command python standalone/test_keymap_screen.py \
  --output build/keymap-screen-source
```

`standalone/capture_keymap_dispatch.py --original PATH --output NEW_JSON` is
explicit optional evidence regeneration. It is not a build input.

This remains a render/dispatch component. `KMSCREEN.EXE` is a diagnostic;
it is not the completed interactive PCKEYMAP replacement. The next gates are
the foreground controller joining this screen to the recovered field model,
transactional file handling, dirty/open/save/exit behavior and Alt-F8 admission/
return/reload. The installed application, physical machine, modem and BBS
services were unchanged. RA608E10 physical acceptance remains pending.
