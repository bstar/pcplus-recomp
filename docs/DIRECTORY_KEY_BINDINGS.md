# Selected-directory KEY and META resources

The optional directory-key build accepts the selected directory record's KEY
and META basenames. KEY at record56h selects a540-byte `.KEY` action table;
META at5Fh selects the terminal-dependent948-byte profile in `.KBD`. The latter
is a keyboard translation table, not an ordinary macro script. Original static
handoff/loader evidence and offsets are recorded in [DIRECTORY.md](DIRECTORY.md)
and [KEY_MAPPING.md](KEY_MAPPING.md).

Build and test through the pinned Nix toolchain:

```sh
./tools/build directory-keys
./tools/build test-directory-keys
./tools/build test-directory-keys-source
```

The terminal is `build/terminal-directory-keys/TERMINAL.EXE`. The matching
ASPECT interpreter/resource and DOS compiler use the same installation layout
as [the ASPECT KEY build](LIVE_ASPECT_KEYS.md). Existing default, capability16
and ASPECT-key terminal executable bytes remain unchanged.

## Selection policy

Names contain one to eight ASCII letters/digits, underscore or hyphen; the
loader uppercases them and appends `.KEY` or `.KBD`. DOS device aliases,
extensions, paths and malformed termination are rejected. A first NUL or space
means no binding; the surrounding directory decoder still requires a bounded
stored field. These bounded basenames are maintained validation, not proof of
the original accepting exactly the same character grammar.

Explicit `/T` and `/K` independently override the corresponding directory
binding. Directory validation still checks both stored fields. A directory name
first probes the current DOS directory, then the single `PCPLUS` environment
directory. Lookup falls through only on missing-path/file errors. Other open,
close, namespace or size errors stop startup. Both candidate paths/flags publish
after the complete lookup succeeds. The existing readers then validate file
size, selected profile/record strings and successful close before committing
those tables. They do not fall back from malformed selected content.

If a named KBD file is missing in both locations, lookup tries `PCPLUS.KBD` in
the same order. If that is also absent, the maintained network defaults remain.
A missing directory KEY resource leaves the existing empty TEXT defaults.
No KEY file is automatically created or overwritten. Missing explicitly selected
CLI files retain the existing strict import failure behavior.

This implementation validates/loads the one retained selected-entry plan during
startup, before UART installation. The original directory applies bindings
through its successful-connect handoff. General connected directory switching,
that original mutation timing, native factory defaults and native KEY file
creation/recovery behavior remain unfinished. Startup admission is the current
maintained contract; it does not close all directory/keymap requirements.

## Ownership and memory

`directory_live.c` enables binding-name validation only with
`DIRECTORY_KEY_BINDINGS`. A CONFIG_CODE-local DOS open-readonly/close probe and
far C policy reuse the existing64-byte keyboard/action paths and option bits.
No user resource is read into the selector or written by lookup. File contents
are loaded by the established bounded KEY/KBD readers. The resource must remain
stable during startup: the probe and subsequent read do not lock or snapshot it.

The helper constructs suffix/fallback names on the stack. Its first link with
static suffix strings reached64KiB DGROUP and was rejected. The accepted product
retains65,520 DGROUP bytes including8KiB stack. _TEXT is65,470 bytes with66 spare;
CONFIG_CODE is63,347 bytes. It adds no persistent near data.

## Evidence

[The independent receipt](validation/directory-key-bindings.json) binds current
sources/products and preserves raw DOS directory, wire and42-byte hardware
captures.292 linked inputs cover all byte classifications, case/suffix bounds,
CWD/PCPLUS/fallback precedence, explicit CLI precedence, owner context, read-only
probe errors and atomic selector publication. Only DOS open/close and file
existence are modeled; the real environment resolver and compiled policy run.

Eleven actual DOS workflows on COM1/2 exercise both bindings, a directory-selected
ASPECT action, CWD and environment selection, CLI overrides, KBD fallback,
missing resources, first-space/NUL blanks and malformed KEY/KBD/name rejection.
Valid cases dial and resume ordinary typing; malformed inputs produce no modem
commands and leave hardware unchanged. Directory accounting checks preserve all
other record bytes. The missing cases also prove no implicit resource creation.

Four current ENiGMA/Synchronet record/replay sessions select `ACTIONS.KEY`
through entry3 without `/T`. Alt-1 runs a DOS-compiled wrapper containing failed
and successful child execution before recorded navigation; manual navigation
then resumes. These BBS sessions cover the directory KEY route; KBD mapping and
fallback are covered by the separate DOS/component cases.

A662-source empty-tree proof reproduces the terminal, interpreter, HLP companion
and DOS compiler. Three preceding terminal variants rebuild with unchanged
executable hashes. The first compile's context-member typo, DGROUP overflow and
an initial BBS fixture's missing Python import are retained as failed preparation
attempts. No original executable/resource is a normal build input.

HOOK, unrestricted directory filenames, arbitrary I/O/combined failures, other
DOS kernels, physical UART/Boca/SPA2102 acceptance and all full application gates
remain open.
