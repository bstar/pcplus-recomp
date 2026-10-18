# YMODEM code placement

The maintained YMODEM engine and batch-header codec now execute in
`CONFIG_CODE`. Their protocol C sources are unchanged from published commit
`245e681`; resident UART, recovered CRC and checked DOS file owners remain behind
explicit call adapters. Ordinary recovered XMODEM code stays in its original
resident placement.

The `18b99f97` build reduces resident code from 65,298 to 61,970 bytes, making
3,566 bytes available in that 64 KiB segment. Near data and stack remain 64,480
bytes. This creates code address space for further application work; it does
not reduce total conventional-memory use. The adapters and segment alignment
increase the retained DOS parent, including PSP, from 314,736 to 315,200 bytes.
The other static storage and child-retention checks still apply.

## Calls across segments

Four public near-cdecl entries retain their existing caller interfaces:
`ymodem_run` and `batch_header_end` take two words, `batch_header_encode` takes
six, and `batch_header_decode` takes three. The encoder's DWORD length occupies
two consecutive words. Both entry wrappers copy exactly the declared argument
words and preserve returned AX/DX and FLAGS while releasing their copies.

Eighteen callbacks provide resident CRC, serviced UART, batch download/upload
ownership and compiler arithmetic. Nine callbacks use explicit one-to-three-word
cdecl frames. Seven zero-argument callbacks have a distinct declaration family
and plain call/return frames. Two register callbacks retain Watcom's actual
32-bit arithmetic helper convention. Shared pointers and state remain near with
DS equal to SS. All four executable code segments survive DOS child execution.

Both assembly sides consume `src/terminal/config_abi.inc`. The executable/map
inspector verifies exact calls, copied arguments, returns, distinct code extents
and MZ segment relocations. There are now 60 configuration bridge pairs and 109
pairs across all static far modules. The malformed-image suite rejects 269
changed frames, targets, returns, relocations and layouts.

## Compiler helper imports

The pinned small-model compiler emits near calls to `__U4D` and `__U4M` while
compiling the unchanged codec. Those calls must reach local thunks in the codec's
new CS. `standalone/omf_imports.py` redirects only the corresponding global
EXTDEF names in the freshly compiled object, before linking. It updates their
record lengths/checksums and retains all symbol indices, type-index bytes,
local symbols, code, data and fixups. The division import occurs twice and the
multiplication import once.

The record identities and variable-width index format follow Open Watcom's
[OMF definitions](https://github.com/open-watcom/open-watcom-v2/blob/master/bld/watcom/h/pcobj.h)
and [linker symbol reader](https://github.com/open-watcom/open-watcom-v2/blob/master/bld/wl/c/objomf.c).
Missing imports, colliding destinations, malformed records and incomplete or
multiple modules reject before writing a normalized object. This build step
reads no original executable. Independent `wdis` output must match after
substituting the two import names back; the inverse object transformation must
also reproduce every original compiler-output byte.

Raw object hashes stay in a separate build artifact because OMF source-path
records differ across checkout locations. The runtime manifest records the
stable import counts and transformation boundary, preserving byte-identical
executable and manifest checks in a fresh source checkout.

## Validation

`./tools/build test-ymodem-far` runs the 269 malformed-image checks and 413
linked migration checks. The latter execute actual linked code, check wide
DWORD encoding/decoding against independent decimal results, observe returned
registers/FLAGS and stack positions across every new callback, and exercise
real framing/file-owner paths with an independent CRC peer. Only DOS, BIOS and
hardware boundaries are modeled. The same 413 checks also pass in the isolated
source checkout without original executables, installation data or historical
build artifacts. The validation recorder authenticates the comparison baseline
against its published source commit separately.

The existing 23 linked YMODEM cases, 30 independent actual DOS peer recipes,
77-command terminal suite and 64-output fresh source rebuild provide separate
behavioral and build evidence. The hash-bound
[validation report](validation/ymodem-far-code.json) records the completed runs,
source identities, historical baseline authentication and retained artifacts.
Stock BBS editor/transfer reports remain separately scoped: ENiGMA's immediate
Home/Insert issue is still a compatibility boundary, and explicit packet
buffering remains an experiment. Physical RS-232/Wi-Fi modem testing, other
protocol families and the complete application remain unfinished.

The same executable also passes four production DOS menu cases, six clipboard
transfer workflows, eleven selected-table reload cases and the controlled
parser-split menu probe. Selected stock Synchronet XMODEM and ENiGMA YMODEM
menu/clipboard downloads pass, including ENiGMA's second filename search after
transfer. See [stock transfer evidence](validation/bbs-clipboard-transfers.json).
Synchronet's editor passes; immediate ENiGMA Home fails while Insert passes in
this run. The separately recorded 30 ms buffering experiment passes both.
Neither editor workflow saves a draft. The temporary synthetic-account logon
exemption is restored and independently verified in the
[account fixture record](validation/bbs-ymodem-far-logon-fixture.json).
