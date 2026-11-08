# Enigma editor navigation checkpoint

The existing17-file compiler-bridge candidate passes explicit Backspace and
up/down/right editing in the stock Enigma editor. This adds coverage without
changing the application binaries or the physical installation. The
[validation record](validation/aspect-compiler-navigation.json) binds the capture,
checks and counterexamples to the [packaged candidate](ASPECT_COMPILER_PACKAGE.md).

Actual DOS BIOS keyboard input enters24 numbered lines. From the blank25th line,
Up and two Right keys select the third character of R24; Backspace removes2 and
insertingX producesRX4. Home, Down, Up and Down return to the blank line.
The audit requires the complete eleven-position document-coordinate history,
including Page Up to line14. After insertingUPMARK, Page Down returns to line25
and UNSAVED is entered. The exact final fourteen-line viewport containsRX4,
UPMARKR14 and UNSAVED, with footerINS25,08.

A separate reference audits the89792 delivered bytes through the final CPR
boundary. All1920 logical cells and the cursor match: zero differing cells.
The test authenticates to the owned stock loopback server, enters its real editor
and disconnects without saving a post. It uses the actual SynthModem Telnet proxy
with paced serial delivery; SIP, DSP, audio and physical CTS are outside this test.

The semantic controls accept the original and reject eleven copied counterexamples,
including missing Backspace/arrows, altered cursor history and a lost edit.
Independent screen controls accept the original and reject eight glyph, attribute,
bottom-row, cursor, prefix, font and proxy-input mutations. The existing Page Down
capture still passes its original acceptance and five rejection controls.
No corrupted copy is supplied to a server or executed as an application.

This is the fifth exact stock-editor snapshot for the current candidate. Other
geometries, keyboard profiles, every intermediate frame, font pixels and physical
hardware still require their own acceptance. Full original ASPECT, emulation,
protocol and Host parity remain open.
