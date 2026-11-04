# Authenticated editor references at admitted startup layouts

The owned editor harness now supports imported25/28/43/50-row physical layouts
with visible or hidden status, preserving the same source-built parent and child.
It exercises actual DOS startup → CSI18t → staged proxy → Telnet NAWS before
stock Enigma/Synchronet login and editing. This extends the
[checked ASPECT size-probe route](ASPECT_SIZE_PROBE_BBS.md). The independent
comparison covers every cell of the accepted logical area, not only the first24
rows of a larger screen.

## Geometry and capture ownership

Compiled initial geometry remains recorded separately. Explicit owned PRM words
select hidden state, selector2, preferred height and video0. Each actual DOS
workflow captures all8000 video bytes and a separate8-byte BIOS/BDA record after
return. The audit independently derives expected physical/logical rows from raw
PRM, checks actual rows/font/mode/columns/page, and decodes real TCP NAWS. It does
not infer a successful layout from a command-line argument or saved preference.

| Physical rows | Visible-status logical rows | Hidden-status logical rows | Font pixels |
| --- | --- | --- | --- |
| 25 | 24 | 25 | 16 |
| 28 | 27 | 28 | 14 |
| 43 | 42 | 43 | 8 |
| 50 | 49 | 50 | 8 |

The pinned pyte/wcwidth oracle now accepts an explicit admitted row count, while
its default remains24. Historical accepted Enigma/Synchronet references retain
byte-identical default cells/cursors. Reference captures still require an exact
delivered prefix, actual final CPR, and fixture consumption of only its own reply.
Later BBS output is held and retained separately. All logical cells are compared;
visible status is checked separately at the physical bottom row. Hidden status
makes that bottom row part of the cell comparison. Original font-probe projection
and unsupported-control refusal remain in effect; font pixels remain unverified.

## Fixture correction and recovery

The initial large-screen probe exposed the test-only BIOS keyboard helper's
4000-byte search bound. Actual Synchronet FSEditor put Insert Mode on row50;
its helper found the subject but never found that footer, so it never entered
the measured key sequence. The helper now accepts only the four explicit physical
screen extents4000/4480/6880/8000. Its default variant remains byte-identical to
the preceding accepted helper. This changes neither application code nor BBS
behavior. Failed prerequisites still lead to its existing bounded Alt-X exit.

That failed helper probe left a10-byte owned LABUSER draft containing only the
synthetic modem's shutdown text +++ATH. The next Synchronet attempt correctly
encountered a draft-resume prompt instead of Subject. After confirming that run
had ended, the exact known test-only draft was moved into an ignored backup,
with hash/length/path recorded; nothing was deleted or published. The recovery
runs retain the unchanged public producer and auditor. The original failed suite
stays failed; accepted per-case records can be collected only when the complete
16-case set has independent passing audits and matching current sources.

The synthetic Hayes boundary's shutdown behavior is not an analog escape/hangup
or carrier acceptance test. Proper completed Synchronet workflows explicitly
abort the test draft and preserve message bodies and official counters. The
Enigma workflow closes an unsaved connection; it does not test the discard menu.

## Reproduction

The owned stock fixtures must already be running. Use fresh output labels:

```sh
./tools/dev --command python lab/bbs/test_size_layout_editors.py \
  --runtime build/STAGE/candidate --terminal build/PARENT/TERMINAL.EXE \
  --runner build/CHILD/ASPECT.EXE --output build/NEW-editor-layouts
./tools/dev --command python lab/bbs/check_size_layout_editor_matrix.py \
  --run build/NEW-editor-layouts --output build/NEW-layout-audit
```

The producer serializes each peer's synthetic account while the two owned BBS
fixtures run independently. `--layout ROWS-HIDDEN` selects explicit probe cases.
The separate collector can combine accepted per-case records from a recovery
run without declaring a failed suite successful. It requires all16 unique cases,
successful producer/cell/size audits and current application/harness/runtime
hashes. The matrix checker then verifies every linked report/capture/source,
actual DOS return/hardware snapshots and the complete paired layout set.

Frame-mutation controls include first and final logical-cell character and
attribute changes, cursor changes, truncated prefix/proxy input and unsupported
font choices. They alter declared copies, never the application or live session.

## Acceptance scope

The [accepted receipt](validation/bbs-size-layout-editors.json) binds16 actual
workflows and46,080 matching logical character/attribute cells, with zero
differences and matching actual/reference cursors. The complete-matrix auditor
verifies all per-case reports, captured hashes, current sources and runtime
identities. Thirty-six copied-capture controls at visible43 and hidden50 rows
(four unchanged controls plus32 rejected mutations) verify first/bottom cell,
attribute, cursor, prefix, font and proxy-input sensitivity. The default24-row
oracle retains two historical references exactly; the default BIOS helper
retains its prior bytes. The original full-suite attempt still fails because of
the stale owned draft; its eight successful Enigma cases and the clean eight-case
Synchronet recovery are explicitly collected and independently checked. This
does not relabel the failed attempt as a successful suite invocation.

This is paced250ms key-framing/20ms serial-input,
8086 DOSBox-X COM3/3E8/IRQ5,19200/8N1/HARD evidence with synthetic Hayes and the
staged proxy. Native key semantics and one final editor frame per layout are separate from
multiline document scrolling, every intermediate redraw or application reflow.

The custom LoC main screen, broader modal return, sustained transfers/cancel/
carrier/reconnect and physical Cirrus/mouse/Boca/SPA2102/SIP/DSP/audio require
separate current-candidate checks. Live setup/HOOK adoption, online local resize,
other original commands/emulations/ASPECT/Host parity and verified deployment
remain open. Installed services, physical DOS/card files, private settings/call
history, host networking and packages remain unchanged. The full goal is active.

Application images remain unchanged: parent SHA256
`a2fd6a3fcdcc30138426d747d8cde400d9fc6eb9ca5fca84d1656aeaf17caa77`,
resident CS65,514/22 spare, near data/stack65,120. Its prior exact569-source
rebuild still matches all current application inputs. The matching ASPECT child
retains its prior bytes and all288 current public inputs. This checkpoint changes
owned validation tooling and evidence, not application code or deployed files.
