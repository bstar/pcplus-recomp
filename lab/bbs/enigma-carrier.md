# Carrier loss, redial and download retry

This test keeps one source-built DOS terminal running while its first BBS TCP
connection is aborted after an actual partial ZIP write. It redials the same
owned ENiGMA instance, runs the DOS-built ASPECT login again, receives the same
ZIP exactly, and opens its NFO page. The original partial must be removed before
the second login starts. Both directory connection updates are checked.

The Python Hayes/nullmodem harness keeps DCD high and cannot prove carrier
recovery. This workflow uses DOSBox-X's built-in modem with `AT&K3` for RTS/CTS.
Its [pinned source](https://raw.githubusercontent.com/joncampbell123/dosbox-x/dosbox-x-v2026.07.02/src/hardware/serialport/softmodem.cpp)
sets emulated DCD low on network loss while retaining CTS/DSR, and raises DCD on
the next successful dial. A separate Telnet bridge handles negotiation and byte
escaping; it generates no Hayes or terminal/protocol responses. This is emulated
carrier behavior, not physical Wi-Fi modem firmware acceptance.

The interruption requires a nonempty `PCRX.$$$` whose bytes match the generated
source prefix. It is not a timed Escape key. The bridge aborts only the first
connection and owns no live-server socket. A video-only INT1C observer records
carrier-loss/completion notices without reading UART registers, inserting keys
or changing product memory. The before/after sampler verifies hardware restoration.

This exposed a larger-file problem hidden by the fast nullmodem model. The
unlimited receive advertisement let a sender queue data and retries faster than
the slow DOS build consumed them. The first retained run saved the exact34,169
bytes but reported an unconfirmed finish; the timed NFO key arrived while the
transfer still owned input. Its gap between forwarded EOF and receiver ZRINIT
was about15.9 seconds. That is a backlog/status counterexample; exact forwarded
`OO` timestamps do not prove a receiver-ZFIN-after-OO violation in that capture.

The maintained receiver now advertises its real8192-byte packet capacity in
ZRINIT while preserving full duplex, overlapped I/O and CRC32. Recovered native
baselines are unchanged. Host and DOS wire expectations require the new credit.
The keyboard recipe allows more time for the retry, but acceptance requires
actual `RX complete`, validated final receiver controls, no unconfirmed notice
and a subsequent NFO response.

The slow receive also demonstrated valid recovery traffic: a sender can replay
old data before a delayed acknowledgment reaches it. The passive audit checks
every replayed byte/CRC and accepts cumulative ACK/ZRPOS evidence for verified
ranges. Required responses must precede new forward data or EOF. The final
receiver ZFIN must precede forwarded `OO`; a later menu key cannot substitute.
Damaged data, future-position ACKs, missing replies, late ZFIN, retained staging
and missing menu responses must reject in the separate capture replay.
The empty-file boundary has a separate synthetic check: its first empty data
packet requires a real ACK. Original capture-producer and later replay-auditor
identities are recorded separately when the analysis code changes.

Prepare and start the isolated larger-archive search fixture as described in
[cancellation testing](enigma-cancel-download.md), then use fresh result labels:

```sh
./tools/dev --command python3 lab/bbs/check_carrier_relay.py --label UNIQUE_UNIT
./tools/dev --command python3 lab/bbs/enigma_carrier_dos.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_CARRIER
./tools/dev --command python3 lab/bbs/check_enigma_carrier_audit.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_CARRIER
```

The [acceptance record](../../docs/validation/enigma-carrier.json) binds current
binaries, source rebuild, transfer regressions, socket-unit tests and retained
failures. Modules/selected menus are copied from the board; users, archives and
mutable runtime are synthetic. Live deployment/catalog acceptance, physical
modem testing and the wider application requirements remain open.
