# Calibrated ASPECT TXPACE service

This source-only component supplies bounded calibration and cooperative pacing around the exact native 38-byte `6B72` delay. Runtime, UART and SET integration belong to the calling application; the component alone does not make those services available.

Build and check with pinned Nix:

```
./tools/dev --command python3 standalone/build_aspect_txpace.py
./tools/dev --command python3 standalone/check_aspect_txpace.py
```

`build/aspect-txpace/manifest.json` binds maintained sources, flat native bytes, OMF objects, generated diagnostic and `TXPACE.EXE`. The checker requires no original executable. It exercises six native CPU cases, 15 compiled service-model cases, three delay-error assertions and two actual 8086 DOS runs. Host clock and busy-loop callbacks are explicit models; actual DOS uses virtual BIOS memory and real virtual PIC state. The component does not substitute a host sleep or fixed loop count for calibration.

## API and caller ownership

`txpace.h` defines `reset()`, `ready()`, `prepare(step)`, `prepare_bounded(step, chunk_limit)` and `delay(units, step)`, prefixed `aspect_txpace_`. DS=SS and near cdecl conventions apply. Preparation requires IF=1; every return restores the entry IF. The clock snapshot briefly saves flags, disables interrupts for the two BIOS word reads, then restores flags. The service never changes PIC masks, interrupt vectors, UART registers or modem controls.

The callback receives ALIGN=1, BEFORE_MEASURE=2, AFTER_MEASURE=3 or DELAY=4. It returns zero on success. Nonzero produces STEP=6 and preserves the supplied result in `aspect_txpace_step_error`; the application maps that result to its own serial/cancellation error. Callback IF corruption produces IF=3, with the caller's entry IF restored. Other errors are ARGUMENT=1, STATE=2, CLOCK=4, LIMIT=5 and RESOLUTION=7.

The caller must provide a bounded, nonblocking **low-level transport/flow/cancellation** callback. It must not dequeue receive bytes, run WHEN handlers, invoke the terminal parser, or recursively call this service. Before measurement, a live UART owner must reject more than 2048 queued bytes and check existing errors/cancellation. Each ALIGN callback must recheck that headroom because the queue can grow after initial admission. After measurement it must poll and check overflow/errors/cancellation again before accepting calibration. At the repository's maximum 115200 baud, standard framing of at least seven bits per character admits fewer than approximately 1810 new bytes in two ordinary BIOS periods; the 4096-byte ring with at least 2048 free bytes provides the intended admission margin. This assumes a functioning standard DOS clock and bounded callback execution, rather than guaranteeing safety under every BIOS, baud rate or hardware failure.

ALIGN polls continue after admission until a fresh BIOS edge. They have an independent limit of 65535 callback polls. Measurement then runs without foreground callbacks for one BIOS period, with interrupts enabled so the UART IRQ continues to collect bytes. The measurement loop is bounded even if the BIOS clock stalls. That instruction bound is not a fixed wall-clock deadline: on a slow CPU, a stalled clock can still take seconds to reject. A caller that requires a tighter independent wall-clock guarantee needs an additional hardware watchdog; none is implied here. No new ASIO descriptor capability is required.

After successful measurement and the post-measure callback, `ready()` becomes true and `aspect_txpace_count` holds the calibrated count. A failed preparation clears readiness and count, except an invalid call made against an already prepared service need not discard that existing calibration. Call `reset()` when CPU/emulator speed changes or when beginning a new lifetime whose timing basis is uncertain.

`delay(0, step)` succeeds immediately, even without preparation or IF=1, matching native zero pacing. Values 1–999 require readiness, a nonzero count, IF=1 and a callback. The service polls before each actual native one-unit delay and after the final unit. Callback overhead and these cancellation opportunities are intentional changes from a single native busy wait.

## Measurement and native differences

Original startup `7956` masks every master PIC IRQ except the timer, counts instructions for one BIOS tick and divides by 55. That is unsuitable during a live UART handoff. Its native `6B72` consumer performs calibrated decrement loops without polling cancellation or flow. This component retains that consumer exactly but deliberately replaces startup calibration.

Maintained calibration measures repeated one-unit calls to native `6B72` with a temporary count of **512**. It observes BIOS time and checks its limit between chunks, using the same busy-loop body that later supplies pacing. At most 7039 chunks are admitted: `floor(55 * 65535 / 512)`. This bounds the accumulated count and avoids a divide overflow. Fewer than four completed chunks are rejected as insufficient resolution. The final count is `floor(chunks * 512 / 55)`; it must be nonzero and fit a word. Publication waits for the post-measure callback. No native zero-count delay is admitted by the service, although the raw native instruction unit retains its original 65536-iteration wraparound behavior.

The measured interval must advance exactly one standard BIOS-day tick; a larger jump or invalid day counter fails explicitly. Midnight is handled using the standard 1573040-tick BIOS day. Measurement quantization can include up to one chunk beyond the tick edge, while loop calls and BIOS reads contribute overhead absent from the later busy loop. Consequently the result is an approximation with explicit limits, not an electrical millisecond guarantee.

Actual DOS observations with stable emulator speed:

| Fixed cycles | Calibrated count | 0 units | 55 units | 999 units |
| ---: | ---: | ---: | ---: | ---: |
| 6000 | 1461 | 0 ticks | 0 ticks | 18 ticks |
| 30000 | 7335 | 0 ticks | 0 ticks | 18 ticks |

The 55-unit interval begins near a tick edge and is slightly shorter than a full period, so its integer BIOS-tick difference can be zero. These results do not imply zero elapsed time. Original masked calibration in the private controlled DOS comparison yielded counts 1490/7482 and 999 units took 18 ticks. A 128-iteration maintained batch yielded 1375/6902 and 17 ticks for 999 units at the same speeds; 512 reduces that observed bias to about two percent in the count. This selects a measured algorithm rather than adding a hidden correction factor.

An earlier component run reused the smaller measurement budget for alignment and failed before producing a result at the faster CPU setting. Its artifacts were retained separately. The corrected component permits independent alignment work: actual DOS required 5152 and 26076 alignment callbacks at the two speeds. A source model explicitly holds the alignment clock for 8000 polls while admitting only ten measurement chunks, guarding against that regression.

The tests also cover stalled alignment/measurement, IF=0 admission, callback errors and IF corruption, invalid clocks, a two-tick jump, midnight, coarse resolution, the maximum allowed count, cancellation before a delay, and native count-zero/floor-wrap behavior. PIC masks are checked before and after calibration in actual DOS; IF is also checked on failure paths. Physical UART traffic during calibration, parent integration, changing CPU speed, abnormal BIOS time and external modem timing remain separate validation requirements.

## Native provenance and transmit semantics

The retained native delay Evidence ID is `ev_a30bfa2cee5690318dc8252472fd4570367e365219605a4b4a1e2253170377fc`. Its original SHA-256 is `a7149212d6d9857e43f3e86112c258c9e11c2aeae0d292ef964a908b43beb850`, resident file mapping `0x1200 + 0x6B72`, from original SHA `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`. The startup investigation and physical limitations are documented in [BREAK_NATIVE.md](BREAK_NATIVE.md).

Native `48CC` sends an ordinary byte, then applies TXPACE, including after its last ordinary byte. Decoded `FF` representing `^@` sends a wire NUL and bypasses local echo and TXPACE. A pause-character match takes the native BIOS pause path instead. A caller must retain these native control-flow distinctions rather than pacing every emitted byte indiscriminately.


The production [SET runtime](ASPECT_SET_RUNTIME.md) now supplies that callback
and invokes this service. Its six linked admission cases include rejection when
queue growth during alignment consumes the free-space margin, and its actual
UART/parent tests are separate from this component's timing evidence.


For object reproducibility, the component builder uses Watcom `-zld` to omit
file-dependency timestamps and canonicalizes only the OMF THEADR source-name
metadata to `src/aspect/txpace.c`. Checksums are validated before and after;
every subsequent record (code, symbols, fixups and other data) must stay exactly
unchanged by normalization. The initial fresh-checkout comparison reproduced
all executable outputs but exposed that C object's absolute path/timestamps;
its failed proof is retained at
`build/application-source-proof-history/set-repro-01/`. The source proof still
requires byte identity for the normalized C object and all124 checked outputs.
