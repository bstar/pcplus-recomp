# DOS door burst-input compatibility

The earlier BRE reference stall is reproduced with a bounded UART observer in
a fresh isolated fixture. All eight name bytes reach the guest UART in one
synchronous call. The guest reads `L`; seven bytes remain pending with FIFO
disabled, receive interrupts enabled and interrupt identification 4. A later
CR finds the same seven pending bytes while the instruction counter has
advanced. The observation locates this failure after the BBS has received the
input, in the door bridge/v86 UART interaction.

The [explicit bridge candidate](patches/enigma-v86-input/README.md) holds pending
wire bytes in a host ring and feeds the UART only when its previous byte has
been consumed. It preserves byte values and order. It does not change the
source-built PCPlus terminal or the original PCPlus recovery evidence.

The actual BRE reference route now accepts the same eight-byte burst, confirms
the name, declines instructions, reaches the game menu, quits normally and
returns through Doors to Main. The instrumented run records every byte consumed
with at most one byte in the UART. A fresh uninstrumented fixture also passes,
so the repaired route does not depend on the observer. Passive audits verify
the original counterexample and reject 15 and 13 damaged captures respectively.
The byte queue passes 25 component checks, including all 256 byte values,
wrapping, backpressure, atomic overflow rejection and shutdown cancellation.

Separate uninstrumented DOS BRE and Global War regressions each pass 13
workflow checks. Their passive audits reject ten and 13 damaged captures.
The [validation record](../../docs/validation/enigma-v86-input.json) binds the
baseline, repaired reference routes, component checks and actual DOS sessions.
All 31 application products and 566 source files retain their prior hashes.

Run the reference route only on a fresh staged fixture whose synthetic game
identity has not yet created a realm:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_v86_burst.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs --label UNIQUE
./tools/bbs-dev --command python3 lab/bbs/check_enigma_v86_burst.py \
  --label UNIQUE --baseline-label BASELINE_LABEL \
  --baseline-candidate build/bbs-lab/BASELINE/candidate
```

The baseline label must retain the actual unpatched UART stall, its declared
name-burst event and followup, immutable-input result and source-image result.
The checker uses actual wire offsets and response ranges for each repaired
phase. It rejects missing confirmation, commands, lifecycle, authentication,
incorrect offsets and damaged UART evidence. It generates no game replies.

DOS acceptance uses another fresh uninstrumented fixture and the existing
`enigma_v86_dos.py` and `check_enigma_v86.py` routes. Traces, image copies, game
output and synthetic databases remain private under ignored `build/`. Original
game images and the live board are never patched. Source and staged worker,
helper, dependency, BIOS and harness identities are recorded separately.

This is a staged compatibility candidate, not full application reconstruction,
full-game or physical-modem acceptance. The bridge depends on the pinned v86
internal UART queue. Its 1ms scheduling is not baud-accurate and does not prove
throughput or binary guest protocols. Integrated overflow/error-path disk
persistence, saved-realm persistence, concurrency and deployment remain open.
Other separate ENiGMA patch experiments are not cumulatively validated by this
fixture, which combines the keyboard decoder, owned v86 modules and this bridge.
