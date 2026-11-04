# Actual larger-height ASPECT sessions

The parent and a current source-built ASPECT child now have actual DOS session
evidence at25/28/43/50 physical rows with profiles4 and6. This advances the
[parent admission component](ASPECT_LARGE_ROWS.md) beyond pure policy checks.
It remains an internal integration checkpoint; normal line switching/startup
preferences and hardware/BBS acceptance are not enabled by these tests.

The ordinary image stays byte-identical:
`644c76d66e3a07118e278c00ddb94dccb26f02e1466645d7e18b8ef715f111bf`.
A diagnostic `--session-rows-probe N` calls the real canonical row transaction
after reset capture and before enabling/dialing the UART, then enters the normal
main loop. Failure exits34 through ordinary cleanup. It requires the ASPECT row
owner and excludes display/status/editor admission probes. Package staging explicitly refuses
these session diagnostics. The diagnostic adds26 resident bytes and no near data;
the ordinary image and deployment pointers are unchanged.

## Session coverage

The [receipt](validation/aspect-large-sessions.json) records exact products,
flags, source manifests, raw captures, checker inputs and source-only rebuilds.

The24 actual DOSBox-X8086 sessions cover two profiles × four heights × three
workflows, on an emulated COM3/IRQ5 with a synthetic modem peer:

-Query/render/return: the peer sends CONNECT and initial text in the same write,
 then renders a marker on the last logical row and requests CPR/DA. The actual
 parent/child parser generates replies. After child exit, literal parent keyboard
 input triggers another CPR and CSI18t size report. Exact bottom contents, logical
 dimensions and parent keyboard resumption are checked.
-RIS: native reset clears the previous bottom marker while retaining accepted
 logical dimensions and the physical status row. The post-child parent still
 answers CPR and reports the selected dimensions.
-Cooperative window: the script waits for peer data while its actual Alt-Z window
 is open. Timed peer chunks, scheduled from script-origin KEYREADY, update the
 last logical row and request CPR before END releases the script. A timer observer
 witnesses the actual window and renderer advancement while visible. The final
 lower-row UPDATEDEND content survives the25-row window prefix restoration,
 script completion and parent return.

The ordinary main loop, scheduling, DOS EXEC, child, shared renderer, parser,
UART/keyboard instructions and checked cleanup execute normally. The peer supplies
only literal input/queries; no terminal reply or product callback is substituted.
The status footer is captured after shutdown: normal25-row connection notices
show Disconnected, while larger layouts retain the existing footer because the
connection-notice lease currently admits only row25. This is a remaining notice
integration gap, not evidence of live carrier loss in these connected sessions.

The observer reads EXEC/JFT/owner/history/cursor state and enqueues literal BIOS
keys: Alt-Z after36 child ticks for window cases, READY after36 return ticks,
and Alt-X after72 return ticks. A separate30-second ADDKEY exit remains as a
bounded fallback. An empty delayed key list produced no serial traffic before the fixture
timed out; early fixed exit schedules truncated paced dialing. The accepted harness uses
real EXEC lifecycle events for interaction and checks real child exit0, rather
than mistaking early-exit fixture output for a modem regression. These are
synthetic BIOS events, not human or physical keyboard tests.

Every session checks the full8,000-byte VRAM capture (comparisons use the selected
physical/logical region), unchanged synthetic PRM, only expected directory
accounting, unchanged staged inputs, parent JFT/sink ownership, generated replies,
selected footer and42-byte UART/PIC/vector restoration. A separate artifact checker
verifies the actual exit cursor/profile and retained far-history bytes across EXEC,
including the relocation-derived segment and63,000-byte pointer bounds.

## Source-built child and repeatability

The matching child is SHA256
`84160498dcd540a725508b8f1f2ade6b4c6c2c548391947795a3abd3e98b67d8`.
It was rebuilt from288 current public source files in a fresh tree, without original
inputs or ancestor Git, with parent render, banked notices/sound/input/help,
help resource, serial/register banks and custom IRQ support. It is byte-identical
to the previous matched child, with an updated source manifest; stale manifests
were not relabeled as current.

The ordinary and four diagnostic parents each reproduce exactly from569 declared
public files in independent empty trees with pinned Nix. The source-proof helper
now permits the bounded numeric argument to `--session-rows-probe`; it still
rejects output-directory injection and undeclared flag values.

Reproduce the receipt's parent flags via `./tools/dev --command python
standalone/build_terminal.py ... --output-dir build/NEW`. For each profile use
`standalone/test_aspect_large_session_dos.py --build PARENT-BUILD --runner
ASPECT.EXE --profile 4 --rows 28 --output build/NEW` inside the pinned environment;
omit `--rows` for all four heights and use profile6 for the other matrix half.
The session harness stages the parent and child together for real sibling lookup,
retains distinct synthetic data, compiles owned scripts, uses a12,000-cycle8086
configuration and captures the complete50-row VRAM allocation. This cycle setting
is not a physical performance measurement. The source-proof and artifact-checker
commands/inputs are recorded separately in the receipt.

## Remaining acceptance

Nested native PROGRAM still excludes28-row14-pixel ROM font restoration. Verify
that path and SAVE/NOCLEAR/return adoption before claiming all larger-height script
workflows. Larger-height connection-notice placement also needs integration;
connection_ui.asm still deliberately refuses non-row25 notice leases. Partial CSI,
errors, cancellation, carrier-loss/reconnect and full transfer interactions at these
heights need their own session coverage, alongside other fixed-height modal owners.

These sessions use a synthetic serial modem and CP437/ANSI streams, not live Enigma,
Synchronet, SIP/analog, physical DCD/CTS behavior or real hardware. Broader emulations,
ASPECT/Host parity and the overall goal remain open. No card, private settings or
call history, installed bridge/service, selected package or deployed application
changed.
