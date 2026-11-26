; Explicitly retained parent owner of the ASPECT REDIAL selection list in the
; exact compact form of src/aspect/redial_selection_store.asm: fifteen 5-byte
; tokens, then a WORD consumed-flag mask (bit i = slot i, bit 15 always 0).
; It lies outside every transient PCCONN extent and outlives module
; release/reload. The initial value is the native DGROUP state at DS:70B4:
; every slot empty with its flag set.
BITS 16
CPU 8086
%ifndef REDIAL_SELECTION_FLAT
; Class RETAINED_DATA is ordered before DGROUP: initialized, never trimmed.
SEGMENT REDIAL_STORAGE public align=16 class=RETAINED_DATA use16
global redial_selection_retained,redial_selection_retained_end
%endif
redial_selection_retained:
times 75 db 0
dw 0x7fff
redial_selection_retained_end:
