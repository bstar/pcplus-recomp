# Connected Enigma editor, Chat and Help return

The unchanged6fd8aafc source parent now passes a Chat/context3 Help round trip
inside an authenticated, unsaved stock Enigma editor session. The actual
SynthModem Telnet proxy remains connected throughout. After Help returns to
Chat, Escape discards the unfinished local `X` and returns to the same editor;
the existing editor key workflow then resumes successfully. No message is saved.
[The receipt](validation/chat-help-bbs.json) records exact products and evidence.

```sh
./tools/dev --command python lab/bbs/test_synthmodem_proxy_dos.py \
  --runtime build/menu-size-accepted-20261104/candidate \
  --terminal build/chat-help-review-20261106/TERMINAL.EXE \
  --label my-chat-help-editor --framing-ms 250 --byte-delay-ms 20 \
  --size-probe --screen-reference --chat-help-overlay
./tools/dev --command python lab/bbs/audit_size_probe_screen.py \
  --output build/bbs-lab/results/enigma/my-chat-help-editor \
  --bridge build/bbs-lab/my-chat-help-editor-proxy
```

This requires the existing owned loopback Enigma lab to be running. Use a new
label. The package beside TERMINAL.EXE supplies the hash-checked PCCHAT.OVL,
PCHELP.RTE and authored PCPLUS.HLP; no vendor helper or private configuration
is loaded. The ordinary editor harness and its server-state lock are reused.
This flag is for the admitted25-row/24-logical-row source profile.

## Actual screens and input

A BIOS hook captures the editor before Chat paints it, after validating the
loaded module/API and parent stack/data segment. A passive timer then captures
Chat with the unfinished `X`, the actual source Help screen, Chat after the
complete PROGRAM return, and the restored editor. Sampling writes only the
observer's own storage; the hooks are restored after the run.

The lower-level modal audit compares all4000 bytes of both Chat frames and
the24 logical editor rows, cursor positions/shapes,25-row BIOS geometry and
PROGRAM/Chat/native-wait state. The acceptance receipt additionally compares
all4000 editor bytes, including the native status bar, and requires `ON-LINE`
before and after. Every byte and attribute matches in this fixture. The local
`X` and Alt-Z/NUL never appear in the BBS input stream.

After returning, the ordinary Home/End/Delete/Insert/Tab/Page-key workflow
still operates in the stock editor. Server logs independently establish real
authentication, editor entry and no saved post. The final unsaved editor image
is bounded by a real CPR and compared with an independent replay of the exact
47819 delivered BBS bytes. All1920 logical cells and their attributes match;
the cursor agrees at row9,column8. Actual terminal-size negotiation reports
80x24 to Enigma while the physical display remains80x25.

Eight copied-evidence controls reject altered character/attribute cells,
bottom cells, cursor, truncated delivered prefix, unsupported font projection
and truncated proxy input. An unchanged copy passes. The live capture,
products, BBS and proxy runtime are not modified by these controls.

The first run's modal data was written relative to C: while the audit expected
D:. Its capture showed correct return, but the outer audit correctly could not
accept a missing file. The observer now writes an explicit D: path, and the
complete run was repeated. The first capture was moved into its ignored
diagnostic result folder rather than left beside the package products.

## Scope still open

The editor is idle during local Help. This proves connected modal return and
resumed BBS input/rendering, not deliberately scheduled remote traffic inside
the DOS child. The Hayes/nullmodem lab model holds CTS ready, so this is not a
physical RTS/CTS or analog test. The physical Boca, SPA2102 SIP/audio path,
other BBS screens/profiles and geometry/allocation/lifetime faults remain open.
The [native-wait/full-FIFO checks](CHAT_HELP_BUSY.md) and prior carrier/transfer
checks apply to these same product hashes but were not rerun or relabeled here.
No physical deployment, selected-package or bridge configuration change occurred.
