# ASPECT stream storage and DOS memory admission

Opt-in `defer_script_buffers=True` builds normal ASPECT
`cbdee1949f0ac6bba34f56ae9c594a17888ef9b5143ee5dca9cd76498737ccfd`.
With the unchanged capability18 parent `61757956`, it passes the real stock
Enigma carrier-loss/redial/exact-retry workflow that failed to launch the
preceding `b61f3a03` child. This is staged software evidence; no deployment or
physical Boca/SPA2102/SIP/audio acceptance is claimed.

## Measured failure and change

The old complete carrier fixture, with and without its optional final-exit
observer, stayed at CONNECT without launching the login script. A short
real-proxy diagnostic recorded DOS EXEC carry set and AX8. A separately
authored small MZ child, deliberately staged under the diagnostic ASPECT name,
queried the real DOS allocator:132544 bytes remained after its own992-byte
block and1168-byte environment. This is a memory probe, not the application
or substitute BBS acceptance. The parent retained478272 bytes; real ASPECT's
MZ minimum was137280 bytes including its PSP, before its inherited environment.

The adapter previously reserved six512-byte CRT stream buffers and six512-byte
pre-PROGRAM copies at startup. The flag allocates each stream buffer when that
stream opens and frees it after fclose, including close failure. An exact
512-byte comparison copy is allocated only while that open stream is bracketed
around PROGRAM. Partial snapshot-allocation failure releases previous copies,
leaves streams owned without publishing an external scope, and returns a heap
error. End/unwind retires every saved copy.

All six slots,512-byte buffers, eight-byte native FILE prefix, exact byte
comparisons and8192-byte C stack remain. No checksum replaces a snapshot and
no script arena or feature capacity is reduced. Twelve pointers replace the
arrays, removing6120 static bytes; added code/alignment leaves a5984-byte DOS
minimum reduction,137280 to131296. The512-byte heap-growth policy and parent
code/data/retention are unchanged. Feature-disabled ASPECT remains exact
`b61f3a03`. A clean public source export reproduces both executables through
the pinned Nix toolchain without originals, prior objects, private configuration
or ancestor Git.

## Validation

- The real DOS8086 adapter fixture passes8819 checks: guarded512-byte buffers,
  failure at each of six snapshot allocations, open/setvbuf/close failures,
  exact saved-byte corruption detection, buffered read continuity and partial
  teardown. No tracked buffer or duplicate free remains.
- The native13-handler/three-helper suite passes7976 checks,16 exact files and
  100 six-slot rounds with near/far heap addresses/sizes and20 JFT entries
  preserved. Binary/text, CRLF/control-Z, sparse positions beyond64KiB, error
  paths and guarded string writes remain covered.
- An unobserved8086 full VM keeps six buffered streams across a third graphics
  child, writes afterward and checks every file. A separate386/UMB50-row run
  also compares both complete8000-byte inner screen/cursor pairs before outer
  ASPECT return. These have different memory footprints.
- One normal DOS8086 parent logs in to stock Enigma through real SynthModem
  Telnet and starts65539-byte receive. After4096 source-prefix bytes reach
  disk, the fixture drops the actual DOSBox modem socket, producing virtual
  NO CARRIER/DCD loss. The stage is empty before a second automatic login.
  The same parent redials, authenticates again and receives the exact file.
  Independent audit checks raw proxy bytes, CRC/finish/controls, both logins,
  directory accounting, carrier notice, bridge/logoff return and hardware/
  settings restoration. No optional resident final-exit witness is used;
  the explicit150-second transfer wait is fixture timing, not physical timing.
- Stock Synchronet retains its exact1920-cell/cursor editor and current ASPECT
  login. Its graphics-viewer workflow keeps the existing386/XMS/UMB profile
  with high observers/helpers.

Exact identities and reports are in
[`validation/deferred-script-buffers.json`](validation/deferred-script-buffers.json).
Earlier cancellation/upload/download and parent rendering receipts retain their
original child identities; they are not relabeled as new-child runs.

Parent size-favoring compilation saved only96 bytes; child function-section
elimination grew the minimum by48. Both experiments are rejected, with local
artifacts retained. Neither switch is part of this change.

## Remaining gates

The physical installation and canonical package recipe remain unchanged.
Refresh active-lease abort/dispatcher/DIV and WAIT/cancel composition with the
dynamic storage, complete package/source identity and reversible deployment
checks, then obtain physical modem/rendering/transfer observations. Broader
original commands, ASPECT, emulations/protocols, Chat and Host parity remain open.
