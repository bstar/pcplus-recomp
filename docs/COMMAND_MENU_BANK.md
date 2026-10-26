# Command-menu bank and live-directory preparation

The reference candidate now keeps the command controller and its constant text
in REFERENCE_CODE, beside the 39-command reference. The serviced screen owner
stays in CONFIG_CODE. Its two compiled calls use an explicit far cdecl entry;
recorder admission calls return in the opposite direction. Shared frame and
near-state ownership do not change. Ordinary, LoC.1 and LoC.2 retain their near
entry and reproduce their previous executable hashes exactly.

This removes a code-space constraint before implementing the live Alt-D
directory. The startup chooser blocks on BIOS keyboard input and must not be
called directly from an active BBS session. Alt-D still reports unavailable;
neither a new chooser nor complete original command parity is claimed here.

| Resource | Before | After |
| --- | ---: | ---: |
| Resident code | 65,386 | 65,386 |
| CONFIG_CODE | 65,184 | 52,161 |
| REFERENCE_CODE | 3,331 | 16,364 |
| Near data and stacks | 64,096 | 64,096 |
| Retained history capacity | 63,000 | 63,000 |

CONFIG_CODE gains 13,023 bytes of space; its total spare capacity is now
13,375 bytes. Resident code still has only 150 bytes free. No stack, queue,
history or feature limit was reduced, and the separate UI bank remains well
below its 64KiB segment limit.

The [receipt](validation/command-menu-bank.json) binds the new executable,
memory layouts, source inputs, artifact hashes and passing checks:

- The memory validator verifies both compiled far calls and their MZ loader
  relocations, plus both recorder admission calls from the new bank.
- `standalone/check_command_menu_bank.py` observes 16 real cross-bank call
  frames and returns, including menu open/key/stop, shared frame identity,
  DS=SS, callee-preserved registers and caller stack ownership. Four damaged
  target/relocation controls are rejected by the full memory validator.
- All 85 command-reference and 29 original-key inputs pass. Actual DOS8086
  COM3/IRQ5 captures verify reference/help/browser return, continued serial
  replies, updated live-screen restoration and unchanged hardware.
- Actual DOS starts and saves a recording through the reference, compiles it
  with the DOS compiler, and replays the exact user UART bytes.
- Stock ENiGMA login/editor semantics and the observed reference/refusal pass
  through the real SynthModem proxy with each input byte spaced by 20ms.
  The final video check requires UNSAVED and OVR 01,08; this is not a complete
  cell-by-cell rendering comparison or a physical modem test.
- A clean export of 746 declared sources reproduces all ten package files.
  Original executables and private configuration are absent from build inputs.
  The same ten files reproduce from only the 746 committed sources at
  `6380609`, excluding pending worktree logger changes.

The staged package is
`build/special-command-bank-20261025/PCPLUSSE`. The terminal SHA256 is
`197f440e82ebad6b5adb97a563b0d70b46ebeb3c752dd64ab38020c190e6c323`.
No card, network, live SynthModem service or live BBS configuration was changed.

Build and check the current variant with the pinned Nix toolchain:

```sh
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --custom-irq --original-reference --output build/NEW-command-bank
./tools/dev --command python3 standalone/check_command_menu_bank.py \
  --terminal build/terminal-reference-c911e6208e81/TERMINAL.EXE
```

Next implement a serviced directory foreground view, explicit idle-line
selection/profile adoption, cancel without session mutation, and directory
accounting/key/script handoff. Active connection, incoming data and screen
restoration must remain intact while browsing. Dedicated port/key-map UI,
other refused services, physical acceptance and the full F01–F16 plan remain.

The later [incremental reader](DIRECTORY_READER.md) supplies a checked,
bounded-work loading component for that view. Parent integration and selection
adoption remain open.
