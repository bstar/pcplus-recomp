; Retained file/path code bank and DOS error notices. DS=SS is restored.
BITS 16
CPU 8086
SEGMENT FILE_CODE public align=16 class=FARCODE use16
GROUP FILE_GROUP FILE_CODE
extern _path_session_begin,_path_session_restore
global terminal_path_begin,terminal_path_restore
terminal_path_begin:
 call far _path_session_begin
 or ax,ax
 jz .done
 push ax
 push ds
 push cs
 pop ds
 mov dx,begin_failed
 mov ah,9
 int 21h
 pop ds
 pop ax
.done:
 retf
terminal_path_restore:
 call far _path_session_restore
 or ax,ax
 jz .done
 push ax
 push ds
 push cs
 pop ds
 mov dx,restore_failed
 mov ah,9
 int 21h
 pop ds
 pop ax
.done:
 retf
begin_failed: db 'Starting directory could not be saved.',13,10,'$'
restore_failed: db 'Starting directory could not be restored.',13,10,'$'
