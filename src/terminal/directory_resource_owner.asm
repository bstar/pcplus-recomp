; Exact resident callbacks for the foreground directory resource-check owner.
BITS 16
CPU 8086
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
SEGMENT _TEXT public class=CODE use16
extern terminal_program_start,terminal_program_kind,terminal_build_keymap
global _directory_resources_program_queue,_directory_resources_defaults
_directory_resources_program_queue:
 mov ax,directory_resource_command
 call terminal_program_start
 or ax,ax
 jnz .done
 mov word [terminal_program_kind],6
.done:
 retf
_directory_resources_defaults:
 push bp
 mov bp,sp
 mov ax,[bp+6]
 call terminal_build_keymap
 pop bp
 retf
SEGMENT _DATA public class=DATA use16
directory_resource_command: db '[DIRECTORY]',0
global directory_resources_ready_notice,directory_resources_failed_notice
directory_resources_ready_notice: db 13,10,'KEY/KBD resources checked. Settings unchanged. Press any key.',0
directory_resources_failed_notice: db 13,10,'Could not prepare KEY/KBD resources. Settings unchanged. Press any key.',0
%endif
