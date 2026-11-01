# Custom LoC menu and transient carrier indication

The user reports that the new DOS build connects through the Boca, SPA2102 and
SynthModem to Enigma with substantially improved interaction. The bridge log
confirms V.32bis CONNECT 9600 on the successful call. The preceding 12000-bps
call lost carrier after signal-quality errors/retraining; the VM answering
modem is now capped at 9600. These are physical observations, not proof of all
editor, reconnect or file-transfer acceptance items.

## Custom menu output

The photo's missing logo/label portions reproduce when the old custom menu
output is replayed through the actual linked PCPlus renderer. The CP437 path
emitted modern SGR 90–97, which the classic renderer ignores. Black padding
therefore remained active for some bright text. The browser uses a separate
truecolor path and did not expose this problem.

The local Enigma module now emits reset/background plus classic intensity and
30–37 foreground sequences for its DOS palette. It removes the blank separator
beneath the logo when the reported height is 24, retaining all menu items,
the footer and the command prompt above PCPlus's status row. The approved
25-row browser output is byte-identical to the previous module.

The portable patch is [loc-main-classic-ansi.patch](../lab/bbs/patches/loc-main-classic-ansi.patch).
The [replay tool](../lab/bbs/check_loc_menu_ansi.py) captures actual module output
and runs it through linked PCPlus parser/render instructions. It independently
compares all 1920 glyph/attribute cells with the source layout and palette.
It models BIOS/UART boundaries; it does not log into or restart the live BBS.

The change is saved in the local Enigma module but **not loaded into the live
process yet**. Restarting Enigma disconnects the active call; wait for bstar's
restart approval or a confirmed idle maintenance opportunity.

## Carrier-lost notice

A separate linked reproduction shows that one low DCD sample retires the
session and leaves its notice latched even when the line immediately returns
high. This is a plausible explanation for the reported notice during usable
interaction; the actual Boca DCD waveform has not been measured.

The custom-IRQ candidate now requires low DCD across four BIOS ticks (about
220 ms) before retiring a MODEM session. High DCD resets the candidate interval.
Foreground polling and PROGRAM-return flow checks share the qualifier. It
preserves register/IF/DF ownership, the existing initially-low-DCD behavior,
and immediate DIRECT-link policy. Confirmed loss still clears owners and
requires a real redial; it does not manufacture an automatic reconnection.
Default builds and child-owned ASPECT sampling retain their previous policy.

Twenty linked timing/ownership cases cover transient and sustained loss,
midnight, low-word rollover, initially low DCD, shared flow checks and DIRECT
policy. Actual DOS package execution and a clean five-executable rebuild pass.
Relevant genuine-loss/redial, script and transfer DOS outcomes are bound in the
validation receipt, separately from the earlier broad application checkpoint.

The initial candidate was staged under `build/connection-test-package-carrier-01`.
The subsequent [connection-alert package](CONNECT_ALERT.md) includes this fix
and is now installed at `C:\PCPLUS`. Its active configuration still matches
`C:\UTILS\PCPLUS`; the newer call-log entry is preserved. Physical validation
of the notice fix remains pending.
