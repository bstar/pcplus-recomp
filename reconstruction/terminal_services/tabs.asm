; Recovered PCPlus 2.01 terminal support instructions; see docs/TERMINAL_SERVICES.md.
BITS 16
CPU 8086
%ifdef TERMINAL_SERVICES_OMF
SEGMENT _TEXT public class=CODE use16
global csi_clear_tabs
extern terminal_tab_stops
extern screen_attribute_row_bytes
extern screen_cursor_column
%define short
%else
ORG 0x246c
%define terminal_tab_stops 0xce10
%define screen_attribute_row_bytes 0x325a
%define screen_cursor_column 0x399e
%endif
%include "encodings.inc"
csi_clear_tabs:
L_246c: push bp
L_246d: mov_load bp,sp
L_246f: push di
L_2470: push si
L_2471: mov dx,[bp+0x4]
L_2474: or_load dx,dx
L_2476: jz short L_24ac
L_2478: mov ax,0xfe
L_247b: mov bx,terminal_tab_stops
L_247e: mov cx,0x1e
L_2481: mov_load di,bx
L_2483: push ds
L_2484: pop es
L_2485: rep stosb
L_2487: dec dx
L_2488: jnz short L_24d4
L_248a: sub_load bx,bx
L_248c: cmp [screen_attribute_row_bytes],bx
L_2490: jz short L_24d4
L_2492: mov cl,0x3
L_2494: mov_load si,bx
L_2496: sar si,cl
L_2498: mov [si+terminal_tab_stops],bl
L_249c: add bx,0x8
L_249f: cmp bx,[screen_attribute_row_bytes]
L_24a3: jc short L_2492
L_24a5: pop si
L_24a6: pop di
L_24a7: mov_load sp,bp
L_24a9: pop bp
L_24aa: ret
L_24ab: nop
L_24ac: sub_load si,si
L_24ae: cmp byte [si+terminal_tab_stops],0xfe
L_24b3: jz short L_24d4
L_24b5: mov al,[screen_cursor_column]
L_24b8: cmp [si+terminal_tab_stops],al
L_24bc: jnz short L_24ce
L_24be: mov al,[si+(terminal_tab_stops+1)]
L_24c2: mov [si+terminal_tab_stops],al
L_24c6: inc si
L_24c7: cmp byte [si+terminal_tab_stops],0xfe
L_24cc: jnz short L_24be
L_24ce: inc si
L_24cf: cmp si,0x1e
L_24d2: jl short L_24ae
L_24d4: pop si
L_24d5: pop di
L_24d6: mov_load sp,bp
L_24d8: pop bp
L_24d9: ret
