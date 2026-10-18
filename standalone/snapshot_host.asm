; Memory-FILE/UI diagnostic boundaries. Real row selector/copy/video brackets.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern snapshot_copy_original,snapshot_row_original,snapshot_write_original
extern snapshot_keyboard_original
; C wrappers are diagnostic adapters, not claimed original instructions.
global _snapshot_copy_c,_snapshot_row_c,_snapshot_writer_c,_snapshot_keyboard_c
_snapshot_copy_c:
 push bp
 mov bp,sp
 push bx
 push es
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call snapshot_copy_original
 pop es
 pop bx
 pop bp
 ret
_snapshot_row_c:
 push bp
 mov bp,sp
 push bx
 push es
 push word [bp+6]
 push word [bp+4]
 call snapshot_row_original
 add sp,4
 pop es
 pop bx
 pop bp
 ret
_snapshot_writer_c:
 push bp
 mov bp,sp
 push bx
 push es
 push word [bp+4]
 call snapshot_write_original
 add sp,2
 pop es
 pop bx
 pop bp
 ret
_snapshot_keyboard_c:
 push bx
 push es
 call snapshot_keyboard_original
 pop es
 pop bx
 ret

global snapshot_open,snapshot_close,snapshot_puts,snapshot_prepare_screen
global snapshot_status,snapshot_error,snapshot_wait_key,snapshot_refresh,snapshot_keyboard_state
snapshot_open:
 inc word [fixture_open_calls]
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [fixture_last_filename],ax
 mov ax,[bp+6]
 mov [fixture_last_mode],ax
 pop bp
 mov ax,[fixture_open_result]
 ret
snapshot_close:
 inc word [fixture_close_calls]
 mov ax,[fixture_close_result]
 ret
snapshot_puts:
 push bp
 mov bp,sp
 push si
 push di
 mov si,[bp+4]
 mov di,[fixture_output_count]
 inc word [fixture_write_calls]
 cmp word [fixture_write_failure],0
 jne .failed
.loop:
 lodsb
 or al,al
 jz .done
 cmp di,4096
 jae .overflow
 mov [fixture_output+di],al
 inc di
 jmp .loop
.done:
 mov [fixture_output_count],di
 xor ax,ax
 jmp .return
.failed:
 mov ax,0xffff
.return:
 pop di
 pop si
 pop bp
 ret
.overflow:
 int3
 jmp .overflow
snapshot_prepare_screen:
 inc word [fixture_prepare_calls]
 ret
snapshot_status:
 inc word [fixture_status_calls]
 ret
snapshot_error:
 inc word [fixture_error_calls]
 ret
snapshot_wait_key:
 inc word [fixture_wait_calls]
 ret
snapshot_refresh:
 inc word [fixture_refresh_calls]
 ret
snapshot_keyboard_state:
 inc word [fixture_keyboard_calls]
 ret

SEGMENT _DATA public class=DATA use16
global snapshot_shadow_enabled,snapshot_shadow_columns,snapshot_shadow_offset,snapshot_shadow_segment
global snapshot_video_stride,snapshot_video_segment,snapshot_video_columns,snapshot_cga_status_port
global snapshot_rows,snapshot_special_row,snapshot_status_pointer
global _snapshot_shadow_enabled
_snapshot_shadow_enabled:
snapshot_shadow_enabled dw 1
global _snapshot_shadow_columns
_snapshot_shadow_columns:
snapshot_shadow_columns dw 5
global _snapshot_shadow_offset
_snapshot_shadow_offset:
snapshot_shadow_offset dw fixture_cells
global _snapshot_shadow_segment
_snapshot_shadow_segment:
snapshot_shadow_segment dw 0
global _snapshot_video_stride
_snapshot_video_stride:
snapshot_video_stride dw 10
global _snapshot_video_segment
_snapshot_video_segment:
snapshot_video_segment dw 0xb800
global _snapshot_video_columns
_snapshot_video_columns:
snapshot_video_columns dw 5
global _snapshot_cga_status_port
_snapshot_cga_status_port:
snapshot_cga_status_port dw 0
global _snapshot_rows
_snapshot_rows:
snapshot_rows dw 3
global _snapshot_special_row
_snapshot_special_row:
snapshot_special_row dw 2
global _snapshot_status_pointer
_snapshot_status_pointer:
snapshot_status_pointer dw fixture_status_text
global snapshot_append_mode,snapshot_filename,snapshot_newline,snapshot_error_text
global _snapshot_append_mode
_snapshot_append_mode:
snapshot_append_mode db 'ab',0
global _snapshot_filename
_snapshot_filename:
snapshot_filename db 'PCPLUS.SCR',0
global _snapshot_newline
_snapshot_newline:
snapshot_newline db 13,10,0
global _snapshot_error_text
_snapshot_error_text:
snapshot_error_text db 'Synthetic open error',0
global _fixture_status_text
_fixture_status_text:
fixture_status_text db 'Synthetic snapshot status',0
global fixture_cells,fixture_destination,fixture_output,fixture_output_count
global _fixture_cells
_fixture_cells:
fixture_cells dw 0x0720,0x1f41,0xff00,0x1742,0x0020
 times 5 dw 0x0720
 dw 0x075a,0x071a,0x0720,0x0720,0x0720
global _fixture_destination
_fixture_destination:
fixture_destination times 160 db 0
global fixture_open_calls,fixture_close_calls,fixture_write_calls,fixture_prepare_calls
global fixture_status_calls,fixture_error_calls,fixture_wait_calls,fixture_refresh_calls,fixture_keyboard_calls
global fixture_open_result,fixture_close_result,fixture_write_failure,fixture_last_filename,fixture_last_mode
global _fixture_open_calls
_fixture_open_calls:
fixture_open_calls dw 0
global _fixture_close_calls
_fixture_close_calls:
fixture_close_calls dw 0
global _fixture_write_calls
_fixture_write_calls:
fixture_write_calls dw 0
global _fixture_prepare_calls
_fixture_prepare_calls:
fixture_prepare_calls dw 0
global _fixture_status_calls
_fixture_status_calls:
fixture_status_calls dw 0
global _fixture_error_calls
_fixture_error_calls:
fixture_error_calls dw 0
global _fixture_wait_calls
_fixture_wait_calls:
fixture_wait_calls dw 0
global _fixture_refresh_calls
_fixture_refresh_calls:
fixture_refresh_calls dw 0
global _fixture_keyboard_calls
_fixture_keyboard_calls:
fixture_keyboard_calls dw 0
global _fixture_open_result
_fixture_open_result:
fixture_open_result dw 1
global _fixture_close_result
_fixture_close_result:
fixture_close_result dw 0
global _fixture_write_failure
_fixture_write_failure:
fixture_write_failure dw 0
global _fixture_last_filename
_fixture_last_filename:
fixture_last_filename dw 0
global _fixture_last_mode
_fixture_last_mode:
fixture_last_mode dw 0
global _fixture_output_count
_fixture_output_count:
fixture_output_count dw 0
global _fixture_output
_fixture_output:
fixture_output times 4096 db 0
