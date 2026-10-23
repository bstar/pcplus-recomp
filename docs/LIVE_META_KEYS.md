# Live KEY TEXT actions

`TERMINAL /T:C:\PCPLUS\CUSTOM.KEY` explicitly imports a540-byte KEY file
before UART installation. Ten records contain a16-bit kind followed by52 bytes
of NUL-terminated stored text. Import validates every record and exact EOF,
closes the file, then commits the table. There is no implicit default-file search
or file creation. Omitting `/T` supplies ten empty TEXT actions.

Alt-1 through Alt-9 select records0..8; Alt-0 selects record9. Kind3 executes
TEXT. Kind1 executes a local DOS PROGRAM through a maintained safe-point
scheduler; see [LIVE_PROGRAM.md](LIVE_PROGRAM.md). Kinds0/2 (ASPECT, HOOK) remain
explicit unsupported actions, including empty definitions, and stop with
errorlevel4. Empty TEXT is a no-op; empty PROGRAM is rejected.
Directory KEY/META bindings remain unsupported; `/T` is a global explicit import.

The recovered caret decoder runs through the existing bounded adapter with a
52-byte source/destination capacity. A trailing caret is rejected before wire
output. `^@` produces stored ff, then wire NUL. Double `^^` produces1eh;
triple `^^^` produces a literal caret. A decoded NUL terminates transmission,
even when additional stored characters follow. KBD bindings use a separate
format and do not apply this caret grammar.

The pause byte comes from PRM01e2, defaulting to `~` without a PRM. Matching
occurs before ff-to-wire-NUL conversion. A pause consumes ten BIOS ticks:
the recovered delay caller passes9 and its callee increments the argument.
Full32-bit day ticks handle low-word wrap and BIOS midnight. PRM01e4 retains
the original calibrated character-delay units in the40-byte import plan; the
live sender deliberately uses fast ordinary-byte pacing. Those units have not
been identified as milliseconds. Local echo is not implemented by this sender.

TEXT output is nonblocking. Ordinary queued output, including terminal reports,
has priority. The foreground poll attempts at most one normal/macro UART write;
UART flow-control work retains its own responsibilities. A blocked transmitter
that makes no progress for36 BIOS ticks cancels TEXT and stops with errorlevel10.
Configured ten-tick pauses do not consume that stall allowance.

Normal keyboard events wait in a32-word FIFO during TEXT, preserving their order.
Escape cancels the action and deferred keys. Alt-X, Alt-H and Alt-D remain local
controls; hangup, redial and observed carrier loss cancel unsent TEXT and queued
keys before another session can start. Bytes already transmitted cannot be
withdrawn. FIFO overflow stops explicitly with errorlevel3. Macro bytes never
enter the ordinary TX ring, so cancellation does not discard queued ANSI replies.

`META_KEYS.md` documents exact recovered dispatch/sender instructions separately
from this maintained scheduling and validation policy. `check_meta_actions_live.py`
executes linked product instructions with modeled hardware, and
`test_meta_actions_dos.py` exercises real DOS file import, BIOS Alt-digit events,
binary UART delivery, pauses and hardware restoration using synthetic files.
Complete scripting, key editing, translation/font selection,
physical modem timing and the full PCPlus application remain open.

## Optional ASPECT action build

The separate [ASPECT KEY terminal](LIVE_ASPECT_KEYS.md) now supports global
kind0 filename actions, including empty no-ops, through the existing Script
owner. The unsupported-ASPECT statements above describe the unchanged baseline
products. HOOK and directory KEY/META import remain open.
