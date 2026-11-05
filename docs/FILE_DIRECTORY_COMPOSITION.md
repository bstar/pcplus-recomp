# File Directory inside BBS editors and active sinks

The unchanged File Directory candidate passes actual Alt-F listing inside stock
Enigma and Synchronet editors. Five additional DOS workflows cover capture,
HOLD, capture with printer, HOLD with printer, and printer alone while the
listing receives a 3,202-byte burst. The executable remains
`74e3f0822044128b68c2f51660efa4e913292cca786edb649c2d662d53e72239`.
The [receipt](validation/file-directory-composition.json) binds these results.

## Stock editor roundtrip

Both workflows open Alt-F with an unsaved KEYTEST draft, enter the owned
`D:\TEST.PRM` specification, observe the real listing, and press Escape. Editing
continues through the existing navigation/editing recipe, then the draft is
discarded. A passive BIOS/VGA observer captures the full editor before and after,
cursor/shape, and listing heading/entry. TEST.PRM must have its real 1,264-byte
size; the filename must be consumed locally rather than sent to the BBS.

Each returned 4,000-byte editor frame matches exactly, including cursor position
and shape. Independent CPR-bounded audits match all 1,920 cells per peer with
zero differences. Server audits require continued editing, normal cancellation
and no published draft/message/transfer writes. The route uses DOS8086 COM3/IRQ5,
HARD flow and the staged SynthModem Telnet proxy, with the existing 250 ms key
framing and 20 ms input pacing. ASPECT retains its previous executable bytes.

Ten copied evidence mutations are rejected at their intended checks: cell,
cursor, shape, listing marker, mode, heading, filename, size, filename leakage
to the wire and missing subsequent editing. They mutate captures only. With
the optional listing key recipe disabled, the native keyboard helper exactly
reproduces the preceding Gateway helper.

## Capture/HOLD and printer pressure

Five actual DOS8086/FPU-disabled COM1/BOTH cases keep the modal page open during
the controlled burst. A passive VGA observation requires both the listing and
the received A-filled exposed background. Fresh DSR responses prove processing
after the burst; ordinary keyboard input and another DSR work after the listing
and after closing the sinks.

| Owners | Exact capture | Exact virtual PRN |
| --- | ---: | ---: |
| Capture | 3,815 bytes | — |
| HOLD | 613 bytes | — |
| Capture + printer | 3,815 bytes | 3,815 bytes |
| HOLD + printer | 613 bytes | 3,823 bytes |
| Printer | — | 3,815 bytes |

The initial 607-byte prefix forces capture writes before enumeration. HOLD omits
both separate held text and the burst from capture, then resumes before final
text. The printer receives all text, including eight held bytes where applicable.
Every output byte is compared. All 92 checks across these five cases pass.

A passive DOS-entry trace records FindFirst/FindNext, caller DS, writes and
closes. It checks no close during that search and, for capture, the same
descriptor with no intervening close between writes across the listing. Final
UART/PIC/vector snapshots, startup directory, fixture settings, executable and
observer/trace completion also pass. The scheduler bounds DOS call count per
turn rather than kernel/media latency.

## Retained fixture failures and scope

The initial BBS recipes used a bare TEST.PRM specification while their harness
worked from C:. Editing passed but listing observations failed. The accepted
recipes explicitly name the staged D: fixture. The first sink configuration
also had a malformed drive-change line: capture matched, but its diagnostic
programs did not run. Fixing the setup restores those missing checks. These
failures remain bound and excluded from acceptance. No application bytes or
production timeouts changed to obtain passing results.

PRN is a DOSBox file-backed device. These results do not establish physical
printer behavior, analog flow timing, SIP/DSP/audio, DOS6.22 or Boca/SPA2102
acceptance. Carrier-loss/reconnect/transfer and media/critical-error composition
remain open. The physical installation and private deployment selector are
unchanged. Internal/configured viewers and the full remaining inventory continue.
