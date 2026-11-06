# Reviewed parent compiler profile

The opt-in `--optimize-size` build saves 1,296 retained conventional-memory
bytes in the capability18/128-pair parent. It produces `dddff45b` instead of
the unchanged disabled control `61757956`. This is preparation for integrating
Chat, not an enabled Chat command or a new selected/deployed package.

`standalone/terminal_size_profile.json` selects measured size-favoring compiler
options for 41 C sources. Each entry records its source digest and before/after
object code/data sizes. A stale source digest stops the build. The normal
builder still uses its previous compiler flags and does not read this profile.
All assembly, ABI declarations, capacities and linker elimination policy remain
unchanged. The C stack, history, screen frames, reset workspace and near data
are not reduced.

The measured object-code saving is 1,283 bytes; segment alignment makes the
retained-parent saving 81 paragraphs, or 1,296 bytes. Minimum module allocation
falls from 478,032 to 476,736 bytes. The retained block including its PSP falls
from 478,272 to 476,976 bytes. Near data remains 65,488 bytes, with 48 spare.
Resident code falls from 65,516 to 65,478 bytes, leaving 58 bytes before the
segment limit. This is a size result; no CPU-speed improvement is claimed.

## Verification

The artifact audit checks every selected object's actual code/data sizes against
the profile and compares retained memory and capacities with a disabled control:

```sh
./tools/dev --command python standalone/check_terminal_size_profile.py \
  --control build/CONTROL/TERMINAL.EXE \
  --terminal build/OPTIMIZED/TERMINAL.EXE \
  --output build/NEW-size-audit
```

The reviewed tests include exact linked menu/reference frames, actual DOS8086
ASPECT execution with six buffered files retained across child launches,
missing-file recovery, external-editor parameter/child/frame/cursor return,
and a stock Synchronet editor through the real isolated SynthModem Telnet
proxy. The latter explicitly uses the existing 386/UMB observer/helper profile;
it does not establish8086 graphics-child memory admission.

The Enigma connection test also passes with this exact parent and the normal
deferred-buffer ASPECT child `cbdee194`: one DOS8086 parent logs in, receives a
partial file, observes real virtual-modem DCD loss after socket interruption,
cleans the stage, redials, logs in again and receives all 65,539 bytes exactly.
An independent raw-capture audit verifies transfer CRC/finish/controls, both
authentications, bridge/logoff return and hardware/settings restoration.

A cold 614-file public source export reproduces the optimized executable
exactly without originals, private configuration, previous objects or ancestor
Git. Disabling the flag reproduces `61757956` exactly. A deliberately stale
profile in a separate source export fails before publishing an executable.
The [acceptance receipt](validation/terminal-size-profile.json) binds all ten
reports, binary/source identities and measured limits. The software tests do
not establish physical Boca/SPA2102/SIP/audio acceptance.

## Rejected experiments and remaining integration

Global function sections plus linker elimination grew minimum allocation by480
bytes and failed the existing native-shadow layout check. Global size-favoring
compilation exceeded resident code limits. Applying it only to far sources
grew allocation by832 bytes; suppressing inlining for all far sources saved
only320 bytes. None of those variants is selected or executed as an accepted
application. The reviewed profile instead selects only measured shrinking
objects; it does not weaken the layout checker.

The checked Chat loader alone occupies 1,328 resident bytes, before frontend
bindings, guards and callbacks. This saving therefore does not establish that
the full integration fits. Complete that binding and repeat actual ASPECT
admission, serial/rendering/transfer checks, package/source reproduction and
physical acceptance. Preserve stack and feature capacities. No installed
candidate selector, physical machine or production bridge changes here.
