# Connect results from a 14.4 modem (roadmap G2)

## How the matcher behaves today (recovered original, unchanged)

The dial-response matcher (`reconstruction/modem_responses/`, run by
`src/terminal/connection.asm`) compares each received byte against the eleven
PRM response slots:

- **Slots 0–6** mean connected at 300, 1200, 2400, 4800, 9600, 19200 and 38400.
- **Slots 7–10** mean failure.
- **The first slot whose bytes complete wins.**
- With autobaud on, the winning slot's rate becomes the DTE rate.

The slot text comes from the user's PRM, not from the program.

Characterization with the bit-exact matcher model (`check_modem_responses.model`)
and Hayes/Rockwell-style 14.4 results:

| Slot 0 text | Modem sends | Result |
| --- | --- | --- |
| `CONNECT` | `CONNECT 14400`, `CONNECT 14400/ARQ/V42BIS`, `CONNECT 2400`, `CONNECT 38400/ARQ` | slot 0: "300" connect, every time |
| `CONNECT^M` | `CONNECT 14400`, `CONNECT 14400/ARQ/V42BIS` | **no match, so the dial times out** |
| `CONNECT^M` | `CONNECT 2400` / `CONNECT 38400/ARQ` | slot 2 / slot 6 (correct) |
| either | numeric `10` (ATV0) | no match, so the dial times out |
| `CONNECT^M` | `CARRIER 14400` … `PROTOCOL: LAP-M` … `CONNECT 38400` (W2) | slot 6: 38400 (correct) |

So, **with the current build**, the safe Boca setup is:

- autobaud **off**, with the DTE rate fixed in SETUP;
- slot 0 set to plain `CONNECT` (no `^M`);
- verbose results (`ATV1`).

Then every CONNECT form connects, and the DTE rate is not changed. With
autobaud on, any CONNECT drops the port to 300 bps.

## Planned change (behind `--modern-results`, default and qualified builds unchanged)

1. **Line framing.** A CONNECT-family slot completes only at the end of the
   result line (CR/LF), or when the slot text itself ends in CR. The longest
   matching slot wins, so generic `CONNECT` can no longer preempt
   `CONNECT 2400`.
2. **Unlisted rates.** `CONNECT <n>` with n in 7200, 12000, 14400, 16800,
   21600, 28800, 33600, 57600 or 115200 connects instead of timing out.
   - Autobaud picks the lowest supported DTE rate that is at least n, capped
     at 115200.
   - With autobaud off, the rate stays as configured.
3. **Suffixes.** `/ARQ`, `/V42BIS`, `/LAPM`, `/REL`, `/MNP`, `/V42` and
   `/COMP` are ignored for matching.
4. **Informational lines.** `CARRIER`, `PROTOCOL:` and `COMPRESSION:` lines
   are consumed, not matched.
5. Failure slots 7–10 keep first-completion behaviour. A failure must never
   wait for a line end that might not come.

## Acceptance checks

Each check runs both on the linked matcher (CPU test) and in actual DOS through
`standalone/test_connection_dos.py`, with the synthetic modem replaying the
string.

| # | Slot 0 | Autobaud | Modem sends | Expected |
| --- | --- | --- | --- | --- |
| A1 | `CONNECT` | off | `CONNECT 14400/ARQ/V42BIS` | online, DTE unchanged |
| A2 | `CONNECT^M` | off | `CONNECT 14400` | online (today: timeout) |
| A3 | `CONNECT` | on | `CONNECT 2400` | online at 2400 (today: 300) |
| A4 | `CONNECT` | on | `CONNECT 14400` | online at 19200 |
| A5 | `CONNECT` | on | `CARRIER 14400` / `PROTOCOL: LAP-M` / `CONNECT 38400` | online at 38400 |
| A6 | any | any | `NO CARRIER`, `BUSY` | failure, immediately (unchanged) |
| A7 | default and qualified builds | — | all of the above | byte-identical binaries; today's behaviour |

The real Boca strings (H1) replace these documented forms as fixtures when the
user captures them.
