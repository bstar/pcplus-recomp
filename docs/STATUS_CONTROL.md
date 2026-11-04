# Normal status control

The optional `--status-control` build now connects Ctrl-] and Toggle Status in
both command menus to the tested offline status transaction. It requires the
existing status and local-control owners. The reference entry is enabled in this
variant, leaving 12 unavailable reference commands. Other variants retain their
previous command availability. This does not close the broader F12 parity gate.

In a supported, disconnected 80×25 view, the command hides/shows the status row
and changes the accepted text area between 25 and 24 rows. The actual status
owner keeps parser bounds, RIS defaults, shadow/video planes, cursor and margins
coherent. It retains history and queued UART data; no saved setting is rewritten.
Ctrl-] is recognized by its control character, matching reference normalization.
Unrelated keys retain normal dispatch. No new resident-code hook, global state,
heap allocation or screen frame is required.

The existing shared owner defers keys during a partial parser operation and
other active owners, then dispatches once after release. Connecting states
retain the existing deferred-key policy. Tracked-connected changes refuse with
status3, leaving the view and wire unchanged. Unsupported geometry and absent
baseline also refuse. This is not an online resize implementation or an agreement
with a BBS about its current layout. Original calibrated timing/pixel equivalence
and complete original terminal-control behavior are not established here.

Selecting from a menu first releases the menu frame. Testing exposed a stale
`clipboard_ui_visible` flag after closing the shared view; the status transaction
correctly refused that apparent active owner. All four frame-release paths now
clear visibility with the other ownership fields. Dedicated checks cover menu,
history, clipboard and elapsed-window closure followed by the real status key.
This visibility correction applies to builds using the shared viewer, independently
of the new optional binding.

[Bound validation](validation/status-control.json) records the exact image,
source hashes, build flags and evidence hashes:

- 36 linked control inputs cover normalized BIOS keys, reference/browser dispatch,
  genuine CPR, history retention, connecting/online refusal, busy-owner deferral,
  unsupported geometry and frame-release ownership. Product instructions execute;
  BIOS/UART/DOS boundaries, including elapsed-view date/time, are modeled.
- 799 existing status/row/reset/preferences/selector/size-report inputs pass on the
  same image, along with all 82 reference checks. These include native renderer
  rollback, UART servicing and failure/recovery boundaries.
- The actual DOSBox-X 8086 application receives BIOS Ctrl-] and Alt-Z selection.
  Serial queries observe text-area reports 24→25→24, with corresponding real CPR
  row clamps. Keys stay local. Normal exit, unchanged synthetic PRM/image, visible
  banner and matching 42-byte interrupt-vector/UART/PIC snapshots pass. The serial
  peer sends queries, never replies on behalf of PCPlus.
- A fresh tree containing only 567 declared public source files reproduces the
  exact terminal image, with original artifacts and ancestor Git unavailable.

The internal image is `build/status-control-accepted-20261104/ordinary/TERMINAL.EXE`,
SHA256 `ee0bd6cd00295643f9500aed5ca4dd8b8552a102574f5d09a45affe739d7308f`.
Resident CS remains 65,418 bytes, with 118 bytes spare; data/stack remains 65,088
bytes. Exact build flags are in the receipt. The pinned rebuild checker accepts
that flags array as a JSON file:

```sh
./tools/dev --command python standalone/prove_terminal_variant.py \
  --terminal build/ORDINARY/TERMINAL.EXE --flags-json build/FLAGS.json \
  --output build/NEW-source-proof
```

No package, connection-test selection, installed bridge/service/configuration or
physical DOS file changed. Normal Ctrl-- needs larger modal-frame support before
exposure. Startup preference application, session/bridge size synchronization,
owned Enigma/Synchronet application testing and physical acceptance remain open.
See [the staged Linux handoff](MENU_SIZE_BRIDGE.md) for the separate pre-session
query/NAWS evidence. Neither component establishes live online resizing.
