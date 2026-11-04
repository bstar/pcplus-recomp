# Accepted text-size reporting

The optional `--window-size-report` build adds ordinary CSI18t reporting to the
current canonical-display component. It replies with CSI8;rows;columns t, using
accepted logical CSI dimensions. Visible status therefore yields24/42/49 rows
for25/43/50 physical rows; hidden status includes the full count. The existing
132-column logical text area reports132, independently of its80-column physical
viewport. It does not infer dimensions from saved preferences or cursor position.

This is maintained protocol extension code, not original PCPlus behavior.
[Xterm's control-sequence specification](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)
defines the18 request and8 response for text-area character dimensions. Only the
ordinary single-parameter18 form is implemented. Other window operations,
private/secondary forms and extra-parameter forms retain their previous inert
behavior. This is not full XTWINOPS or xterm emulation.

## Display and queue contract

The native dispatcher gets a conditional entry for final byte `t`; flat original
assembly and report-disabled builds retain the previous table/behavior. The
handler lives in DISPLAY_CODE. It does not move the cursor, use its save bank,
change margins/origin/modes/attributes, touch text/history/shadow, redraw or
change display selection. Normal CSI temporary parsing fields still change.

Admission requires a supported profile4/6 and coherent80-column video layout,
B800 text storage, logical width80/132, positive rows up to50, agreeing bounds
and a representable shadow extent. Active program/ASPECT/transfer/geometry or
stopping owners do not emit a reply. It performs no BIOS/DOS or blocking UART
operation. The ordinary foreground transport subsequently delivers queued bytes.

The complete response is formatted in16 bytes of existing executable-bank
storage, then reserved/copied into the existing1024-byte TX ring. Count,
head/tail range/relation and full capacity are checked before any queue byte
is written. A full or malformed ring refuses the complete report without partial
output, a busy wait or a new fatal error. ISR ownership remains RX-only. Report
slots have nonuser provenance, so later delivery does not classify this metadata
as typed user input. Other queued bytes retain order, including across wrap.
This does not promise one physical UART write or suppress normal flow servicing.

## Evidence

[Receipt](validation/window-size-report.json) binds complete images, source hashes
and reports. Ordinaryf995e1a1 has65418 resident bytes (118 spare), DGROUP65088,
and DISPLAY_CODE4784. Diagnosticc4700bb0 has65428/108 spare and DGROUP65136.
The handler adds no near data; its mutable response storage is in the code bank.
The first DISPLAY_CODE object now starts at offset0; retained-bank inspection
checks the actual full extent. Report-disabled control remains byte-identical
ffd8db19, including its preceding nonzero bank offset.

Forty-four linked report inputs cover actual parser replies over both profiles,
visible/hidden25/28/43/50 geometry, origin/margins/attributes/save-bank preservation,
deferred wrap and following text, an existing132-column viewport, exact query
consumption with a following data byte, unsupported forms and subsequent normal
queries, full/near-full/wrapped queues, provenance and actual UART delivery, and
corrupted-ring refusal. BIOS/UART effects are modeled; actual parser/report/
queue/provenance/UART code executes. The same ordinary image passes the prior755
selector/import/row/status/reset inputs, for799 linked inputs total.

An actual8086 DOS parent initializes/dials a synthetic modem on COM3/3E8/IRQ5,
then receives three delayed query chunks after a genuine keyboard byte reaches
the wire. With origin-relative margins active, it emits exactly one size reply
8;24;80t and its genuine CPR remains4;5R. Private/extra-parameter forms elicit no
additional size reply. Initial banner, CPR/DA, configured init/dial, unchanged
synthetic PRM/image and42-byte sampled vector/UART/PIC restoration also pass.
The peer sends query bytes, never a fabricated terminal reply. Separate DOS
canonical selector/video/shadow and diagnostic-package-refusal workflows pass.

Ordinary, diagnostic and disabled control reproduce exactly from567/569/566
public sources in fresh trees without original artifacts or ancestor Git.
This does not establish complete binary-transfer, ASPECT-report, BBS, modem/DSP,
SIP/analog or physical acceptance of the extension.

```sh
# Add to the internal canonical-display build flags:
--window-size-report

./tools/dev --command python standalone/check_window_size_report_live.py \
  --terminal build/ORDINARY/TERMINAL.EXE --output build/NEW-size-report
```

## Bridge integration still required

No SynthModem source, configuration or running service changes here. A bounded,
explicit pre-session Linux owner must elicit/validate the reply while it owns
the local CONNECT menu, then supply the accepted dimensions to Telnet NAWS before
connecting the BBS. It must handle timeout/refusal, cancellation, stale replies,
reconnect and concurrent typing without scanning or stealing arbitrary bytes
from a proxied BBS/transfer stream. An unconfirmed size must not be called an
agreed geometry. Existing staged codec resize/editor evidence remains separate.

Normal line/status commands, automatic startup preference application,
larger-screen UI loans and online resize remain guarded. No package or deployment
pointer changed. A read-only management doctor found the physical DOS PC
unreachable (No route to host); no physical job or remote update was attempted.
All13 unavailable reference commands and full application acceptance remain open.
