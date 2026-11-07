# Keyboard-editor entry during occupied terminal states

[Four DOS8086 workflows](validation/keymap-owner-dos.json) supplement the
earlier32 CPU admission cases. The exact reviewed `44891156…` parent and its
matched companions run against a synthetic serial modem. Real BIOS keys enter
recording, raw monitor, scrollback and a split ANSI sequence. Alt-F8 is attempted
while each state owns the terminal, then again after release.

An owned source-built counting child occupies the PCKEYMAP executable slot.
It appends one byte to a synthetic log and returns normally. The independent
UART peer checks that no launch exists after the occupied interval and before
the allowed request. Exactly one post-release entry, resumed keyboard input,
unchanged KBD/PRM/application files, normal DOS exit and UART/PIC/vector
restoration are required in every case. No product memory, owner callbacks or
instructions are injected or patched. This fixture is not packaged.

Each workflow also requires evidence of the real occupied state:

- Recording publishes the exact `recbeforerecafter` bytes as a complete ASPECT
  source, excluding the attempted local command, with staging files resolved.
- Raw monitor logs the exact binary peer bytes, including NUL/FF/ESC and an
  apparent CPR request, without an ANSI response during the monitor interval.
- A passive BIOS-timer observer records the scrollback header/footer while
  the viewer is open. Escape then restores terminal input.
- The peer splits ESC/CSI collection by0.8 seconds around the attempted key.
  The actual terminal's resulting cursor-position reply proves completion
  before the post-release request. This is a bounded fragment interval, not an
  unbounded inter-character-wait guarantee.

These checks measure real UI refusal/release and PROGRAM admission with a
counting child. They do not replace the separate real-helper GUI/BBS results or
prove every internal gate, low-memory/error state, transfer state or nested
command combination. Physical Boca/SPA2102/SynthModem audio/CTS/DCD and private
configuration acceptance remain open. Installed files and the deployment
selector are unchanged.

```sh
./tools/dev --command python standalone/test_keymap_owner_dos.py \
  --terminal build/keymap-prefix-connection-verified-20261107/terminal/TERMINAL.EXE \
  --output build/my-keymap-owner-check
```
