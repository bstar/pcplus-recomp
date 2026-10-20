; Preserve each unguarded BIOS sequence byte-for-byte. Guarded parent waits
; return Escape after a trap requests cancellation, so local owners unwind.
%macro TERMINAL_WAIT_KEY 1
 %ifdef TERMINAL_TRAPS
  extern terminal_trap_key
  call far terminal_trap_key
 %else
  xor %1,%1
  int 0x16
 %endif
%endmacro
