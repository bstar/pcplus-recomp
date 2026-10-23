# Capturing and projecting a terminal session

The optional session-projection build joins actual-session capture to PRM
projection through a far-callable terminal API. It handles inactive modem
settings explicitly and keeps working storage on the existing stack. No near
data is added. KEY kind2 remains disabled; no returned helper settings apply.

Build with `./tools/dev --command make session-projection`. The normal product is
`build/terminal-directory-keys-process-bank-session-capture-projection/TERMINAL.EXE`.
The API `terminal_session_project(baseline, output)` is declared in
`src/terminal/session_projection.h`. It requires the guarded foreground CPU and
owner context described in [session capture](SESSION_CAPTURE.md). The caller
supplies a disjoint opaque baseline with established identity/version/lifetime.
The API does not read a file or prove that its baseline matches the session.
The optional [retained-baseline build](SESSION_BASELINE.md) now provides
`terminal_session_project_bound`, sourcing exact accepted startup/live-setup
bytes from far storage instead of requiring a separate caller baseline.

## Group policy

MODEM target sessions and MODEM directory entries supply an active modem plan.
Serial-only sessions and DIRECT entries pass an explicit inactive group to
`prm_project_session`. Contradictory selectors, invalid directory context or
mode/entry mismatches reject before output publication.

An inactive modem's private baseline fields remain byte-identical, including
invalid or unterminated values that startup deliberately never used. They are
not presented as valid active settings. The serial plan still supplies shared
pause/delay fields; current line BREAK projects independently. For an active
modem, the existing validator runs and shared serial/modem conflicts reject
atomically. No normalization makes incompatible active values representable.

The existing all-active `prm_project_active` retains NULL rejection and output
behavior. The session interface permits only its modem input to be NULL. Other
objects remain required, disjoint and nonwrapping. Opaque bytes and string tails
remain preserved. This covers the supported subset, not every native PRM field.

## Implementation and evidence

The optional [live sound/mouse projection](SESSION_CONTROLS.md) now augments this
path with validated active sound policy and accepted mouse preferences. It
preserves raw nonzero sound words and adds no extra PRM frame. Its flag leaves
the older session/register products' executable behavior unchanged.

The projector executes in HOOK_CODE. Explicit bridges reach resident serial/modem
decoders and CONFIG_CODE transfer validators; memory services retain their
register ABI. A code-resident nine-rate table avoids the nearly full DGROUP.
The normal product has 702 near-code bytes free, unchanged 65,520-byte data/stack
usage and a 1,983-byte HOOK_CODE bank.

54 linked cases execute capture, group admission, all bridges and decoders,
and atomic projection without substituting functions. Thirty-six full-image
cases cover all nine DTE rates across four session configurations. Other cases
cover inactive corrupt private fields, active conflicts, invalid settings/policies
and pointers. Hooks reject interrupt/port IO; active globals and baseline stay
intact. The standalone 8086 DOS suite passes 2,688 checks, retaining the preceding
2,660 checks. Independent 1,264-byte oracles check both active and inactive images;
a fresh link reproduces the diagnostic executable.

Five actual 8086 DOS runs use an explicit diagnostic terminal. Its source probe
calls the production API after real startup/import/CLI/directory selection,
before mouse/UART acquisition. Serial, MODEM, directory MODEM, directory DIRECT
and serial with invalid inactive private fields produce exact expected images.
Input files and 42-byte hardware samples stay unchanged. The normal product
contains neither that probe entry nor fixture filenames. These are startup
projection checks, not online helper handoff tests.

The normal product also passes a COM2 directory-selected ASPECT execution and
serial handback workflow. All three preceding directory terminal variants rebuild
to identical bytes. These checks exercise coexistence; no HOOK helper is scheduled.

An empty tree with 681 source files reproduces six products: normal and diagnostic
terminals, ASPECT, DOS compiler, help resource and settings editor. An initial
link exposed a trailing-underscore mismatch in register wrappers; explicit wrappers
fixed it before execution. A negative linked fixture initially expected a modem
error while also creating an earlier shared-delay conflict; it now isolates the
intended failure.

The [independent receipt](validation/session-projection.json) binds current
sources, exact object imports, normal/probe separation, raw DOS images and
hardware samples, COM2 handback and the six-product source proof.

Next: integrate the retained baseline with the helper owner, cover native fields, establish
register lifetime and ASPECT handback, and route HOOK through the guarded PROGRAM
owner. Returned commit, combined exit/trap ownership, online BBS tests and
physical hardware remain open.
