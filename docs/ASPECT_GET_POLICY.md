# GET status-line policy

GET's original DS1D46 input is **STATUS_HIDDEN**, not terminal autowrap.
The earlier GET components and frozen fixture called it `wrap`; that annotation
was wrong. The recovered instruction bytes and historical observations remain
unchanged. Current source names it `aspect_get_status_hidden` and
`runtime_get_status_hidden`.

Fresh REA static observations establish the shared role:

- Overlay17 GET owner F29F, Evidence
  `ev_581226febafac6bb3a3fec10f24ab8d8c5f725deeb377b01b6b6dd35156e0415`,
  reads DS1D46 at F339 and DS7A80 at F342 for default-width clipping.
- Original resident status toggle46BA, Evidence
  `ev_13f7d32173103cb3de49e9cff09a921f857661655a62c361d2af59c3688e5125`,
  toggles DS1D46, selects physical rows DS7A74 when hiding the status line and
  DS7A80 when showing it, and updates the last row and effective rows.

The first observation uses a non-runnable overlay analysis image with SHA256
`5347274e7bdb429ae1e15edf5bd5fe68710d26166508f90f3b030b5e30836254`;
the second uses original PCPlus2.01 SHA256 `6401ccfd…`. Complete exports remain
under ignored local analysis storage. Static inspection does not prove runtime
behavior, and no analysis image was executed. An initial query used the plain
overlay image and an unobserved F2A1 entry; it failed and supports no conclusion.

## Checked parent binding

Optional `ASPECT_GET_POLICY` requires GET display and publishes capability22.
Capability21 retains its INFO0..10 contract. Capability22 adds
INFO11=STATUS_HIDDEN and INFO12=STATUS_ROWS. Both use tagged `F000|byte`
responses under the per-request PSP/DS/MCB/descriptor/token/callback checks.
Older client versions refuse BEGIN.

The maintained parent stores visibility in `ui_flow_suppressed`. Its packed
status-row position `ui_flow_coordinate_base` supplies the STATUS_ROWS role:
the high byte counts text rows preceding the status row, and the low byte must
be zero. This is the maintained layout representation, not an original DS alias.
The controller validates the boolean, nonzero row count and physical bound;
captures them at field BEGIN; and refuses operations if either changes while
the field is retained. Checked error retirement remains possible. No child
pointer is retained and no UART operation is added.

`runtime_get_context_parent_policy()` arms the native checkpoint; the command
wrapper selects it with argument FFFF in this opt-in profile. After reserving
the parent/keyboard anchor, preparation reads both values before any operand.
It passes STATUS_ROWS to the recovered owner's row calculation while retaining
the independent logical view bound in the editor. Explicit0/1 policy remains
a legacy component-test interface, not the production parent binding.

For an80-column,25-row display with STATUS_ROWS24:

| Status line | Input position | Native default width |
| --- | --- | --- |
| Shown | Row23, column75 | 5 |
| Hidden | Row24, column75 | 5 |
| Hidden | Row23, column75 | 80, spanning the next row |

Coordinates are zero-based. The third case fits the25-row view; a reserved
24-row view can still reject it. Autowrap is a separate terminal setting.
The frozen fixture's `wrap` field remains an archival label.

## Validation and remaining integration

[The receipt](validation/aspect-get-policy.json) binds these checks:

- Actual recovered owner, readers/integer CRT, serviced editor/WHEN/client,
  native confirmation and abort/longjmp:142 frozen cases, three modal faults,
  six added policy probes, and an exact45-source cold replay. The policy probes
  cover the three table rows and three before-operand invalid-metadata refusals.
  Parent, BIOS keys, serial and native WHEN action bodies are controlled peers.
- Actual full parent bridge/controller/native cursor/parser:43 CPU replays,
  including eight added policy/version cases. BIOS/DOS PSP/UART are modeled;
  no child callback executes.
- DOS8086 child client:308 checks with controlled parent responses.
  A752-source isolated rebuild reproduces parent/client and both reports.
- Actual DOS video/BIOS/native cursor:103 case groups and811,165 checks,
  including policy changes and255 CP437 bytes; a nine-source exact cold replay.
  Parent admission is controlled.
- Full experimental capability22 interpreter links with GET still disabled.
  The reviewed capability20 parent and child rebuild byte-for-byte unchanged.
- All566 recovered native bytes retain their frozen digest; all65,536 numeric
  filter inputs pass in DOS8086, with a six-source exact isolated reproduction.

The policy parent retains DGROUP65520 bytes, only16 bytes spare, and requires a
minimum481024-byte DOS module allocation plus PSP. This build-layout result
does not establish that the parent and future GET-enabled child fit on hardware.
Full GET/interpreter linkage, production typed aliases, shared FOPEN scratch
lifetime, native dispatcher shutdown, actual parent/child receive and WHEN
actions, FLOAT.RTE, compiler grammars, connected scripts and physical acceptance
remain open. Neither the selected package nor installed machine changed.

```sh
./tools/dev --command python standalone/build_aspect_get_owner.py \
  --checkpoint --serviced --context --command --parent-policy \
  --output build/my-get-policy
./tools/dev --command python standalone/build_script_field.py \
  --policy --output build/my-policy-field
./tools/dev --command python standalone/build_get_display_client.py \
  --policy --output build/my-policy-client
```

The later [full GET interpreter checkpoint](ASPECT_GET_VM.md) composes the
optional policy with actual typed execution and parent services. Its capacity
failures and compiler limitations remain separate from the checks above.
