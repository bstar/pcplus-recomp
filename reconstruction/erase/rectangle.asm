; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global csi_service_2530
extern erase_scroll_up
extern erase_scroll_down
extern erase_far_fill
extern erase_far_move
extern erase_move_bytes
extern erase_lineflags_enabled
extern screen_line_flags
extern screen_attribute_row_bytes
extern screen_viewport_enabled
extern screen_viewport_left
extern screen_columns
extern screen_viewport_active
extern screen_viewport_right
extern erase_shadow_offset
extern erase_shadow_segment
%define short
%else
ORG 0x2530
%define erase_scroll_up 0x6edc
%define erase_scroll_down 0x6ec2
%define erase_far_fill 0x63fa
%define erase_far_move 0x6412
%define erase_move_bytes 0x85b4
%define erase_lineflags_enabled 0x3260
%define screen_line_flags 0xcf86
%define screen_attribute_row_bytes 0x325a
%define screen_viewport_enabled 0xcdfa
%define screen_viewport_left 0xce2e
%define screen_columns 0x7a72
%define screen_viewport_active 0x3256
%define screen_viewport_right 0x7a7e
%define erase_shadow_offset 0x5dea
%define erase_shadow_segment 0x5dec
%endif
%include "encodings.inc"
csi_service_2530:
L_2530: push bp
L_2531: mov_load bp,sp
L_2533: sub sp,0x20
L_2536: push di
L_2537: push si
L_2538: mov word [bp-0x18],0x1
L_253d: mov al,[bp+0x9]
L_2540: sub_load ah,ah
L_2542: mov_load si,ax
L_2544: mov al,[bp+0x7]
L_2547: mov [bp-0xa],ax
L_254a: sub_load ax,si
L_254c: inc ax
L_254d: mov [bp-0x8],ax
L_2550: cmp word [erase_lineflags_enabled],0x0
L_2555: jz short L_25b4
L_2557: cmp [bp-0xa],si
L_255a: jz short L_25b4
L_255c: cmp word [bp+0xa],0x0
L_2560: jz short L_25a2
L_2562: mov word [bp-0x2],0x1
L_2567: mov dx,[bp-0xa]
L_256a: sub_load dx,si
L_256c: cmp word [bp+0xa],0x0
L_2570: jng short L_2580
L_2572: mov_load di,si
L_2574: lea cx,[si+0x1]
L_2577: mov_load ax,si
L_2579: add_load ax,dx
L_257b: mov [bp-0x4],ax
L_257e: jmp short L_2588
L_2580: mov_load cx,si
L_2582: mov [bp-0x4],si
L_2585: lea di,[si+0x1]
L_2588: push dx
L_2589: add cx,screen_line_flags
L_258d: push cx
L_258e: add di,screen_line_flags
L_2592: push di
L_2593: call erase_move_bytes
L_2596: add sp,0x6
L_2599: mov dx,[bp-0x2]
L_259c: mov cx,[bp-0x4]
L_259f: jmp short L_25a6
L_25a1: nop
L_25a2: mov_load dx,ax
L_25a4: mov_load cx,si
L_25a6: sub_load ax,ax
L_25a8: mov_load bx,cx
L_25aa: mov_load cx,dx
L_25ac: lea di,[bx+screen_line_flags]
L_25b0: push ds
L_25b1: pop es
L_25b2: rep stosb
L_25b4: cmp word [screen_viewport_enabled],0x0
L_25b9: jnz short L_25be
L_25bb: jmp near L_27b6
L_25be: mov ax,[bp+0x4]
L_25c1: or ah,0x20
L_25c4: mov [bp-0x14],ax
L_25c7: mov word [bp-0x12],0x1
L_25cc: cmp [bp-0xa],si
L_25cf: jz short L_25d4
L_25d1: jmp near L_26ca
L_25d4: mov al,[bp+0x6]
L_25d7: mov_load bl,al
L_25d9: sub_load bh,bh
L_25db: mov al,[bp+0x8]
L_25de: sub_load ah,ah
L_25e0: mov [bp-0x10],ax
L_25e3: cmp ax,[screen_viewport_left]
L_25e7: jc short L_2600
L_25e9: mov ax,[screen_columns]
L_25ec: cmp [bp-0x10],ax
L_25ef: jnc short L_25f8
L_25f1: cmp word [screen_viewport_active],0x0
L_25f6: jnz short L_2600
L_25f8: mov word [bp-0x2],0x0
L_25fd: jmp short L_2605
L_25ff: nop
L_2600: mov word [bp-0x2],0x1
L_2605: cmp [screen_viewport_left],bx
L_2609: jna short L_2622
L_260b: mov ax,[screen_columns]
L_260e: cmp [bp-0x10],ax
L_2611: jc short L_261a
L_2613: cmp word [screen_viewport_active],0x0
L_2618: jz short L_2622
L_261a: mov word [bp-0x4],0x0
L_261f: jmp short L_2627
L_2621: nop
L_2622: mov word [bp-0x4],0x1
L_2627: mov ax,[screen_attribute_row_bytes]
L_262a: mul si
L_262c: add ax,[bp-0x10]
L_262f: mov [bp-0x6],ax
L_2632: cmp word [bp-0x2],0x0
L_2636: jz short L_2684
L_2638: mov [bp-0xe],si
L_263b: cmp word [bp-0x4],0x0
L_263f: jz short L_2684
L_2641: cmp word [screen_viewport_active],0x0
L_2646: jz short L_2668
L_2648: mov al,[screen_viewport_right]
L_264b: mov ah,[bp-0xa]
L_264e: mov [bp+0x6],ax
L_2651: mov ax,[screen_columns]
L_2654: sub ax,[bp-0x10]
L_2657: add [bp-0x6],ax
L_265a: mov_load ax,bx
L_265c: sub ax,[screen_columns]
L_2660: inc ax
L_2661: mov [bp-0xc],ax
L_2664: jmp near L_2780
L_2667: nop
L_2668: mov ah,[bp-0xe]
L_266b: sub_load al,al
L_266d: mov [bp+0x8],ax
L_2670: sub bl,[screen_viewport_left]
L_2674: mov_load al,bl
L_2676: mov ah,[bp-0xa]
L_2679: mov [bp+0x6],ax
L_267c: mov ax,[screen_viewport_left]
L_267f: sub ax,[bp-0x10]
L_2682: jmp short L_2661
L_2684: cmp word [bp-0x2],0x0
L_2688: jz short L_269a
L_268a: cmp word [screen_viewport_active],0x0
L_268f: jz short L_269a
L_2691: mov word [bp-0x12],0x0
L_2696: jmp near L_2780
L_2699: nop
L_269a: cmp word [bp-0x2],0x0
L_269e: jnz short L_26b8
L_26a0: cmp word [screen_viewport_active],0x0
L_26a5: jnz short L_26b8
L_26a7: mov word [bp-0x12],0x0
L_26ac: mov ax,[screen_viewport_left]
L_26af: sub [bp+0x8],ax
L_26b2: sub [bp+0x6],ax
L_26b5: jmp near L_2780
L_26b8: mov_load ax,bx
L_26ba: sub ax,[bp-0x10]
L_26bd: inc ax
L_26be: mov [bp-0xc],ax
L_26c1: mov word [bp-0x18],0x0
L_26c6: jmp near L_2780
L_26c9: nop
L_26ca: mov [bp-0xe],si
L_26cd: mov ax,[screen_viewport_left]
L_26d0: mov [bp-0xc],ax
L_26d3: mov_load ax,si
L_26d5: mul word [screen_attribute_row_bytes]
L_26d9: mov_load bx,ax
L_26db: cmp word [screen_viewport_active],0x0
L_26e0: jz short L_26e6
L_26e2: add bx,[screen_columns]
L_26e6: cmp word [bp+0xa],0x0
L_26ea: jz short L_2766
L_26ec: mov ax,[bp-0xa]
L_26ef: mul word [screen_attribute_row_bytes]
L_26f3: mov_load di,ax
L_26f5: cmp word [screen_viewport_active],0x0
L_26fa: jz short L_2700
L_26fc: add di,[screen_columns]
L_2700: cmp word [bp+0xa],0x0
L_2704: jng short L_2716
L_2706: mov [bp-0x4],bx
L_2709: mov ax,[screen_attribute_row_bytes]
L_270c: shl ax,1
L_270e: mov [bp-0x2],ax
L_2711: mov [bp-0x6],di
L_2714: jmp short L_2726
L_2716: mov [bp-0x4],di
L_2719: mov ax,[screen_attribute_row_bytes]
L_271c: shl ax,1
L_271e: neg ax
L_2720: mov [bp-0x2],ax
L_2723: mov [bp-0x6],bx
L_2726: mov ax,[bp-0x4]
L_2729: shl ax,1
L_272b: add ax,[erase_shadow_offset]
L_272f: mov dx,[erase_shadow_segment]
L_2733: mov_load si,ax
L_2735: mov [bp-0x1a],dx
L_2738: mov di,[bp-0x8]
L_273b: dec di
L_273c: jz short L_276f
L_273e: push word [bp-0x1a]
L_2741: push si
L_2742: mov_load ax,si
L_2744: mov dx,[bp-0x1a]
L_2747: add ax,[bp-0x2]
L_274a: push dx
L_274b: push ax
L_274c: push word [screen_viewport_left]
L_2750: mov [bp-0x20],ax
L_2753: mov [bp-0x1e],dx
L_2756: call erase_far_move
L_2759: mov ax,[bp-0x20]
L_275c: mov dx,[bp-0x1e]
L_275f: mov_load si,ax
L_2761: mov [bp-0x1a],dx
L_2764: jmp short L_273b
L_2766: mov [bp-0x6],bx
L_2769: mov ax,[bp-0x8]
L_276c: mov [bp-0x12],ax
L_276f: mov ah,[bp-0xe]
L_2772: sub_load al,al
L_2774: mov [bp+0x8],ax
L_2777: mov al,[screen_viewport_right]
L_277a: mov ah,[bp-0xa]
L_277d: mov [bp+0x6],ax
L_2780: mov ax,[bp-0x6]
L_2783: shl ax,1
L_2785: add ax,[erase_shadow_offset]
L_2789: mov dx,[erase_shadow_segment]
L_278d: mov_load si,ax
L_278f: mov [bp-0x1a],dx
L_2792: mov di,[bp-0x12]
L_2795: mov_load ax,di
L_2797: dec di
L_2798: or_load ax,ax
L_279a: jz short L_27b6
L_279c: push word [bp-0x1a]
L_279f: push si
L_27a0: push word [bp-0x14]
L_27a3: push word [bp-0xc]
L_27a6: call erase_far_fill
L_27a9: mov ax,[screen_attribute_row_bytes]
L_27ac: shl ax,1
L_27ae: add_load si,ax
L_27b0: mov ax,[bp-0x1a]
L_27b3: jmp short L_2795
L_27b5: nop
L_27b6: cmp word [bp-0x18],0x0
L_27ba: jz short L_27e1
L_27bc: mov si,[bp+0xa]
L_27bf: or_load si,si
L_27c1: jl short L_27d2
L_27c3: push si
L_27c4: push word [bp+0x8]
L_27c7: push word [bp+0x6]
L_27ca: push word [bp+0x4]
L_27cd: call erase_scroll_up
L_27d0: jmp short L_27e1
L_27d2: neg si
L_27d4: push si
L_27d5: push word [bp+0x8]
L_27d8: push word [bp+0x6]
L_27db: push word [bp+0x4]
L_27de: call erase_scroll_down
L_27e1: pop si
L_27e2: pop di
L_27e3: mov_load sp,bp
L_27e5: pop bp
L_27e6: ret word 0x8
