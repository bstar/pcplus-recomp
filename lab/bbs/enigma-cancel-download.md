# Canceling an ENiGMA download

The actual DOS Escape workflow exposed a client bug: the normal ZMODEM output
callback stops accepting writes once the local cancellation fault is latched.
The engine's cancel burst therefore could not reach the UART. The surrounding
owner sent only the two CAN bytes used by X/YMODEM, leaving SEXYZ sending binary
data into the ANSI parser. An actual retained capture ends with the terminal's
unsupported-function stop instead of a usable BBS menu.

The maintained ZMODEM failure path now sends eight CAN bytes and ten backspaces
through the existing bounded, fault-tolerant physical writer. X/YMODEM retains
its two-byte policy. The ZMODEM owner then consumes residual receive bytes with
the real UART low-water/RTS handling before releasing the parser. It requires
nine quiet BIOS ticks and allows180 total drain ticks. If input never becomes
quiet, the session exits with status14 instead of passing binary data to ANSI.
This changes maintained behavior; the recovered native baselines are untouched.

The first three-tick quiet interval passed two sessions but failed a later run
when delayed serial delivery outlasted it. That counterexample is retained.
Linked checks now inject late bytes after four and six modeled BIOS ticks, as
well as continuous input. They require exact partial-file cleanup, the full
cancel burst and either a clean return or the bounded fatal exit.
A separate BIOS-clock jump counterexample caught a high-word deadline branch
that returned to the parser. Both elapsed-time checks now take the fatal path
for that discontinuity; the focused model retains the failing prior binary and
requires status14 on the corrected one. Upload cancellation also retains the
source file and closes its owned handles.

`enigma_cancel_download_dos.py` uses a separately owned ENiGMA candidate and a
generated stored ZIP containing32KiB of deterministic data. The existing
independent timer sampler inserts Escape through BIOS INT16h only after the
actual transfer footer shows received KiB. It does not modify product state or
generate protocol replies. A high-bit marker in its captured timer word proves
that BIOS accepted the key. The usual hardware sampler also runs.

The acceptance requires a CRC-valid source-matching data packet before cancel,
no earlier EOF, the full cancel burst on the wire, no remaining partial/staging
files at the next NFO request, a real NFO response, an exact retry of the same
34,169-byte ZIP, and a further NFO response on the same authenticated connection.
The server must show a failed canceled protocol followed by a successful retry.
Normal DOS exit, original device state and unchanged input identities remain
required. A completed download alone cannot pass this workflow.

The larger fixture also exposed two narrow assumptions in the passive auditor.
An exact already-verified replay can remain in flight after EOF; its bytes must
still match and its completion reply must be observed before that late packet
finishes. SEXYZ's `zmodem_get_zfin` alternates ZFIN and ZABORT retries while
awaiting the receiver's ZFIN. The auditor admits that sequence only after an
initial ZFIN, with verified EOF, the actual receiver's ZFIN and literal `OO`.
An initial abort or application text cannot substitute for completion.
`check_enigma_cancel_audit.py` damages payload/control/EOF/finish/menu evidence
one condition at a time; each corruption must reject.

The DOS harness now closes accepted nullmodem clients and bounds listener
shutdown after an emulator timeout. A separate actual DOS infinite-loop program
verifies that an accepted serial connection cannot leave the harness waiting
forever, and that timeout remains a failed test rather than a compatibility pass.

With a fresh checked candidate, prepare the larger isolated fixture and start
it through the pinned BBS environment:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_search_fixture.py \
  --candidate build/bbs-lab/NEW/candidate \
  --server-root /home/bstar/projects/black-flag-bbs --transfer-bytes 32768
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate
./tools/dev --command python3 lab/bbs/enigma_cancel_download_dos.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_LABEL
./tools/dev --command python3 lab/bbs/check_enigma_cancel_audit.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_LABEL
./tools/dev --command python3 lab/bbs/check_dos_harness_timeout.py \
  --label UNIQUE_TIMEOUT_LABEL
```

Use a new result label for every attempt. The server is isolated, its archives
and users are synthetic, and its staged decoder is separate from the live board.
The test does not establish live-catalog, physical RS-232 Wi-Fi modem or complete
application acceptance. The [acceptance record](../../docs/validation/enigma-cancel-download.json)
keeps current evidence and earlier failed attempts separate.

The later [carrier checkpoint](enigma-carrier.md) adds the built-in modem path,
finite receive credit and final receiver-ZFIN-before-OO ordering. This earlier
receipt identifies its own binary/auditor; its file/menu passes do not replace
that stronger confirmation and carrier acceptance.
