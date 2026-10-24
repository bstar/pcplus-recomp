# Native screen-width request adapter

The missing mode service at CS:2A6E is a 34-byte adapter, recovered through REA
from the selected original PCPlus2.01 image. Its rebuilt flat bytes match the
original exactly; the relocatable OMF build uses named data and reset imports.
This is an application reconstruction prerequisite. The interactive terminal's
width boundary remains explicit until the actual geometry/reset path is ready.

The original image SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
REA Evidence `ev_b597875f82bfb0ccc9874ec7a07979258dd2d34cac4d826b047f01d2ba16f854`
comes from Ghidra12.1.2's 16-bit real-mode import. Linear addresses
`12A6E..12A90` correspond to CS offsets `2A6E..2A90`; they are not unique
segment:offset aliases. Complete inline evidence is retained locally in
`analysis/screen-width-20261024.rea.json`; its digest and source/tool identities
are in the [verification receipt](validation/screen-width-request.json).

The adapter preserves BP/SI, saves configured-wide word DS:1D2E, writes its raw
word argument there and calls native reset CS:20A4 with cdecl argument zero.
On ordinary return it restores the saved configuration word and removes its own
argument with `RET 2`. This is a temporary reset request, not a permanent setting
assignment. It neither validates a Boolean range nor defines an AX result.
The reset dependency must preserve SI and BP. Nonlocal abort cleanup is not
provided by this short native adapter.

The source-owned WIDTH.EXE is an explicit reset-boundary observer, not a working
132-column terminal. Sixty linked cases cover raw arguments0/1/2/8000h/FFFFh,
four old settings and three values written by the reset observer. They verify
the transient setting, exactly one reset(0), restored configuration, caller
registers, DS=SS and stack cleanup. All sixty match controlled replay of the
original adapter instructions with the same declared reset-boundary model.
No original reset instructions run in that oracle. A DOS8086 fixture performs
two actual calls and checks both requested values and configuration restoration.
An empty five-source-file tree reproduces the observer executable exactly.

```sh
# Source-only build, linked checks, DOS observer and empty-tree reproduction:
./tools/build test-width-request
# Separate, explicit original input for paired instruction replay:
./tools/build test-width-request-compat
```

Normal builds and checks read no original executable, private configuration,
disk image or REA database. The optional comparison reads only the verified
original adapter bytes. This adds no new application binary or card deployment.

The next integration work retains the full width requirement: connect the real
native reset/geometry, allocator and viewport services; provide consistent
80/132-column screen, cursor, scroll, erase and attribute storage; audit fixed
80-column UI/renderer owners; and own cleanup on errors or abandoned reset.
The current maintained RIS restores a captured profile and cannot substitute
for the original configuration-sensitive reset. Wider DOS/video and live BBS
tests must follow that integration. F04 and the full application remain open.
