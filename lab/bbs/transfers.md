# Actual BBS file transfers

These tests connect the source-built DOS terminal to the owned loopback
Synchronet and ENiGMA½ servers. The BBS's actual SE/X/Y/Z helper is the protocol
peer. The modem bridge handles Hayes/Telnet transport; it does not acknowledge
blocks or supply terminal replies. All accounts, files and file areas are
synthetic, under ignored `build/bbs-lab/`.

Use `./tools/dev --command` for DOS probes and `./tools/bbs-dev --command` for
server setup/reference probes. The latter supplies the Nix runtime dependencies
for the BBS helpers. No global package installation is required.

After the base lab servers have been installed, prepare transfer areas with no
active lab sessions:

```sh
# Synchronet must already be serving its owned loopback runtime.
./tools/bbs-dev --command python3 lab/bbs/synchronet_transfer.py setup
# ENiGMA loads these settings at startup.
./tools/bbs-dev --command python3 lab/bbs/enigma.py stop
./tools/bbs-dev --command python3 lab/bbs/enigma_transfer.py setup
./tools/bbs-dev --command python3 lab/bbs/enigma.py start
```

The DOS probe runs from its private D: drive and invokes `C:\TERMINAL` from the
frozen build directory. Short transfer filenames therefore resolve to the
owned result directory. Use a new result label for every attempt; only one
session may use each synthetic BBS account at a time.

## Verified checkpoint

Frozen terminal SHA256
`036a80922c783887249224122f1f44b856d0ff8ae22a106ffe843cb5c9f1cdad`
passes all four actual DOS XMODEM-1K/CRC workflows:

| Server | Direction | Result label | Source / accepted bytes |
| --- | --- | --- | --- |
| Synchronet | Download | `bbs-transfer-download-2` | 11521 / 11648 |
| Synchronet | Upload | `bbs-transfer-upload-1` | 11521 / 11648 |
| ENiGMA½ | Download | `bbs-transfer-download-1` | 11521 / 11648 |
| ENiGMA½ | Upload | `bbs-transfer-upload-1` | 11521 / 11648 |

Each transfers eleven 1024-byte and three 128-byte blocks, preserving 127 SUB
padding bytes. Every frame acknowledgement and the two-EOT closure are checked
against the observed opposite-direction bytes. The installed files, official
server metadata and subsequent menu interaction pass; uploads preserve their
source bytes/inode/size/mtime. All completed runs restore sampled hardware,
preserve the synthetic PRM and change only the directory's expected call
accounting fields. ENiGMA's bounded server-log audits independently confirm a
single authenticated session, stock helper exit 0, then the file menu and list.
The download log audit was performed retrospectively with an explicit end
offset before the next session; the upload audit ran inside its harness.

The passive auditor also passes ten regression groups, including checksum
framing, retransmissions, false SOH prefixes and rejection of missing/falsely
attributed acknowledgements. This does not make checksum-mode BBS transfers a
tested case; only CRC/1K was run against these actual servers here.

The first Synchronet DOS attempt, `bbs-transfer-download-1`, is retained as a
**harness failure**. Unsupported ADDKEY token `period` stopped its key queue at
the filename dot, before Alt-R or any native transfer. The timeout also exposed
Python3.14 connection cleanup waiting indefinitely. The retry uses literal `.`,
an isolated D: working directory and bounded cancellation of owned connection
tasks. No shared target was created or removed. The report deliberately contains
four passing runs and this failed attempt, so `all_recorded_runs_passed` is false.
No terminal executable or server protocol implementation changed for the retry.

Independent reference probes also retain the initial incorrect post-transfer
pause/navigation assumptions and Synchronet's one-EOT upload failure. Those
reference failures are distinct from actual DOS results; the native DOS sender
already handles NAK/second EOT correctly. Reference captures stay in each
server's ignored transfer directory.

[Recorded results, provenance and artifact hashes](../../docs/validation/bbs-transfers.json).

## Evidence required

`test_transfer_dos.py` launches the actual DOS executable with an explicit
SHA256 and a fresh result label. It records both application byte streams,
observation-only read timestamps, Telnet negotiation, DOS video memory and
before/after IRQ/UART/PIC state. Its passive protocol audit locates a validated
first block matching the owned source, then checks sequence numbers, integrity,
retransmissions, padding, EOT and acknowledgements. It requires actual
post-transfer keyboard input and a subsequent BBS menu response.

Downloads must match every accepted payload block in the DOS destination.
Uploads must leave the DOS source unchanged and match the installed server
file; a separate official server metadata API audit is required. Normal DOS
exit alone cannot pass either direction. Original XMODEM has no original-length
field: its SUB padding remains in the resulting file. The test records source
and accepted lengths separately.

`record_transfers.py --run SERVER:LABEL ...` publishes selected results and
artifact hashes to `docs/validation/bbs-transfers.json`. Include failed attempts
as separate labels when recording successful retries. Wire captures, databases,
configuration backups and server executables remain in ignored build storage.

## Server configuration

Synchronet uses pinned development commit
`9de2c48d0265b07e1a8406d8a55d31df4fad7ee8` (3.22a), its stock `sexyz`, and a
dedicated `pcplab` file directory appended to the existing configuration.
`synchronet_transfer.py` registers the deterministic `PCXTEST.BIN` through the
official `FileBase` API. The existing configuration prefix is backed up and
verified unchanged. Protocol `1` selects XMODEM-1K/CRC; `X` selects the stock
original/checksum configuration. The stock transfer path includes a hang-up
question and a post-transfer pause before returning to the file menu.

ENiGMA½ uses pinned commit `6c25317168b762f7d9088a54d3f8295438827a0e`
(0.5.1-beta), its bundled SE/X/Y/Z helper, and a dedicated `pcplus_transfer`
storage area. `enigma_transfer.py` seeds the source through official
`oputil fb scan`; metadata checks use the upstream `FileEntry` API. The helper's
ELF loader/library paths are adapted to the pinned Nix environment, with
original and adapted hashes recorded. Its protocol implementation is unchanged.

The stock ENiGMA protocol selector filters by `external.recvArgs` when no
receive filename is supplied, including download selection. Its bundled
XMODEM configuration defines only `recvArgsNonBatch`, so it is omitted there.
The lab explicitly configures `recvArgs` for one fixed, owned blind-upload
filename, `PCXUP.BIN`, and puts XMODEM first in the selector. This is a limited
single-file lab configuration, not batch support or an unmodified-default
configuration pass. Server source, escape decoder and stock artwork remain
unchanged. Source references:

- [Protocol selector](https://github.com/NuSkooler/enigma-bbs/blob/6c25317168b762f7d9088a54d3f8295438827a0e/core/file_transfer_protocol_select.js)
- [Default protocol definitions](https://github.com/NuSkooler/enigma-bbs/blob/6c25317168b762f7d9088a54d3f8295438827a0e/core/config_default.js)

## Boundaries

The serial path is COM2/19200/8N1/HARD in DOSBox-X with ready CTS. These runs
cannot establish physical Wi-Fi modem buffering, CTS/DCD wiring or hardware
timing. They do not establish YMODEM/ZMODEM, complete application reconstruction
or editor compatibility. The independently reproduced ENiGMA fragmented-escape
editor failure remains separate; see [editors.md](editors.md).
