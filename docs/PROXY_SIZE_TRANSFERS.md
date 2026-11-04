# Binary transfers after startup size negotiation

This check combines the current source-built application, saved startup geometry,
the staged SynthModem size-probe implementation and the owned stock ENiGMA file
helper. It extends [the earlier proxy transfers](PROXY_BBS_TRANSFERS.md) and
[startup-layout checks](MENU_SIZE_LAYOUTS.md). Results are recorded separately
from physical acceptance; no installed application or service is updated here.

The [receipt](validation/proxy-size-transfers.json) binds four passing DOS
workflows and their independent audits: 262,156 transferred payload bytes,
two exact upload/download pairs and nine copied-capture controls. The unchanged
application is SHA256
`a2fd6a3fcdcc30138426d747d8cde400d9fc6eb9ca5fca84d1656aeaf17caa77`,
with all 569 declared public inputs still matching its source-only rebuild.

## Route and payload

The test runs DOS 8086 COM3/3E8h/IRQ5 at 19200/HARD through the synthetic Hayes
serial shim, actual staged SynthModem TelnetProxy and stock loopback ENiGMA
file base with its real SE/X/Y/Z helper. The proxy asks CSI18t before opening
the BBS session. Only the proxy handles Telnet; the serial shim forwards online
bytes unchanged. Input-sequence framing is 250ms with no per-byte delay.

Two upload/download pairs exercise 25 physical rows with the status visible
(80x24 logical) and 50 rows with the status hidden (80x50 logical). Every
direction starts a separate DOS process. Each generated upload is 65,539 bytes,
contains every byte value and 215 copies of a size-reply lookalike, alongside
Telnet-looking bytes. Its paired download reads the stored upload through
the actual file-base helper. Fresh DOS83 names avoid replacing previous files.

The independent auditor removes exactly the observed `loc` menu selection and
one startup-size reply from client serial input. The remaining bytes must equal
the decoded raw Telnet application stream, including size-looking sequences
inside the file. It does not search and strip matching patterns from binary data.

## Required evidence

The producer requires CRC-valid ZFILE/data, exact length, ZEOF, ZFIN/OO and
opposite-direction controls, plus real post-transfer BBS commands and ordered
menu output. Uploads also require the official FileEntry API's name, area,
length and SHA256 to match the actual stored file. Downloads require exact DOS
destination bytes. File existence or a helper exit alone is insufficient.

Independent capture checks bind the actual NAWS, saved PRM, BIOS rows/font,
full 8000-byte video capture, normal DOS return, 42-byte hardware snapshot
restoration, temporary-file cleanup and exact serial/proxy streams. The auditor
replays the CRC and control checks at the observed post-menu time boundary.
The matrix checker binds all source and capture hashes and requires each
upload/download pair to have the same payload SHA256.

Copied-evidence controls accept the unchanged capture and reject wrong NAWS,
an altered owned prefix, damaged payload CRC, wrong BIOS font, incorrect official
file size, different stored bytes, altered hardware and truncated proxy output.
These controls only alter ignored copies; no live catalog or source payload
is changed.

## Retained fixture failures

An initial large download completed its protocol and exact file, but the menu
check expected `64.00` while stock ENiGMA formats the size as `64 KB`. The driver
now obtains the numeric display text from the pinned `core/string_util.js`
formatter. That source is included in the unchanged-server input checks.

A later exact download triggered the synthetic account's cumulative 640K
achievement. Its pause consumed the first character of the scripted search,
and the strict menu-return check rejected the run. The optional
`--post-menu-reset` sequence opens the current file list, dismisses a possible
interrupt, exits the list and reopens it. It requires the actual second list
command and full filename/size response in the observed stream. This fits the
bounded DOS keyboard command without abbreviating the initial full-name search.
An intermediate abbreviated-search experiment returned no entries because
stock search token matching requires the filename token; that rejected capture
is also retained. The BBS achievement system is retained; failed evidence is
not relabeled as passing.

The next upload reached the 512KB Kickstart achievement. Its protocol, stored
bytes and official metadata passed, but its first list command dismissed that
pause instead of opening the list. The same optional reset is therefore applied
to both directions in the final matrix. The ordered helper-return/file-list and
actual post-command response gates remain required.

The existing 500ms guarded-hangup fixture prevents modeled modem commands from
becoming BBS keyboard input. This is a synthetic guard interval, not a measured
or changed Boca S12 value. Each source/helper/configuration set is frozen while
its producer runs, and a new label is required for retries.

## Reproduction and remaining gates

The later [cancel/retry check](PROXY_CANCEL_RETRY.md) adds one actual stock-helper
local-cancel/data/cleanup/retry workflow in the same DOS process and connection
at 25-visible geometry. It has separate BIOS and corrupted-capture evidence;
the four separate-process successful transfers below retain their original scope.

```sh
./tools/dev --command python lab/bbs/test_proxy_size_roundtrips.py \
  --runtime build/STAGED_PROXY/candidate \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW_LABEL
./tools/dev --command python lab/bbs/check_proxy_size_roundtrips.py \
  --run build/NEW_LABEL --output build/NEW_LABEL-independent
./tools/dev --command python lab/bbs/check_proxy_size_transfer_controls.py \
  --label NEW_LABEL-upload-25 --output build/NEW_LABEL-controls
```

This matrix does not prove local cancellation, real DCD loss, same-process
reconnect/retry, every layout/protocol, public BBS compatibility or unframed
transport. SIP/audio, SynthModem DSP, SPA2102, physical Boca carrier/RTS/CTS,
16MHz throughput and the reported physical BUSY condition remain separate
acceptance gates. Broader original PCPlus parity remains open.
