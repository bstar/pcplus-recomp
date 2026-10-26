# Validated directory selection proposals

`directory_selection_stage` connects a reader-published far page to the existing
configuration decoder without rereading the PRM or changing the active session.
The caller supplies its accepted PRM, actual active configuration, chosen entry,
literal/legacy expansion policy, command-line category mask and retained path
spellings. Success publishes a 1190-byte far proposal containing the raw selected
header/record, paths, proposed configuration and transfer preferences. A failed
call preserves the complete previous proposal. Invalid pointer/alias/path bounds
also preserve the result object.

The component checks the page's first/count and selected-entry range, validates
global and directory settings before honoring overrides, validates transfer
preferences and retains original private/opaque metadata. Stored passwords are
never transmitted. KEY/META/script syntax can be validated without executing or
opening those resources. The function performs no DOS, BIOS or UART calls and
allocates no storage. It uses DOS16 near cdecl, DS=SS; ES is scratch for far data.

This is an application prerequisite, not a completed dialing chooser. Alt-D in
the LoC.4 application remains the [read-only view](DIRECTORY_VIEW.md). The later
[LoC.5 integration](DIRECTORY_PREVIEW.md) adds live preview; adoption remains open.
The source-built terminal/package and all live services are unchanged. No card
deployment or physical modem acceptance is claimed.

## Evidence

The [receipt](validation/directory-selection.json) binds these checks:

- 294 independently constructed 1,190-byte golden vectors execute the linked
 8086 instructions and repeat under real DOS8086: all 200 entry numbers, partial
 pages, all 16 CLI masks, literal and A–J expansion, private/opaque bytes, binding
 syntax, 63-byte paths, transfer preferences and DIRECT's modem-skip policy.
 Rejections include malformed pages, global/record/active settings, unterminated
 strings, unsupported bindings, empty targets and unsafe transfer paths.
- 39 additional linked cases reject null/wrapping extents, exact/partial aliases
 and alternative segment:offset spellings of the same physical memory. They
 preserve all caller data and the result. Interrupt and IN/OUT hooks reject
 any attempted IO in every linked case.
- DOS independently compares complete proposal/result bytes, all source objects
 and guard bytes against the host's golden vectors: 6,174 native assertions pass.
 The input vector file stays exact and the 42-byte hardware snapshot is restored.
- Measured component stack high water is 4,290 of 8,192 bytes. This excludes a future
 live UI caller's buffers, which must be included in its integration checks.
- An isolated 32-source export outside every Git ancestor, with no analysis or
 original installation present, reproduces SELECT.EXE and all ten objects
 exactly and repeats the linked and DOS checks. The same proof passes from
 committed sources at `2280272`, excluding the pending telephone-log changes.

The first isolated-build attempt rejected an absolute NASM THEADR source path.
The builder now assembles the logical relative source path. This corrected the
object reproducibility mismatch without changing executable bytes; the failed
attempt remains under `build/directory-selection-source-20261025`. Its later
`path-control.json` reproduces the differing THEADR names and verifies that all
remaining object records are identical.

## Reproduce

```sh
./tools/build test-directory-selection
./tools/dev --command python3 standalone/prove_directory_selection.py \
  --output build/directory-selection-source-NEW
```

The executable is a diagnostic with synthetic golden inputs, not a replacement
terminal. Its accepted SHA-256 is
`e70e6e6b792643f19b65e4cb4ff9306bea4d7e4980db73804f6822818095230e`.

## Remaining application handoff

The view must copy the accepted baseline through `hook_baseline_copy`, capture
the actual session through `terminal_session_capture_far`, stage a proposal in
its leased far snapshot, and present bounded public fields/errors. The caller
must include its own buffers in the 8 KiB stack accounting; no stack, history or
screen capacity should be reduced to make it fit.

Before adoption, establish canonical resource identities/claims, load the
selected key/meta/translation/script resources, check baseline freshness and
retire or preserve accounting against the old selection. Quiesce and hand off
UART/profile ownership through the existing live transition rules. Transfer
preferences need their own active comparison; the configuration change mask
only classifies its existing serial/modem/directory fields. Preview success
alone does not authorize a connected-port switch, prove resource availability,
or establish the page's provenance. Path spellings are not filesystem locks.

The full F01–F16 plan, original interface restoration, ENiGMA rendering/input,
physical serial/VoIP/reconnect/transfers and card acceptance remain open.
