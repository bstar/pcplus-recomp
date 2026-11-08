; Dispatcher-facing C ABI, with original abort only after retired GET scopes.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _runtime_get_command_run,_runtime_get_command_ready,aspect_abort_recovered
global _runtime_get_command_execute
_runtime_get_command_execute:
 push bp
 mov bp,sp
 push word [bp+4]
 call _runtime_get_command_run
 add sp,2
 or ax,ax
 jz .return
 push ax
 call _runtime_get_command_ready
 or ax,ax
 pop ax
 jz .return
 mov sp,bp
 pop bp
 jmp aspect_abort_recovered
.return:
 mov sp,bp
 pop bp
 ret
