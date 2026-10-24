# Carrier loss during an incomplete width request

Six actual DOS workflows pass with the unchanged SUB-checkpoint terminal and
ASPECT interpreter. The four main cases cover source/precompiled scripts and
open/closed script windows with a native `WHEN DISCONNECT CALL` worker.
Two controls omit that worker and use three- and thirty-second `WAITFOR`
timeouts. The [independent receipt](../../docs/validation/peer-width-carrier.json)
binds 142 artifacts and 120 producer checks.

DOSBox-X's built-in Hayes modem owns result codes, UART modem status and DCD.
An ephemeral loopback TCP peer supplies display data only. After the child
acknowledges a committed 132-column mode and returns the actual cursor reply
`ESC[2;128R`, the peer sends an incomplete `ESC[?3`, waits one second and
closes the connection. It sends neither Hayes responses nor a timeout-ending
`END` marker. The observer sees the partial parser while carrier is high,
then sees offline status, retired parser/ASPECT/PROGRAM/native-bank owners and
the retained logical width of 132.

The native CALL worker waits for an active WAITFOR to finish, as established
in [WHEN runtime recovery](../../docs/ASPECT_WHEN_RUNTIME.md). Early exploratory
runs incorrectly scheduled Alt-D before a thirty-second wait had completed;
the script still owned the terminal and consumed that key. These failed
`build/peer-width-carrier-01` through `-08` probes remain local evidence. The
observer identified the live child and active wait rather than a blocked
return prompt. The three-second pilot `-09` passed; all six final runs use
fresh output directories and the final frozen driver. No application behavior
was changed to shorten native waits.

The final key schedule waits for child completion. Handler cases write
`START|WIDE|LOST|`; controls write `START|WIDE|RETURN|`. Both finish normally.
At the subsequent real Alt-D BIOS read, the observer requires an already-exited
child and idle command owners. The same DOS parent initializes and dials again.
The second connection requires actual 80- and 132-column cursor replies,
manually typed `ready`, and a further cursor reply after that input. This
distinguishes working redial/keyboard handling from a successful final exit.

The passive observer chains INT10/21/1C and INT16, records separate parent and
child DS=SS images and never supplies keys or changes application memory.
It avoids reading a released child allocation. It unhooks before the independent
46-byte UART/PIC/vector snapshot, which includes INT16 and matches exactly
before and after every run. DOS compilation must produce the exact host ASX.
All runs use 8086, COM2/IRQ5, 19200/8N1/HARD. `AT&K3` is emulator fixture
configuration; it is not a prescribed initialization string for the Boca modem.

For a fresh case:

```sh
./tools/dev --command python3 lab/bbs/peer_width_carrier_dos.py \
  --terminal build/SELECTED-SOURCE-PRODUCT/TERMINAL.EXE \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --compiler build/aspect-compiler-dos/ASPCOMP.EXE \
  --window --disconnect-handler --output build/YOUR-FRESH-CARRIER-CASE
```

Omit `--compiler` or `--window` for the other main combinations. Controls omit
`--disconnect-handler`, keep the window open and omit the compiler, with
`--wait-seconds 3` or `--wait-seconds 30`. Seal all six fresh paths with
`record_peer_width_carrier.py`, one `--case` per path, and `--output`.
Accepted paths begin `build/peer-width-carrier-final-` and end in `window-01`,
`source-window-01`, `plain-01`, `source-plain-01`, `timeout3-01`, `timeout30-01`.

This checks emulated DCD loss after a committed wide mode with a second CSI
pending. It does not inject a failure inside the native width transaction,
prove immediate cancellation of every WAITFOR, or exercise a real BBS over
this carrier path. General DOS/OS interruption, wide transfers, broader
application families and physical Boca/SPA2102 integration remain open.
The absent DOS card has not received these experimental builds.
