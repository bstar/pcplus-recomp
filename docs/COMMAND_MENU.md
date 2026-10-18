# Maintained command menu and help

Alt-Z opens a keyboard command menu in the maintained DOS terminal. This is
source-owned UI and help, not a recovered copy of PCPlus menus or help text.

| Group | Commands |
| --- | --- |
| File | Receive, send, screen file, capture open/close, capture hold/resume, CR-adds-LF, exit |
| Connection | Dial the selected target, hang up, send BREAK |
| View | Redisplay, filename clipboard, raw monitor, printer copy |
| Setup | Edit the eligible saved PRM with PRMEDIT |
| Help | Using the menu, keyboard/session commands, application status |

Left/Right or Tab changes groups; Shift-Tab moves backward. Up/Down and Home/End
select a command. Enter or a listed letter runs it. F1 shows contextual help.
Within help, Up/Down or PgUp/PgDn changes topics. `/` searches command names and
help prose with an ASCII case-insensitive query of at most31 characters. Escape
leaves a search/help page, then closes the menu. Alt-X exits directly.

Each command uses its existing service and eligibility checks. Capture still
asks for a DOS path and Enter accepts PCPLUS.LOG. Receive/send still ask for a
file or directory and offer F2 protocol selection. The settings command requires
the supported explicit current-folder8.3 PRM binding. Dial means the already
selected startup/directory target; this menu does not add a dialing-directory
browser during an active session. Unsupported whole-application features are
described as unfinished in the status help.

## Ownership and memory

The existing redisplay owner saves the live80x25 screen/cursor and supplies the
menu frame. Before normal receive parsing, it restores the live frame; afterward
it saves the updated live frame and restores the menu. Incoming UART data,
history, capture, parser controls and terminal replies continue while browsing.
Keyboard input stays local to the menu. Search text and cursor keys do not leak
to the BBS.

A selected command first closes the menu and restores the live screen. Its BIOS
key value then re-enters the existing command dispatcher. Redisplay/clipboard
commands acquire their ordinary guarded owner through the same path. No key is
injected into the BIOS queue or sent to the UART for this handoff. Active parser,
transfer, child/PROGRAM, macro, monitor/controller, BREAK, snapshot and modem
control ownership prevent a new menu. The existing mode3/page0/80x25 geometry
checks apply.

Menu logic is another CONFIG_CODE-local C module. Its constant names, help and
item table use Watcom's segment-constant objects based on the default code
segment. This places them in CONFIG_CODE under this build's compiler options,
before uninitialized far storage. Watcom documents this placement through
[`__based(__segname("_CODE"))`](https://open-watcom.github.io/open-watcom-v2-wikidocs/cguide.html#Segment_Constant_Based_Pointers_and_Objects).
Only48 added bytes of bounded state/query storage consume DGROUP. Existing
resident code and the85 checked far bridge pairs are unchanged. The linker/MZ
verifier checks menu entry placement, near state, retained code and uninitialized
screen/history extents; the real DOS PRMEDIT workflow exercises that retention.

## Verification

`standalone/check_command_menu_live.py` runs actual linked code with BIOS,
UART, video and DOS filesystem/PRN kernel boundaries modeled. Five groups/149 declared inputs cover navigation, contextual help
and bounded prose search, normal command dispatch, live receive/replies and
ownership/geometry refusal. It compares selected service state against the
existing direct hotkey path without replacing product functions. The printer
command opens the modeled checked device, stops admission on the next toggle,
and closes it through the normal drain/poll service.
An open capture also exercises menu hold/resume and close, verifying that held
text is omitted and resumed text reaches the checked file owner.

`standalone/test_command_menu_dos.py` runs three production DOS workflows on fresh
synthetic media. An independent INT1C observer samples actual menu/help rows and
the footer. The first workflow verifies groups, help search and a new remote
screen/status query during browsing. The second verifies exact processed
capture, a screen file containing live text rather than menu text, and canceled
receive/send prompts, then hangs up and dials the same selected target again
through menu commands. The third runs the real PRMEDIT child, checks that cancel
preserves the full PRM image, then reopens the menu and resumes typed serial
output. All cases include the independent UART/vector/PIC restoration checks
from their existing harnesses.

```sh
./tools/build test-command-menu
```

The initial DOS development recipe omitted Enter at the existing capture-path
prompt. Later keys therefore stayed in that prompt and no log was created. The
corrected recipe explicitly accepts the default; the failed attempt remains in
ignored local artifacts. Linked tests also exposed an incorrect conditional
conversion of code-based string pointers in the footer. Explicit branches now
pass the named code-segment objects to the far-pointer renderer.

[`validation/command-menu.json`](validation/command-menu.json) binds the149 linked
inputs, three DOS workflows, full77-command terminal regression and64-output
source-only rebuild to the frozen executable. It retains the actual observer,
wire, file, PRM and child artifacts by hash.

The same frozen executable passes selected stock Synchronet and ENiGMA menu-to-
clipboard/download workflows; ENiGMA also reopens it for the post-transfer file
search. `bbs-clipboard-transfers.json` retains a refused early Synchronet attempt
separately from its settled retry. The exact transient acquisition failure is
unproven, so this does not claim menu availability during every parser/owner
state. The stock editor recheck passes Synchronet and ENiGMA with an explicit30ms
buffering control; immediate ENiGMA retains Home/Insert failures. No BBS post is
saved. Temporary synthetic Synchronet logon exemptions are restored and
independently read back; physical modem behavior remains unverified.

Original pull-down layout, mouse interaction, complete settings/key editing,
other geometries and physical modem tests remain open. This component does not
close F02 or any whole-application gate.
