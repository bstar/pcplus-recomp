# Receive-buffer pressure

[Linked driver checks](validation/uart-receive-pressure-linked.json) pass13 cases
per normal/mouse product on parent3b453f2b/c3a1acb1. Twenty pressure streams each
receive65,536 exact bytes through the actual linked RX interrupt, ring reader,
flow scheduler and RTS instructions:1,310,720 exact bytes in total. Hardware
registers, scheduling and the reactive sender are modeled.

HARD uses all256 byte values. SOFT/BOTH exclude XON/XOFF from payload because
the real UART consumes them as controls. BOTH preserves the recovered software
receive-flow precedence; it does not independently lower RTS while software
receive flow is active. CTS is held low in HARD/BOTH; software flow-control
bytes still use the existing control-byte path. This does not measure physical
CTS timing or application transmission during a stall.

Selected cases add512 bytes already in flight after a pause or defer THRE for
three peer/reader steps on the first software pause. Observed peak queue lengths
are3,104 through3,648, below the4,096-byte capacity. Pause/resume pairs repeat
across multiple ring wraps; exact received data, final pointers and cleared flow
metadata are checked. Six deliberately uncooperative peers offer5,000 bytes:
the driver preserves the first4,096 and counts904 drops without overwriting
unread data. This negative-peer result is not successful lossless reception.

The first normal cohort failed a checker assumption that RTS-low was written
once per pause. Native receive code writes the same low MCR value for multiple
bytes above high water. The corrected checker validates every transition and
retains the exact-stream, occupancy, flow and overflow assertions. That failed
cohort remains separate.

~~~sh
./tools/dev --command python3 standalone/check_uart_receive_pressure.py \
  --product build/terminal --output build/uart-receive-pressure/normal-new
./tools/dev --command python3 standalone/check_uart_receive_pressure.py \
  --product build/terminal-mouse --output build/uart-receive-pressure/mouse-new
~~~

## Actual DOS foreground path

The separate `standalone/test_uart_sustained_dos.py` sends65,536 bytes through
raw monitor into its DOS file owner, then requires normal ANSI/keyboard/query
resume, application exit, UART restoration and observer-chain collection. The
stock transparent nullmodem keeps CTS asserted; its peer does not honor RTS.
Even a successful run therefore cannot prove DOS receive-watermark timing.
The raw-monitor display prefix oracle is replaced by an explicitly named BIOS
observation/chain check: a64KiB stream scrolls many screens. Exact binary logging
and the ordinary ANSI display on return retain their separate assertions.

[Two independently audited DOS sessions](validation/uart-sustained-dos.json)
now pass on the unchanged parent, in8086 and386 CPU modes. Each logs65,536 exact
all-byte values, returns to normal ANSI/query/keyboard handling, exits normally,
and restores42 UART/PIC/vector bytes plus the observer's INT16/INT2F chains.
The file and peer captures are independently checked; the raw-monitor screen
is not treated as a complete65536-byte display oracle. The separate original
all256 display-prefix regression retains its own purpose.

These sessions keep CTS asserted and do not honor RTS. They establish selected
foreground/file continuity, not actual DOS high-water timing or physical serial
throughput. Sustained normal ANSI reception, other foreground owners, audio
pressure and physical UART/modem behavior remain open.

## Collector failure and correction

Initial8086 attempts captured the exact dump and normal application return, but
hung in the post-exit observer collector. The first harness also raised on the
missing observer file before saving its transcript; subsequent attempts preserve
the complete failed transcript and result. Shorter keyboard delays, CLD and a
direct vector lookup did not resolve the collector failure.

The cause is the helper's missing NASM CPU constraint. BITS16 selects16-bit
operands but does not prohibit386 instructions. The default collector emitted
`0F85` near JNZ for its long conditional branches. Explicit `CPU 8086` instead
emits inverse short JZ plus a near JMP (`74 03 E9`), preserving the condition on
an8086 instruction set. The shared monitor observer and collector now declare
CPU8086. The sustained-test collector also clears DF and records entry flags;
its successful runs enter with DF clear, so DF was not this failure's cause.

`standalone/check_monitor_collector_cpu.py` reproduces both assembler variants
without loading any PCPlus code. Identical binaries within each variant run in
both emulator CPU modes: legacy386 succeeds, legacy8086 times out, and the fixed
helpers restore vectors and write their report in both modes. The independent
receipt verifies the actual branch bytes and source/capture identities. This is
a test-helper correction, not an application binary change or an emulator bug.
All failed predecessor cohorts remain unaccepted.

The first386 bulk comparison additionally failed because the harness's existing
file allowlist did not include its three newly preserved transcripts. The list
now names those exact generated files; fresh386/8086 runs pass every retained
file, stream, exit, observer and restoration assertion.

~~~sh
./tools/dev --command python3 standalone/test_uart_sustained_dos.py \
  --cpu 8086 --output build/uart-receive-pressure/dos-8086-new
./tools/dev --command python3 standalone/test_uart_sustained_dos.py \
  --cpu 386 --output build/uart-receive-pressure/dos-386-new
./tools/dev --command python3 standalone/check_monitor_collector_cpu.py \
  --output build/uart-receive-pressure/collector-new
~~~

Actual DOS receive-watermark timing, broader foreground/ANSI and physical tests
remain required. No full F03 or application gate closes.
