# Publish a selected translation resource

Directory resource staging already returns a translation table and its canonical
filename. Copying only the table into the terminal would leave Reload and Edit
bound to the previous board. `xlt_live_resource_adopt` publishes both in one
foreground operation, without reopening the selected file or resolving CWD.
It is currently enabled only by `DIRECTORY_RESOURCE_ADOPTION` in the component
build. The application selection action and UART transaction are still pending.

The caller supplies three disjoint near allocations: path64, selected table256
and active table256, with DS=SS and input/UART quiesced. Mode1 requires an
absolute uppercase DOS83 path. Modes0/2 require a blank path, clear the Reload/
Edit identity and preserve unused active table bytes. The caller still owns
mode, enabled flag and RX-mask publication. This API does not switch them.

Invalid mode, extents, aliases and identities leave all bindings and destination
bytes intact. Pending settings or reload offers refuse without consuming them.
The owner also retains any observed uncertain translation-reader close in a
serialized flag, independent of staging resets; cancel and rebind cannot make
resource adoption proceed after that uncertainty. No close is retried.

Successful publication owns copies of the filename and table. Reusing the
caller's buffers cannot change Reload/Edit. These are process-local lifetime
and damage checks; they do not authenticate a source or lock external writers.

The [validation receipt](validation/xlt-resource-adoption.json) records 13 real
DOS8086 workflows and 823 native assertions, including canonical Reload/Edit
after CWD drift, mode0/2, 63-byte names, caller reuse, pending settings/reload
offers, invalid extents/paths and both declared forms of uncertain close. Actual
DOS opens/reads/closes execute; wrappers count calls and inject only the two
explicit close errors. Adoption itself performs no IO. The component exercises
the production owner and reader, not a model of publication.

```sh
./tools/dev --command python3 standalone/build_xlt_resource_adoption.py
./tools/dev --command python3 standalone/test_xlt_resource_adoption_dos.py \
  --output build/xlt-adoption-NEW
```

Selection adoption, accounting/context handoff, script execution, dialing, the
full F01–F16 application, complete independent BBS character/attribute comparison,
physical Boca/SPA2102 and card acceptance remain open. The existing compiler
package is rebuilt as an exact-byte control; this API is not wired into it yet.
