# Opening settings from the terminal

With `TERMINAL.EXE`, `PRMEDIT.EXE` and an existing, externally identified2.01
`PCPLUS.PRM` in the current DOS directory, run:

```dos
TERMINAL @PCPLUS.PRM
```

Alt-F10 opens the maintained settings editor after the terminal has started.
Tab and PageUp/PageDown navigate fields/pages; F10 validates and saves; Escape
closes the editor, with confirmation before discarding unsaved edits. Press a
key at the return prompt to resume the same terminal session.

**Saved changes currently take effect on the next terminal startup.** The open
connection keeps its existing configuration. The candidate decoder is now linked
in the terminal, but adopting its staged settings during the session is still
unfinished. The shortcut is the editor invocation step of that workflow, not a
claim that live configuration application or F02/F06 is complete.

The shortcut requires an explicit `@` current-directory8.3 leaf using letters,
digits, `_` or `-`; it accepts upper/lowercase. Drive-qualified and longer paths
remain supported by normal startup import but cannot open this editor yet. The
editor independently rejects DOS devices and recovery names before file I/O.
Unsupported requests leave the terminal running; the scheduler records status1
for an unavailable path,2 for a busy owner,0 for a queued request. These paths
still need a visible explanatory prompt in the eventual complete settings UI.

The launch is deferred to the foreground main loop. It uses the existing
PROGRAM owner to drain pending terminal replies and physical TEMT, send an
owned XOFF where configured, close capture, preserve DTR, lower RTS, release
the UART IRQ, retain all parent storage and execute local `PRMEDIT.EXE` directly.
It passes only a leading space and the bounded filename; COMSPEC and shell
command parsing are not involved. On return it restores the80x25 screen,
cursor/shape, configured UART format and ISR without discarding pending RBR,
then releases only its own software pause. A failed EXEC or nonzero editor exit
returns through the same restoration path and reports the failure at the key
prompt. NONE flow cannot guarantee incoming-data preservation during a child.

An active macro, child, BREAK, monitor, print controller or modem negotiation
prevents a second setup owner. Escape/Alt-X cancel a pending launch before EXEC.
The original Alt-S upload shortcut remains available. This is a maintained
Alt-F10 binding rather than a claim to reproduce the original Setup menu ABI.

`check_setup_live.py` executes the real linked scheduling, transport, process
and restoration code under modeled kernel/BIOS/UART boundaries. Its32 inputs
cover direct tails, unsupported paths, competing owners, cancel, failed EXEC,
failed child and physical TEMT/XOFF/XON ordering. `test_setup_live_dos.py` opens
the production editor from the running DOS terminal, checks cancel and an exact
baud-save image, then verifies the original terminal display, serial replies
and final UART/vector/PIC restoration. Synthetic PRMs and a loopback serial peer
are used throughout; this does not establish physical modem behavior.

Run both as part of `./tools/build test-terminal`. The editor's save/recovery
policy is in [SETUP_EDITOR.md](SETUP_EDITOR.md); staged runtime validation is in
[LIVE_CONFIGURATION_PLAN.md](LIVE_CONFIGURATION_PLAN.md).

This checkpoint passes all50 terminal regression commands and reproduces60
byte-identical outputs from a fresh maintained-source checkout. The actual DOS
cases additionally check that ordinary typed bytes reach the serial peer after
editor return. Hash-bound evidence is in [validation/setup-live.json](validation/setup-live.json).
