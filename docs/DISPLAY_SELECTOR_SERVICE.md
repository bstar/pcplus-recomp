# Verified physical display selector service

The internal display-preferences component now links `native_display_select()`
in DISPLAY_CODE. It implements the recovered selector decisions through the
actual BIOS mode/font/geometry helpers, then checks physical results. It changes
physical display state only: it does not commit canonical terminal geometry,
RIS defaults, screen/frame ownership, saved preferences or a live selector.
It must not be bound directly to a normal key or menu.

| Selector | Mode operation | Desired rows |
| --- | --- | --- |
| 0 | Keep current mode | Current physical rows |
| 1 | Baseline text mode | Probed baseline rows |
| 2 | Baseline text mode | Native preferred-row/font decision |
| 3 | Configured mode when eligible | Probed rows after mode change |
| 4 | Configured mode when eligible | Native preferred-row/font decision |

For3/4, the preferred mode WORD must be signed-positive and font capability
nonzero. Otherwise the native policy chooses baseline selector1 and ignores the
preferred row WORD. VGA-style row selection recognizes low-byte28/43/50;
EGA-style selection recognizes43 and otherwise uses its baseline font. With no
font capability the native helper keeps existing rows. The actual recovered
row code, rather than a replacement BIOS implementation, performs those calls.

The newly linked33-byte mode helper at6F3E follows its original vendor branch:
with detected extended-mode capability and AL>=12h it invokes INT10/AX6F05
with the requested mode in BX; otherwise it uses standard INT10/AH0. Its flat
bytes match [public provenance](../reconstruction/program_ui/provenance.json),
REA `ev_a795f64b2b71fadddc43be729f8b5026037c55863fdc20acc960f7ee17a61808`.
The bank now contains639 recovered bytes. The selector owner is maintained C
integration code, not a byte-exact recovery of original DISPLAY2EAA.

## Result and failure contract

The far-cdecl API takes selector, preferred rows, preferred mode and caller-owned
nonwrapping24-byte near result storage. DS=SS, IF=1, DF=0 and exclusive foreground
ownership are required. The result contains independently probed geometry,
requested selector and accepted selector. Invalid selector/pointer/context
returns before a destructive request; the initial probe must accept the current
80-column page0 text display. Existing probe admission recognizes modes2/3/7,
segments B800/B000 and25/28/43/50 rows. Other/custom text modes remain unsupported.

Eligible configured modes must actually probe as the requested low-seven-bit
mode, and requested font effects must match their native capability/low-byte
outcome. A refused/unrecognized request attempts native baseline recovery, verifying
both expected mode3/7 and25 rows (a matching row count alone is insufficient):
return3 means verified80x25 fallback, accepted selector1 and fallback flag1;
return4 means recovery was not verified, accepted selectorFFFF and geometry
must not be treated as usable. Ordinary configured-mode/capability policy
fallback returns0 with accepted1/fallback1. Other successful requests return0
with their selector and independently measured geometry.

The original commits its selector even when BIOS effects do not produce the
requested rows. This maintained service explicitly reports that failure and
verified fallback. Invalid original selectors home the cursor before returning;
this detached physical service does not own the cursor/UI operation. It adds no
implicit terminal reset, status toggle or font/screen preservation promise.
The application owner must interpret results inside its own rollback contract.

## Bound verification

[Receipt](validation/display-selector-service.json) binds full images, source
hashes, reports and actual DOS selector records. The ordinary image starts5bb9c9e7;
the separate diagnostic startse10cdd9a. DISPLAY_CODE is3693 bytes, up513 from
its preceding component. Ordinary resident CS remains65398/138 spare, DGROUP
65072/464 spare. No additional screen plane or heap allocation is introduced.

Ninety-five linked CPU inputs exercise the physical selector chain, independent
canonical state, VGA/EGA/CGA capability and low-byte decisions, signed preferred
mode boundaries, text modes2/3/7, verified graphics refusal fallback, refused
fonts, failed recovery, invalid inputs/context and the actual vendor branch.
BIOS effects and refusals are modeled. The vendor test establishes the native
branch and recovery, not support on a physical vendor adapter. Existing181
startup-capture,102 row-transaction,76 status and250 reset-default inputs pass
against the same ordinary image, for704 linked inputs total.

Actual8086 DOSBox-X startup diagnostics execute eight selections, writing
DSEL.BIN: baseline25; preferred43; keep43; configured mode3/25; mode3/50;
two ineligible-mode policy fallbacks to25; then a graphics12h request with
verified failure/fallback to text25. Canonical geometry deliberately stays24
while this raw sequence runs before UART enable. Subsequent existing canonical
row transactions and video/full-shadow/status captures pass. Both normal and
exclusive GROWS.BIN refusal runs preserve the synthetic PRM/executable, send
zero serial bytes and restore all42 sampled vector/UART/PIC bytes. The diagnostic
still cannot be packaged. These are emulator observations, not physical Cirrus,
mouse, modem or online acceptance; hardware refusal injection is CPU-modeled.

Ordinary, diagnostic and disabled-control images reproduce exactly from declared
public sources with no originals or ancestor Git. Disabled control remains
7e61a128. No package, deployment pointer, installed bridge, private settings or
physical system changes. The internal selector pointer is not a deployment source.

## Next application work

Compose selectors with the existing BIOS/canonical/RIS/mouse rollback transaction,
including the accepted fallback geometry and saved selector distinction. The
current foreground row owner admits mode3/B800 only; it cannot simply accept
this service's mode2/7 results. Then apply captured startup preferences, define
live setup/HOOK adoption and selector cycling, and finish larger-screen modal
loans and guarded commands. Online DOS/bridge size/refusal/recovery policy and
BBS/package/physical acceptance remain open. All13 unavailable reference commands
remain unavailable; this is not a finished Toggle Lines implementation.
