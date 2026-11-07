# Matched EMULATE connection candidate

The new public payload combines the tested capability 20 terminal `856a9c85`,
EMULATE/ALARM interpreter `5c641ac4` and compiler `ac58a8a1`. It preserves the
existing setup/translation executables, Chat overlay, Help files and launchers.
Only the three principal executables, README and source-version text differ
from the preceding ALARM recipe. Application code is unchanged in this checkpoint.

The deterministic 13-file archive is staged at
`build/emulate-connection-candidate-20261107/archive/PCPLUSSE.ZIP`:

```
5d786da9de50a6d92b28eec8f768057bdd1b26b7cf9cb06558b5cec6575487ac
```

The [tracked recipe](../standalone/emulate_connection_candidate_recipe.json)
pins every file and archive byte. The packager checks the actual published
parent version and both parent/interpreter selections; nine positive/negative
contract cases include mixed pairs and invalid recipes rejected before building.
The matching older capability 19 selection remains valid.

Four actual DOS8086 synthetic-card workflows pass: precompiled START with the
BIOS UART entry omitted, SETUP, independent magenta special-edition splash
capture, and Chat/contextual Help return. The packaged compiler produces exact
ASX containing EMULATE VT220/ANSI plus ALARM/DATE/TIME; the packaged interpreter
executes those commands and writes the expected result. All six synthetic
PRM/DIR/KEY/KBD/XLT/FON preservation sentinels remain exact in each mode, as do
all packaged files. COM3/IRQ5, hardware/vector and environment restoration pass.
These use dummy UARTs and do not establish physical modem acceptance.

A separate clean public-source reproduction is pending at this source checkpoint.
The candidate is staged only: installed R59A85A8, its private configuration and
call history remain unchanged. Native abort/fatal-reset expansion, stronger
sustained flow/headroom and physical Boca/SPA2102/SynthModem acceptance remain
open. The wider original-feature inventory remains open too.
