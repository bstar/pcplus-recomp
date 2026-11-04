# ENiGMA editor across Telnet size updates

The staged [codec resize API](../lab/bbs/patches/synthmodem-window-size/README.md)
now has an actual, authenticated multiline-editor comparison on the owned
loopback ENiGMA fixture. This tests the remote editor boundary needed by the
unfinished online PCPlus Status/Lines controls. It does not enable those controls.

Two independent sessions use the same staged codec, synthetic account and draft.
The control advertises80x24 throughout. The second advertises80x24, enters30
numbered hard lines, advertises80x25 while the body is focused, edits and pages,
then advertises80x24 and repeats before explicitly discarding the draft.
Server NAWS logs independently identify each session and its ordered sizes.
The message table count is checked before and after both sessions.

| Operation | Observed document position in both sessions |
| --- | --- |
|30 numbered lines entered | INS31,01 |
| Type G after growing | INS31,02 |
| Page Up, then Page Down | INS17,02 → INS31,02 |
| Type S after shrinking | INS31,03 |
| Page Up, then Page Down | INS17,03 → INS31,03 |
| Escape, select Discard, Enter | Message-area menu |

The nine captured editor-output steps, including seed, both markers, four page
operations and the two discard-selection steps, are byte-identical between
sessions. Both final page redraws retain numbered lines18–30 and the expected
G/GS draft tail. The returned menu is also compared, with only its explicitly
located wall-clock text excluded; both raw hashes and actual clock values remain
in the report. A stricter preliminary repeat caught a minute rollover in that
field. No editor bytes are normalized.

Neither resize produces display data during its500ms observation window.
Subsequent paging still moves14 document lines, exactly as in the fixed-size
control. Thus this particular art-backed editor preserves focus, draft and
navigation across NAWS updates, but these updates do **not** establish dynamic
editor reflow or redraw. NAWS logging alone must not be used as an acknowledgment
that the active application adopted a new layout.

The Node peer executes the actual staged codec and real TCP BBS connection. Its
declared home CPR matches the existing independent editor reference; it is not
the DOS renderer. Sources are hashed before the run and verified afterward;
the fixture lock excludes other cooperative DOS lab runs. Captures stay under
ignored build storage. The [receipt](validation/telnet-editor-resize.json) binds
the accepted result and source identities.

```sh
./tools/dev --command python lab/bbs/test_telnet_resize_editor.py \
  --codec build/telnet-resize-checked-20261104/src/telnet/TelnetCodec.js \
  --output build/NEW-editor-resize
```

The installed SynthModem, live LoC board and PCPlus packages are unchanged.
DOS-to-bridge control, coherent local/remote geometry, refusal/disconnect
recovery, other editors/art/pages, full-route binary transfers and physical
Boca/SPA2102 acceptance remain open. The offline status owner still refuses
connected requests; these tests do not justify removing that guard.
