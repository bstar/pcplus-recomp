; Admitted ANSI control behavior recovered from PCPlus2.01 resident ENQ/EOT/GS.
; See docs/C0_CONTROLS.md. No original bytes are an application build input.
BITS 16
CPU 8086
SEGMENT _TEXT public align=1 class=CODE use16
extern render_character,terminal_enqueue_al
global terminal_c0_render_far,terminal_c0_transmit_far
; AX carries one byte. Native render is caller-cleaned; preserve AX in this
; maintained bridge. Its native BP/SI/DI behavior and DS=SS requirement remain.
terminal_c0_render_far:
 push ax
 call render_character
 pop ax
 retf
terminal_c0_transmit_far:
 call terminal_enqueue_al
 retf

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern attributes_monochrome,terminal_newline_mode_9020
extern screen_cursor_column,screen_cursor_row,terminal_aspect_active
extern attribute_screen_cursor_left_far,terminal_abort
global terminal_c0_enquiry_far,terminal_c0_eot_far,terminal_c0_gs_far
; Original0e7c..0edd: legacy9020 emits1F,column,row; otherwise mode0 displays
; ENQ only in the ANSI glyph policy. Configured answerback modes1/2 are not
; imported or implemented here and retain an explicit unsupported boundary.
terminal_c0_enquiry_far:
 cmp word [terminal_newline_mode_9020],0
 jne .report
 cmp word [terminal_c0_enquiry_mode],0
 jne .unsupported
 mov ax,5
 jmp c0_glyph
.report:
 mov ax,0x1f
 call far terminal_c0_transmit_far
 mov ax,[screen_cursor_column]
 call far terminal_c0_transmit_far
 mov ax,[screen_cursor_row]
 call far terminal_c0_transmit_far
 retf
.unsupported:
 mov ax,0x0e7c
 jmp far terminal_abort

; Original4cd7 tests script-active or remote-request-disabled before its
; default glyph tail. Do not enable the original remote command evaluator.
terminal_c0_eot_far:
 cmp word [terminal_aspect_active],0
 jne .glyph
 cmp word [terminal_c0_remote_enabled],0
 je .glyph
 mov ax,0x4cd7
 jmp far terminal_abort
.glyph:
 mov ax,4
c0_glyph:
 cmp word [attributes_monochrome],0
 je .done
 call far terminal_c0_render_far
.done:
 retf

; Original1292..12ae: the normal ANSI policy invokes the native cursor-left
; service. The legacy9020 escape service remains an explicit missing branch.
terminal_c0_gs_far:
 cmp word [terminal_newline_mode_9020],0
 jne .unsupported
 cmp word [attributes_monochrome],0
 je .done
 call far attribute_screen_cursor_left_far
.done:
 retf
.unsupported:
 mov ax,0x1292
 jmp far terminal_abort

SEGMENT _DATA public class=DATA use16
; Source-owned defaults. No PRM field or command can enable these modes yet.
global terminal_c0_enquiry_mode,terminal_c0_remote_enabled
terminal_c0_enquiry_mode: dw 0
terminal_c0_remote_enabled: dw 0
