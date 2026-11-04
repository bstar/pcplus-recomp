# Original Toggle Lines controls

The optional `--line-control` build connects original Ctrl-minus, the native
Alt-Z reference's Toggle Lines item and View → Toggle Lines in the command
browser to the accepted-selector transaction. It requires `--display-startup`
and its composed display, full-frame, ASPECT-row, notice and status owners.
The flag is disabled by default. These bindings are maintained integration of
recovered behavior; they are not a byte-exact recovery of the whole application.

## Behavior

Ctrl-minus is recognized by normalized character31, as in the original. Reference
and browser frames release before the display transaction starts. Configured
video-mode WORD zero selects a two-choice cycle; every nonzero WORD selects four.
The next choice starts from the last accepted selector, including after verified
fallback. Saved words are not rewritten. The operation preserves current status
visibility, including a live Ctrl-] choice differing from the saved hidden word,
and reconciles physical mode/rows, parser bounds, RIS defaults and shadow state.
Current history remains available. BIOS mode/font selection and fallback use the
existing recovered helpers and checked composition described in
[selector transactions](DISPLAY_SELECTOR_TRANSACTION.md).

The owner admits disconnected, coherent mode3/B800,80-column layouts at
25/28/43/50 physical rows in narrow profiles4/6. Shared exclusive owners defer
keys through the existing queue. Tracked-online or unsafe geometry/transaction
states refuse; they do not attempt live NAWS or send Ctrl-minus to the peer.
Absent imported preferences or an accepted selector returns status7 and retains
the baseline rather than inventing saved preferences. Existing shutdown and
rollback contracts remain in force. This is not arbitrary VGA/font preservation.

## Evidence

The [receipt](validation/line-control.json) binds the current parent images,
public source hashes, captures, checkers and isolated rebuilds.

- 179 linked inputs exercise all accepted heights, normalized shortcut variants,
  two/four-choice cycles, menu-frame release, actual RIS/query paths, visibility
  preservation, accepted fallback, deferred requests and refused states. Actual
  product C/ASM executes; BIOS/UART/DOS boundaries and fault timings are modeled.
- 81 native reference inputs retain all39 original labels and their placement,
  contextual help, navigation, refusal and existing command dispatch. Eleven
  original reference commands remain unavailable. This is not full parity.
- 51 selector,36 status-control and57 startup inputs also pass on the same image:
  404 linked inputs in this checkpoint.
- 15 actual8086 DOSBox-X workflows use BIOS keyboard input for direct Ctrl-minus,
  native reference and browser selection. A passive timer captures56 stage
  records with actual BDA rows/font/mode/columns/page and the bottom two video
  rows. Actual parser area/CPR replies follow each accepted layout. The tracked
  online fixture retains its43-row layout and sends no shortcut/menu bytes.
- Independent artifact verification derives selector sequences from raw PRM
  words, rebuilds both observers and checks all56 geometry/font/tail records,
  full8000-byte final frames, exact serial bytes, unchanged PRM, normal DOS return
  and42-byte UART/PIC/vector restoration. The online fixture uses synthetic Hayes
  replies and does not establish real SIP/DCD or BBS acceptance.
- Enabled and disabled parents each reproduce exactly from569 declared public
  sources without originals or ancestor Git. A fresh288-source child build
  matches current shared inputs and remains byte-identical to the accepted child.
  The builder rejects line bindings without the startup owner before output.

The first full matrix stopped on a wrong test expectation: selector3's configured
mode3 after43 rows retains350 scanlines and produces25 rows with14-pixel glyphs.
The recovered43-row font helper explicitly selects350 scanlines; configured
mode3 uses its native mode call, while baseline selection explicitly restores400.
The test had assumed every25-row stage uses16 pixels. Its expectation was
corrected, the entire15-case matrix rerun, and the independent verifier checks
this distinct font transition. No application workaround or tolerated mismatch
was introduced. Earlier incomplete/failed matrix output is excluded.

Enabled SHA256:
`6f9148ccdbd5cd6d8260d1c7fb6dee6e70a6836a1bdd1926b1bc39d6fb4b31a9`.
Resident CS remains65,514 bytes with22 spare; near data/stack remains65,120.
CONFIG_CODE grows59,728→59,760 and REFERENCE_CODE18,778→19,100; DISPLAY_CODE stays
5,525. No new resident code, near static data or screen plane is added by these
bindings. Disabled bytes retain the preceding startup candidate
`14358a87ca5a7f4429c87d10981eedbb0eeb1564d2e25b835d351c645f858ff0`.
Further resident additions still require banking.

## Reproduction and remaining work

Use the receipt's enabled flags, adding `--line-control` to the preceding
startup composition, and fresh output directories:

```sh
./tools/dev --command python standalone/check_line_control_live.py \
  --terminal build/NEW/enabled/TERMINAL.EXE --output build/NEW-linked
./tools/dev --command python standalone/check_command_reference.py \
  --terminal build/NEW/enabled/TERMINAL.EXE
./tools/dev --command python standalone/test_line_control_dos.py \
  --terminal build/NEW/enabled/TERMINAL.EXE --output build/NEW-DOS --jobs 3
./tools/dev --command python standalone/check_line_control_artifacts.py \
  --run build/NEW-DOS --output build/NEW-independent
```

Live setup/HOOK adoption, online DOS/bridge sizing, owned Enigma/Synchronet
rendering/editor/transfer composition and physical Cirrus/mouse/Boca/SPA2102/SIP
acceptance remain open, alongside the full original-parity inventory. Nothing
was installed on the physical PC. The selected connection-test package, private
settings/call history, bridge/BBS services, networking and packages are unchanged.
The full application goal remains active.
