# Offline BIOS and terminal row transaction

The optional `--row-geometry-owner` extends the [banked BIOS service](DISPLAY_ROWS_TERMINAL.md)
with a source-built foreground transaction. It changes physical rows and the
canonical parser, configured RIS defaults, native status placement and shadow
image together. It does not enable Toggle Lines or add a menu/key binding.

`terminal_row_geometry_set(rows)` admits25,28,43,50 physical rows in narrow
80-column, unprotected mode3/B800 text profiles4/6, while disconnected. Adapter
capability and the actual BIOS geometry must agree with the current canonical
layout. Visible status reserves the bottom row; hidden status permits all rows.
Success performs the real configured RIS reset: it clears content and restores
configured attributes, tabs and key map, rather than capturing peer state as new
defaults. It preserves history storage and queued UART input.

Admission excludes active modal, script, recorder, transfer, parser, pending
output, notice, frame and reset-bank owners. It verifies DS=SS, IF=1, DF=0,
geometry/cursor caches, pointers, supported line settings, and mouse ownership.
The older status-toggle transaction remains restricted to physical80x25.

## Commit, rollback and storage

The transaction stages captured defaults before BIOS mutation. The existing
mouse owner suspends its callback before mode/font changes and resumes after a
coherent commit or verified rollback. Pending encoded mouse input arriving at
the pause boundary is restored before native callback registration. Fresh driver
motion baselines remain reset. Failed mouse handoffs use the existing quarantined
owner and fatal exit14; they do not discard retained callback storage.

The exclusive loan occupies25522 bytes of the inactive63000-byte frozen-history
workspace:8000 video bytes,8192 shadow bytes, two4096-byte metadata planes,
128 line flags,948 key bytes,30 tab bytes and32 ANSI parameter bytes. Current
history is untouched. No new heap or far frame allocation is introduced; linked
code still increases retained memory. The reset bank uses the same workspace
only while its own owner is active. Its entry initializes the native data image
anew (`standalone/terminal_reset_host.asm`, `terminal_reset_test_initialize`).
The linked regression exercises rows43→25, width80→132→80, configured RIS and
rows28. Native width leaves its viewport-active latch set; the row owner refuses
until genuine RIS retires it. That limitation remains explicit.

On failure the owner first restores the previous BIOS geometry, then live/reset
words, bytes, screen planes, maps and UI layout. It restores the saved cursor
position and shape only after verified BIOS recovery. Unverified BIOS recovery
requests the established fatal exit2/service6EF6, so foreground parsing cannot
continue under a fabricated successful rollback. This does not snapshot arbitrary
downloaded fonts or every VGA register; the supported paths use native ROM fonts.

Return codes:0 committed;1 invalid request;2 reset capture missing;3 admission or
staging refused;4 failure with verified restoration;5 BIOS recovery failed and
shutdown requested;6 mouse handoff failed and shutdown requested.

## Evidence

[Bound receipt](validation/row-geometry-transaction.json) records full identities
and report hashes. The ordinary image starts7e61a128 and the separate startup
diagnostic starts9d8ba4e8. Ordinary resident CS is65392 bytes (144 spare),
DGROUP65072 (464 spare), CONFIG_CODE58490 and DISPLAY_CODE3180 bytes. The
mouse bank is2999 bytes. The diagnostic has65404 resident bytes (132 spare).

The linked CPU suite executes102 inputs covering visible/hidden geometry,
capabilities and refusals, actual RIS and parser CPR, generalized native status,
complete owned-state rollback, shared workspace reuse, UART ISR arrival and
high-water flow control, mouse handoffs, pending input and quarantine failures.
BIOS effects, DOS allocations and INT33 driver/vector boundaries are modeled.
Mouse arrival seeds native pending data at the pause boundary; it does not
establish physical callback timing. No function, instruction or return address
is patched. The UART burst includes3576 arbitrary bytes retained without drops,
with RTS held until actual receive draining and flow polling release it.

The actual8086 DOSBox-X parent diagnostic executes probe25 then25,28,43,50,25
before UART enable/connection start. Six records include BIOS and canonical
geometry; video/full-shadow captures prove the native status sits on the physical
bottom and unused shadow cells are zeroed after each transaction. Normal and
exclusive GROWS.BIN refusal runs preserve synthetic PRM/executable bytes, restore
all42 sampled vector/UART/PIC bytes and send zero bytes to a connected virtual
serial peer. Exclusive refusal returns23. Diagnostic packaging is rejected.
These DOS tests do not exercise live receive during mutation or inject BIOS faults.

The ordinary image also passes the existing76 status and250 captured-default
inputs. Four complete source-only exports rebuild exactly without original
artifacts or ancestor Git. With the geometry option disabled, ordinary bank and
raw diagnostic executables remain exactlya1c86342 andf302f571 respectively.

## Remaining integration

The [selector composition](DISPLAY_SELECTOR_TRANSACTION.md) now adds checked
selector/cycle/saved-application APIs, separately from normal command binding.
Guarded larger-screen UI/frame loans,
online DOS/bridge size agreement and refusal/recovery policy remain open. There
is no live BBS, SIP, physical Cirrus/mouse/modem acceptance or replacement-package
claim here. All13 unavailable reference commands remain unavailable. The
606 recovered native bytes retain their existing provenance; the new transaction
is maintained integration code, not a byte-exact recovery of the original owner.

No deployment pointer, ready package, private settings, installed bridge or
physical system is changed. The ignored row-geometry pointer selects an internal
component only; the connection-test pointer continues to select deployment.
