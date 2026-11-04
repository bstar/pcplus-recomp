; C far-cdecl bridges to the unchanged resident cursor/scroll services.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern scroll_up,screen_set_cursor
extern terminal_reset_resize_rows_far
global terminal_status_scroll_far,terminal_status_cursor_far,terminal_status_defaults_far
terminal_status_scroll_far:
 call scroll_up
 retf
terminal_status_cursor_far:
 push bp
 mov bp,sp
 mov ax,[bp+6]
 mov dx,[bp+8]
 call screen_set_cursor
 pop bp
 retf
terminal_status_defaults_far:
 push bp
 mov bp,sp
 mov ax,[bp+6]
 call far terminal_reset_resize_rows_far
 pop bp
 retf
