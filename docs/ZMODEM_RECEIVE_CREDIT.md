# Configurable ZMODEM receive credit

Machine launch profiles can now choose a ZMODEM receive credit with `/Z:n`,
where `n` is a decimal byte count from1 through8192. For example:

```dos
TERMINAL @BOCA.PRM COM1 38400 8N1 HARD /Z:256
```

The [validation record](validation/zmodem-receive-credit.json) keeps the host,
linked and actual DOS scopes separate and binds their source/receipt hashes.

This requests a checkpoint within256 payload bytes from the remote sender.
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
