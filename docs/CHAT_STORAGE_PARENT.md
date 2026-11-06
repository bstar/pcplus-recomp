# Exclusive Chat storage

The opt-in `--chat-storage` parent adds explicit acquire/release calls for the
existing frozen history workspace and screen frames. It adds no near state and
does not reduce capacities. It requires the loader, original reference and
large-frame options. Alt-O and the Chat input/output frontend remain unbound.

Parent `75c84373` uses 478,080 minimum module bytes/29,895 retained paragraphs,
including its PSP in the latter figure. Near data stays 65,488 bytes and
resident code is 65,488 bytes. Normal DOS8086 ASPECT execution with six files
held across three child launches still passes. The remaining admission margin
is tight; this does not prove the future frontend fits.

## Ownership contract

`terminal_chat_storage_acquire` and `terminal_chat_storage_release` are FAR
foreground register calls with the parent's DS=SS. They preserve registers;
CF0 means success and CF1 refusal. Acquisition reuses the existing view owner
with the distinct internal value2. It checks inactive view/menu/export/search
state and uses the common terminal/view admission guards, requiring narrow
80-column storage. There is no new heap, near owner flag or private frame.

While held, normal redisplay key/before/idle/stop wrappers cannot enter viewer
C or overwrite its borrowed storage. Stop does not silently retire the lease.
Existing directory editor/browser, screen-file, native reset and ASPECT frame
guards reject the nonzero owner. Direct PROGRAM scheduling now also refuses
this specific owner, closing a path that did not reject ordinary redisplay.
Normal viewer/program behavior is unchanged with the feature disabled.

The caller owns module lifetime. It must close/abort and unload its module
before explicit storage release; the lease API does not discover or manage an
arbitrary caller's handle. It is a storage primitive, not a complete keyboard,
RX/TX, notice, trap or cursor owner. The final frontend must establish those
guards, pending-input policy and geometry and sequence retirement correctly.

## Evidence

The linked-code suite checks 54 cases and 16 lifetime cycles: common owner/video
refusals, exact 63,494 snapshot/index bytes and 16,000 frame bytes, FAR register/
stack preservation, refused/repeated release, competing public frontend guards,
ordinary viewer return and the browser's Connection/Redial action after release.
A defensive ASPECT frame-acquire check uses the existing modeled caller/MCB
setup. BIOS/UART boundaries remain modeled; this is not physical acceptance.

The dedicated DOS8086 caller loads the actual source-built parent as a DOS
overlay and calls its own storage and loader code on its real DS=SS and declared
stack. It patches no product instruction and links no loader or Chat code.
At two relocation addresses it acquires storage, loads the separate module,
opens Chat, paints a buffered local glyph, rejects active unload, checks
before/idle/stop/key/reset exclusion and the loaded image CRC, then closes,
unloads and releases. Guards and PSP/JFT/largest-free-memory checks pass.
Parent main/PSP startup is not executed in this composition fixture; normal
main admission has separate ASPECT and BBS runs.

A 629-file clean public export reproduces parent/module/header. Adding the three
dedicated caller files produces a 632-file export that repeats the DOS test and
matches its executable/result exactly. Neither export has originals, private
configuration, prior objects or ancestor Git. Fresh disabled controls reproduce
both `61757956` and the preceding loader parent `03a2149b` exactly.

Stock Synchronet editor/graphics return passes with its existing 386/UMB helper
profile. Enigma's first normal DOS8086 carrier test loses the first connection
correctly but never redials. A same-input repeat passes two ASPECT logins,
staging cleanup, redial and exact 65,539-byte retry, with an independent raw
capture CRC/finish/control/hardware audit. Recipe, keyboard helper, executables,
PRM and login-script bytes match across the pair. The cause of the first miss
is unestablished; the ephemeral loopback endpoint and mutable server session
state differ. This is retained as an open connection-reliability check, not
discarded as an assumed timing issue.

The [checkpoint receipt](validation/chat-storage-parent.json) separates verified
storage work from that unresolved run. No selected package, physical machine
or production bridge changes. No physical/SIP/audio or full parity claim.

```sh
./tools/dev --command python standalone/check_chat_storage_live.py \
  --terminal build/PARENT/TERMINAL.EXE --output build/NEW-linked-storage
./tools/dev --command python standalone/test_chat_storage_dos.py \
  --terminal build/PARENT/TERMINAL.EXE --output build/NEW-DOS-storage
```

Resolve the intermittent redial miss, then bind the original Chat entry and
foreground input/RX/TX/history/log/help/TEXT/notices/traps/frame/cursor behavior.
Repeat final memory, Enigma/Synchronet, package/source and physical gates.

The [passive key-owner diagnostic](CARRIER_KEY_OWNERS.md) now observes the
actual parent key-read boundary with the same retained TSR footprint. Passing
observed requests are kept separate from the still-unexplained earlier miss.
