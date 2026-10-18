; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_send_telink
global metadata_at_e5db
global metadata_at_e5dd
global metadata_at_e5e0
global metadata_at_e5e1
global metadata_at_e5e2
global metadata_at_e5e5
global metadata_at_e5e8
global metadata_at_e5eb
global metadata_at_e5f0
global metadata_at_e5f3
global metadata_at_e5f5
global metadata_at_e5f7
global metadata_at_e5fa
global metadata_at_e5fb
global metadata_at_e5fe
global metadata_at_e5ff
global metadata_at_e602
global metadata_at_e605
global metadata_at_e608
global metadata_at_e60a
global metadata_at_e60c
global metadata_at_e60f
global metadata_at_e610
global metadata_at_e613
global metadata_at_e614
global metadata_at_e617
global metadata_at_e61a
global metadata_at_e61d
global metadata_at_e620
global metadata_at_e621
global metadata_at_e624
global metadata_at_e627
global metadata_at_e62a
global metadata_at_e62b
global metadata_at_e62e
global metadata_at_e633
global metadata_at_e635
global metadata_at_e637
global metadata_at_e63b
global metadata_at_e63c
global metadata_at_e63d
global metadata_at_e640
global metadata_at_e644
global metadata_at_e645
global metadata_at_e647
global metadata_at_e648
global metadata_at_e64b
global metadata_at_e64d
global metadata_at_e652
global metadata_at_e654
global metadata_at_e658
global metadata_at_e659
global metadata_at_e65a
global metadata_at_e65d
global metadata_at_e661
global metadata_at_e662
global metadata_at_e664
global metadata_at_e665
global metadata_at_e668
global metadata_at_e66a
global metadata_at_e66f
global metadata_at_e671
global metadata_at_e675
global metadata_at_e676
global metadata_at_e677
global metadata_at_e67a
global metadata_at_e67e
global metadata_at_e67f
global metadata_at_e681
global metadata_at_e682
global metadata_at_e685
global metadata_at_e687
global metadata_at_e68a
global metadata_at_e68f
global metadata_at_e692
global metadata_at_e695
global metadata_at_e698
global metadata_at_e69a
global metadata_at_e69d
global metadata_at_e69f
global metadata_at_e6a2
global metadata_at_e6a4
global metadata_at_e6a5
global metadata_at_e6a6
global metadata_at_e6a9
global metadata_at_e6ab
global metadata_at_e6ac
global metadata_at_e6ae
global metadata_at_e6b1
global metadata_at_e6b2
global metadata_at_e6b5
global metadata_at_e6b7
global metadata_at_e6ba
global metadata_at_e6be
global metadata_at_e6c0
global metadata_at_e6c2
global metadata_at_e6c5
global metadata_at_e6c8
global metadata_at_e6ca
global metadata_at_e6cc
global metadata_at_e6cf
global metadata_at_e6d2
global metadata_at_e6d4
global metadata_at_e6d7
global metadata_at_e6d8
global metadata_at_e6db
global metadata_at_e6dc
global metadata_at_e6de
global metadata_at_e6e1
global metadata_at_e6e4
global metadata_at_e6e7
global metadata_at_e6e8
global metadata_at_e6e9
global metadata_at_e6ec
global metadata_at_e6ee
global metadata_at_e6f0
global metadata_at_e6f2
global metadata_at_e6f4
global metadata_at_e6f6
global metadata_at_e6f8
global metadata_at_e6fa
global metadata_at_e6fc
global metadata_at_e6fe
global metadata_at_e701
global metadata_at_e704
global metadata_at_e707
global metadata_at_e709
global metadata_at_e70b
global metadata_at_e70e
global metadata_at_e710
global metadata_at_e711
global metadata_at_e712
global metadata_at_e715
global metadata_at_e717
global metadata_at_e718
global metadata_at_e71a
global metadata_at_e71b
global metadata_at_e71e
global metadata_at_e720
global metadata_at_e723
global metadata_at_e726
global metadata_at_e729
global metadata_at_e72a
global metadata_at_e72c
global metadata_at_e72f
global metadata_at_e731
global metadata_at_e732
global metadata_at_e735
global metadata_at_e738
global metadata_at_e739
global metadata_at_e73c
global metadata_at_e73f
global metadata_at_e741
global metadata_at_e744
global metadata_at_e748
global metadata_at_e74a
global metadata_at_e74d
global metadata_at_e74f
global metadata_at_e750
global metadata_at_e753
global metadata_at_e754
global metadata_at_e755
global metadata_at_e757
global metadata_at_e758
global metadata_at_e759
global metadata_at_e75a
global metadata_at_e75c
global metadata_at_e75d
global metadata_at_e75e
global metadata_at_e760
global metadata_at_e761
extern metadata_stat_file
extern metadata_basename
extern metadata_local_cancel
extern metadata_send_zero
extern metadata_carrier
extern metadata_identification
extern metadata_size_low
extern metadata_unwind
extern metadata_timed_byte
extern metadata_transmit_byte
extern metadata_time
extern metadata_date
extern metadata_checkpoint
extern receive_drain
%else
ORG 0xe5da
%define metadata_stat_file 0x3b56
%define metadata_basename 0x3ea4
%define metadata_local_cancel 0x3f4b
%define metadata_send_zero 0x40aa
%define metadata_carrier 0x4861
%define metadata_identification 0x7920
%define metadata_size_low 0x9006
%define metadata_unwind 0x9065
%define metadata_timed_byte 0xaad9
%define metadata_transmit_byte 0xab0b
%define metadata_time 0xcd3a
%define metadata_date 0xcd76
%define metadata_checkpoint 0xcd94
%define receive_drain 0xf03e
%endif
%include "encodings.inc"
metadata_send_telink: push bp
metadata_at_e5db: mov_load bp,sp
metadata_at_e5dd: sub sp,0x1a
metadata_at_e5e0: push di
metadata_at_e5e1: push si
metadata_at_e5e2: push word [bp+0x4]
metadata_at_e5e5: call metadata_stat_file
metadata_at_e5e8: add sp,0x2
metadata_at_e5eb: mov word [bp-0x8],0x0
metadata_at_e5f0: call metadata_local_cancel
metadata_at_e5f3: or_load ax,ax
metadata_at_e5f5: jz short metadata_at_e605
metadata_at_e5f7: mov ax,0x7
metadata_at_e5fa: push ax
metadata_at_e5fb: mov ax,metadata_checkpoint
metadata_at_e5fe: push ax
metadata_at_e5ff: call metadata_unwind
metadata_at_e602: add sp,0x4
metadata_at_e605: call metadata_carrier
metadata_at_e608: or_load ax,ax
metadata_at_e60a: jnz short metadata_at_e61a
metadata_at_e60c: mov ax,0xf
metadata_at_e60f: push ax
metadata_at_e610: mov ax,metadata_checkpoint
metadata_at_e613: push ax
metadata_at_e614: call metadata_unwind
metadata_at_e617: add sp,0x4
metadata_at_e61a: call receive_drain
metadata_at_e61d: mov ax,0x16
metadata_at_e620: push ax
metadata_at_e621: call metadata_transmit_byte
metadata_at_e624: call metadata_send_zero
metadata_at_e627: mov ax,0xff
metadata_at_e62a: push ax
metadata_at_e62b: call metadata_transmit_byte
metadata_at_e62e: mov word [bp-0x2],metadata_size_low
metadata_at_e633: sub_load si,si
metadata_at_e635: mov_load di,si
metadata_at_e637: mov al,[si+metadata_size_low]
metadata_at_e63b: cbw
metadata_at_e63c: push ax
metadata_at_e63d: call metadata_transmit_byte
metadata_at_e640: mov al,[si+metadata_size_low]
metadata_at_e644: cbw
metadata_at_e645: add_load di,ax
metadata_at_e647: inc si
metadata_at_e648: cmp si,0x4
metadata_at_e64b: jl short metadata_at_e637
metadata_at_e64d: mov word [bp-0x2],metadata_date
metadata_at_e652: sub_load si,si
metadata_at_e654: mov al,[si+metadata_date]
metadata_at_e658: cbw
metadata_at_e659: push ax
metadata_at_e65a: call metadata_transmit_byte
metadata_at_e65d: mov al,[si+metadata_date]
metadata_at_e661: cbw
metadata_at_e662: add_load di,ax
metadata_at_e664: inc si
metadata_at_e665: cmp si,0x2
metadata_at_e668: jl short metadata_at_e654
metadata_at_e66a: mov word [bp-0x2],metadata_time
metadata_at_e66f: sub_load si,si
metadata_at_e671: mov al,[si+metadata_time]
metadata_at_e675: cbw
metadata_at_e676: push ax
metadata_at_e677: call metadata_transmit_byte
metadata_at_e67a: mov al,[si+metadata_time]
metadata_at_e67e: cbw
metadata_at_e67f: add_load di,ax
metadata_at_e681: inc si
metadata_at_e682: cmp si,0x2
metadata_at_e685: jl short metadata_at_e671
metadata_at_e687: mov [bp-0x6],di
metadata_at_e68a: mov word [bp-0x4],0x0
metadata_at_e68f: push word [bp+0x4]
metadata_at_e692: call metadata_basename
metadata_at_e695: add sp,0x2
metadata_at_e698: mov_load si,ax
metadata_at_e69a: cmp byte [si],0x0
metadata_at_e69d: jz short metadata_at_e6ba
metadata_at_e69f: mov di,[bp-0x6]
metadata_at_e6a2: mov al,[si]
metadata_at_e6a4: cbw
metadata_at_e6a5: push ax
metadata_at_e6a6: call metadata_transmit_byte
metadata_at_e6a9: mov al,[si]
metadata_at_e6ab: cbw
metadata_at_e6ac: add_load di,ax
metadata_at_e6ae: inc word [bp-0x4]
metadata_at_e6b1: inc si
metadata_at_e6b2: cmp byte [si],0x0
metadata_at_e6b5: jnz short metadata_at_e6a2
metadata_at_e6b7: mov [bp-0x6],di
metadata_at_e6ba: cmp word [bp-0x4],0x10
metadata_at_e6be: jnl short metadata_at_e6de
metadata_at_e6c0: mov cl,0x5
metadata_at_e6c2: mov dx,0x10
metadata_at_e6c5: sub dx,[bp-0x4]
metadata_at_e6c8: mov_load ax,dx
metadata_at_e6ca: shl ax,cl
metadata_at_e6cc: add [bp-0x6],ax
metadata_at_e6cf: mov [bp-0x2],dx
metadata_at_e6d2: mov_load si,dx
metadata_at_e6d4: mov ax,0x20
metadata_at_e6d7: push ax
metadata_at_e6d8: call metadata_transmit_byte
metadata_at_e6db: dec si
metadata_at_e6dc: jnz short metadata_at_e6d4
metadata_at_e6de: call metadata_send_zero
metadata_at_e6e1: mov di,metadata_identification
metadata_at_e6e4: lea si,[bp-0x1a]
metadata_at_e6e7: push ds
metadata_at_e6e8: pop es
metadata_at_e6e9: mov cx,0xffff
metadata_at_e6ec: xor_load ax,ax
metadata_at_e6ee: repne scasb
metadata_at_e6f0: not cx
metadata_at_e6f2: sub_load di,cx
metadata_at_e6f4: xchg di,si
metadata_at_e6f6: shr cx,1
metadata_at_e6f8: rep movsw
metadata_at_e6fa: adc_load cx,cx
metadata_at_e6fc: rep movsb
metadata_at_e6fe: lea bx,[bp-0x1a]
metadata_at_e701: mov [bp-0x2],bx
metadata_at_e704: cmp byte [bx],0x0
metadata_at_e707: jz short metadata_at_e723
metadata_at_e709: mov_load si,bx
metadata_at_e70b: mov di,[bp-0x6]
metadata_at_e70e: mov al,[si]
metadata_at_e710: cbw
metadata_at_e711: push ax
metadata_at_e712: call metadata_transmit_byte
metadata_at_e715: mov al,[si]
metadata_at_e717: cbw
metadata_at_e718: add_load di,ax
metadata_at_e71a: inc si
metadata_at_e71b: cmp byte [si],0x0
metadata_at_e71e: jnz short metadata_at_e70e
metadata_at_e720: mov [bp-0x6],di
metadata_at_e723: mov si,0x57
metadata_at_e726: call metadata_send_zero
metadata_at_e729: dec si
metadata_at_e72a: jnz short metadata_at_e726
metadata_at_e72c: mov al,[bp-0x6]
metadata_at_e72f: sub_load ah,ah
metadata_at_e731: push ax
metadata_at_e732: call metadata_transmit_byte
metadata_at_e735: mov ax,0xa
metadata_at_e738: push ax
metadata_at_e739: call metadata_timed_byte
metadata_at_e73c: cmp ax,strict word 0x6
metadata_at_e73f: jz short metadata_at_e750
metadata_at_e741: inc word [bp-0x8]
metadata_at_e744: cmp word [bp-0x8],0x3
metadata_at_e748: jnl short metadata_at_e74d
metadata_at_e74a: jmp near metadata_at_e5f0
metadata_at_e74d: jmp short metadata_at_e75a
metadata_at_e74f: nop
metadata_at_e750: mov ax,0x1
metadata_at_e753: pop si
metadata_at_e754: pop di
metadata_at_e755: mov_load sp,bp
metadata_at_e757: pop bp
metadata_at_e758: ret
metadata_at_e759: nop
metadata_at_e75a: sub_load ax,ax
metadata_at_e75c: pop si
metadata_at_e75d: pop di
metadata_at_e75e: mov_load sp,bp
metadata_at_e760: pop bp
metadata_at_e761: ret
