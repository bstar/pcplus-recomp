# Configurable ZMODEM receive credit

Machine launch profiles can now choose a ZMODEM receive credit with `/Z:n`,
where `n` is a decimal byte count from1 through8192. For example:

```dos
TERMINAL @BOCA.PRM COM1 38400 8N1 HARD /Z:256
```

The [validation record](validation/zmodem-receive-credit.json) keeps the host,
linked and actual DOS scopes separate and binds their source/receipt hashes.

This advertises256-byte receive credit to the remote sender. Checked reception
with credit below8192 also clears CANOVIO, requesting synchronous frames while
retaining CANFDX and CRC32 (flags33). The default/8192-byte checked offer and all
legacy API offers retain flags35. A sender can ignore the credit; the stock
SEXYZ helper still uses larger packets.
It does not set the DTE speed, modem carrier speed, UART ring size or decoder
workspace. Omitting the switch preserves the existing8192-byte offer. The
8192-byte decoder remains available for peers that ignore smaller offers.
The setting affects receiving only; outgoing transfers still negotiate the
remote receiver's capabilities.

The switch is a source-owned startup policy suitable for a machine's batch
file. It is not written into an unidentified PCPlus PRM field. Zero, overflow,
values above8192, duplicate switches and invalid command tails are rejected.
The parser stages the value alongside the other startup options and publishes
them only after the entire command tail validates. Help and parse failures
preserve the prior state. A fresh parse without the switch restores the default.

The core exposes `zm_run_profile` with an explicit receive-credit argument;
zero selects the existing default. Existing `zm_run` and `zm_run_link` entry
points retain their previous behavior. Invalid arguments return before session
mutation or transport/storage callbacks. The linked terminal independently
checks an invalid receive policy before opening batch storage.

The [native conservative checkpoint](validation/zmodem-native-conservative.json)
binds53 host,99 actual DOS and14 linked recovery cases, alongside64 file-owner
fault assertions and160 ordinary linked regressions. Both CRC widths cover
credits0,1,128,256,1024,8191 and8192 in the checked host API. Two actual DOS
component cases additionally exercise checked recovery with256-byte credit.
Fresh unchanged-stock-helper paced host runs complete65797 exact bytes at
6000bps/default offers and1200bps/native256-byte synchronous offers. Each
experiment forbids rewriting any complete offer and passes independent
source/CRC/EOF/ZFIN/OO/opposite-control audits. These host experiments do not
establish the current DOS-to-stock-BBS audio workflow or physical acceptance.

The [fresh independent DOS interoperability record](validation/zmodem-native-conservative-lrzsz.json)
also passes two full automatic-receive sessions against pinned lrzsz, one with
CRC16 and one with CRC32. Each receives empty, one-byte and65797-byte all-octet
files with native credit256/flags33, then returns to keyboard/DSR interaction
and normal DOS/UART/IRQ restoration. A separate passive audit checks exact
source bytes, CRCs, file positions, EOF/ZFIN/OO and every actual receive offer.
The harness has no per-byte timestamps, so it supplies no opposite-control
causality or audio/BBS/hardware acceptance. The older linked/DOS validation
record above retains its earlier binary, offer flags and case counts.

Small advertised credit alone is insufficient for the stock SEXYZ sender:
the [stock measurements](validation/sexyz-receive-credit-stock.json) show that
it can still send8192-byte packets after a256-byte offer. The separately pinned
[sender candidate](validation/sexyz-send-credit-candidate.json) bounds both
packet size and synchronous groups. Pairing this policy with that candidate
still requires actual DOS/BBS/audio testing. Neither smaller credit nor the
host tests establish sustained audio performance or physical modem acceptance.

The direct DOS pairing exposed a separate SEXYZ empty-file defect: its ZRPOS
guard rejected positions equal to file size, including zero for an empty file.
The original credit-only candidate and its failed batch are retained. A
separate [Nix candidate](validation/sexyz-send-credit-eof-candidate.json) built
with `tools/build-sexyz-send-credit-eof` permits
exactly EOF while retaining rejection beyond EOF. Its source-function guard
checks cover170 cases. The real DOS terminal then receives the complete empty,
one-byte and65797-byte batch with `/Z:256`; a passive source/CRC/EOF/ZFIN/OO
audit measures both maximum packet and synchronous-group payload at256 bytes.
Keyboard/DSR, source preservation, hardware restoration and normal exit pass.
This direct stdio-helper/TCP test has no BBS login or audio bridge. Neither
sender candidate has been installed on the live BBS.

Verification is split between the source-built host API test, the linked
8086 parser, linked foreground/UART/file-owner tests, actual DOS component
tests and the full DOS terminal against independent lrzsz. The terminal test
accepts `--receive-credit n`, records the exact startup arguments, checks the
offered credit on the serial wire and still requires exact files, hardware
restoration, normal exit and post-transfer keyboard/DSR interaction. Its
`--large` fixture crosses64KiB. These boundaries remain distinct from the
pending slow-audio campaign.
