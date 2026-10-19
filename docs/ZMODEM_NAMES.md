# ZMODEM wire and DOS filenames

ZMODEM downloads now accept bounded remote basenames up to255 bytes and map
them to local DOS filenames. The exact ENiGMA game-details download that failed
with `PCPLUS PROBE 01 (1991).ZIP` now completes as `8868026D.ZIP`, with all1301
bytes verified, ZEOF/ZFIN/OO confirmed and NFO interaction after the transfer.

`src/transfer/zmodem_name.c` preserves valid DOS8.3 spelling. Other leaf names
use the eight uppercase hexadecimal digits of CRC32 over the entire wire name,
with ASCII letters folded to uppercase. A safe final1..3-character extension
is retained in uppercase; other extensions use `DAT`. High bytes are opaque
identity bytes. Empty/dot paths, names longer than255 bytes, controls/DEL and
slash/backslash/drive separators are rejected. Device-shaped remote names can
map to safe hexadecimal aliases; the generated stem cannot name a DOS device.
The existing checked storage grammar still owns staging-name conflicts.

This is a maintained compatibility policy. The legacy metadata codec and its
36-byte result ABI stay unchanged. The new adapter validates bounded frame
terminators and padding, normalizes only the local name in a disjoint1024-byte
workspace, then uses that codec for numeric/extension metadata validation.
Results remain atomic and extension offsets still refer to the original input.
YMODEM retains its existing filename behavior.

The ZMODEM session retains the full original wire identity separately from the
13-byte local name passed to storage. A repeated active offer must match that
full identity, even when two remote names produce the same local alias. The
sender still receives DOS8.3 names from its existing source callback. Its
header encoding and source-file enumeration are unchanged.

Existing local targets use the established checked `ZSKIP` policy. Repeated
downloads therefore preserve the existing file. A different wire name can have
the same alias; it is also skipped when that target exists. Use another receive
directory to save such a file. The tests include the real CRC32 collision
between `Game 9P4Ppbwljq4gg3.ZIP` and `Game o6dYr6fHK42eTT.ZIP`, both mapping to
`4F09E7D3.ZIP`. A changed active identity aborts its owned stage; a committed
target remains intact and the later offer is counted as skipped.

All new session storage fits the existing exclusive10KiB transfer arena. The
8086 diagnostic reports a9554-byte session, and the live wrapper adds8 bytes.
The application keeps DS=SS and the existing arena ownership/cleanup contracts.
The normalized-header workspace reuses the session's1KiB data buffer. The
application's resident segment remains65502 bytes; the additional codec lives
in CONFIG_CODE. The source-only build verifies segment and DGROUP bounds.

Validation includes446 independent alias/metadata/engine checks,92 existing
engine regressions,79 sender-window checks and68 actual8086 DOS filesystem
cases. These cover case/extension behavior, high bytes, bounds and overlapping
spans, malformed/missing terminators, CRC16/32 long-name retries, existing aliases
and real hash collisions. The first adapter version accepted a missing metadata
terminator for a short filename because zero padding supplied one; the existing
regression caught it. Both terminators are now required within the received frame.

The custom ENiGMA probe retains passive CRC/payload/handshake checks and maps
the expected wire name to its independently calculated local alias for real
filesystem assertions. Its server audit checks the actual custom search/details
return route. Existing short-name editor/transfer workflows remain separate
regressions. See [the validation record](validation/zmodem-long-names.json).

The historical [search evaluation](validation/enigma-search.json) retains the
pre-fix failure and paired production-codec replay. The new adapter handles
that wire/local distinction before the unchanged strict codec. The live board
remains unmodified; its staged key decoder, physical Wi-Fi modem validation,
full filename UI/catalog integration and whole-application gates remain open.
