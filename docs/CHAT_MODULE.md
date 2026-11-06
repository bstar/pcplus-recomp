# On-demand Chat module

Chat now builds as `PCCHAT.OVL`, a source-only DOS MZ overlay with a single far
dispatch entry. The module is 3,386 file bytes: a 48-byte MZ header and a
3,338-byte initialized image with two relocations. It links with default libraries
disabled, no CRT, private data, BSS, private stack or extra allocation paragraphs.
The parent's DS=SS and stack remain in use. Linker notices about the missing
private stack are expected for this overlay, not permission to execute it as an
ordinary process.

Microsoft documents DOS4B03 as loading into caller-supplied memory without a new
PSP. The load and relocation segments are provided separately; this implementation
sets both to the owned destination. See the primary
[MS-DOS Encyclopedia EXEC reference](https://www.pcjs.org/documents/books/mspl13/msdos/encyclopedia/section5/).
Runtime evidence here uses DOSBox-X's DOS8086 environment, not a physical MS-DOS
kernel or the complete PCPlus parent.

## Build and admission

`standalone/build_chat_module.py` compiles the existing session, renderer and send
owners with a small versioned dispatch wrapper. It checks the MZ size, entry,
image bounds, unique disjoint relocation words and zero data/stack requirements.
The ABI has a 50-byte request and 358-byte caller-owned session; C compile-time
assertions and a version query check those sizes.

The build generates `expected.h` from the exact module. The loader checks complete
file length and CRC32 before calling DOS, then checks the loaded image's CRC32
with relocation words normalized back to their original values. No entry is
published or queried before that image check. Alignment, capacity, conventional
address range and state/image overlap are checked before loading. These CRCs
bind a particular build against accidental corruption/stale files; they are not
a cryptographic authenticity system. Module and source exports also retain SHA256.

The caller must exclusively own the destination and separate state, keep the
artifact unchanged throughout preflight/loading, and enforce the shared storage
lease. DOS opens the pathname again for4B03, so concurrent file replacement is
outside this proof. The loader does not discover memory ownership or infer a
free region from an address. Production must use the frozen absolute resource
identity rather than depending on a mutable current directory.

## Lifetime and ABI

An 18-byte caller handle tracks the bound session, entry and loaded/busy/active
states. Far API entries allow the loader to occupy CHAT_LOAD_GROUP; local file
and4B03 primitives share its CS. The bank is 1,328 bytes and has no own DGROUP
data. Its C imports are restricted to the declared local DOS primitives, its
own image-check entry and the compiler's small-code marker. It must not use near
CRT file wrappers located in another code segment.

Dispatch supports query, open, key, receive, step and abort. Every call checks
version, session identity and lifecycle state. Reentrant calls, loads and unloads
are refused while a callback is active. A live session must close or abort before
unloading. Retirement invalidates the handle before the caller reuses storage;
it does not free a block or restore the application's frame. No function pointer
from retired module code may be invoked directly.

Two failed intermediate layouts exposed near calls across distinct code frames:
first the fixture's banked adapter called near loader APIs; then a banked loader
called near CRT file wrappers. The loader APIs are now far, with bank-local raw
DOS file primitives. Runtime CS checks, the import guard and full workflow tests
cover the corrected layout. Those timed-out attempts remain local and are not
accepted results.

## Actual DOS proof

The reviewed fixture does not statically link Chat code. It reserves all remaining
DOS memory and performs six loads into guarded existing scratch storage at two
different relocation bases. It checks unchanged PSP, 20 JFT entries, largest free
block, DS=SS and far callbacks. Five malformed file variants and a missing file
are rejected before code entry; alignment/capacity/overlap bounds, wrong ABI,
active unload and reentrant calls are rejected. Flipping an ordinary loaded byte
or a relocation word fails the read-only image check; originals are restored
before any module call.

The unchanged composed-session fixture also runs through loader proxies, with
Chat absent from its static link map. Its frame and effect files match a freshly
built, native-audited static reference byte for byte: 568 full frames/cursors,
1,071 effects, all 1,024 RX history/log effects while TX is refused, and the
previous abort/reopen checks. This validates the loading path with the full
component workflow, not only a query or single-character call.

A separate 35-file public-source export rebuilds the module and both DOS hosts
exactly and repeats these checks. It excludes original binaries, prior objects,
private data and Git metadata. Exact report and artifact identities are in
[the receipt](validation/chat-module.json). BIOS/scroll/UI/sink reference limits
from [the session checkpoint](CHAT_SESSION.md) remain; this does not establish
live UART, BBS or physical acceptance, concurrent artifact mutation, arbitrary
memory corruption or every DOS I/O failure path.

## Parent work remains

The later [presentation variant](CHAT_PRESENTATION.md) adds separately versioned
physical screen/cursor save and restore without changing this default module.
Its DOS lifecycle is verified; the parent frontend remains unbound.

The mechanism avoids permanently linking the 3,338-byte module image. The
1,328-byte loader bank still costs conventional memory; the selected parent has
not been rebuilt with it. Fund that resident cost and prove the existing storage
lease before binding pre-dequeue hold, receive filter, idle service and command
entry. Preserve current ASPECT admission, stack and stream capacities.

The subsequent [reviewed parent compiler profile](TERMINAL_SIZE_PROFILE.md)
saves 1,296 retained bytes without reducing these capacities. Its opt-in parent
is a separate candidate; the loader and frontend have not yet been added, so
the saving alone does not close the admission gate.

The [resident-loader checkpoint](CHAT_LOADER_PARENT.md) subsequently links the
optimized loader into an opt-in real parent and tests its memory admission.
Its separate module remains unbound to foreground Chat; storage ownership and
application hooks are still open.

Original Chat Alt-number keys call the native48CC TEXT sender over the54-byte
records directly. The frontend must preserve that route rather than silently
executing all general KEY action kinds. Help, notices, real log/history/TX,
trap/cancel policy and frame/hardware-cursor restoration also need integration.
Then repeat full Enigma/Synchronet and memory gates, exact package/source checks,
reversible deployment and physical observations. No selected package, physical
file or production SynthModem service changes at this checkpoint.

```sh
./tools/dev --command python standalone/test_chat_module_dos.py \
  --output build/NEW-chat-module
```
