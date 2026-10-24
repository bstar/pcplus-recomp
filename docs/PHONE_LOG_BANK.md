# Telephone logger code bank

The [event queue](PHONE_LOG_QUEUE.md), formatter, clock and checked append
backend now have a dedicated `PHONE_LOG_CODE` bank. The experimental terminal
builder can link it without reducing compiler/VM stacks, protocol limits or
screen buffers. It does not yet produce a live telephone log: startup settings,
path selection, modem events, shared file reservations and poll scheduling
remain unconnected.

The standard full terminal still rebuilds to SHA256
`2978657cb75ac29067796c98d81ff253b91eee96b995924d266d05bdfbae471c`.
The bank-linked Special Edition is
`build/terminal-phone-log-bank-4a10b5574901/TERMINAL.EXE`, SHA256
`e716e88dd9fb9c233cbb67cb88a2906d0c098e45d82abc7206d51f0b8d355ea7`.
Its code bank is 6,058 bytes, its near data/stack is 64,416 bytes with
1,120 bytes spare, and resident code is 65,498 bytes with 38 bytes spare.
Those margins still constrain the remaining application hooks.

## ABI and storage

Ten explicit far cdecl entries copy only their declared argument words into
the bank's near-C frames. Assembly application callers can call these far
entries directly; no new resident near public-entry stubs are needed. The
ordinary DS=SS convention remains in force throughout.

Seven DOS/capture callbacks use the compiler's register ABI. Ten CRT/canonical
callbacks reuse existing CONFIG resident services through logger-local names.
The eighth new DOS callback needs a different frame: `_dos_write` takes a far
buffer, so its final near written-count pointer spills onto the stack and the
runtime consumes that word. The bank adapter retains the original spill, the
resident adapter copies it from BP+8 into the runtime call, and the bank return
consumes the original exactly once. Register-only forwarding was wrong here;
the short-write rollback DOS case exposed the bad frame. The corrected case
passes with the actual zero-byte truncate and subsequent explicit retry.

The bank build defines `PHONE_LOG_QUEUE_EXTERNAL` and supplies the exact
666-byte initialized owner in `phone_log_storage.asm`. `PHONE_DATA` is ordered
before near data, ahead of the uninitialized far screen buffers. The first
attempt used compiler-generated initialized FAR_DATA after those buffers,
which serialized them and failed the existing memory inspector. Explicit
storage fixes that without weakening the inspector or shrinking the buffers.
Near/far standalone builds retain their original C-owned storage and are
retested separately.

The memory inspector checks the actual linked entry frames, near/far targets,
all eighteen callback relocations, the special DOS spill adapter, queue cookie,
full queue extent and retained parent memory. The ordinary assembly glob
excludes these optional bank modules; they enter only through the bank builder.
Diagnostic-only near client entries and CONFIG substitutes never enter the
application build.

## Verification and limits

The [validation receipt](validation/phone-log-bank.json) records the exact
bank diagnostic/source rebuild, terminal memory inspection, 68 damaged-ABI
rejections and two actual8086 terminal runs. The bank diagnostic repeats all
nine queue/clock/PRM/file cases with314 assertions through the real far bridges. The clean rebuild
copies 24 declared files and reproduces its DOS executable and eleven objects
without originals, old objects or REA data. Compiler adaptation changes only
explicit EXTDEF names; THEADR normalization changes only the source filename.
Instructions, data, fixups and symbol indices remain unchanged.

Early full-terminal runtime attempts exposed test setup problems. The long
feature-chain mount path caused a DOSBox host buffer-overflow abort before the
application; no coredump was available, and there was no OOM evidence. The
shortened product path preserves the exact executable hash and avoids that
abort. The modem-only fixture also lacked valid 8/4 mouse scales, and the
Special Edition splash requires an Enter key before dialing. The dedicated
terminal harness now supplies both explicitly, using the ordinary program
without binary patches. Earlier failed attempts remain local and excluded
from accepted evidence.

```sh
./tools/build test-phone-log-bank
./tools/build test-phone-log-bank-source
./tools/dev --command python standalone/test_phone_log_bank_terminal.py \
  --terminal build/terminal-phone-log-bank-4a10b5574901 --label my-bank-run
```

Add `--phone-log-bank` to the established full-terminal builder options to
produce the experimental bank-linked application. A deterministic short suffix
keeps option combinations distinct without long DOSBox mount paths. It is not
the deployed card build. This checkpoint closes neither F07/F10 nor the full
application/hardware compatibility gates.

Next, bind saved PRM enable/path selection, capture all connection lifetimes
including nested ASPECT paths, and schedule accepted events with UART service.
The existing external reservation slot is used by the recorder; the logger
must coexist with it while protecting canonical identities against capture,
history, scripts and other writers. Queue-full, retry and recovery outcomes
need visible application handling before BBS/load/modem/card acceptance.
