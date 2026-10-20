; Source-owned CRT/platform storage; native instruction sources stay unchanged.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern program_spawn_extension
extern _native_allocate,_native_release,_native_backup_alloc,_native_backup_free
extern _native_copy
global _native_spawn_extension,_native_child_divide
global program_service_92a8,program_service_92a4,program_service_860f
global program_service_85fc,program_service_9286
_native_spawn_extension: jmp program_spawn_extension
program_service_92a8: jmp _native_allocate
program_service_92a4: jmp _native_release
program_service_860f: jmp _native_backup_alloc
program_service_85fc: jmp _native_backup_free
program_service_9286: jmp _native_copy
; Child must never enter a parent's DS-dependent arithmetic recovery frame.
_native_child_divide:
 mov ax,0x4c0c
 sti
 int 0x21
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
global program_errno,program_dos_error,program_dos_major
global _native_crt_error,_native_dos_error,_native_dos_major
program_errno:
_native_crt_error: dw 0
; Environment/tail errors write a WORD here, while DOS mapping writes AL.
; Keep a full word; packing the DOS version into its high byte corrupts it.
program_dos_error:
_native_dos_error: dw 0
program_dos_major:
_native_dos_major: db 3
global program_pair_low,program_pair_high,program_exec_active
global _native_pair_low,_native_pair_high,_native_exec_active
program_pair_low:
_native_pair_low: dw 0
program_pair_high:
_native_pair_high: dw 0
program_exec_active:
_native_exec_active: dw 0
global program_overlay_gate,program_overlay_callback
program_overlay_gate: dw 0
program_overlay_callback: dw 0
global program_exec_block,program_exec_tail,program_exec_tail_segment
global program_exec_fcb1_segment,program_exec_fcb2_segment,program_fcb1,program_fcb2
program_exec_block: dw 0
program_exec_tail: dw 0
program_exec_tail_segment: dw 0
 dw program_fcb1
program_exec_fcb1_segment: dw 0
 dw program_fcb2
program_exec_fcb2_segment: dw 0
program_fcb1: times 37 db 0
program_fcb2: times 37 db 0
global program_batch_prefix,program_comspec_name2
program_batch_prefix: db '/c ',0
program_comspec_name2: db 'COMSPEC',0
; The Borland inherited-handle environment extension is disabled: these are
; source-built Watcom children, whose DOS handles are inherited by DOS EXEC.
global program_state_7b52,program_state_7b29,program_state_7b2a
global program_state_7b2b,program_state_7b00,program_heap_mode
program_state_7b52: dw 0
program_state_7b29: dw 0
program_state_7b2a: db 0
program_state_7b2b: db 0
program_state_7b00: db 0
program_heap_mode: dw 0
global program_state_e462,program_state_e45e,program_state_e460,_native_backup_extent
program_state_e462:
_native_backup_extent: dw 0
program_state_e45e: dw 0
program_state_e460: dw 0
%ifdef NATIVE_PROCESS_DIAGNOSTIC
global _runtime_arena
_runtime_arena: times 0x3aca db 0
%endif
