# Capability18 real-BBS transfer recovery

The staged normal parent `61757956` retains separate software acceptance from
the installed physical release. The test uses the same65539-byte all-values
file as the preceding Enigma upload/download checkpoint, with source SHA256
`c62fdfdef826f32aa019b9543f718b0c7bb86204972a699a30b815e4d8b66e4e`.

## Cancel and retry on one connection

An actual DOS8086 session enters the stock Enigma file base through the isolated
SynthModem proxy and begins ZMODEM receive. The test's BIOS key producer waits
for visible8KiB progress and presses real Escape. A separate filesystem watcher
captures a nonempty4096-byte source-prefix disk stage before cancellation,
then verifies an empty receive directory before the second transfer starts.

The session returns to the ordinary BBS file list/search, selects the same file
and receives it exactly. It then returns to the list/search again. Both transfers
use one DOS process, one proxy connection and one authenticated BBS session.
The stock external helper exits255 after cancellation and0 after the retry.

Independent audit verifies the first CRC data packet, absence of a completed
first ZEOF before cancellation, ordered partial/cancel/cleanup/search/retry,
exact destination and standard CRC/control/finish for the completed retry.
Raw Telnet/application bytes, NAWS80x24, product/server inputs and hardware/
configuration restoration remain checked. This is a real BBS helper and real
DOS client cancellation; it does not model physical DCD loss.

Exact results are bound in
[`validation/snapshot-lease-recovery.json`](validation/snapshot-lease-recovery.json).
Repeat only against the owned loopback fixture, with a fresh label:

```sh
./tools/dev --command python lab/bbs/test_proxy_cancel_retry_dos.py \
  --runtime build/menu-size-accepted-20261104/candidate \
  --terminal build/terminal-lease18-final-20261106/TERMINAL.EXE \
  --file P24E532.BIN --label lease18-cancel-repeat
```

The proxy snapshot is unchanged and owns Telnet. The synthetic serial modem is
CTS-ready; these results do not establish SIP/audio/DSP, analog Boca CTS timing,
every protocol/layout or physical acceptance. Production services, the package
selector and private machine files are unchanged. Carrier-loss/reconnect is a
separate gate from this same-connection cancellation test.

## Carrier test found a memory-admission failure

Neither of the complete current-pair carrier runs reached the scripted login:
the optional resident final-exit witness run and the separate unobserved
control both failed the required two-login/redial/retry checks. Their normal
DOS exits are not accepted as application success. The bridge remained at its
CONNECT prompt; no authenticated Enigma sessions were recorded.

A shorter real-proxy diagnostic captured one attempted ASPECT EXEC with DOS
return carry set and AX8, and no child-exit record. The diagnostic reuses the
tested passive DOS return trampoline with a one-EXEC record. Eight assembled
modeled-predecessor controls verify AX/BX/flags forwarding and recording across
caller DF/CF and successful/error DOS results. This is diagnostic evidence of
DOS launch rejection, not a passed carrier workflow or a complete new observer.
Its reused record's first word is tag4B00h, not a requested allocation size;
the returned BX word is not interpreted as available memory.

Short synthetic modem controls launch the full login script successfully with
the current pair, including DOS precompilation, the sibling help resource,
paced BIOS input and an unqualified TERMINAL command. Those controls are
deliberately cancelled while waiting for a synthetic prompt; their generic
CPR/banner checks fail because the probe supplies only a CONNECT prompt. They
are diagnostic contrasts, not extra passing BBS workflows. A first paced-input
probe failed to find its helper on C: and timed out; it is excluded.

The current ASPECT MZ requests at least137280 bytes including its PSP, loaded
image and minimum extra allocation. The parent retains478272 bytes (29892
paragraphs) according
to its existing manifest. This leaves little conventional-memory margin for
DOS, environments and resident helpers. Further memory-map/stack-lifetime
measurement is required before selecting an application change. No stack-size
reduction or altered executable has been promoted merely to pass this test.

Real-BBS carrier loss, same-process redial/retry and physical integration remain
open. The next application task is to recover sufficient memory for this full
launch configuration, then rerun the unchanged carrier acceptance checks.

## Independent receive-pressure composition

All five internal-viewer capture/HOLD/virtual-printer combinations pass with
the current parent. The local page and restored live frame/cursor are exact
while3202 bytes arrive; capture and PRN bytes, file ownership, query/keyboard
return and hardware/configuration preservation are checked. These are synthetic
COM1/BOTH-flow fixtures, not sustained physical flow-control acceptance.

The historical synthetic PRM fills its undefined fields with A5h. Its external
viewer field was therefore malformed when used with the current external-tool
feature: the first attempt never opened the internal file and correctly failed
its viewer checks. That attempt is retained and excluded. The explicit
`--internal-fallback` option clears only that65-byte synthetic tool field;
all five reruns then pass without any application change. The configured
external viewer retains its separate actual BBS roundtrip evidence.
