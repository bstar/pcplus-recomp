; Maintained register adapters for the recovered callee-cleaned stack ABI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern text_write_cell,text_write_char,text_write_packed,text_fill_cells,text_write_bios
global text_put_cell,text_put_char,text_put_packed,text_fill,text_put_bios
; AX byte offset, DX attribute, CX character.
text_put_cell:
 push cx
 push dx
 push ax
 call text_write_cell
 ret
; AX byte offset, CX character; leave the video attribute unchanged.
text_put_char:
 push cx
 push ax
 call text_write_char
 ret
; AX byte offset, CX original packed form (character high, attribute low).
text_put_packed:
 push cx
 push ax
 call text_write_packed
 ret
; AX byte offset, DX count, CX original packed form.
text_fill:
 push cx
 push ax
 push dx
 call text_fill_cells
 ret
; CX character, DX attribute; BIOS page is caller's attribute high byte.
text_put_bios:
 push cx
 push dx
 call text_write_bios
 ret
