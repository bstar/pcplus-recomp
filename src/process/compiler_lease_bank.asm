; Link-order markers bracket the actual compiled code bank.
BITS 16
CPU 8086
%ifdef BANK_START
%assign left BANK_PADDING
%assign part 0
%rep 6
%if left > 0
SEGMENT LEASE_PAD %+ part public align=16 class=LEASE_PAD use16
%assign chunk left
%if chunk > 65520
%assign chunk 65520
%endif
 resb chunk
%assign left left-chunk
%assign part part+1
%endif
%endrep
%if left > 0
%error bank padding exceeds fixture capacity
%endif
%ifdef COMPILER_LEASE_RETAINED
SEGMENT LEASE_BANK public align=16 class=LEASE_MODULE use16
%else
SEGMENT LEASE_BANK public align=16 class=LEASE_BANK use16
%endif
GROUP LEASE_BANK_GROUP LEASE_BANK
global _compiler_lease_bank_start
_compiler_lease_bank_start:
%else
%ifdef COMPILER_LEASE_RETAINED
SEGMENT LEASE_BANK public align=16 class=LEASE_MODULE use16
%else
SEGMENT LEASE_BANK public align=16 class=LEASE_BANK use16
%endif
GROUP LEASE_BANK_GROUP LEASE_BANK
global _compiler_lease_bank_end
_compiler_lease_bank_end:
%endif
