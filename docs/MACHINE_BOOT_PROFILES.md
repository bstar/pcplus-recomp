# Machine and boot-mode profiles

DOS now selects the physical machine first, then that machine's memory/mouse,
CD-ROM or network mode. The machine choices are GREENTREE, DTK, CHIPS, ENOS and
BAH. This selects CONFIG.SYS directives before device drivers load, instead of
trying to replace CONFIG.SYS from an already-running AUTOEXEC.BAT.

GREENTREE is the default machine. Its default mode remains Expanded memory +
Mouse. To reach the management FTP server choose **GREENTREE → Network
management (Ethernet / FTP)**. Backspace returns from a submenu to the machine
menu, per [Microsoft's DOS submenu documentation](https://jeffpar.github.io/kbarchive/kb/096/Q96556/).

## Files

Each machine has an independent directory under C:\BOOT: GREEN, DTK, CHIPS,
ENOS or BAH. Its editable source files are:

- CONFIG.SYS: that machine's DOS device/memory sections and mode labels.
- AUTOEXEC.BAT: its DOS initialization, retaining the original mode labels.
- SYSTEM.INI: its Windows driver configuration.
- WINSYS: optional matching Windows driver files copied when applying it.
- PROFILE.TXT: provenance and verification limits.

The original SCRIPTS\COMPS entries were AUTOEXEC files only. Their startup
commands were imported for all five machines; independent CONFIG.SYS files
were seeded from the current shared configuration and can now diverge.
GREENTREE uses its confirmed MMOUSE driver, acceleration6, and its installed
GD5422/GD5424 release1.50 Windows driver at640x480/256colours. Other machine
Windows profiles begin with standard VGA640x480/16colour display fallbacks;
their specific display drivers and sound configurations remain to be verified.
Do not describe those fallbacks as optimized hardware-specific installations.

The root CONFIG.SYS is generated from the five source CONFIG.SYS files; changing
a source CONFIG.SYS requires rebuilding/deploying the combined menu. Changes
to per-machine AUTOEXEC.BAT are read at the next selected boot without rebuilding.
The compiler supports the existing named mode sections and recursive INCLUDE
with validation; all machine menu identifiers remain at most eight characters.
It emits45 distinct choices from the current nine modes per machine.

The root AUTOEXEC.BAT is a stable dispatcher. ROUTE.BAT maps DOS's selected
menu identifier to MACHINE and the original CONFIG mode, then Windows settings
are selected before calling that machine's AUTOEXEC.BAT. Legacy mode identifiers
are accepted as GREENTREE for recovery during a partially switched boot menu.
The old CHOOSE.BAT now directs the user to the boot menu instead of overwriting
the new dispatcher with an old AUTOEXEC.

## Windows settings and drivers

WINSEL.BAT remembers which Windows profile is active in BOOT\WINCUR.BAT.
When changing machines, it saves the current Windows SYSTEM.INI back into the
outgoing machine's directory, copies the incoming WINSYS files if present,
and applies that machine's SYSTEM.INI. SYSBEFOR.INI holds the pre-switch copy.
WINLAST.INI records the last source applied. The same unchanged machine/source
leaves the live Windows settings untouched. An explicitly edited source is
applied on the next boot, with the current live settings backed up first.

Missing profiles and copy failures stop application startup with a visible
message. The owned five-byte ZERO.COM helper clears a preceding comparison
errorlevel before DOS COPY, which can preserve an earlier status in some shells.
Its generator specifies the full code: mov ax,4c00h; int21h. No original binary
is an input to the profile compiler.

Installed Windows binaries remain outside Git. Driver files sharing a filename
across different chipsets must be kept as matching sets in each WINSYS folder;
do not swap just a display.drv name while retaining another chipset's VDD.
Before rebuilding, pull the current remote profile sources: Windows settings
may have been saved there since the last local staging operation.

From the PCPlus repository, compile using the pinned environment:

```sh
./tools/dev --command python tools/machine-profiles/compile.py PROFILE_DIRECTORY OUTPUT_DIRECTORY --default GREEN
```

The generated CONFIG.SYS and AUTOEXEC.BAT go to C:\, ROUTE.BAT/WINSEL.BAT/ZERO.COM
to C:\BOOT, and CHOOSE.BAT to C:\. Read back and verify each replacement, keeping
the prior menu until its successor and source files are fully staged.

## Validation and recovery

Validation covered all45 routing pairs, Windows save/restore across machine
switches, same-profile source edits, and missing-profile refusal. Two isolated
boots using the original DOS kernel selected GREEN EM and CHIPS N, loaded
EMM386 and dispatched the correct profile. Test fixtures replaced hardware
startup commands; these tests do not establish real hardware compatibility
on the four other machines or Windows rendering success.

Installation read-back is recorded privately in build/machine-profiles-01.
The previous root CONFIG.SYS, AUTOEXEC.BAT and CHOOSE.BAT are backed up on the
machine at C:\BOOT\MACHBK01. To restore them from DOS:

```dos
C:\BOOT\OLDMENU.BAT
```

Then reboot. The installation itself preserves the current live Windows files
and PCPlus configuration. After Dark remains disabled following its reported
activation crash. The NIC/modem IRQ5 sharing still requires separate network
and modem boots; this menu does not make simultaneous use safe.
