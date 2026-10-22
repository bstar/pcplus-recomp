# Startup retention code placement

The pure startup retention calculation now executes in the existing CONFIG_CODE
segment behind the unchanged near terminal_program_initialize entry. This frees
164 bytes in each resident code segment without adding near data.

| Product | Near-code spare before | Near-code spare after | Near-data spare |
| --- | ---: | ---: | ---: |
| Normal | 154 | 318 | 112 |
| Mouse | 6 | 170 | 64 |

The body still computes the maximum retained end across the near stack, far
terminal/history/snapshot data and UI buffers. Its instruction sequence is
unchanged except for the outer RET becoming RETF; its private rounding helper
remains a near call inside CONFIG_CODE. The public wrapper adds the far frame
and returns through the established near ABI. The routine has no external near
calls, DOS/BIOS/port operations or DS/SS changes.

The [independent placement audit](validation/program-startup-bank.json) binds
old/new source bodies, products, maps and measured capacities. Eight linked
normal/mouse cases verify retained size independently from static end symbols,
AX/PSP and register preservation, a stack canary, IF/DF preservation and DS=SS
while interrupts are enabled. The new cases observe exactly the resident and
CONFIG_CODE execution segments. All60 existing linked PROGRAM inputs pass,
and26 application/component products reproduce from a fresh declared-source
tree without originals.

All13 actual DOS attached PROGRAM cases pass in
build/aspect-parent-process/startup-bank-01/result.json. Two actual DOS SOFT/BOTH
offline helper/redial cases pass in build/program-offline-modem-dos/startup-bank-01:
the child observes an offline parent without XOFF, runs with released UART,
changes UART/video state, and the parent restores both and redials cleanly.
These cover real DOS retention/shrink/child/return behavior in addition to the
linked ABI boundary checks.

Current parent identities are a31eb517 (normal), 5aecd64f (mouse) and0b5006ff
(external renderer); full normal/mouse hashes are in the acceptance receipt.
The ASPECT child remains183f852d and compilerfc200c8c. ASIOv6 and capabilities12/13
are unchanged. The preceding accepted recorder audio retains parentdd86139f;
it does not establish a new-parent audio outcome.

This is a limited placement step. Both code banks and near data remain bounded,
and substantial application growth still needs further placement work. Broader
current-parent carrier/flow/BBS/audio validation and every full F01–F16/physical
requirement remain open.
