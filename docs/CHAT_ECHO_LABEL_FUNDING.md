# Native echo memory gate restored

`--code-label-offsets`, combined with the optional echo build, restores the
previous479408-byte foreground allocation budget and passes actual DOS8086
nested-ASPECT acceptance with the unchanged interpreter. **This closes the
measured echo memory gate; foreground TEXT shortcuts remain unbound.**

The parent is457ebb171b564d7548cd1a27ba58e6b68e7dc8b1b3cc877e6efd7257fd280a82.
It retains API0103 module5b6892e7…d45622, the original splash/version annotation,
8192-byte application stack,512-byte interpreter heap-growth policy, all six
stream buffers and the existing history/display/workspace capacities.

## Representation changes

The command browser and reference put all their immutable labels in the same
code bank as their readers. Their item tables can therefore store explicit
code-based offsets instead of repeating a segment word for every label pointer.
The browser also stores its bounded category/letter fields as unsigned bytes;
the key remains a word. The reference structure removes padding between items.
Compile-time assertions require8-byte browser items and9-byte reference items.

Every original label, help paragraph, key, category, action and navigation route
is retained. Conversions to far pointers still happen at the existing text
reader boundaries. This is explicit code-segment addressing, not an ordinary
near pointer that would read labels from DS. The optional flag requires the
packed original-reference build. Without it, the existing full-pointer layouts
remain available as a control.

The echo scope also reuses AX for identical0/1 state stores. Admission guarantees
that the wait-active word is zero before it is incremented. Saved cancellation
and timeout words still restore on exit; nested wait behavior is unchanged.

| Measurement | Full-pointer control | Compact-label parent |
| --- | ---: | ---: |
| Minimum allocation | 479872 | 479408 |
| Resident CS | 65368 | 65368 |
| Near DS=SS | 65504 | 65504 |
| Browser object code/constants | 12712 | 12453 |
| Reference object code/constants | 3409 | 3206 |
| Reference code bank | 16121 | 15659 |
| Echo code bank | 808 | 808 |

The table representation saves462 object bytes and464 allocated bytes after
linker alignment. Together with the scope-store changes, this recovers480
allocation bytes from the prior partial-funding image, and960 from the initial
unfunded echo image. The result equals the earlier foreground budget and is16
bytes above the preceding timing image. These observations do not characterize
every possible DOS memory layout.

## Verification

Both parent variants are built from the same current source and128-pair text
dictionary. Their1146 complete4000-byte browser/help/search/reference frames,
return values and action/owner states match exactly. This includes all five
category labels and the original39-command reference. Actual DOS8086 additionally
launches the external editor through both the reference and browser, preserving
the full frame, cursor, local parameters, child command tail/CWD, and subsequent
UART/parser/keyboard behavior.

The compact parent passes all26 nested-ASPECT checks: three NOCLEAR DOS children,
six held streams, missing-file recovery, files and exact viewport restoration.
The full-pointer control, differing only in the representation flag, fails the
child/stream/file/viewport checks under the same test and interpreter. That
negative report remains explicit. The interpreter rebuilt from current source
is byte-identical cbdee194; its authored help is unchanged.

All six native echo/CSI/C1/IRQ/wait/cancellation/admission CPU groups pass,
including nested original CSI-M and stopped-clock return. Ordinary DOS8086 Chat
entry/input/RX/Escape and held-prefix/CPR return also pass. These supplied-scope
echo checks do not prove live TEXT key scheduling or busy-key cancellation.

Synchronet passes25 real proxy/editor checks including ASPECT login and graphics
viewer return; its observer and key helper use386/UMB. Enigma passes16 real
carrier-loss/cleanup/redial/finish checks with two script logins, an exact65539-byte
retry, unchanged fixture PRM and no saved post. The established150-second retry
allowance is unchanged. An independent wire/CRC/control audit accompanies that
run. These BBS workflows leave Chat inactive; they are software loopback checks,
not Boca/SPA2102/SIP/audio/physical acceptance.

A fresh3645-file public-source export without analysis, originals, private
configuration, prior objects or ancestor Git reproduces the exact parent/module/
header and repeats the six echo CPU groups. The same export separately rebuilds
the exact cbdee194 interpreter and authored help. Disabling both new echo/table
features reproduces5ecf8774…092846 exactly.

An initial build correctly rejected a stale reference-source size-profile hash.
The compact ROW macro initially cut across the help generator's declaration
boundary; retaining the original first ROW declaration restores that extraction
without changing help bytes. Those failed builds are retained and not accepted.

The previous [partial-funding receipt](validation/chat-echo-size.json) also had
an incorrect recorded resident-CS value. The exact067cfdf5 map shows65368,
not65464; its allocation, executable identity and report bindings are unchanged.
That metadata has been corrected.

Next keep foreground TEXT scheduling primarily inside the existing loadable
module, initialize/synchronize local echo and presentation state, and verify
all ten keys with pre-read/RX fairness and real busy-key cancellation. Help,
Alt-Z/send-mode, broad Chat fault/geometry/sustained traffic, packaging/deployment,
hardware and full original parity remain open. The selected/installed package,
private call history/settings and production bridge/network are unchanged.

See the [receipt](validation/chat-echo-label-funding.json),
[echo scope](CHAT_ECHO_OWNER.md) and [full inventory](FEATURES.md).
