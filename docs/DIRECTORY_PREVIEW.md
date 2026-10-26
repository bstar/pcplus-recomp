# Serviced Alt-D selection preview — 2.01-LoC.5

The explicit `--directory-preview` build adds Enter on a published Alt-D page.
Preparation runs on the next foreground idle turn, then shows the proposed name,
target, connection mode, COM/IRQ/base, DTE speed and line settings, flow control,
terminal profile, saved protocol and transfer preferences. Escape returns to the
directory; another Escape returns to the updated BBS screen. Preparation can be
canceled before it runs. Invalid settings show a readable refusal and preserve
the current session and previous proposal.

The original magenta splash now identifies version 2.01-LoC.5. Original logo,
LoC Special Edition and Sysop bstar remain. Older variants retain their own
version strings. The staged application contains no private PRM/DIR/XLT files.

This is the live preview milestone. It does not adopt the selected entry, dial,
change active settings, execute stored scripts or send stored passwords. The
full dialing chooser, original interface restoration and F01–F16 plan remain
required. The live SynthModem/BBS/network and removable card are unchanged.

## Accepted state and storage ownership

The CONFIG_CODE entry copies the accepted in-memory PRM through
`hook_baseline_copy`, which verifies its generation-bound corruption seal. It
captures the actual session through a far-cdecl adapter to
`terminal_session_capture_far` with policy 1. It then runs the
[selection transaction](DIRECTORY_SELECTION.md). The startup importer is not
called; a changed on-disk PRM cannot silently replace the accepted source.

The preview borrows another 1,190 bytes of the empty command-history snapshot,
immediately after its two 1,394-byte page buffers: 3,978 bytes total. Live history,
live screen and viewer screen remain separate. The existing browser/editor/
PROGRAM guards retain this lease until the command view releases. No buffers,
history, queues or stacks are reduced. The resident code does not grow.

The full owner call, including accepted PRM and actual configuration locals,
uses 6,292 of 8,192 stack bytes in linked execution. The memory validator checks
the bank locations, exact actual-policy adapter instructions, forwarded caller
word and MZ relocation. Damaged policy, argument and relocation controls reject.

| Resource | LoC.4 | LoC.5 |
| --- | ---: | ---: |
| Near data and stack | 64,272 | 64,272 |
| Resident code | 65,506 | 65,506 |
| Physical full-screen buffers | 12,000 | 12,000 |
| Minimum retained parent bytes | 402,240 | 405,520 |
| History capacity | 63,000 | 63,000 |

## Acceptance evidence

The [receipt](validation/directory-preview.json) binds the final candidate and
its tests. Linked menu tests cover the real far leases, accepted baseline,
actual COM3/IRQ5 at 38400 despite different configured values, CLI precedence,
private-field suppression, unchanged adoption planes, bounded errors and
cancel/return. A separate case displays a complete 63-byte download path and
115200 DTE speed. The complete owner stays within the 8 KiB stack budget.

Actual DOS8086 COM3/IRQ5 at 19200 captures the path prompt, loading, first/last
pages and proposed settings with a passive timer observer. The preview contains
the expected target and transport fields, hides private fields, answers the BBS
cursor query and returns to ordinary keyboard input and the updated BBS screen.
Its PNG is rendered using the actual captured VGA ROM font.

The stock ENiGMA editor test opens the preview before resuming typing, through
the actual SynthModem proxy with 20ms input-byte pacing and 250ms key framing.
It requires observed preview/pages, successful authentication, exact Home/
Insert editor semantics, `UNSAVED`/`OVR 01,08` video and no saved post. This is a
software connection test, excluding SIP/DSP, analog audio and physical CTS/DCD.

Packaged START repeats nested DOS source compilation and exact script replay;
SETUP returns after the saved-settings editor and captures the LoC.5 splash.
Both preserve private fixture files, restore PCPLUS and hardware and retain
the packaged binaries. A clean 758-source export reproduces all ten package
files exactly without an original installation or ancestor Git metadata.

## Reproduce

```sh
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --custom-irq --directory-preview --output build/preview-NEW
./tools/dev --command python3 standalone/check_directory_view.py \
  --terminal build/terminal-directory-preview-c6142e053593/TERMINAL.EXE
./tools/dev --command python3 standalone/test_directory_view_dos.py \
  --terminal build/terminal-directory-preview-c6142e053593/TERMINAL.EXE \
  --preview --label preview-NEW
```

Use the staged package path and binary identity from the receipt when reviewing
these results. Packaging does not access or update a removable card.

## Remaining application work

Selection adoption must resolve canonical resource identities and claims,
stage KEY/META/translation/script resources, check baseline freshness, and
flush or retain accounting against the old selection. UART/profile handoff
must follow the existing quiescence and confirmation rules. Transfer settings
need their own comparison against active preferences. A preview is not proof
of resource availability or permission to switch a connected UART.

ENiGMA rendering/input, sustained data, disconnect/reconnect and transfers still
need the real Boca/SPA2102 route. Broader BBS workflows, other original command
services, full F01–F16 and card/hardware acceptance remain open.
