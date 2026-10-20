# Concurrent upload ownership

This test opens two actual loopback ENiGMA connections using regular synthetic
users. The reference peers declare their ANSI cursor response and generate
valid Telnet/ZMODEM input. It supplements the actual DOS tests; it does not
establish concurrent DOS clients or physical modem behavior.

Client B starts a 65,539-byte generated upload. It sends enough acknowledged
data for the receiver to flush a real prefix to disk. Client A then starts a
different file, sends an acknowledged partial, cancels, and opens an NFO. Only
A's partial may be retired. No file or catalog entry may be installed yet.

A retries its 1,501-byte file, completes the actual upload details form and
opens the NFO again. Throughout A's recovery, B continues sending valid data
and receiving acknowledgments. B's temporary pathname and inode must survive,
and every recorded prefix must match B's source. B then completes its transfer,
details form, visible achievement pauses and NFO route. Both stored files, uploader identities, hashes and
sizes must match, and private temporary data must be removed.

The passive auditor separately checks recorded bytes/events, data CRCs, ACK and
finish chronology, overlapping external protocol processes, distinct logged-in
sessions, NFO responses, snapshots and official FileEntry metadata. Its negative
cases include coherent event/wire corruption, partial loss/replacement, wrong
source/owner, premature installation, retained data and missing NFO evidence.

Prepare a new checked upload fixture using the existing
[search fixture](enigma-search.md) and [transfer-owner stage](patches/enigma-transfer-owner/README.md).
Do not reuse a fixture containing files from an earlier attempt. Run through
the pinned BBS environment:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma_concurrent_upload.py \
  --candidate build/bbs-lab/NEW/candidate --setup
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/NEW/candidate --private-tmp
./tools/bbs-dev --command python3 lab/bbs/enigma_concurrent_upload.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_LABEL
./tools/bbs-dev --command python3 lab/bbs/check_enigma_concurrent_audit.py \
  --candidate build/bbs-lab/NEW/candidate --label UNIQUE_LABEL
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/NEW/candidate
```

Setup adds only the regular synthetic `locpeer` account to the isolated user
database. The driver records raw traffic, events, snapshots and official API
results under ignored `build/`. Source fingerprints must remain unchanged
during the run. The setup marker also binds the driver used to provision the
additional account. An error retains its capture and a failing report.

Four retained attempts explain harness corrections: a receiver ACK need not
mean stdio has flushed 1KiB to disk; ANSI color sequences can split visible
pause text; the actual details form can initially focus the year field; and
a new user's upload achievements interrupt File Base entry with two paused
notices. A menu-transition log does not prove that its input view is ready.
The driver now observes source-backed disk data, matches visible processing
text and accepts the same description/tags/year/button positions as the DOS
observer. It acknowledges the achievement notices and waits for the actual
File Base command prompt before sending Search. These failures are not reported
as application defects.

The [sanitized validation record](../../docs/validation/enigma-concurrent-upload.json)
binds 18 workflow checks, 19 rejected evidence corruptions, exact staged core
identity and the preceding DOS/cleanup-error checkpoint. All 31 application
products remain unchanged. Concurrent file-list protocol network tests,
simultaneous deletion errors, concurrent DOS clients, live deployment,
upload carrier loss, original dates and full application gates remain open.
