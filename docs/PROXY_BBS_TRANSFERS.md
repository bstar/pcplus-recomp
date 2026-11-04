# Current release transfers through the actual SynthModem proxy

This checkpoint uses the current Screen Pause candidate,
SHA256 `501629c093d731be8f3324f185e128af76e00c2942e5ad3463c1ce7da54edb6e`,
with the real installed SynthModem TelnetProxy and the stock owned ENiGMA file
base/helper. Application bytes and the physical deployment selection are unchanged.

The route is DOS8086 COM3/3E8h/IRQ5,19200/HARD → modeled Hayes serial shim →
actual SynthModem proxy → owned loopback ENiGMA → its real SE/X/Y/Z helper.
The shim answers modem commands but forwards the online stream raw. Only the
actual proxy negotiates and encodes/decodes Telnet. It advertises the compiled
80x24 geometry, has the in-band menu escape disabled, and uses250ms input
sequence framing with no artificial per-byte delay. No SIP or DSP is involved.

## What is checked

The driver selects an explicit source-matched terminal and uses the original
splash and real Alt-Z/PgUp/PgDn/F2 commands. The existing passive ZMODEM audit
still validates ZFILE/data CRCs, exact length, ZEOF, ZFIN/OO and opposite-direction
controls. It also requires actual post-transfer BBS input and menu output,
normal DOS return, unchanged configuration/source files and restored hardware.

The download is the owned11521-byte PCXTEST.BIN fixture. Uploads generate a fresh
DOS83 filename and unique deterministic binary contents containing every byte
value. No existing upload is replaced or deleted. The upload audit queries
ENiGMA's official FileEntry API and independently checks the installed file,
area, length and SHA256. A bounded server-log audit checks authentication,
the helper's successful exit and the file-base return route in the same session.
No message is posted.

The serial observer previously assumed every upstream was Telnet-encoded.
For an explicit raw proxy it now observes application bytes directly, preserving
literal FF bytes and their offsets. Its269 encoded-stream and263 raw-stream
partitions cover all byte offsets, including FF-FF and FF-FB sequences.
Normal direct-BBS observation retains its original Telnet decoder.

The wrapper additionally requires exact equality between its observed online
streams and the actual proxy's serial input/output captures. Product, proxy and
selected server/config/helper files are hashed; the final runs check those
inputs did not change during the session. The [receipt](validation/proxy-bbs-transfers.json)
keeps protocol results, observer evidence and route identities separate.

## Retained teardown fixture failures

The first upload passed protocol, stored bytes, official metadata, hardware and
menu checks. Its wrapper failed full-output equality: the proxy had emitted673
additional bytes from the final file-list redraw when the DOS test exited.
The DOS observation was an exact prefix, with no byte mismatch. Increasing the
final wait from three to eight seconds did not fix it. The trace then showed
the actual cause: the minimal Hayes shim forwarded PCPlus's configured
`+++ATH` hangup into the BBS as input, triggering another redraw at teardown.

An explicit fixture option now recognizes only that configured guarded hangup.
It requires quiet before `+++` and between `+++` and `ATH`, acknowledges the
modem command and closes the upstream, instead of forwarding modem-control
bytes to the BBS. The declared500ms guard matches this synthetic fixture's
observed approximately600ms post-escape pause; it is not a measurement or
configuration change for the Boca's S12 register. Partial candidates expire
and are forwarded, and unguarded/binary sequences remain data. This option is
off by default and is not a complete Hayes escape/command interpreter.

The guard checker covers294 partitions, invalid guards, bounded partial flushes
and binary preservation. Existing modem/Telnet and packetization regression
groups still pass. The strict proxy/observer equality checks remain. Failed
artifacts are retained, and each retry uses a fresh upload filename rather
than removing previous successfully stored files.

## Upload details focus

The first guarded upload exposed a separate test-navigation failure: the real
helper finished, but Enigma stayed on UPLOAD DETAILS and the file was not
committed. The strict menu/metadata gates correctly rejected that run. The
non-archive scanner in `core/file_base_area.js` supplies a filename description,
so `core/upload.js` starts details focus at tags rather than description. The
old three-Tab sequence cycled tags → year → Continue → description, where Enter
inserted a newline. The corrected recipe uses two Tabs, then Enter. The driver
hashes these source files, the view controller and the exact menu definition in
addition to the protocol/helper inputs. Failed traces remain available; file
existence or helper exit alone is never accepted as completed upload evidence.

## Remaining acceptance

These tests exercise the actual proxy and BBS transfer helper, extending the
independent-peer [release matrix](TRANSFER_RELEASE_READINESS.md). They do not
exercise the SPA2102's audio/SIP path, SynthModem's DSP, the Boca's physical
carrier/flow timing, remote public BBSes or every transfer protocol. The physical
BUSY report and full original-feature inventory remain open. No live LoC server
or SynthModem service is restarted, and no DOS machine file is deployed here.

Use a new label for every run; the driver locks the shared synthetic account:

```sh
./tools/dev --command python lab/bbs/test_proxy_transfer_dos.py \
  --runtime /path/to/synthmodem --terminal build/SELECTED/TERMINAL.EXE \
  --label new-proxy-download --mode download
```
