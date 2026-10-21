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

## Isolated source candidate

The [candidate receipt](../../docs/validation/sexyz-receive-finish-candidate.json)
binds a source-built baseline and closing-owner candidate to the same pinned
upstream commit. The62 original C/header files reproduce the shipped standalone
source digest exactly. Only `sexyz.c` changes among those files; the candidate
adds the closing owner and the maintained framing codec. Full corresponding
source and LICENSE accompany each Nix output. A Nix `--rebuild` check succeeds.

The candidate's ZFIN receive branch retains exclusive protocol ownership until
literal OO, with a total monotonic deadline using RecvTimeout clamped to1..60
seconds. It polls in one-second pieces, checks cancellation/disconnect both
before and after polling, and fails closed on timer errors/backward time.
Incoming bytes cannot reset the deadline. At most512 bytes and nine CRC-valid,
zero-position queued closing headers may precede OO. It does not send extra
replies to already queued retries, which could otherwise leak to the sender's
resumed display. Unexpected headers, bad CRC, nonzero positions, noise and an
incomplete closing pair remain failures. Loss recovery beyond this bounded
queued-retry policy is not accepted by these checks.

The receipt includes24 real C-owner cases with modeled boundary callbacks,
four real receiver comparisons, and ten actual candidate subprocess cases with
closing-tail faults. The shipped and same-source stock builds both retire
before delayed OO; the candidate and independent lrzsz reference remain live
and consume it. Every subprocess case transfers the original11521-byte payload.
Real candidate tests accept queued closing headers/flow, reject corrupt or
over-limit tails, and honor a one-second configured timeout for missing OO.

Build and test isolated outputs with pinned Nix:

```sh
nix --extra-experimental-features 'nix-command flakes' build \
  ./nix#sexyz-source-baseline ./nix#sexyz-receive-finish-candidate \
  --out-link build/bbs-lab/sexyz-finish-build

./tools/dev --command python3 lab/bbs/check_sexyz_finish_bounds.py \
  --source build/bbs-lab/sexyz-finish-build-1/share/sexyz-source \
  --output build/bbs-lab/sexyz-finish-bounds-NEW

./tools/dev --command python3 lab/bbs/check_sexyz_receive_finish.py \
  --source-baseline build/bbs-lab/sexyz-finish-build/bin/sexyz \
  --candidate build/bbs-lab/sexyz-finish-build-1/bin/sexyz \
  --output build/bbs-lab/sexyz-receive-finish-candidate-NEW

./tools/dev --command python3 lab/bbs/check_sexyz_finish_integration.py \
  --candidate build/bbs-lab/sexyz-finish-build-1/bin/sexyz \
  --output build/bbs-lab/sexyz-finish-integration-NEW
```

Each result directory must be fresh. The INI override in real fault tests lives
beside an exact isolated copy of the candidate; neither global configuration
nor the existing BBS helper is replaced. The DOS executable, stock server inputs
and SIP/DSP runtime remain unchanged. The candidate is identified by its Nix
package path and recorded binary hash, separate from the shipped helper.

## Next integration step

Keep the unmodified stock result as an open compatibility gap. The next test is
a separately identified candidate BBS fixture and real audio upload, retaining
the full-size source, unchanged DOS binary, DTE, modem runtime, artwork and all
data/control/storage/return/cleanup gates. Candidate helper results cannot be
reported as unmodified stock compatibility. Preserve AUDIOUP.BIN, its official
metadata and the existing stock server; use fresh isolated storage rather than
overwriting the accepted file or weakening duplicate protection. The user's LAN
server and global modem runtime remain unchanged. No upstream issue or message
has been sent.

The [prepared candidate board](../../docs/validation/enigma-receive-finish-instance.json)
now runs separately at127.0.0.1:23235 from the same tracked ENiGMA commit. It
has consistent snapshots of synthetic databases and private logs/drop/storage.
Only its ZedZap receive command selects the candidate; all other configuration
differences are the declared local path/port relocation. The copied AUDIOUP
entry is preserved and removed through the official CLI inside this clone;
the original board's entry/file/helper/code remain unchanged. Seven actual
navigation prerequisites and thirteen read-only isolation/namespace checks pass.

The audio driver accepts this instance only through explicit `--fixture-lab`,
records its manifest/helper hash and freezes the prerequisites, candidate source
and independent auditors. Audit metadata/storage queries bind to that recorded
instance and reject mismatched roots/manifests. Default runs retain the stock
namespace. This preparation grants no candidate audio acceptance.

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_receive_finish_instance.py setup \
  --lab build/bbs-lab/enigma-rxfinish-candidate-NEW
./tools/bbs-dev --command python3 lab/bbs/enigma_receive_finish_instance.py start \
  --lab build/bbs-lab/enigma-rxfinish-candidate-NEW
./tools/dev --command python3 lab/bbs/check_audio_upload_navigation.py \
  --fixture-lab build/bbs-lab/enigma-rxfinish-candidate-NEW \
  --output build/bbs-lab/enigma-rxfinish-candidate-NEW/navigation
./tools/dev --command python3 lab/bbs/check_receive_finish_instance.py \
  --lab build/bbs-lab/enigma-rxfinish-candidate-NEW \
  --output build/bbs-lab/enigma-rxfinish-candidate-NEW/isolation
```

The fixture owns one fixed loopback port. A fresh setup refuses an existing
directory or occupied port; it does not stop another listener. The prepared
instance can be reused for read-only checks while its upload target is absent.
After upload, preserve the receipt and file before considering another fixture.

Physical Boca/SPA2102, other peers, pressure/cancel/loss and all F01–F16 gates
remain open.
