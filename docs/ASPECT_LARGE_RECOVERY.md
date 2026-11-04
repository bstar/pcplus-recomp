# ASPECT parser recovery on accepted text heights

Two defects were found while exercising the attached ASPECT renderer at larger
text heights. A partial CSI timeout left `ansi_parse_error=4` in the parent;
subsequent numeric CSI queries were rejected until a reset. Separately, a private
mode list such as `CSI ?6;3h` could commit origin mode before discovering that the
native width owner refused the current screen layout. These are maintained
application fixes, distinct from byte recovery of the original program.

The OMF escape decoder now clears the previous parse error when a fresh CSI
starts. It retains the error for inspection between sequences and does not reset
the display, consume extra UART input or change the flat recovered module. A
477-byte flat assembly comparison remains identical to the preceding checkpoint.

The actual native width admission has been split into a read-only check and a
transaction-preparation wrapper. Attached mode-list preflight calls that same
check before any item in the list executes. It validates the real owner, geometry,
cursor, viewport and hardware state rather than introducing a separate height
rule. Rejected preflight writes only stack storage: no backup pointers, scratch
counts, video, row defaults or preceding mode items change. Accepted 25-row width
requests continue through the original transaction and rollback path. Larger-row
width switching itself remains unsupported.

## Validation boundaries

The [receipt](validation/aspect-large-recovery.json) binds exact parent images,
source-only rebuilds, checkers and immutable DOS captures. The fault matrix uses
profiles 4 and 6 at 25/28/43/50 physical rows with visible status:

- Partial CSI timeout returns normally, then keyboard input and fresh CPR/size
  queries work without RIS.
- Unsupported `?6;12h` lists fail atomically at every height. `?6;3h` refusal is
  tested at the three larger heights; supported 25-row width requests have their
  separate positive linked regression.
- Unsupported media-copy requests leave both printer sinks unowned.
- Escape during parser continuation returns typed cancellation, releases the
  child and restores normal keyboard/query handling.

The Escape event is scheduled twelve BIOS ticks after actual child EXEC. The
earlier 36-tick probe raced the continuation timeout and could open the native
abort-confirmation dialog instead; that observation was not a proven cancellation
defect and no confirmation policy was changed to make this test pass. Cooperative
window controls retain their existing 36-tick event.

The independent verifier checks every logical character and attribute, exact
typed exit, cursor, returned BIOS geometry and owner release. It also checks the
relocated 63,000-byte far-history ring's bounds, segment and captured content
across EXEC. Expected error messages derive from the fixed runner vocabulary and
the parent's error path, not from snapshots copied into expected output.

These are actual DOS parent/child sessions over an owned synthetic serial peer,
plus linked CPU tests whose hardware boundaries are modeled. They are not real
DCD transitions, Enigma/Synchronet acceptance or physical Boca/SPA2102 tests.
Same-process carrier/reconnect and in-flight transfer composition at larger
heights remain next. Normal line controls, other fixed-height modal owners,
broader ASPECT services and the full application parity inventory remain open.

No diagnostic image is packaged for installation. The selected deployment package,
physical DOS files, installed SynthModem service and private connection settings
are unchanged. The ordinary candidate retains DS=SS with 65,120 near bytes and a
65,450-byte resident code segment; diagnostic parents use 65,476 resident bytes.
Every code segment remains below 64 KiB. The attached child is unchanged.
