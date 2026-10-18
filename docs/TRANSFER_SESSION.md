# Native transfer session owner

The reconstruction now composes one ordinary native XMODEM receiver invocation across handshake, multiple blocks, retries, cancellation and EOT into a source-only DOS diagnostic. It retains the original stack frame and receiver state for the entire session. The default diagnostic uses a replaceable scheduled UART/time/UI adapter and a bounded memory-file sink. It is not a live UART transfer or a DOS file installer.

## Native evidence and control flow

The original PCPlus2.01 EXE identity is SHA256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`. `reconstruction/transfer_session/provenance.json` records1027 exact recovered instruction bytes, their file ranges, flat hashes and saved REA evidence. Ordinary builds need only reviewed ASM/provenance; original access is restricted to explicit analyst regeneration or optional replay.

| Native range, end exclusive | Contract |
| --- | --- |
| overlay21 `d656..d6a4` | Clear counters/file token, select streaming for protocol10/11, set buffer pointer and baud-derived32-bit rate |
| `efb0..efcb` | Clear session/received/expected byte totals and related state |
| `d6a4..d731`, `d731..d73c`, `d73c..d752` | Actual near-C receive entry, stack frame, optional filename/prefix and binary open; explicit failure epilogue |
| `d752..d87c` | Initial C/W/U/G handshake, CRC/checksum selection, fallback and readiness |
| `d87c..d8ae`, `d8ae..d8e8` | Establish nonlocal context, classify its return, error write/close and flow gate |
| `dc1f..dc6a` | Retry limit, keyboard cancellation, carrier loss and streaming control read |
| `f070..f0d3`, `f0d4..f0df` | Polling wait, cancel/carrier checks and first-arrival timestamp |
| resident `9048..9065`, `9065..9086` | Actual near setjmp and longjmp |
| `da31..da3a`, `da9e..daa7`, `dcfd..dd4a` | Ordinary validated-block gate, success epilogue and EOT file-commit selection |

Saved overlay REA exports supply the session/handshake instructions. The focused resident9048 gap was confirmed using an entry-anchored **analysis-only** derivative, changing only MZ IP/CS header words to9048/0 and preserving all code bytes. It was never executed. REA Evidence `ev_5e9883fbf1946afde585338918ee467ff5dc65e55e792ba44922b0db819f2d4e` is retained in [the public evidence record](evidence/transfer-session/setjmp.json); derivative identity is `5f36c090550bcd37bb6b30a9c1d74b4c8936293e52ae1738e789713cd8fc7711`. The owned REA session was closed.

`9048/9065` are **setjmp/longjmp, not an event queue**. The ten-byte context stores BP, DI, SI, SP and return IP at offsets0/2/4/6/8. A first setjmp return is0. Longjmp value0 becomes1. Longjmp restores the saved stack and registers and returns directly to the saved code location; it does not return normally to its caller. DS=SS and the same live code segment/frame are required. Receiver `cd94` names this context. Double CAN invokes longjmp with7; the context owner immediately maps return7 to status11 and proceeds through error cleanup. Return1 maps status10; return15 maps status15; other nonzero values map status11.

Handshake observations are actual instruction execution: ordinary protocol4 emits `C`, protocol9 `W`, protocol12 `U`, streaming10/11 `G`. First-attempt arrival selects DI=1 for CRC. Ordinary input silence emits three `C` bytes followed by **eleven** NAKs and continues with DI=0 for checksum; the historical postdecrement loop does not represent a clean handshake failure. Poll iterations are36 when wait-mode0,200 otherwise, or91 when the short-wait flag is nonzero. These are original callback units, not asserted wall-clock milliseconds. The retry limit compares exactly15, not greater-or-equal15; a maintained owner needs an independent upper bound.

The surrounding `d0d0` application entry also prompts/validates filenames, saves/restores UI/string state, switches application owner services, selects receive/send and refreshes the screen. Its complete UI lifecycle remains outside this module. The new composite is a transfer-component owner, not a reconstruction of every application transfer menu.

## Linkable entry and shared state

`session_receive(const char *filename)` is the actual near-C entry. It establishes BP, reserves58h bytes and saves DI/SI. Arguments remain caller-owned. The native initializer clears the file token, counters and buffer pointer. A NULL filename skips fopen **after clearing that token**; it cannot preserve a preopened stream. Native string concatenation is unbounded; a maintained adapter must validate filename/prefix lengths before entry. The default fixture uses only synthetic `TEST.BIN`, empty prefix and source-owned `wb`.

Native fragments continue by **jumps within the same frame**, not by repeatedly invoking a per-frame probe. DI carries the CRC/checksum selection, and BP locals hold retries at-14h, block-zero metadata at-0eh, current/previous control at-10h/-2 and pending error at-4. `standalone/build_transfer_session_composite.py` emits named source-owned DS aliases and branch bridges that compose session, [receive validation](TRANSFER_RECEIVE.md), [CRC](TRANSFER_BLOCKS.md) and the recovered FILE periodic/tail controllers. Its generated `composite_state.inc` is the exact integration alias inventory; it does not embed an original memory image.

| Original DS | Shared source ownership |
| --- | --- |
| `3996` | Protocol selector |
| `39c0` | Owned receive buffer pointer; composite arena11264bytes (10240-byte flush threshold plus a maximum block) |
| `cd34`, `cc9a`, `cc9c`, `cd32` | Buffer used, accepted number, wire number/complement |
| `cd80`, `cd8a` | Accepted count and error count |
| `8ffa/8ffc`, `cb2c/cb2e` | Received/session32-bit byte totals |
| `9006/9008` | Optional declared32-bit length; ordinary fixture leaves0 |
| `cbaa` | Opaque FILE token, **not** a DOS handle |
| `cd94` | Ten-byte active nonlocal context |
| `cdcc` | Streaming gate, initialized for protocol10/11 |
| `ce06/ce08`, `905a/905c` | Start timestamp and baud-derived32-bit rate |
| `1d1e` | Original receive flow-control switch |

No live stack/context pointer should escape beyond the owner lifetime. The bounded11264-byte arena is isolated here; adding it to the current terminal's nearly full DGROUP would require a separate memory design.

## Replaceable IO contract

The composite builder accepts `--adapter /absolute/adapter.asm`. All default synthetic behavior is confined to `standalone/transfer_session_composite_io.asm`; recovered sources and generated shared-state/branch adapters remain the same. A production adapter may call maintained C file services through an explicit near ABI. The default adapter's memory sink is not claimed as recovered file IO.

| Adapter export | Near ABI |
| --- | --- |
| `composite_timed_byte(timeout)` | Word byte0..255 orffff; callee removes2 bytes |
| `composite_header_byte()` | Same result; plain ret |
| `composite_transmit_byte(byte)` | Word argument; callee removes2 |
| `composite_flush_input()` | Discard currently queued input only |
| `composite_delay_ticks(value)` | Original timing boundary; callee removes2 |
| `composite_local_cancel()`, `composite_carrier_present()` | Word boolean; plain ret |
| `composite_clock()` | DX:AX timestamp |
| `composite_status(code)`, `composite_progress()` | Status is caller-cleaned cdecl; progress has no arguments |
| `composite_file_open(path,mode)` | Caller-cleaned cdecl, opaque nonzero FILE token or0 |
| `composite_file_write(buffer,size,count,token)` | Caller-cleaned cdecl; return complete element count |
| `composite_file_close(token)` | Caller-cleaned cdecl; seal/close only,0 orffff |
| `composite_setflow(value)`, `composite_timestamp(path)` | Caller-cleaned cdecl; flow and timestamp services |
| `composite_path_test(path)`, `composite_display_path(path)` | Original path/display boundaries, caller-cleaned |
| `composite_ui_print(text,attribute,position)` | Callee removes6 bytes |

The adapter also provides fixture entry/reset/assert symbols for this standalone DOS program; a live owner replaces that diagnostic host rather than exporting test UI to users. UART/time boundaries must service local cancellation and maintain real deadlines. Protocol9/12 specialist controllers, batch metadata and nonzero-size long division remain explicit INT3 boundaries in the default adapter.

The receive arena reserves11264bytes because native flushing occurs **after** a full block is stored. A1024-byte block can begin after79 blocks of128 (used10112) and require11136bytes before the flush. The original10240-byte fixture arena failed this legal mixed-size test and corrupted following state; its first failed result is retained under ignored `mixed-arena-first-failure.json`. The corrected bound and both CRC/checksum regressions pass.

The memory adapter releases scheduled future frames only on declared transmit triggers. It models immediate queued bytes within a frame, while the next frame becomes available after ACK/NAK. Thus native input flushing is exercised without accidentally treating every future block as already queued. This is an explicit deterministic UART model; no physical modem packet timing is asserted.

## File completion safety

Native periodic fwrite is `(buffer,used,1,FILE)`: AX>=1 is complete-element success, not acceptance of a short byte count. Its error path closes and returns failure. Native final EOT paths ignore fwrite/fclose return values and can return1 after failure. Exhausting the15-timeout path can return0 **without closing the stream**. Neither an ACK nor owner return1 alone authorizes installation.

A maintained storage owner must keep the first write/close error independently, seal rather than install from the native fclose callback, and install only after native owner success **and** clean storage state. On every owner failure it must abort/close/delete its owned stage, retaining recovery evidence on uncertain close. This contract matches the separate maintained download backend; the composite checker deliberately proves why both conditions are necessary. The default memory fixture does not install files and does not claim crash atomicity.

## Validation

```sh
./tools/dev --command python3 standalone/build_transfer_session.py
./tools/dev --command python3 standalone/check_transfer_session.py
./tools/dev --command python3 standalone/test_transfer_session_dos.py
# Optional genuine original instructions, explicit ignored input:
./tools/dev --command python3 standalone/check_transfer_session.py --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
./tools/dev --command python3 standalone/build_transfer_session_composite.py
./tools/dev --command python3 standalone/check_transfer_session_composite.py
./tools/dev --command python3 standalone/test_transfer_session_composite_dos.py
```

The unit diagnostic passes53 source-only CPU cases and30 additional genuine-original comparisons:83 total. Tests include native near nonlocal stack/register restoration for values0/1/7/15/8000h/ffffh, all protocol initialization gates, handshake/fallback, cancel/carrier/timeouts, retry boundary and actual open/prefix preamble. DOS8086 also passes initialization, C handshake, setjmp restoration and genuine double-CAN cancellation.

The composite passes24 CPU cases: CRC/checksum,128/1024/mixed payloads,96 blocks of128,12 blocks of1024 and79 blocks of128 followed by1024 crossing periodic flush, duplicates, CRC/sequence retransmit, double CAN, local cancel, carrier loss, timeout exhaustion, periodic/final write failure and final close failure. BP/SI/DI/caller ES and the near stack are checked. DOS8086 completes one actual native checksum session through EOT write/close into the bounded memory sink. Results and binary hashes are in ignored `build/transfer-session*/`.

This closes source composition for the demonstrated ordinary unknown-length receiver path. Live UART deadlines, physical-modem transfer, real DOS storage adapter execution in this composition, batch protocols, streaming/window behavior, application menus and complete original PCPlus reconstruction remain open.
