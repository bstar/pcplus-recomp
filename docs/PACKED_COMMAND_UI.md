# Command-browser memory recovery

The optional `--packed-command-ui` terminal build recovers4224 bytes from the
external-editor parent while retaining the exact reviewed ASPECT interpreter
and its512-byte heap-growth policy. The corrected candidate is
`build/editor-packed-ui-v3-20261106/TERMINAL.EXE`, SHA256
`72f3ced9e6090cd0e443ce822184c04612e8d244b51fc9e16f1f1ac196c86b09`.
Its minimum retained module is478656 bytes; DS=SS remains65488 bytes and resident
code65516 bytes. It is also3744 bytes below the reviewed viewer parent's
retention. No command, history buffer, script stack or stream capacity is removed.

This resolves the measured CRT startup/capacity gate for the software candidate.
The [acceptance receipt](validation/packed-command-ui.json) binds the executable,
UI comparison, source rebuild, actual DOS tests and both stock BBS sessions.
It does not deploy the candidate or close physical acceptance/full original parity.

## Source and runtime design

The build packs230 authored literals in `command_menu.c` using64 deterministic
byte-pair entries.12738 literal bytes become7972 plus a128-byte dictionary.
Each token refers only to earlier entries; the measured expansion depth is3.
The generator independently expands every literal and requires exact original
bytes before compiling. Compiler include/pragma directives and segment-name
strings are preserved. Only this module's display literals are transformed;
no private settings, original executable, resource database or external archive
is a build input.

The existing menu code bank holds both strings and dictionary. The C decoder
uses a bounded64-byte pending stack and no allocation. Drawing and help retain
their existing clipping/wrapping policies. Search uses a31-byte rolling window
over decoded characters, preserving overlap and case-insensitive matching.
No new DGROUP or resident-code allocation is introduced.

The optional `--command-ui-pairs 0` build is an uncompressed decoder control.
It is used for comparison, not memory admission: its retention is483056 bytes.
Reproduction flags distinguish the control from the actual packed product.
Removing the packing flag entirely reproduces the preceding editor image
`93f08d0c...` exactly from public source.

## Category pointer correction

Initial linked UI probes exposed a pre-existing two-dimensional based-array
conversion problem: category labels read unrelated configuration strings.
The new variant explicitly converts the category-array base to a far pointer
before applying the12-byte row stride. Both the packed candidate and uncompressed
decoder control use this correction, and the test explicitly requires all five
correct category labels. Their1146 complete4000-byte frames, menu return values
and owner/action states match through browsing, help, search and reference routes.
This is a comparison with a corrected control, not a claim that corrupted prior
category screens are unchanged.

The first generator attempt also transformed a pragma symbol string; the linker
rejected it before execution. Directive filtering was corrected. Those failed
attempts are retained locally and excluded from acceptance.

## Composed validation

Eighteen actual DOS8086 modal workflows cover12 editor and six viewer routes,
including both menus, cancellation, malformed configuration, maximum parameters,
child command-tail/current-directory identity and exact screen/cursor return.
Five copied linked-layout controls are rejected without executing damaged images.
A clean public-source export reproduces both packed and feature-disabled images.

The unchanged23caac93 ASPECT runner completes four script calls, all six
simultaneous file streams, missing-file handling and subsequent file recovery.
This distinguishes the memory fix from the rejected128-byte heap shortcut.

Final Enigma and Synchronet sessions execute sequentially through isolated
SynthModem proxies. Both run the Alt-A graphics child inside the unsaved stock
editor, restore the exact editor/cursor/shape, continue editing and abort the
draft. Independent reference interpretation matches1920 cells per server with
zero differences. The passive Synchronet witness records a successful real
script open and no CRT allocation message. It uses verified UMB observer/key
placements and retains the existing laboratory CPU/geometry restrictions.

Six X/Y/ZMODEM workflows after editor execution pass, including YMODEM
cancel/retry. Four carrier-loss/reconnect cases pass during text/graphics
children and partial YMODEM receive/ZMODEM upload. Same-parent redial and fresh
keyboard input are required. No physical SIP/audio/CTS claim follows.

An earlier v2 concurrent Enigma run restored the child/editor frame but failed
later semantic/final-screen checks. It is excluded. The final sequential v3
recipes pass; this does not establish that the category fix caused the timing
failure, nor acceptance of every timing pattern or disabled input framing.

Nested ASPECT PROGRAM composition, broader original language/emulation/protocol
parity, Host mode and physical hardware acceptance remain open. The installed
selection and reviewed package recipe remain unchanged at this checkpoint.
