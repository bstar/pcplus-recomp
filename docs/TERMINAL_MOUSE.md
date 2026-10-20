# Selectable terminal mouse integration

The terminal can now run the recovered mouse producer and native keyboard
consumer together with the maintained DOS owner. This is a selectable source
build; the ordinary terminal and the other26 preceding application products
remain byte-identical. [Acceptance evidence](validation/terminal-mouse.json)
separates application execution from the earlier [bank component](MOUSE_BANK.md)
and [current component regressions](validation/mouse-bank-terminal-regression.json).

```sh
./tools/build terminal-mouse
./tools/build test-terminal-mouse
./tools/build test-terminal-mouse-source
./tools/build test-terminal-mouse-unwind
```

The executable is `build/terminal-mouse/TERMINAL.EXE`. Use its existing DOS
command line, for example `TERMINAL @PCPLUS.PRM`. An explicit2.01 PRM supplies
the measured04E4/04E6 X/Y scales; both must be1..999. A command line without a
PRM uses source-owned8/8 scales. These are maintained fallback choices, not a
claim about original factory defaults. The original six direction/Enter/Escape
event mappings are enabled. Missing INT33 or an unsupported storage API leaves
BIOS keyboard input available without acquiring a mouse owner.

## Lifecycle and memory

Assembly startup initializes the owner's C BSS explicitly before any exit path;
DOS does not promise cleared BSS. The real startup preference reader validates
the mouse fields from its existing single PRM read, after validating the other
plans and before committing them. Invalid scales fail before mouse/UART
acquisition, with a configuration error. No new PRM layout or second file read
is introduced. Startup directory browsing and `/S` setup precede acquisition.

The parent releases unused PSP memory using its existing trusted retained bound.
The DOS allocator then owns a separate guarded block; no CRT heap initialization
is needed. The selectable build has65372 resident code bytes and64848 near
data/stack bytes. Its2348-byte `MOUSE_CODE` segment has a distinct CS. Static
inspection verifies five C entry pairs, two resident keyboard services, native
queue aliases/defaults and retention of all code/data/far buffers.

The real native keyboard routines consume the producer's shared state. The
application does not substitute BIOS key injection or a test-only mouse path.
Before PROGRAM detaches the UART and executes a child, it suspends the mouse
owner. After the console acknowledgement, screen restoration and UART reclaim,
it resumes the owner. This also suspends the parent for the complete ASPECT
child lifetime, including a nested DOS/RUN/SHELL lease. The child and return
prompt remain keyboard-only; this does not add a mouse implementation to ASPECT.

Ordinary shutdown restores the exact opaque driver and native state and frees
the DOS block. If restoration/release remains quarantined, DOS4C cannot safely
free callback code. After the other application owners are cleaned up, the
terminal reports `Mouse restore failed; application memory retained.` and uses
DOS31 with exit14 and the checked retained extent. The parent sees status030Eh:
termination type3 and exit14. Memory intentionally remains allocated. There is
no general unload command; driver repair or restarting DOS may be necessary.

## Actual DOS evidence

An independent CRT observer launches the unmodified production executable using
only its ordinary command line. It snapshots all576 driver bytes, registers its
own prior callback, and checks the actual DOS MCB chain. Its timer/INT33 monitor
uses public driver calls and video cells; it neither reads product variables nor
supplies a replacement keyboard/renderer service.

Seven actual8086 DOS workflows pass69 independent assertions:

- Normal serial replies, ordinary keyboard input and exact driver restoration.
- Actual registered callback events navigate two menu rows and select Write
  screen. The resulting snapshot contains the live terminal, not menu text.
- A real PROGRAM child verifies that the parent callback is absent, changes
  driver state and registers/retires its own callback. Parent input then resumes.
- A timer deliberately clears INT33 while the native callback remains registered.
  The application returns030Eh with a retained owner and correct MCB extent.
  The observer then invokes that still-valid callback with foreign DS, retires
  it, restores the original driver and reclaims the controlled retained blocks.
- Invalid X scale rejects before dialing or callback registration.
- A controlled absent vector preserves keyboard/serial operation.
- A controlled unsupported state-size response preserves keyboard/serial
  operation without registering a product callback.

The repair/reclamation in the quarantine case belongs only to the observer;
the production program does not silently call an unknown replacement driver.

The linked production policy adds17 cases for poisoned BSS, far/cdecl staging,
transactional PRM rejection, invalid parent bounds, resize/allocation errors,
BIOS fallback and retained-memory boundaries. These declare DOS/driver errors
as modeled boundaries; the actual quarantine proof above is separate.

With the selectable capability7 parent,89 actual DOS cases cover all22 unwind
boundaries under DIV, foreign-DS DIV, typed abort and native longjmp, plus the
child-divide control. Three port/flow regressions bring that total to92. They
verify ordinary DOS return, parent resources, VM reuse and UART/video/file
recovery; they are not an exhaustive fault/flow cross-product or per-boundary
opaque mouse-driver comparison. Existing owner variants also retain244 linked
cases and130 actual DOS assertions. Fresh source trees reproduce29 application
products and the three component variants without originals or prior objects.

## ENiGMA and remaining work

The selectable terminal passes20 checks through the isolated owned search/index/
details route: actual DOS source compilation/login, all six NFO navigation keys,
paging, empty search, return stack and byte conservation with client writes
paced20ms apart. The synthetic fixture supplies explicit8/4 PRM scales. Select
it with `enigma_search_dos.py --mouse-terminal`; the default remains unchanged.
This uses the separate decoder candidate and generated catalog. It changes
nothing in the live board and makes no TCP receive-boundary or physical-modem
guarantee. See [ENiGMA acceptance](ENIGMA_COMPATIBILITY.md).

Remaining work includes startup-directory mouse input, return-prompt mouse
acknowledgement, live PRM settings UI/adoption, ASPECT's own mouse services,
other geometries and original window/macro/error services. Physical mouse and
RS-232 modem testing, other DOS kernels and arbitrary driver/kernel corruption
are unverified. The complete F01–F16 application gates remain open.
