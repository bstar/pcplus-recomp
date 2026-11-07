# Alt-P capacity diagnosis

The experimental `a057b35c…` parent has a confirmed conventional-memory
regression. The unchanged `856a9c85…` parent passes the same held-stream,
nested-child and EMULATE workload with interpreter `5c641ac4…`.

An optional passive DOS observer now also records AH=4A resize requests, actual
returned AX/BX/carry and the pre-request block's MCB owner/size. It makes no DOS
requests inside the hook and writes no application or MCB bytes. The original
observer, with resize tracing disabled, remains byte-identical. The record
format is version 3 only when the new option is selected; old formats remain
readable. Observation is limited to the first 16 admitted child memory calls.

In the separate 386/UMB diagnostic, the exact candidate requests 8,259 paragraphs.
DOS returns carry set, AX=8 (insufficient memory), and BX=8,228 as its maximum.
The request is 31 paragraphs, or **496 bytes**, above that maximum. The sampled
MCB belongs to the requested ES block. Its size is initially 8,227 paragraphs,
then 8,228 following the failed growth; the observer records that change without
causing it. Four child exits are 7, 0, 0, 7; DS=SS and sampled cleanup/process
owners are clear. Profile switching precedes the held-file failure.

The unchanged control with the same observer passes 30 checks. Its sampled
resize requests succeed through 8,675 paragraphs, **7,152 bytes** beyond the
candidate's reported maximum. The 16-record trace fills: that extent is a lower
bound on observed demand, not the full peak or a sufficient funding target.
Saving only the 496-byte first-request deficit would not restore the workload.

The observer is loaded in UMB; both application binaries are unchanged. A prior
conventional-memory observer prevented child entry and produced no admitted
allocation/exit records. That run is interference evidence, not evidence for the
file-open failure. Neither observed environment replaces the ordinary, unobserved
8086 acceptance gate. The cause established here is a failed DOS block resize;
mapping every call to its precise CRT allocation owner remains separate work.

[The capacity receipt](validation/line-port-capacity.json) binds the exact
binaries, observer bytes, source hashes and captures. The next application
change must remove sufficient residency without reducing streams, buffers or
stacks, then pass the complete ordinary workload. See
[the live integration and residency constraints](LINE_PORT_LIVE.md).

```sh
./tools/dev --command python standalone/test_aspect_heap_startup_dos.py \
  --terminal build/line-port-terminal-20261107-reviewed/TERMINAL.EXE \
  --runner build/line-port-aspect-20261107/ASPECT.EXE \
  --output build/NEW-resize-trace --nested-program --streams-around-child \
  --held-streams --emulate-profile-switch --exit-watch --heap-resize-watch \
  --exit-watch-high --cpu 386
```

This candidate command is expected to return failure after writing its report.
No installed package, release selector, physical card or network service changes.
