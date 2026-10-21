# Stock SEXYZ receive ownership ends before closing OO

The [full audio upload02 receipt](../../docs/validation/synthmodem-audio-upload-02.json)
records81 positive checks out of82. The required late-tail gate remains false.
This is a different failure from upload01's native premature replay: upload02
has12 exact packets with no replay, validated opposite controls and FIN/OO,
an exact11521-byte official upload, preserved source data/stat, actual details
form completion and a fresh search/list. All12330 online DOS bytes survive the
independent offline caller decoder, actual guest DATA_RX and Telnet path exactly.
All66879 BBS display bytes survive. Normal DOS, UART/PIC/IRQ and helper timer
cleanup pass; frontend skipped/failed/pending byte counts and gateway errors
are zero.

The receiver exits at `2026-10-21T05:13:06.047Z`. Its last ZFIN byte is submitted
to the DOS frontend256.981ms later. PCPlus submits its required literal `OO`
259ms after that exit, roughly2ms after the final reply byte. The relay observes
the pair319.372ms after helper retirement. These are transport observations,
not DOS application-consumption timestamps. The two wall/monotonic anchors
differ by532ns, with maximum2084ns sampling interval. No late retransmitted
header is present, but the two late closing bytes are not waived.

The final keyboard suffix is independently observed as Enter, Tab, Enter,
S/Enter, AUDIOUP.BIN/Enter/Enter. The server reaches a new search and file list.
That successful navigation does not prove that every returned BBS form will
handle the late closing bytes safely.

## Isolated receiver evidence

The [subprocess counterexample](../../docs/validation/sexyz-receive-finish.json)
uses the unchanged maintained host C sender and the same11521-byte all-octet
payload. It delivers the complete transfer and waits for the real receiver's
ZFIN, then withholds only the sender's closing OO for up to350ms.

* Stock pinned SEXYZ3.6 exits with0 before OO is delivered. The host fixture
  correctly reports a closed transport when it subsequently attempts delivery.
* Independent pinned lrzsz remains live, consumes OO and exits with0.

Both receivers install exact files and the source owner closes once. Attempted
and delivered wire are separate artifacts. This is a real helper subprocess
test with a modeled delivery delay, not a DOS, audio, BBS or physical test.
No receiver reply is fabricated and no running server is changed.

```sh
./tools/dev --command python3 lab/bbs/check_sexyz_receive_finish.py \
  --output build/bbs-lab/sexyz-receive-finish-NEW
```

The helper's shipped build manifest identifies upstream commit
`e7a825704ef5329c7ef8408749671291a85ef7f2`.
The corresponding [sexyz.c receive_files implementation](https://github.com/SynchronetBBS/sbbs/blob/e7a825704ef5329c7ef8408749671291a85ef7f2/src/sbbs3/sexyz.c)
returns directly on ZFIN/ZCOMPL after `zmodem_recv_init` sends the reply.
The separate [zmodem.c receive-files wrapper](https://github.com/SynchronetBBS/sbbs/blob/e7a825704ef5329c7ef8408749671291a85ef7f2/src/sbbs3/zmodem.c)
has an OO wait, but SEXYZ uses its own receive loop. Current upstream master
was also reviewed on2026-10-21 and retains that immediate-return path; upgrading
without a verified change is not an established remedy.

The ordinary DOS sender cannot ensure OO precedes receiver retirement when the
receiver exits before its reply has traversed the slow link. Omitting OO or
emitting it before the peer's ZFIN would fail the required finish checks.

## Next integration step

Keep the unmodified stock result as an open compatibility gap. Prepare a
separately identified receiver candidate that retains protocol ownership for a
bounded closing handshake after ZFIN. It must consume the exact closing pair,
preserve any legitimate closing retries, service disconnect/cancel, and reject
corruption, incomplete closure and endless flow/noise without an unbounded
purge. Reuse the configured timeout rather than assuming a fast TCP round trip.

Use the existing Nix toolchain for the source build. Compare stock, candidate
and reference in the isolated delayed-OO test before configuring the owned
loopback lab. Any candidate audio run must use a fresh owned fixture, retain
all existing data/control/storage/return/cleanup gates, and be labeled as using
a modified helper. Preserve AUDIOUP.BIN and its official metadata from upload02.
The user's LAN server and global modem runtime remain unchanged. No upstream
issue or message has been sent.

Physical Boca/SPA2102, other peers, pressure/cancel/loss and all F01–F16 gates
remain open.
