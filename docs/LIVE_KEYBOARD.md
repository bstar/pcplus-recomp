# Keyboard use in the source-built terminal

The live terminal now connects the recovered BIOS acquisition and79-slot raw
key classifier to a bounded UART sender. Navigation, keypad and function keys
use source-owned network bindings by default. These defaults are maintained
choices for modern BBS use, **not recovered factory PCPLUS.KBD contents**.
The original format and execution evidence are in [KEY_MAPPING.md](KEY_MAPPING.md)
and [KEYBOARD_MAPPING.md](KEYBOARD_MAPPING.md).

```text
TERMINAL COM1 38400 8N1 HARD
TERMINAL @PCPLUS.PRM /E:PCPLUS.DIR /K:MYKEYS.KBD /B:AUTO
```

## Default keys and local commands

Supported raw classification covers all79 binding slots: keypad operators and
digits, Tab/Backtab, Insert/Delete, Backspace, Home/End, Page Up/Page Down,
F1..F12, Shift/Ctrl function variants, ordinary and enhanced navigation banks.
The two navigation banks remain distinct slots even when their default bytes
match. ANSI and VT220 display profiles use the same maintained initial network
bindings; an explicit KBD can provide different blocks for each profile.

| Key | Maintained default wire bytes |
| --- | --- |
| Up/Down/Right/Left |`ESC[A`, `ESC[B`, `ESC[C`, `ESC[D` |
| Home/End |`ESC[H`, `ESC[F` |
| Insert/Delete |`ESC[2~`, `ESC[3~` |
| Page Up/Page Down |`ESC[5~`, `ESC[6~` |
| Tab/Shift-Tab | Tab /`ESC[Z` |
| Backspace/Enter | BS /CR |
| F1..F4 |`ESCOP`, `ESCOQ`, `ESCOR`, `ESCOS` |
| F5..F12 | CSI15/17/18/19/20/21/23/24 followed by`~` |
| Shift/Ctrl function keys | Corresponding network sequences with modifier2/5 |

DECCKM changes every matching arrow string in the active map between CSI and
SS3 forms; this applies to custom imported slots as well. It does not transform
arbitrary longer or unrelated escape sequences. ASCII keys otherwise follow
the recovered classifier rather than being treated as KBD slot numbers.

Alt-X exits, Alt-H invokes configured hang-up and Alt-D retries the selected
target after cleanup. These live commands take precedence over imported
bindings. A recognized original local command that requires an unreconstructed
application service stops with **errorlevel4** and the message
`Unsupported keyboard binding or local command; terminal stopped.` Examples
include unsupported ASPECT/PROGRAM/HOOK KEY actions. Alt-1..Alt-0 now invoke
TEXT from an explicitly imported `/T:FILE.KEY`; see [LIVE_META_KEYS.md](LIVE_META_KEYS.md). Original
no-op or unmapped keys remain ignored rather than being transmitted as arbitrary
scan bytes. The complete original menus, scrollback commands, macros and
settings UI remain open.

## Explicit KBD import

`/K:FILE.KBD` reads the block for the effective display profile after validated
PRM/directory selection and before UART acquisition. The path is explicit;
there is no installed-file search, fallback file or automatic default import.
The file must have a positive length divisible by948 and contain the selected
profile. All79 selected12-byte strings must terminate within their slots.
Only a completely read, validated and successfully closed block replaces the
default map. Malformed input fails startup before serial hardware access.

The reader preserves raw bytes and opaque tails, with no assumed maximum block
count. Storedff emits wireNUL; stored00 terminates the binding. KBD slots do not
interpret caret escapes or pause markers. Their storage limit is11 content
bytes. `.KEY` files have a different action/macro format and cannot be used as
KBD maps. Directory SCRIPT/KEY/META bindings remain explicitly unsupported even
though this independent `/K` import is available.

The live sender validates the whole binding and reserves TX-ring capacity before
queuing any byte. Invalid slots or unterminated bindings stop with errorlevel4;
queue overflow stops with errorlevel3 without partially queuing that binding.
It uses foreground flow-aware UART progress, not the original blocking
per-byte calibration delay or complete KEY macro engine.

## BIOS choice and keypad distinctions

`/B:AUTO` is the default. The recovered36-byte detector reads physical BDA0496h
bit4 and selects INT16h10/11 when set, otherwise00/01. `/B:STANDARD` forces00/01;
`/B:ENHANCED` forces10/11 for firmware where those functions exist but the flag
is unreliable. Manual ENHANCED is an override, not a capability probe. See
[KEYBOARD_DETECTION.md](KEYBOARD_DETECTION.md) for the original instructions and
physical XT/AT validation boundary.

The live read path retains raw E0 distinctions before classification. It also
maps alternate BIOS words1ce0/35e0 to the proved keypad Enter/slash identities
e00d/e02f. Those two aliases are maintained compatibility behavior; the original
dispatcher directly proves only the latter forms. The second UI normalizer is
not used to erase keypad identities before live classification.

## Verification boundary

The recovered mapping and detection modules have source-only flat/OMF, CPU and
DOS diagnostics. Host codecs and DOS KBD tests cover malformed files, exact
offsets, ff/NUL, unchanged destinations, close errors and profile blocks beyond
64K. `check_key_output.py` checks actual linked TX-ring/UART instructions,
whole-binding atomicity and all79 slots. `test_terminal_keys.py` exercises BIOS
events, modifiers and explicit synthetic profile4/6 import through the live DOS
binary: ten actual DOS cases pass, including F11/F12 with Shift/Ctrl, both
imported profiles, binary NUL and quiet rejection of invalid files.
`check_key_live.py` passes95 linked inputs: all79 raw key slots,12 automatic/
manual BIOS selections, two low-E0 aliases and two empty enhanced-page local
boundaries. Runtime results belong to their recorded binary hashes; these checks do
not establish physical keyboard/firmware or full original UI compatibility.

```sh
./tools/build test-keyboard_mapping test-keyboard-mapping-raw test-keyboard_detection
./tools/build test-keymap test-keymap-dos
./tools/build terminal test-terminal
```
