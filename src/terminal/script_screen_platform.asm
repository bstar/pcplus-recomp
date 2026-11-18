; Maintained parent adapters for the recovered local ASPECT screen services.
; All public entries are NEAR in ASPECT_CODE, DS=SS and DF=0. The caller owns
; admission, captured scope, geometry and transaction retirement. These helpers
; do not poll UART/keyboard, feed the parser, acquire snapshots or write history.
; Native RETn and register interfaces are retained; no GET cursor clamp here.
BITS 16
CPU 8086

SEGMENT _TEXT public class=CODE use16
extern terminal_clear_home,terminal_control_home,attributes_reset
extern ui_read_byte,text_write_char
global terminal_screen_resident_begin,terminal_screen_resident_end
terminal_screen_resident_begin:
screen_clear_resident:
 call terminal_clear_home
 retf
screen_home_resident:
 call terminal_control_home
 retf
screen_reset_resident:
 call attributes_reset
 retf
; Register arguments keep these resident bridges small; native dependencies
; consume the copied words and return directly to the matching RETF.
screen_read_resident:
 push ax
 call ui_read_byte
 retf
screen_write_resident:
 push dx
 push ax
 call text_write_char
 retf
terminal_screen_resident_end:

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern attribute_screen_set_cursor_far,attributes_normal_value
extern terminal_screen_native_scroll,terminal_screen_native_frame
global terminal_screen_scroll,terminal_screen_draw_box
global terminal_screen_clear_home,terminal_screen_set_cursor
global terminal_screen_reset_attribute,terminal_screen_read_attribute
global terminal_screen_write_attribute,terminal_screen_home

; Stack attribute,bottom/right,top/left,count; exact 6EDC kernel, RET8.
terminal_screen_scroll:
 jmp terminal_screen_native_scroll

; Stack attribute,bottom/right,top/left, RET6. Native 6FEC takes a fourth
; near glyph pointer. Put the eight bytes on the same DS=SS stack, so the
; native reader needs neither a foreign DS nor additional near DATA.
;
; This profile uses the verified original startup frame: DS3352=1B7A,
; DS1B7A=C9 CD BB BA BC CD C8 BA. Runtime frame selection is not claimed.
; Source: original6401ccfd, DATA filebase25950, offsets28CA2 and274CA.
terminal_screen_draw_box:
 push bp
 mov bp,sp
 sub sp,8
 mov word [bp-8],0xcdc9
 mov word [bp-6],0xbabb
 mov word [bp-4],0xcdbc
 mov word [bp-2],0xbac8
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 lea ax,[bp-8]
 push ax
 call terminal_screen_native_frame
 mov sp,bp
 pop bp
 ret 6

terminal_screen_clear_home:
 call far screen_clear_resident
 ret

; AX=row, DX=logical column; the native cursor handles viewport transitions.
terminal_screen_set_cursor:
 call far attribute_screen_set_cursor_far
 ret

; AX=new full normal WORD. CLEAR's native byte reader owns input semantics.
terminal_screen_reset_attribute:
 mov [attributes_normal_value],ax
 call far screen_reset_resident
 ret

; Stack physical video-byte offset, RET2, AX=zero-extended byte.
terminal_screen_read_attribute:
 mov bx,sp
 mov ax,[bx+2]
 call far screen_read_resident
 ret 2

; Stack physical video-byte offset,value, RET4. Only low value byte is stored.
terminal_screen_write_attribute:
 mov bx,sp
 mov ax,[bx+2]
 mov dx,[bx+4]
 call far screen_write_resident
 ret 4

; Exact 1F56, including conditional attribute-boundary adjustment. CLEAR instead
; homes to csi_origin_row through the distinct 24E2 service above.
terminal_screen_home:
 call far screen_home_resident
 ret
