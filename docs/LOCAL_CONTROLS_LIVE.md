# Original Clear, Reset and Duplex controls

The optional `--local-controls` original-reference candidate enables Alt-C Clear
Screen, Alt-U Reset Terminal and Alt-E Duplex Toggle, through both direct BIOS
shortcuts and the original Alt-Z reference. The same commands also appear in
the maintained View/Connection browser with contextual help. All39 original
labels remain; only these three previously unavailable commands are enabled.
The selected parent without directory view now has16 unavailable commands.
This is partial F02/F04/F05 coverage, not full application parity.

## Behavior and ownership

Clear uses the recovered clear/home routine and preserves history. Reset calls
the recovered local entry with argument1, restoring the captured startup parser,
keymap, display and mode baseline; it preserves serial/connection ownership.
Duplex uses the original word policy: zero becomes1, all other values become0.
Ordinary input then follows the existing full/half-duplex output/echo owner.

The foreground handler runs after menu/frame restoration. Parser, macro,
PROGRAM, transfer, ASPECT, wait, snapshot, BREAK, raw/controller and view owners
retain priority. Recognized local commands enter the existing ordered key FIFO
while these owners are active; they run after admission without becoming UART
bytes. Missing reset-baseline state yields typed status2 without modifying the
screen. The helper's status word otherwise reports0(executed) or1(deferred).
This does not implement command execution inside the ASPECT child's own UI.

Four checked resident-to-bank bridge pairs and one dispatch far entry preserve
the DS=SS ABI. The native Reset/Duplex entries retain their24 normalized original
instruction bytes. The segment verifier checks their near targets, far calls,
relocations and shared-state owner. Six intentionally damaged, never-executed
images are rejected. The full logging/reference candidate retains64,800 near
bytes and65,532 resident code bytes, leaving four code bytes. Further commands
need deliberate banking before additional resident entries are added.

## Validation and packaging

Linked CPU tests cover direct actions, native duplex values, preserved history,
exclusive-owner deferral, missing baseline and reference-to-live return. Three
actual DOS8086 COM3/IRQ5 workflows cover direct keys, Alt-Z and a local command
queued during partial CSI input. Real cursor queries verify clear/reset home and
half/full-duplex echo; the normal color, private fixture and hardware restoration
are checked. Package splash and SETUP/cancel return checks pass as well.

The feature-disabled terminal remains byte-identical to the installed9f2a37e7
baseline. The full candidate is e69a8050ea5d31793f07490e325052db8b37382475dafc3d437b2c806c08c5fb;
a Git-free tree of declared sources reproduces it exactly with no original inputs.
A source-matched ASPECT rebuild remains byte-identical to the selected84160498
interpreter. The minimal reference/control variant is also buildable; it retains
an explicit reference-bank alignment anchor when the splash is absent.

BUSY cleanup/retry and three successful calls in one DOS process pass on this
image. Its300-second paced UART endurance also passes all601 frames, every
reply and final glyph/attribute check, with modal return and hardware restoration.

Fresh DOS Enigma and Synchronet editor sessions retain exact final cells/cursor
and call-log checks, with250ms key framing/20ms byte pacing. These are owned lab
sessions, not physical modem/SIP/audio evidence. Physical BUSY diagnosis and
hardware acceptance remain open; this candidate is staged separately and does
not replace the active deployment selection.

The [validation receipt](validation/local-controls-live.json) binds exact products
and tests. Use fresh build output directories and labels when repeating:

```sh
./tools/dev --command python standalone/build_terminal.py \
  --original-reference --local-controls --output-dir build/NEW-controls
./tools/dev --command python standalone/check_local_controls_live.py \
  --terminal build/NEW-controls/TERMINAL.EXE --output build/NEW-control-checks
```
