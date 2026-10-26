# Alt-Z command reference — 2.01-LoC.3

The later [command-menu bank](COMMAND_MENU_BANK.md) keeps this behavior while
moving the controller out of CONFIG_CODE. Its package/hash/memory measurements
supersede the corresponding staging details below; Alt-D remains unfinished.

The new `--original-reference` candidate restores the original 39-command
reference arrangement: two Communications columns, Before/After/During/Other
subsections, Setup and Other Functions on the right. Backtick opens the separate
maintained command browser. Both views use the existing serviced foreground
screen owner; closing them restores the updated BBS display.

Arrows/Tab select an entry, Enter or its shortcut activates it, and F1 opens
authored contextual help for implemented commands. Escape returns from help to
the reference and then to the BBS. Backtick switches from the reference to the
browser; another backtick switches back. Local navigation never reaches the BBS.
This navigation, highlighting and command activation are maintained behavior.

Nineteen reference entries reach existing services or information. Twenty
unfinished commands are dim and show a visible refusal. Their original keys
also open that refusal from the terminal instead of ending the session.
Alt-D selects the pending directory command, and Alt-F8 selects the pending
key-map editor. The browser retains its explicit selected-target dialing
command. Alt-F5 opens the checked script filename prompt, and
Alt-W now reaches translation editing. Recorder ownership still blocks a new
script/serial owner until the recording is saved or canceled.

Alt-P continues to use the saved-settings editor. The dedicated original
line/port popup, live directory chooser, key-map editor, original mouse/pull-down
behavior and missing command services remain required. Displaying their names
and refusing them safely does not implement those services or close F02.

## Original evidence and source ownership

The [provenance](../reconstruction/command_reference/provenance.json) binds all
39 functional names and the frame/shortcut data to the identified original
2.01 executable's SHA256 and file offsets. REA's Ghidra MZ verification confirms
the immutable file/module identity and appended overlay extent. A memory search
does not find the reference because its bytes are appended data, not initialized
load-module memory; that negative result is not evidence of absence from the
file. The original file bytes were separately checked at the recorded offsets.

Names/grouping come from static artifact data. The new rendering and help are
authored source. No original runtime screenshot, original input-controller
equivalence, exact color equivalence or vendor help prose is claimed. Ordinary
builds never read the original executable or an analysis database.

## Build, preview and validation

```sh
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --custom-irq --original-reference --output build/NEW-reference
```

The local stage is `build/special-reference-final-20261025/PCPLUSSE`, with ten
public files including LOCHELP.HLP. The splash and VERSION.TXT identify LoC.3.
The card is absent and has not been written. A separate local `private-boca`
folder holds the previously described BOCA.PRM/LOC.BAT preparation; physical
flow/carrier behavior still requires confirmation.

`build/reference-dos/reference-01-20261025/reference.png` is an actual DOS video
capture rendered with the captured VGA ROM font. It is not a mockup or a web
font approximation. The passive timer observer never writes product memory,
reads UART registers or injects keys.

The [receipt](validation/command-reference.json) binds:

- 85 linked inputs covering all 39 labels/coordinates/attributes, all 20 direct
  refusals, navigation/help/browser return, UART parsing/replies/live frame,
  real transfer prompt/cancel, script/recorder ownership, translation and guards.
- The existing 29 original-key inputs on the same larger candidate.
- Actual DOS8086 COM3/IRQ5 reference, refusal, source help and browser captures;
  continued background cursor replies, unchanged PRM, exact hardware restoration,
  ordinary keyboard resumption and no hidden redial.
- A stock ENiGMA editor session through the actual corrected SynthModem proxy.
  The observer proves the reference/refusal opened inside the editor before
  typing resumes. Editor semantics, no saved post, the exact UNSAVED/OVR 01,08
  video result and normal return pass.
- Packaged START/SETUP and recorder cancellation through the backtick browser.
- Recording started/saved through the restored reference, followed by actual
  DOS compilation and exact UART replay, with hardware/file cleanup verified.
- Exact ten-file reproduction from 746 declared source inputs, with no originals
  or ancestor Git metadata. Ordinary, LoC.1 and LoC.2 controls retain their exact
  earlier binary hashes.
- The same ten files reproduce from only the 746 committed sources exported
  at `6d11fcc`, excluding all uncommitted worktree changes. Use the source-proof
  command with `--commit 6d11fcc` to repeat that boundary.

The 3,331-byte REFERENCE_CODE bank holds the new code and text. The full parent
retains 64,096 bytes of near data/stack; resident code is 65,386 bytes and
CONFIG_CODE is 65,184 bytes. Existing stacks and feature limits are unchanged.
This is a software UI/BBS checkpoint. Physical serial/audio integrity, transfers,
reconnects, multiline rendering and the rest of F01–F16 remain open.
