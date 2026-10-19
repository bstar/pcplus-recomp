# Full native status drawing across code segments

The source-built `build/status-renderer/STATUS.EXE` now composes the recovered
515-byte2FB8 status body, its19-byte row-fill service, the175-byte
[helpers](STATUS_HELPERS.md), the maintained bounded formatter and actual native
text/window video routines. This is the renderer needed for native SET refresh;
the interactive terminal's guarded status operation and state staging remain
the next integration work. Production SET still supports only WHENCASE.

```sh
./tools/build test-status-renderer
```

The status body and helpers run in CONFIG_CODE. Their near calls enter explicit
adapters for the resident text, packed-cell, string and length services. Each
adapter retains the far return and CONFIG near return, copies only its declared
argument words and respects the native RET4/RET6 or cdecl cleanup. Data and stack
share DS=SS. The near formatter adapter calls the actual far C formatter with
the current stack-word vector and an explicit count.

Normal75E8 formatting receives capacity136 and twelve caller words. The
alternate2FB8 path receives capacity92 and eight words, matching its smaller
stack buffer. Format, capacity and argument failures become typed3/7/10 results.
The native body can still paint emphasis attributes after formatting fails;
the tests preserve that mutation and require the failure result rather than
claiming atomic drawing or a successful redraw.

Nine actual8086DOS cases compare all4,004 bytes of the video aperture:

- Normal FDX and HDX rows, including14 script-label emphasis attributes and the
  native81st cell just beyond the visible80×25 screen.
- Empty and eight distinct alternate key labels, checking field order and the
  80-character limit.
- Hidden status, leaving every sampled byte untouched.
- The native centered message branch and actual row fill.
- Unsupported zero-padding, capacity overflow and exhausted argument vectors,
  with typed failures and the native post-format emphasis writes.

The DOS host independently checks SP, BP/SI/DI, DS=SS, IF/DF and both ends of
the8KiB stack after every renderer call. No text renderer, UI service or
formatter function is skipped. Carrier is a declared diagnostic word, and video
selects the non-CGA path. The separate helper proof covers CGA instructions with
scripted port values, not physical timing.

Resources are compact maintained constants and owned synthetic state. The
diagnostic does not copy the original initialized data segment. Its key labels
have eleven owned bytes each, sufficient for ten displayed characters and NUL;
this is a maintained storage layout, not a claim to recover the original data
allocation. Flat native status bytes remain unchanged; only relocatable code
can select CONFIG_CODE through `STATUS_CONFIG_CODE`.

The [validation record](validation/status-renderer.json) binds current source,
the actual DOS proof and fresh source-only rebuilding. Remaining work includes
parent-owned serial/UI state, bounded script-label staging, the guarded status
RPC, persistent setting lifetimes, nonzero pacing calibration and physical
modem/CGA validation. No whole-application gate is closed by this component.
