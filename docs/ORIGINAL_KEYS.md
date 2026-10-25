# Original keyboard candidate — 2.01-LoC.2

The new explicit `--original-keys` terminal variant restores direct access to
several original commands while retaining the tested BBS keyboard assignments.
It is staged for the next card update; the card is absent and was not written.

| Key | LoC.2 behavior |
| --- | --- |
| Alt-R | Open the checked ASPECT recorder; press again to save an active recording |
| Alt-S | Open the eligible saved-settings editor |
| Alt-P | Open that editor with its port field initially selected |
| Alt-F6 | Open serviced redisplay/history |
| PgUp/PgDn | Send an assigned keyboard-profile binding; a native-local unassigned key opens send/receive |
| Alt-F10 / Ctrl-PgUp | Retain the existing settings/history aliases |
| Alt-Z → File → Send/Receive | Open transfers regardless of page-key assignments |

Alt-P currently uses the complete source-built settings editor; it is not a
reconstruction of the original dedicated line/port popup. The original Alt-Z
reference layout, backtick/mouse pull-downs, live Alt-D directory chooser and
Alt-F8 key-map editor remain required. This checkpoint does not claim full
original command or application parity.

The recorder uses the existing checked foreground/file owners. Its direct key
acquires the same guarded saved-screen owner as the command menu. Serial input,
terminal replies and live-screen restoration continue during its dialog. Send
and receive use private dispatcher actions so they no longer conflict with
Alt-R/Alt-S. Invalid keyboard bindings keep their explicit errors instead of
being mistaken for an unassigned page key.

## Build and staged files

```sh
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --custom-irq --original-keys --output build/NEW-original-keys
```

The current stage is `build/special-original-keys-help-20261025/PCPLUSSE`.
It contains ten public application files, including the previously omitted
authored `LOCHELP.HLP` needed by the helper's searchable help. The magenta
splash and VERSION.TXT identify this variant as 2.01-LoC.2. The separately
prepared local `private-boca` directory contains BOCA.PRM and LOC.BAT; those are
outside the public package and retain the physical-confirmation requirements
in [the connection checkpoint](ENIGMA_REPLACEMENT.md).

The ordinary terminal and LoC.1 branded control retain their exact previous
binary hashes. The larger LoC.2 parent uses 64,096 bytes for near data/stack
and 65,382 bytes of resident code, preserving the existing stacks and limits.
Its compiler, interpreter, settings editor and translation editor remain exact.

## Validation

The [receipt](validation/original-keys.json) binds these distinct checks:

- Seven linked CPU groups cover 29 inputs: direct record/save, serviced dialog
  input and cursor reports, setup eligibility, history aliases, assigned and
  unassigned page keys, menu transfer access and exclusive-owner refusal.
- Actual DOS records a new script, replaces an existing script only after
  confirmation, and cancels while preserving an existing file. The accepted
  recordings compile in DOS and replay the exact UART bytes. Hardware and file
  cleanup verify in each case.
- Actual DOS8086 Alt-S and Alt-P enter/cancel the editor, retain the exact PRM
  and resume receive/render/query and ordinary keyboard traffic.
- Packaged START/SETUP pass on COM3/IRQ5. The independent splash capture contains
  2.01-LoC.2. The help resource passes its 49-check DOS diagnostic.
- The exact branded candidate logs into stock lab ENiGMA through the actual
  corrected SynthModem proxy, passes editor semantics and the expected video
  snapshot, and returns normally. No post is saved.
- An empty tree of 744 declared source inputs reproduces all ten package files
  exactly without originals or ancestor Git metadata.

The initial package attempt exposed a help extractor that only accepted literal
ENTRY titles. It now preprocesses the authored text block with the pinned C
preprocessor and retains all 24 menu topics; ordinary help bytes remain exact.
An initial recorder harness variable collision and a model probe that bypassed
the main-loop screen transaction were corrected before acceptance. Their failed
logs remain in ignored build storage.

Physical Boca/SPA2102 operation, sustained integrity/flow, repeated reconnects,
transfers, multiline rendering and the complete F01–F16 plan remain open.
