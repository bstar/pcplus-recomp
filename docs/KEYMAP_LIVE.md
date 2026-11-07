# Alt-F8 keyboard mapping in the live terminal

The opt-in `--keymap-editor` parent launches the source-built PCKEYMAP helper
through the existing drained PROGRAM owner. Alt-F8, the original Alt-Z
reference and Setup → Keyboard mapping reach the same action. Alt-W continues
to select translation editing. This is a software checkpoint, not a deployed
connection-test package or full original helper parity.

Startup freezes the explicit `/K` path, or the startup directory's PCPLUS.KBD,
as an absolute path. Changing the working directory cannot redirect the
selected file. The helper must be beside the parent executable; no PATH or
current-directory executable fallback is used. It receives the current profile,
the frozen filename and, when needed, `/LEGACY` to retain the parent's BIOS
keyboard selection. This requires the matched source helper; the proprietary
helper's argument contract is different.

Recording, parser/macro work, transfers, monitor/controller ownership, snapshots,
ANSI waits and active redisplay refuse entry. The ordinary PROGRAM guards,
display lease, UART suspension and hardware restoration remain responsible for
the child handoff. No new DGROUP storage or smaller history/stack is introduced.

After ordinary helper outcomes, the parent strictly rereads the selected
profile, including after a failed child return. This retains the original
caller's unconditional reload policy: a valid file can become active even if
the helper exits with an ordinary error. An invalid file preserves the live
mapping and produces an acknowledgement. Success also updates the existing
RIS keyboard baseline. Recovery exit14, abnormal child termination or an
uncertain read close exits with14 without adopting disputed bytes. Opening a
different file/profile in the helper does not redirect the parent's selection.

[The validation receipt](validation/keymap-live.json) binds the executable,
matched overlays/helper, disabled control, source reproduction, DOS workflows
and BBS rendering checks. The enabled parent retains479408 bytes,1216 more
than the disabled parent. DGROUP remains65520 bytes, history63000 and the
main stack8192 and native reset's private stack4096. CONFIG_CODE is65311 bytes; its remaining225-byte margin is
small and remains guarded by the build's segment and call-frame audits.
The new far bank is267 bytes. Six new far routes and three near adapters are
checked against linked opcodes/relocations.

The feature-disabled build remains byte-identical to the installed
`5b634d5c…` parent. The size-profile source hashes include the optional UI
guards; its historical object measurements describe the disabled feature,
not the enabled mapper. The enabled image's actual linked layout is recorded
separately in its manifest.

```sh
./tools/dev --command python standalone/test_keymap_editor_dos.py \
  --terminal build/keymap-live-verified-20261107/TERMINAL.EXE \
  --helper build/keymap-helper-lowpeak-20261107/PCKEYMAP.EXE \
  --output build/my-keymap-workflows
./tools/dev --command python standalone/prove_keymap_live_source.py \
  --parent build/keymap-live-verified-20261107/TERMINAL.EXE \
  --output build/my-keymap-source-proof
```

The workflow adapter intentionally replaces the generic harness's unchanged-KBD
checks with exact whole-file expected bytes. Every other hardware, PRM, peer,
startup-reply and exit check remains required. Owned fake children exercise
malformed data, recovery exit and valid-file/error-return behavior. No original
executables or private keyboard files are application/test inputs.

[Actual BBS mapper returns](KEYMAP_BBS.md) now supplement this checkpoint:
edit/save, exact frame/cursor restoration and subsequent editor input pass in
Enigma and Synchronet, the latter using an RTS-aware software modem model.
Remaining gates include matched-helper package admission, targeted refusal/close-fault
injection and physical Boca/SPA2102 acceptance. Native
intro/about/prompt styling, broader filenames, new-file/default behavior and
other display geometries remain open. The installed RA608E10 package is unchanged.
