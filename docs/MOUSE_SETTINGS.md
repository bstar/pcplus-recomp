# Mouse settings during a session

The selectable mouse terminal now has a matching50-field `PRMEDIT.EXE` and
adopts saved X/Y scales when setup closes. The ordinary48-field editor and27
preceding application products remain byte-identical. The
[settings checkpoint receipt](validation/mouse-settings.json) records its tested builds;
[terminal integration](TERMINAL_MOUSE.md) describes the underlying owner.
The later [ENiGMA cancellation checkpoint](validation/enigma-cancel-download.json)
changes the four terminal products and preserves the matching editors. Its
source proof identifies those later binaries separately from this settings run.

```sh
./tools/build terminal-mouse
./tools/build package-mouse
./tools/build test-package-mouse
./tools/build test-setup-mouse
./tools/build test-terminal-mouse
./tools/build test-terminal-mouse-source
```

The build stages the matching editor beside the selectable terminal. Copy both
executables to the DOS working directory containing an externally identified
PCPlus2.01 PRM. Run `TERMINAL @PCPLUS.PRM`, open Alt-F10, and use the Terminal
page's Mouse X scale and Mouse Y scale fields. Save with F10, close with Escape
and acknowledge the return prompt. The next native mouse events use the saved
scales. The editor and return prompt still use the BIOS keyboard.

`package-mouse` stages the terminal, matching editor, XLT editor, ASPECT runner,
DOS compiler and two authored script examples under `build/dos-package-mouse`.
It checks each input manifest/source identity before copying. No configuration
or original executable is bundled. Copy those declared files into the DOS
working directory to use the sibling helpers together.

The package acceptance checks all ten declared file identities, compiles its
example with the packaged DOS compiler, compares the result byte for byte, and
runs both the compiled example and the source through the packaged runner.
Terminal navigation and settings adoption use the separate workflows below.

Both values admit1..999. They map only PRM04E4/04E6; unknown bytes stay opaque.
They are appended at indices48/49, leaving all preceding field indices intact.
The Terminal page uses14 field rows and retains its help/footer rows. Loaded
invalid values are repairable rather than silently normalized. To repair a
file before mouse/UART acquisition, use `TERMINAL /S @PCPLUS.PRM` with the
matching editor. The ordinary editor remains the separate48-field build.

## Staging and ownership

The existing canonical setup owner reads the saved PRM once after a successful
editor return. It validates the mouse candidate with the other settings before
publishing any active plan. A changed candidate reports change bit4000h; an
unchanged file does not advertise a mouse change. Failed children, aborted
transactions, rebinding and failed validation discard pending mouse offers.

The parent mouse is suspended throughout the editor. A successful foreground
acknowledgement updates only the suspended owner's retained settings. Resume
initializes the driver with those scales. It does not allocate another owner
or replace the original driver/native snapshots. Repeated changes and a revert
therefore still restore the actual pre-session state at shutdown.

Reconfiguration checks the driver vector, state size, snapshot guards and native
callback depth. If those no longer match, it retains quarantine and the parent
stops the session through its existing safe shutdown policy. It does not reset
an unknown replacement driver. Normal missing/unsupported-driver fallback stays
on BIOS input; applying scales does not acquire a newly installed driver.

## Evidence

The pure editor model passes470 inputs for the50-field variant and450 for the
ordinary48-field regression, including actual DOS runtime checks. Mouse-specific
cases cover range rejection, exact two-byte edits, invalid loaded values and
explicit repair. Both ordinary and selectable editors reproduce from a fresh
source tree, as do all31 selected application products.

The linked production policy passes31 cases, including staging without driver
mutation, failed-offer discard, unchanged-file handling, driver/guard/depth
quarantine, rebinding with an unpublished offer, and repeated edits/revert
retaining one original snapshot/allocation.
The first rebind candidate incorrectly applied16/8 after a new binding should
have kept8/4. A replay of that frozen candidate retains the counterexample;
the corrected binding discards the offer and passes the regression.

Twelve actual8086 DOS workflows pass119 independent assertions. In addition to
the earlier menu, child, fallback and retained-callback cases, they prove:

- Saving16/8 changes the native event result: a16-unit vertical movement selects
  the expected second menu row at scale8. The old scale4 would select a different
  row. The selected Write screen action produces the actual live-screen file.
- Discarding staged edits leaves the original movement behavior and PRM bytes.
- A controlled child saving invalid mouse data plus a valid color edit does not
  partially apply the color or scales. New received text retains the old color.
- A child reporting failure after saving valid new values likewise leaves the
  active settings intact, while retaining the expected on-disk changes.
- Startup `/S` repairs both zero scales before acquisition; ordinary terminal
  replies and native mouse menu input then work.

All576 opaque driver bytes restore exactly in the normal cases. The controlled
quarantine case still returns030Eh, retains a valid callback, and is repaired and
reclaimed only by the independent observer. Component regressions retain244
linked cases and130 actual DOS assertions. The new capability7 parent passes92
actual fault-recovery cases; the separate isolated ENiGMA route passes20 checks
with DOS source login and20ms-paced client bytes. Those are distinct scopes.

The current terminal uses65394 resident code bytes,64864 near data/stack bytes
and a2666-byte mouse bank. Ten far bridge pairs are checked. The source proof
preserves all27 preceding application binaries and the ordinary editor's
pre-change checksum. No original executable, installation or analysis database
is an application build input.

Startup-directory mouse input, return-prompt mouse acknowledgement, the ASPECT
child's own mouse services, physical mouse/modem validation, other DOS kernels
and the wider application requirements remain open. The live ENiGMA decoder
is unchanged. No whole-application gate closes.
