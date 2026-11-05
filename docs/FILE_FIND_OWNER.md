# Private DOS search owner

`src/filesystem/find_owner.c` and `find_kernel.asm` provide the maintained search
component for File Directory. It is not linked into TERMINAL yet. The new owner
uses the original DOS4E/4F enumeration family and DTA layout identified through
REA, with an explicit adaptation: each call saves the caller's current DTA,
installs a private DTA, performs one search, and restores the caller's DTA on
both success and error. The original helper leaves its shared DTA installed.

The 43-byte continuation buffer and owner/error words occupy FILE_CODE rather
than DGROUP. A separate linked diagnostic verifies that placement. The component
has no allocation or open file handle. The foreground DS=SS contract and register
preservation remain explicit at the assembly boundary. Interrupts are not
disabled around DOS calls; application admission and UART servicing still need
integration.

Begin validates a nonempty, terminated specification of at most67 bytes and an
8-bit attribute mask. It refuses a second active owner. Search errors are
latched until close, preventing a later Next from reusing invalid continuation.
Failures preserve the caller's output. Successful results publish bounded8.3
names, attributes, raw DOS date/time and the full32-bit size. Date formatting
belongs to the later presentation layer.

The later [File Directory frontend](FILE_DIRECTORY.md) extends the initial
63-character component limit to67, allowing its64-character field to append
`*.*` after a drive colon or backslash. The earlier receipt below retains the
original component checkpoint; the frontend receipt binds the current build.

## Verification

The [receipt](validation/file-find-owner.json) binds the exact diagnostic,
original-free source rebuild, actual DOS test and negative control.

The 253 actual DOS8086/FPU-disabled checks install an independent foreign DTA
and begin its own search using separate raw DOS endpoints. Across the new
owner's FindFirst/FindNext, they compare the foreign DTA pointer and all43 bytes,
then resume that original foreign search and require its next filename. They
also verify exact file size/date/time, directory attributes, invalid arguments,
busy-owner refusal, absent paths, missing files, unchanged outputs after errors,
and100close/reopen cycles. The foreign DTA and original caller DTA are restored
before the diagnostic exits.

An isolated copied diagnostic with only the restore-DTA interrupt replaced by
two NOP bytes fails the runtime checks and is rejected by the test harness.
The control never runs on the physical machine. An empty source export, with
no original executables or prebuilt objects, reproduces the accepted FIND.EXE
exactly in the pinned Nix environment.

The component does not establish complete File Directory behavior. The next
step is its serviced foreground window, native formatting and paging, protected
capture/printer/log resource admission, error acknowledgement and direct/menu
dispatch. Internal/configured viewers, external editor integration, online BBS
return, DOS6.22, hardware behavior and full feature parity remain open.
