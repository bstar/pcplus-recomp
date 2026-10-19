# Native status helpers and bounded formatter

This component recovers four PCPlus 2.01 status helpers and supplies a maintained formatter for their bounded format subset. It does not implement the complete status owner, parent RPC, full C runtime, or all SET services.

Run through the pinned Nix toolchain:

```
./tools/dev --command python3 standalone/build_status_helpers.py
./tools/dev --command python3 standalone/check_status_helpers.py
```

The normal build reads maintained source and authored fixtures. It produces four flat units, OMF helpers, a CONFIG formatter, and `build/status-helpers/STATUS.EXE`. The checker uses six controlled CPU cases and actual 8086 DOS execution: 25 format cases and nine compositions of source-built helpers, formatter and existing native text/UI routines. Reports bind source dependencies, generated diagnostic, objects and executable hashes.

The optional `check_status_helpers.py --original [path]` compares the 175 flat bytes against a private original, writes a separate `checks-native.json`, and preserves the ordinary report. It does not make originals a normal build dependency.

| Native entry | Bytes | Recovered behavior |
| --- | ---: | --- |
| `75E8` | 72 | Formats into a 136-byte stack buffer, then calls native string drawing |
| `7630` | 43 | Writes character bytes at alternating video addresses; optional CGA synchronization |
| `3226` | 42 | Clears the status row, measures and centers a message, then draws it |
| `7E0E` | 18 | Waits for CGA status transitions around one character store |

OMF defaults to `_TEXT`, class `CODE`. `-DSTATUS_HELPERS_CONFIG` selects `CONFIG_CODE`, class `FARCODE`; `STATUS_HELPERS_SEGMENT` and `STATUS_HELPERS_CLASS` can also be set explicitly. NASM `-Dsymbol=replacement` can rename imports or exports. Near calls require the selected owner and its near adapters to share a code segment. Data and stack must share DS=SS: stack buffers become near string pointers.

`status_format` is a far cdecl function in `CONFIG_CODE`, class `FARCODE`. Its explicit arguments are destination, capacity, format, near word vector and word count. It uses no global data or callable CRT helpers. Capacity is 1–136 bytes; pointers must refer to validated owned near spans in the current DS. Supported conversions are `%[-][width][.precision]s`, `%[-][width]c`, `%[-][width]d`, and `%%`, with width and precision at most 135. Zero-padding flags such as `%03d` and `%01s` are explicitly rejected. Decimal conversion interprets words as signed 16-bit values, including −32768. The result is the produced byte count; errors are −1 for capacity/overflow/null string, −2 for unsupported format, and −3 for insufficient arguments. On a valid-capacity failure it clears the first destination byte. This boundary intentionally rejects formats outside that subset.

Authored tests include high CP437 bytes, embedded NUL characters, empty strings, truncation, padding, signed boundaries, exact capacity, malformed and truncated formats, rejected zero-padding flags, and missing arguments. The DOS diagnostic calls the far formatter through an explicit near adapter, then executes recovered `75E8` and actual `6BF0` video drawing. It also composes `3226` with actual string length and status-fill routines. These tests do not substitute a simulated screen renderer.

The native normal status format produces **81 characters for an 80-column row**. Its final blank and attribute land in the next video cell beyond the visible 4000-byte 80×25 screen. The source composition checks that observed write. The alternate key-label format at **DS:46D2 is a direct string**, eight `%-10.10s` fields; it produces 80 characters. It is not a pointer word. Earlier private notes that dereferenced its initial bytes were corrected before this promotion. DISPLAY does not gate native `2FB8` status refresh; a future live service must preserve that distinction.

Controlled original comparisons established 14 safe formatter vectors and four normal plus one alternate status case. The maintained formatter matched the same authored values in actual DOS. These bounded observations do not establish all native status branches, full CRT equivalence, physical CGA timing, hardware carrier status, persistent SET adoption, or the eventual parent service lifecycle. The CPU proof supplies explicit input-port values for CGA instructions. The DOS diagnostic selects non-CGA video and aborts if an unexpected CGA word service is reached. Native `7630` with count zero on its non-CGA path retains its original wraparound loop; the checker deliberately avoids that unsafe call rather than silently changing it.

Provenance: original SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`; resident file mapping `0x1200 + entry`. Retained REA assembly Evidence IDs:

- `75E8`: `ev_66145bc4e929b3601579df8553ba01115e84583cc89791856f6373412b96a1e0`
- `7630`: `ev_886d51619d021c33169246f2179d4bdf65a8176e78d66f21f794e02415f42c56`
- `3226`: `ev_b8511543eb4d45f00409105d501ea81104b0d7454793bedbaaef7b5165e52c09`
- `7E0E`: `ev_baeddcf32df16d0ecba90dac291a1bc1d917cc8e9737a0253064450480a30b92`

The public [validation record](validation/status-helpers.json) records this component's bounded checks. It does not certify full application integration.
