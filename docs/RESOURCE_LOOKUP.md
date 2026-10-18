# Default resource lookup

Saved translation mode 1 now searches for `PCPLUS.XLT` in the DOS current
directory first. If opening that name reports file/path not found (DOS errors 2
or 3), startup tries one directory from the inherited `PCPLUS` environment value:

```dos
SET PCPLUS=C:\PCPLUS
TERMINAL @C:\PCPLUS\PCPLUS.PRM
```

The PRM argument remains explicit. The default XLT directory is the process's
current directory, not automatically the directory beside that PRM or executable.
This checkpoint integrates fallback for the default XLT table only. PRM, KBD,
KEY and other resources retain their existing explicit-selection rules.

An explicit `/X:FILE.XLT` reads exactly that path and does not inspect `PCPLUS`.
Identity mode 0 and the 7-bit mode 2 also ignore it. A valid current-directory
table wins even when the environment is malformed. Empty, short, suffixed,
unreadable or unsuccessfully closed current tables stop startup; they are not
silently replaced by another copy. A failing fallback table also stops startup.
Successful reads commit only after exactly 256 bytes, EOF and checked close.

## Bounded environment and path policy

The maintained helper reads the environment segment through PSP offset 2Ch.
It checks the MCB signature and nonzero paragraph extent, rejects physical
segment overflow, and scans at most 64 KiB through a complete environment
terminator. It validates the entire environment before using a match, including
entries after it. These are bounded structural checks, not a complete DOS heap
ownership proof. Caller output cannot overlap the PSP or inspected environment.

The first exact uppercase `PCPLUS=` entry wins. Missing or empty values mean no
fallback; an empty first duplicate is not replaced by a later one. The value is
one directory, not a semicolon-separated PATH list. Controls, non-ASCII bytes,
whitespace, quotes, wildcards and redirection/list characters are rejected.
The resulting DOS path is at most 63 bytes plus NUL. A backslash is appended
unless the value already ends in one. As in the original resolver, `PCPLUS=D:`
therefore selects `D:\PCPLUS.XLT`, not the current directory on drive D.

The generic `resource_pcplus_path` helper accepts an ASCII 8.3 resource leaf and
performs no DOS I/O or file probing. It preserves output on every failure.
The default XLT owner applies current-file precedence and the checked reader.
Its unchanged eight-byte result gains status 6, `XLT_DOS_RESOURCE`, for malformed
or oversized environment selection; existing reader status values 0–5 retain
their meanings. Explicit-reader behavior remains unchanged.

This is startup-only selection. RIS retains the already loaded table without
reading files or the environment. Confirmed [live mode changes](LIVE_TRANSLATION_SETUP.md) now bind both candidate
namespaces before the child. Explicit [same-table reload](TRANSLATION_RELOAD.md) now retains the actual
canonical source;63-byte limits include resolved CWD. Automatic lookup for the
remaining resources are still open.

## Original evidence and maintained differences

The retained REA assembly and pseudocode for original resident 353Dh show a
read-mode probe of the requested filename, then `getenv` through DS324Ch, initially
pointing to `PCPLUS`. It copies the directory, conditionally appends backslash,
then appends the supplied filename. The original performs unchecked copies,
can underflow its last-character read for an empty value, and falls back after
any failed open. The maintained implementation uses explicit errors and bounds;
its file/path-not-found restriction deliberately prevents hiding a damaged or
inaccessible selected table.

Selected original SHA-256:
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resolver 353Dh–35A5h is 105 bytes at original file offset 473Dh, SHA-256
`c7ec6dcd6c2a8f0bd8bbe662d0c4e31f1fa7db0b4c2b844848a054bc47fa3319`.
REA evidence: assembly
`ev_1cd43dbde8697560fddafd763fd3ab56971d91bd6badd8b88553d8e1cc1d6417`;
pseudocode `ev_e36893dd21a8e0238063e007dda32a4fd0f457d6c1d4a7e9ad9eb4e7db399009`.
These are reused retained static observations, not a newly observed original
execution. No native analysis session or synthetic analysis executable was run.

## Verification

```sh
./tools/build test-resource-lookup
./tools/build test-terminal
```

[Resource validation](validation/resource-lookup.json) binds 117 linked inputs,
30 generic DOS resolver assertions and 12 actual DOS inherited-environment/startup
cases to source, executable, toolchain and artifact identities. The linked suite
covers all directory lengths 1–64, complete 64 KiB scanning, malformed MCBs and
terminators, duplicate precedence, forbidden characters, access/size/read/close
errors, PSP/environment aliases and default-loader argument rejection. Peak
observed stack use while executing CONFIG_CODE in that suite is 442 bytes;
this does not measure deeper DOS-kernel stack consumption.

Actual DOS cases check directory values with/without separators, current-file
precedence, explicit `/X`, identity mode, damaged/missing files, empty/oversized
values, and a nested 63-byte path. They verify mapped screen output, actual
terminal replies, unchanged fixtures, and independent UART/PIC/IRQ snapshots.
Startup failures send no modem commands. The complete terminal regression and
fresh public-source rebuild are separate checks. Physical UART/modem behavior,
concurrent changes to files/environment and whole-application resource coverage
remain unverified.
