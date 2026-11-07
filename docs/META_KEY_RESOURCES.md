# Meta Keys resource identity

KEY-file selection now has checked DOS resource lookup and picker-directory
binding. A resolved path can be retained across loading, editing and saving;
later current-directory changes or a newly appearing local copy do not redirect
that operation. This component is not yet connected to the interactive parent.

## Named lookup and retained identity

`meta_key_resource.c/.h` exposes near-cdecl DS=SS operations and a required
74-byte near result. Requests are already-normalized DOS83 names from the
filename workflow, or explicit DOS83 paths. Bad arguments leave the result
unchanged and perform no DOS calls. Valid calls report status, native DOS error,
environment error, selection source, existence and a 64-byte path.

Named lookup uses the existing DOS21/AH60 canonicalizer and bounded
`resource_pcplus_path` environment reader. It first resolves and inspects the
current request. Existing regular files win, including readonly files; KEY
content validation belongs to the checked reader. Only file/path-not-found
errors 2/3 on a bare name enable PCPLUS fallback. Qualified requests remain
explicit and do not search the environment. Operational canonicalization or
attribute errors stop selection, rather than hiding an inaccessible current
file with a different copy. A corrupt existing current KEY is likewise selected
and then rejected by the strict reader, without fallback.

The PCPLUS environment is not consulted when a current file is usable. First
exact uppercase PCPLUS entry, empty/duplicate handling, full environment
termination and MCB/PSP bounds come from the existing helper. A validated dummy
leaf extracts its parent, allowing the actual KEY leaf to retain the broader
ASCII DOS83 punctuation supported by checked KEY IO. Malformed/oversized
fallbacks report errors. Canonical identities must satisfy the same 63-byte
path/53-byte recovery-parent policy as checked KEY replacement.

MISSING retains the canonical absent target chosen by lookup: the current
identity if no environment fallback exists, or the configured fallback identity
when it was selected. This is context for the later default/create owner,
**not permission or a claim to create it**. The owner must check status, admit
and claim the resource, then recheck/use exclusive checked creation. A nonexistent
parent can still make that later creation fail.

The original resident 353d resolver and KEY read/write wrappers are documented
in [resource lookup](RESOURCE_LOOKUP.md) and [KEY mapping](KEY_MAPPING.md), with
retained REA identities. They re-resolve filenames for IO and fall back after
failed probes. Retaining a successful canonical identity, restricting fallback
to absence and refusing invalid paths are maintained policies. This checkpoint
is not claimed as a whole-workflow native instruction comparison.

## Picker-directory binding

Pattern planning is split deliberately. First request the canonical current
`*.KEY` pattern and enumerate it. Only an empty current scan requests the PCPLUS
pattern; a usable current list therefore does not depend on a valid environment.
An absent fallback supplies no pattern. Enumeration errors remain distinct from
empty results; the caller must not turn an error into a fallback.

After accepting a stem, pure `meta_key_resource_selected` composition joins it
to the **frozen selected pattern's parent** and validates the resulting absolute
path. It does not search again or perform DOS IO. This preserves selection of a
fallback file even if a current-directory copy appears before loading. Callers
must retain the selected identity for Save as well.

These APIs provide names and identities, not file/EXEC admission, claims or an
external filesystem lock. Runtime drive remapping, concurrent replacement and
aliasing outside the DOS namespace model are not prevented. The frozen pattern
must come from the checked planner. ASCII path/leaf policy applies; retaining
CP437 display bytes in the picker is not a claim of complete OEM path support.

## Verification

```sh
./tools/dev --command python standalone/build_meta_resource.py \
  --output build/NEW-meta-resource
./tools/dev --command python standalone/prove_meta_resource_source.py \
  --build build/NEW-meta-resource --output build/NEW-meta-resource-source
```

The source-built DOS8086 test passes 699 assertions, including per-byte
preservation after a rejected file load. It uses owned fixture files and
separately allocated synthetic PSP/environment blocks. Real DOS canonicalization,
attributes and picker enumeration prove current/PCPLUS precedence, current-file
independence from malformed environments, empty-list fallback, punctuation names,
explicit drive-relative paths and readonly loading. A short current KEY is not
silently replaced by its valid fallback copy. Missing lookup creates no file.

The composed test loads a fallback file, freezes its identity, creates a new
current-directory copy, changes CWD, and performs checked save. Independent
readback verifies the intended fallback update and unchanged competing copy.
Default D:\KEEP and C:'s separate C:\ALT working directory are restored/unchanged.
Five explicit kernel-wrapper modes exercise canonical failure, attribute failure,
unterminated/oversized canonical output, a short canonical output and an
ineligible directory attribute. These are declared faults, not observed hardware
failures. Argument/alias guards reject before IO and preserve outputs.

Object inspection verifies zero globals/constant data in the new resource
module. Shared helpers and caller stack still require application memory
admission. The diagnostic checks DS=SS and far file buffers, with an explicitly
ordered null guard. An isolated 28-file source export reproduces its executable
and complete results without originals, private files, prior objects or ancestor
Git. The outer pinned Nix environment supplies tools. See the
[receipt](validation/meta-key-resources.json).

## Remaining integration

A live editor owner still needs file/EXEC admission and canonical claims spanning
selected target, stage and backup; it must reconcile baselines, implement original
missing-file defaults/create with checked IO, retain uncertain-close recovery,
and adopt the accepted table. Picker/UI lifetime, screen/cursor restoration,
foreground/UART scheduling, transient module and application memory/capacity,
BBS regressions and physical acceptance remain separate. No parent/package,
remote service or installed RCE81708 file changed; no full-parity gate is closed.
