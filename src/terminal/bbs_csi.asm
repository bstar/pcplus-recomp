; Maintained ECMA-48 CSI compatibility for modern BBS hosts, not original
; PCPlus code. Built only with --bbs-csi (TERMINAL_BBS_CSI); see docs/BBS_CSI.md.
; No DGROUP data.
;
; The recovered dispatcher (reconstruction/ansi/dispatch.asm) ends a sequence
; at the first byte the parameter reader does not collect. For a private
; prefix it does not know ('<', '=', or '?'/'>' after parameters), for ':' and
; for intermediates other than '"', '$' and "'", the rest of the sequence was
; then printed: SyncTERM's ESC[=255h left "255h" on screen. This routine
; consumes the remainder through its final byte (40h..7Eh), exactly as
; ECMA-48 5.4 defines a control sequence, and ignores it.
BITS 16
CPU 8086
extern ansi_next_byte,ansi_unread_byte,ansi_control_character

SEGMENT _TEXT public class=CODE use16
; BX = near service. The _arg form passes AX as one cdecl word argument.
bbs_csi_near_call:
 call bx
 retf
bbs_csi_near_call_arg:
 push ax
 call bx
 add sp,2
 retf

SEGMENT BBS_CSI_CODE public align=16 class=FARCODE use16
global csi_bbs_skip_far
; The dispatcher has already consumed the byte that ended parameter
; collection (it is ansi_command). Bounded: at most 64 further bytes.
csi_bbs_skip_far:
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 mov cx,64
.next:
 push cx
 mov bx,ansi_next_byte
 call far bbs_csi_near_call
 pop cx
 cmp ax,0xffff          ; receive timeout: abandon the sequence
 je .done
 cmp ax,0x1b            ; ESC starts a new sequence: put it back
 je .unread
 cmp ax,0x80            ; not a CSI byte: put it back for display
 jae .unread
 cmp ax,0x18            ; CAN and SUB cancel the sequence
 je .done
 cmp ax,0x1a
 je .done
 cmp ax,0x20            ; other C0 controls execute in place
 jae .graphic
 push cx
 mov bx,ansi_control_character
 call far bbs_csi_near_call_arg
 pop cx
 jmp short .more
.graphic:
 cmp ax,0x40            ; 20h..3Fh: parameter or intermediate byte
 jb .more
 cmp ax,0x7f            ; 40h..7Eh: final byte; DEL is ignored
 jb .done
.more:
 loop .next
 jmp short .done
.unread:
 mov bx,ansi_unread_byte
 call far bbs_csi_near_call
.done:
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 retf
