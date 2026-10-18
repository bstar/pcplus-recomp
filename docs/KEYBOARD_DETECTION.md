# Enhanced BIOS keyboard selection

The original selects enhanced INT16h functions from a BIOS data-area flag,
without invoking an enhanced BIOS function as a probe. Recovered resident
`7916..793a` is36 exact bytes. Startup overlay3 `d7a6` calls it with argument1 at
`d7bb`, before continuing application initialization. Its mode byte DS7ac0 is
outside the1,264-byte PRM block; no PRM field controls this helper's decision.

`reconstruction/keyboard_detection/provenance.json` binds the verified original
SHA256, range/file offset/hash and retained REA startup-caller evidence. The
helper was absent from automatic resident procedure exports; its actual bytes
were independently decoded with Nix-managed16-bit ndisasm. This is not a newly
generated REA procedure export. A direct-reference search of the resident image
and31 code overlays found reads7836/7842 and writes791b/7932; that does not
exclude indirect aliases elsewhere.

## Original behavior and maintained interface

Original `keyboard_select_bios_original(word)` is near, callee cleanup2, DS=SS:

1. Clear the mode byte to0.
2. If the argument is0, return without reading the BDA.
3. Otherwise set ES0 and test physical0496h bit10h (`0040:0096` bit4).
4. If set, write mode10h. Otherwise retain0.

Original argument1 means AUTO, not forced enhanced operation. BX/DX/ES/AX/flags
are scratch; AX is unspecified for argument0 and0/1 for AUTO. There is no INT16h,
DOS call, controller IO or keyboard-queue mutation. BIOS read7836 uses AH=mode;
peek7842 uses AH=mode+1, selecting functions00/01 or10/11 respectively.

Build `detect.asm` with `-DKEYBOARD_DETECTION_OMF`, importing the existing byte
`keyboard_bios_mode`. Maintained near wrapper `keyboard_detect_bios_mode()` has
no arguments, selects AUTO through the recovered helper and returns full AX0/10h.
It preserves BX/CX/DX/ES/BP/SI/DI/DS. Application startup can implement:

| Policy | Action |
| --- | --- |
| AUTO | Call the recovered detector through the preserved wrapper |
| STANDARD | Set mode0, selecting standard INT16h services |
| ENHANCED | Set mode10h, an intentional manual override of BDA detection |

AUTO is a read-only memory check that avoids unsupported enhanced BIOS calls
when the flag is clear. It reproduces original policy; it cannot certify every
XT/AT clone's firmware flag. STANDARD is the fallback for unreliable flags or
enhanced services. Manual ENHANCED requires those services to exist and is not
capability detection. Physical XT/AT validation remains open.

## Retained E0 keys versus UI normalization

First normalizer77d2 retains words with AL or AH equal to E0. `keyboard_read`
64fe uses that layer. Second normalizer7fe2, reached through
`keyboard_read_extended`7878, converts AL=E0 to AL0 for scan-only UI routing and
strips AH from ordinary characters.

The inspected terminal-style loop at1b83 calls **64fe**, stores AX to DS:cffa,
then invokes dispatcher1604 at1b93. It does not use the second normalization.
Original dispatcher comparison branches1a40..1a5d distinguish enhanced keypad
Enter `e00d` and slash `e02f`, selecting KBD slots5 and4.

| Raw word | After77d2 | After additional7fe2 |
| --- | --- | --- |
|e00d |e00d |000d |
|e02f |e02f |002f |
|1ce0 |1ce0 |1c00 |
|35e0 |35e0 |3500 |

The inspected dispatcher proves e00d/e02f support. Direct1ce0/35e0 handling is
not established. Mapping those alternate encodings to keypad keys is a maintained
compatibility choice, not an unchanged original branch. A live classifier must
declare whether it consumes retained BIOS words or the second UI-normalized
form. Enabling enhanced BIOS cannot restore distinctions already stripped.

## Source-only checks

```sh
./tools/dev --command python3 standalone/build_keyboard_detection.py
./tools/dev --command python3 standalone/check_keyboard_detection.py
./tools/dev --command python3 standalone/test_keyboard_detection_dos.py
```

Flat assembly matches the original36-byte hash without original build inputs.
CPU checks cover all256 BDA flag bytes and256 explicit-standard resets, preserved
wrapper registers, untouched BDA and stack cleanup; interrupts are forbidden in
that fixture. Actual DOSBox-X checks AUTO against its real emulated BDA and the
standard-reset branch. Enhanced F11/F12/keypad delivery still requires the
application's live keyboard tests; these checks do not certify physical firmware.
