# Profile changes during setup

Alt-F10 can switch the maintained VT2204 and ANSI6 profiles during the session.
After saving and closing PRMEDIT, a separate question asks whether to switch,
reset keys/modes and clear the screen. Y confirms; any other key retains the
current profile. The answer returns to the terminal without consuming the next
ordinary key. A combined save asks independently about profile and same-port
serial changes, so either choice can be declined without discarding the other.

A [COM move](PORT_HANDOFF.md) is confirmed before the profile question. Declining or failing the COM move defers its serial/profile group together. Once the COM preflight passes, the profile can be accepted or declined separately; a new byte or carrier before commit cancels the move and coupled profile. These
remain partial maintained implementations of profiles4/6. Other emulations,
original factory profile resources and the full native loader are not supplied
by this workflow.

## Staging and identity

No live profile, keyboard or view changes before validation and confirmation.
With no `/K`, the same source-owned79-slot network defaults are built into a
separate948-byte buffer. The default builder takes a caller-owned near buffer
and rejects null/wrapping extents before writing; ordinary startup uses the same
builder for its live keymap.

With explicit `/K`, startup retains its DOS canonical absolute identity. The
target profile's complete948-byte block is then read through the existing strict
reader, validated and successfully closed before confirmation. Open, seek,
size, short-read, invalid-slot and close failures retain the active profile and
mapping. An explicit failed import never falls back to network defaults. The
canonical name must fit the reader's63-byte path contract; an overlong absolute
name disables the live switch while leaving the startup mapping usable.

The retained absolute name prevents a child working-directory change from
retargeting the keyboard read. This is DOS namespace binding, not a file-version
lock. A newly read valid target block may reflect a deliberate file update.
The PRM and selected directory continue to use their independent existing
identity/selection policies. Active parser ownership rejects profile staging.

## Committing a clean view

The foreground PROGRAM owner still owns the UART handoff. Once the child and
choices finish, it restores mode3 and the saved view, then commits a confirmed
profile before reinstalling the UART ISR. The old captured RIS baseline first
restores clean source-owned geometry, flags and modes rather than copying the
BBS's current cursor, margins, SGR or character-set state into the new defaults.

The desired display/profile settings are applied through the same display-only
routine used at startup. The staged keyboard is installed, tabs are initialized,
and the view is cleared/homed with the new configured attributes. Capturing RIS
then makes the new profile and mapping the baseline for later ESC c. No original
profile-loader or PCSETUP shared-memory shortcut is invoked.

The serial connection/controller, original hardware snapshot, RX/TX ownership,
application file owners and global META definitions remain in place. A switch
does not redial or transmit a modem/terminal-reset command to the BBS. Buffered
input remains available and fresh device-attribute queries report the selected
profile. A keyboard staging failure can still allow independently confirmed
serial/settings changes; a busy serial gate can still allow a confirmed profile.
The terminal view is intentionally cleared only after an accepted switch.

## Evidence

`check_live_setup_profile.py` executes32 linked cases through the actual policy,
choice, strict KBD reader, renderer, reset and driver. Both directions, repeated
switches, default/explicit maps, new DA replies and subsequent RIS are checked,
along with decline, all import failure categories, canonical identity, combined
choices, an established modem session and caller-owned default staging. Only
kernel/BIOS/UART boundaries are modeled; product functions are not substituted.

The actual DOS editor suite adds four profile cases: accepted default switch,
decline, explicit target map and missing target block. A loopback peer verifies
fresh DA/CPR and the correct post-switch F1 sequence. Screen cells prove clear
versus preservation; all UART/PIC/vector samples match startup and the independent
timer observes no unwanted line/rate change. These complement the six existing
settings/serial cases. Physical modem/BIOS testing remains separate work.

Run `./tools/build test-terminal`. The current hash-bound evidence is in
[validation/setup-live.json](validation/setup-live.json). Native reset/loader
reconstruction remains documented separately in [TERMINAL_RESET.md](TERMINAL_RESET.md).
