# Stable foreground recorder state

The [owner checkpoint](validation/recording-owner.json) moves nine immutable
recorder templates into code storage and allocates the terminal's stable
recording owner. It preserves script bytes and write boundaries. The assembly
host initializes the owner at startup and calls its shutdown API before exit.
Record controls and automatic foreground taps are still required; this does
not establish usable recording from the command menu or close any F01–F16 gate.

The recorder's templates occupy223 bytes in CONFIG_CODE. Explicit far reads
copy fixed templates into bounded near stack buffers before output callbacks;
callbacks continue receiving ordinary near DS=SS spans. The header remains one
84-byte write request, so failure/short-write behavior retains its boundary.
The largest such copy is the header. Near-data usage falls by224 bytes after
alignment, without shrinking the existing capture buffers or terminal stack.

`src/recording/foreground.c` owns a326-byte publisher,64-byte filename field and
two-byte serialized cookie. Its far-cdecl APIs initialize, inspect, begin, feed
one transmitted/received byte, stop, cancel, clean up and shut down. Inspection
borrows read-only near state. The initialized cookie guards explicit clearing
of potentially dirty BSS; an unexpected cookie rejects initialization. Repeated
initialization preserves active and unresolved ownership. The default filename
is `PCPLUS.ASP` and resides in code storage before initialization copies it.

Shutdown cancels an active unpublished recording, leaving an original target
unchanged. It preserves a complete unpublished stage, original recovery backup
or uncertain close instead of deleting or retrying them. It reports unresolved
ownership as RF_RECOVERY. Resolved write/publication/cleanup errors remain
observable; denied opens and successful cancellation do not turn an otherwise
normal exit into a failure. The assembly host retains an existing exit error or
sets exit12 when recorder shutdown reports an error. Recovery notices remain UI
work, along with explicit save/cancel/recovery choices.

| Evidence | Accepted scope |
| --- | --- |
|17 recorder and31 publisher host cases |Exact generated source, short writes, counter boundaries and declared filesystem/close/cleanup fault models. |
|18 ordinary DOS cases |Actual files, maintained DOS compiler and UART replay, including all256 bytes,2048-byte output, long sliding prompts, replacement and recovery races. |
|18 banked DOS cases |The same cases with publisher/core in a genuinely different CS from resident DOS callbacks. |
|18 stable-owner DOS cases |One-byte owner feeds, deliberately dirty owner/filename initialization, unexpected-cookie refusal, busy initialization, shutdown cancellation and repeated shutdown preservation. |
| Six current linked owner cases |Actual terminal far APIs, exact ASP bytes, DS=SS, stable ownership, independent/colliding capture, write-error cleanup and modeled ambiguous close without retry. |
|11 current actual DOS capture cases |Existing terminal startup/shutdown, capture/UI/UART and file behavior after owner integration. |
|24 capture /27 history /78 ZMODEM linked inputs |Existing behavior against the new terminal; kernel and hardware boundaries are modeled. |
|546 ABI corruption checks |Adds owner/cookie placement, both assembly lifetime calls, nine far owner entries and all nine code templates to earlier bridge/callback/relocation checks. |
| Three linked far-code cases |Controller entries, resident services and UART ISR/IRET return continue to pass. |

The ordinary, banked and owner campaigns match in all18 case pairs: status
words, source, bytecode, recovery files and observed UART bytes. The host core
also reproduces all17 previously accepted case records exactly,
including source hashes, write/close counts, errors and byte counters. The
banked diagnostic now includes the production memmove service, and its sliding
prompt case exercises that path. An initial mouse build exposed a duplicate
`terminal.obj` name; naming the new module `foreground.c` avoids overwriting the
existing mouse module. The failed build log is retained under ignored storage.

The current keyboard terminal is
`477849f5ad0f655c89336424d8ec07565a1404e267a18c5d25da2290743896f4`.
It leaves112 near-data bytes and478 resident-code bytes free. The mouse build,
`e7fc8af020d8ac162e71e44a967d1a8558d7e03f5a6ce5d7c9dc79a76482917c`,
leaves64 near-data bytes and330 resident-code bytes. Both pass the static bank,
state, template and relocation audit. Runtime mouse acceptance remains separate.

Next add Record start/save/cancel/recovery controls using these existing bounded
fields and code-resident UI text. Feed intended received prompts and successfully
emitted user/binding bytes, excluding reports, protocols, scripts and children.
Enforce transfer, setup, port-change, child, error and exit ownership throughout.
Then run actual foreground recording, DOS compilation/replay and affected modern
BBS workflows using the resulting exact binaries. Physical modem compatibility,
current-binary BBS/audio and full application acceptance remain open.
