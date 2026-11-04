# Canonical display selector transaction

The display-preferences component now composes the
[physical selector service](DISPLAY_SELECTOR_SERVICE.md) with the existing
[BIOS/canonical row owner](ROW_GEOMETRY_TRANSACTION.md). Its optional far APIs
are `terminal_display_select(selector, rows, mode)`,
`terminal_display_apply_saved()` and `terminal_display_cycle()`. No normal
key/menu or automatic startup application is enabled yet.

A commit reconciles actual mode/rows with parser bounds, captured RIS defaults,
status placement, complete shadow storage and accepted-selector metadata. It
performs configured RIS, clearing content and restoring configured attributes,
tabs and keys. It retains current history and queued UART bytes. The raw saved
preference capture remains unchanged. Success is a coherent accepted display,
not proof that BIOS honored the original request.

## Selection and publication

The owner retains its disconnected, mode3/B800,80-column, unprotected profile4/6
admission and existing exclusive frame/recorder/script/transfer/notice gates.
It preflights the predicted row count, saves the existing rollback planes and
suspends the actual mouse owner before mode/font changes. After physical
selection it uses independently probed rows; if fallback changed the plan, it
restages RIS defaults for the accepted count before rendering.

An ordinary selector success or verified physical fallback can commit. A physical
return3/fallback1 becomes transaction return0 with accepted selector1,
`terminal_display_fallback=1` and `terminal_display_physical_result=3`. An ordinary
policy fallback records physical result0 instead. Live selector readiness is
published only after canonical/RIS/status/shadow/cursor commit. A subsequent
mouse-resume failure retains that coherent selector/geometry and requests the
existing quarantined fatal exit14; it does not resume normal parsing.

Saved application requires a successful preference capture. It normalizes the
saved status-hidden WORD by zero/nonzero and selects the saved selector/rows/mode.
Cycling requires both saved preferences and a live accepted selector. It uses
two choices when preferred-video WORD is zero and four for every nonzero WORD,
then cycles from the **accepted** selector. Signed-negative preferred modes still
choose the four-way cycle, while physical admission can fall back to selector1.
Malformed selectors are refused; publicFFFF cannot enter the private row-only
sentinel path. Missing captured/live selection returns7. Actual MZ entry clears
live-selector readiness independently of BSS contents. A successful direct
`terminal_row_geometry_set()` invalidates the derived selector, since it did not
select through that policy. A status visibility change alone does not change the
physical selector.

## Recovery

Rejected resulting modes2/7 are not accepted into the mode3 foreground renderer.
The owner first restores mode3/B800, then the old physical rows, before restoring
owned live/default words, bytes, UI state,8000 video bytes,8192 shadow bytes,
metadata planes, line flags, keys, tabs, parameters and cursor. Late real-renderer
refusal restores the previous selector metadata as well. The existing inactive
frozen-history loan supplies rollback storage; no new heap or screen frame is
allocated. It does not snapshot inactive mono/graphics VRAM, arbitrary downloaded
fonts or every VGA register.

Transaction returns retain the row owner's meanings:0 committed;1 bad request;
2 missing reset capture;3 admission/staging refused;4 verified old-state
restoration;5 old BIOS geometry unverified and fatal exit2/service6EF6 requested;
6 mouse handoff failure and fatal exit14 requested;7 missing saved/live selector.
The physical service's result codes remain a separate domain. A failed physical
baseline recovery can still be recovered by restoring the old admitted geometry;
only that independently verified old state permits return4.

## Evidence

[Receipt](validation/display-selector-transaction.json) binds source hashes,
ordinaryffd8db19 and diagnostic35bba5bf, results and actual DOS records.
Ordinary resident CS is65404/132 spare, DGROUP65088/448 spare and DISPLAY_CODE4379
bytes. The extra selector words consume16 aligned near bytes; diagnostic DGROUP
is65136. This is not a claim of unchanged retained memory.

Fifty-one composed CPU inputs cover visible/hidden commits, accepted fallback,
actual RIS/status/shadow/parser CPR, saved cycles and readiness, invalid public
selectors, online/owner refusal, alternate-text restoration, late renderer
failure, fatal BIOS recovery, actual UART ISR arrival, real mouse ownership,
post-commit quarantine, direct-row invalidation and actual MZ readiness reset.
Actual C/ASM instructions execute; BIOS effects, DOS allocation and INT33 driver
boundaries are modeled. Faults change real-boundary inputs without replacing
product functions/instructions. They do not establish physical driver timing.
The same ordinary image passes95 physical-selector,181 import,102 row,
76 status and250 reset-default inputs:755 total linked inputs.

The actual8086 DOSBox-X parent records nine composed stages in TSEL.BIN:

| Stage | Physical / effective rows | Accepted selector | Fallback / physical result |
| --- | --- | --- | --- |
| Baseline |25 /24 |1 |0 /0 |
| Preferred43 |43 /42 |2 |0 /0 |
| Keep mode |43 /42 |0 |0 /0 |
| Configured mode3 |25 /24 |3 |0 /0 |
| Mode3, preferred50 |50 /49 |4 |0 /0 |
| Ineligible mode, selector3 |25 /24 |1 |1 /0 |
| Ineligible mode, selector4 |25 /24 |1 |1 /0 |
| Refused graphics mode |25 /24 |1 |1 /3 |
| Apply saved, hidden status |25 /25 |1 |1 /3 |

Each stage returns0, reports live-selector readiness1, and has captured video
and full shadow agreeing with content rows/status placement and zeroed unused
shadow. The genuine status-toggle owner restores visible24 before the existing
canonical-row sequence. Normal and exclusive GROWS.BIN refusal workflows also
verify the raw selector records, unchanged synthetic PRM/image, zero serial
output and42-byte sampled vector/UART/PIC restoration. These diagnostics run
before UART enable; they do not establish live RX during the actual DOS mutation
or inject hardware faults in DOS. Diagnostic packaging remains rejected.

Ordinary, diagnostic and disabled-control images reproduce exactly from566/568/
563 public sources in fresh trees without ancestor Git/original artifacts.
Disabled control remains7e61a128. No deployment pointer, ready package, installed
configuration, bridge, live BBS or physical machine changes here.

## Remaining application gates

The APIs are internal, disconnected services. An optional
[accepted text-size reply](WINDOW_SIZE_REPORT.md) now provides a nonmoving query
endpoint; Linux collection/NAWS coordination is not integrated yet. Automatic startup application and
normal command bindings still need guarded UI integration, larger-screen modal
loans and explicit online DOS/bridge size agreement before a new connection can
use changed geometry. Saved/live setup/HOOK adoption and foreground modes2/7 or
custom modes remain unfinished. The status-toggle owner is still physical25-only.
Physical Cirrus/mouse/Boca/SPA2102, BBS/package and full application acceptance
remain open. All13 unavailable reference commands remain unavailable. Do not
select this internal component through the connection-test deployment pointer.
