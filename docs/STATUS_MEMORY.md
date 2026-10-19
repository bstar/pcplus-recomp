# Near-memory space for native status integration

The interactive terminal's DS=SS group previously used65,488 bytes, leaving48.
The native SET/status work needs additional state and resources, so the
redisplay viewer now keeps its fixed prose in CONFIG_CODE and its row index
beside the far frozen-history snapshot.

Fourteen unchanged strings occupy902 bytes of code storage. The247-word index
occupies494 bytes at offset63000 in REDISPLAY_STORAGE, immediately after the
snapshot and within the64KiB segment. C uses a far pointer for the index and
for fixed text; editable query/path buffers remain near for their DOS callers.
The checked8KiB stack remains the same size.

The resulting DS=SS group uses64,096 bytes and leaves1,440, reclaiming1,392 after
alignment. Link-time memory checks verify the index segment, exact extent,
non-overlap and retention through DOS child EXEC. The validation recorder also
finds each fixed string in the actual CONFIG_CODE bytes.

This is a memory prerequisite for [native SET/status](ASPECT_SET_NATIVE.md),
not completed status rendering. The remaining status owners, bounded state,
resident operation and session-setting lifetime still need integration.

Validation binds the rebuilt terminal to linked full-history navigation/search,
actual DOS browsing/export/clipboard workflows, ASPECT renderer compositions,
scoped Synchronet/ENiGMA checks and a fresh source-only rebuild. ENiGMA retains
the explicit30ms buffering condition; immediate-forwarding compatibility and
physical modem testing remain open. See the [record](validation/status-memory.json).
