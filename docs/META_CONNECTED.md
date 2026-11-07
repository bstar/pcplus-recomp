# Connected Meta editor and capacity gate

The opt-in Alt-M parent `b92cdae7…` passes a local editing round trip inside
actual stock Enigma and Synchronet editors through the real SynthModem Telnet
proxy. It is **not release eligible**: a separate ordinary DOS8086 six-stream/
nested-child workload regresses versus the unchanged installed-build control.
No physical files, deployment selector, BBS service or SynthModem configuration
were changed. RCE81708 remains installed.

## Connected behavior

The passive BIOS/VGA observer captures the stock editor before Alt-M, the Meta
window with an accepted `ZZZ` definition, and the stock editor after Escape.
Both servers preserve all4000 screen bytes, cursor position, cursor shape,
25-row geometry and BIOS mode3. The local edit never reaches the BBS, no KEY
file is implicitly saved, and the ordinary Home/End/Delete/Insert/Tab/Page-key
editing workflow resumes. The synthetic draft remains unsaved; server evidence
checks authentication/editor entry and no published message.

Independent replay of the exact delivered BBS prefix matches all1920 logical
cells and attributes with zero differences. A real CPR bounds each snapshot;
actual NAWS is80x24 while BIOS remains80x25. Ten copied-evidence controls per
server reject damaged return characters/attributes, cursor/shape, heading,
definition, incomplete observer, truncation and leaked local keys; unchanged
copies pass. Existing non-Meta observer and BIOS-helper variants remain exactly
byte-identical in six comparisons against their preceding committed source.

Enigma runs the observed workflow on DOS8086. Synchronet's ordinary unobserved
DOS8086 core workflow passes separately. Its12KB passive observer prevents
ASPECT startup in conventional memory, so the accepted observed run explicitly
uses DOS386/XMS/UMB and records observer segmentCC4Bh. That diagnostic change is
not an application fix or a physical-memory claim. The source-built ASPECT
helper is rebuilt with current source provenance and remains byte-identical to
`5c641ac4…`; stale manifests are not waived.

These tests use the existing250ms key framing and20ms input pacing. They do not
prove immediate/unframed delivery, physical CTS, Boca/SPA2102/SIP/audio behavior,
all BBS screens, other geometries or complete original PCPlus parity.

## Confirmed capacity regression

All ordinary tests below use the same DOS8086 fixture, source-built interpreter,
six buffered streams across three nested DOS children, VT220/ANSI switching,
missing-file recovery and same-process continuation. No observer is installed.

| Parent | Minimum retained bytes | Result |
| --- | ---: | --- |
| Disabled/installed control `ff6bb369…` |479024|All30 checks pass |
| Meta loader only `b2f3722c…` |480608|Workload fails |
| Alt-M frontend `b92cdae7…` |483616|Workload fails |

The full frontend fails seven checks: FIRST completion/count/file, six-stream
completion/files, three nested children, and final profile viewport restoration.
The owned missing-file recovery and later keyboard/connection shutdown still
work. The visible native report is out-of-memory at opcode9B, step20. This is a
release-blocking failure, despite the passing connected modal/editor checks.

Separate386/UMB passive allocation traces retain failures alongside the control:

- Frontend: an AH4A resize requests8547 paragraphs; DOS reports carry, AX8 and
  maximum8536, an immediate176-byte shortfall. Recorded exits are8,8,0,8.
- Loader only: an AH48 allocation requests254 paragraphs; DOS reports carry,
  AX8 and maximum9 paragraphs. Recorded exits are10,10,0,10.
- Control: all four exits are0 and no sampled memory request fails. Successful
  sampled resize demand reaches8675 paragraphs.

The observer records only a bounded prefix of allocations and changes the
launch environment. These traces identify concrete DOS memory refusals; they
do not establish the complete peak or a sufficient funding target. Saving only
the first176-byte deficit would not establish workload recovery. The ordinary
unobserved run remains the acceptance gate.

## Next application work

Reduce the retained cost of Meta loading and frontend integration without
removing the editor or reducing streams, stack, history, receive buffers or
screen capacities. The loader-only refusal shows that moving only UI prose is
insufficient. Evaluate a shared/transient loader/frontend design and reuse the
existing arena with explicit lifetime/verification guards. Then repeat the
ordinary30-check workload, the existing direct/fault loader and editor checks,
the eight frontend cases, exact source reproduction and both connected BBS
round trips before considering deployment.

[The combined receipt](validation/meta-connected.json) binds accepted BBS
captures and negative controls, ordinary paired capacity results and separate
allocation traces. Failed attempts and the lower-memory control remain distinct;
no failure is converted into compatibility acceptance.
