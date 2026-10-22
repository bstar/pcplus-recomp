; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_expand
extern window_scroll
extern window_frame
extern window_pace
extern window_vertical
extern window_shadow
extern window_state_7a8e
extern window_state_7a66
extern window_state_7ac4
extern window_state_7a94
extern window_state_7a72
extern window_state_7a74
extern window_state_7ab2
extern window_state_7ab4
%define short
%else
ORG 28808
%define window_scroll 28380
%define window_frame 28652
%define window_pace 27506
%define window_vertical 32586
%define window_shadow 32050
%define window_state_7a8e 31374
%define window_state_7a66 31334
%define window_state_7ac4 31428
%define window_state_7a94 31380
%define window_state_7a72 31346
%define window_state_7a74 31348
%define window_state_7ab2 31410
%define window_state_7ab4 31412
%endif
%include "encodings.inc"
window_expand:
L_7088: push bp
L_7089: mov_load bp,sp
L_708b: sub sp,0x20
L_708e: push di
L_708f: push si
L_7090: mov word [bp-0x12],0x3
L_7095: mov word [bp-0x1e],0x0
L_709a: mov word [bp-0x10],0x1
L_709f: cmp word [window_state_7a8e],0x0
L_70a4: jnz short L_70e0
L_70a6: cmp word [window_state_7a66],0x0
L_70ab: jnz short L_70e0
L_70ad: mov word [bp-0xc],0xd
L_70b2: cmp word [window_state_7ac4],0x64
L_70b7: jnl short L_70be
L_70b9: mov word [bp-0xc],0x6
L_70be: mov bx,[bp+0xa]
L_70c1: sub bx,[bp+0xe]
L_70c4: shl bx,1
L_70c6: sub bx,[bp+0xc]
L_70c9: add bx,[bp+0x8]
L_70cc: cmp bx,0x28
L_70cf: jnc short L_70d5
L_70d1: add word [bp-0xc],0x2
L_70d5: cmp bx,0x19
L_70d8: jnc short L_70e5
L_70da: add word [bp-0xc],0x2
L_70de: jmp short L_70e5
L_70e0: mov word [bp-0xc],0x0
L_70e5: mov word [bp-0x6],0x0
L_70ea: mov ax,[bp+0x6]
L_70ed: or ah,0x20
L_70f0: mov [bp-0xe],ax
L_70f3: mov ax,[bp+0xa]
L_70f6: sub ax,[bp+0xe]
L_70f9: mov_load cx,ax
L_70fb: cwd
L_70fc: sub_load ax,dx
L_70fe: sar ax,1
L_7100: add ax,[bp+0xe]
L_7103: dec ax
L_7104: mov [bp-0x8],ax
L_7107: mov ax,[bp+0x8]
L_710a: sub ax,[bp+0xc]
L_710d: cwd
L_710e: sub_load ax,dx
L_7110: sar ax,1
L_7112: add ax,[bp+0xc]
L_7115: dec ax
L_7116: mov [bp-0x16],ax
L_7119: mov dx,[bp-0x8]
L_711c: inc dx
L_711d: mov [bp-0xa],dx
L_7120: inc ax
L_7121: mov [bp-0x20],ax
L_7124: cmp cx,0x27
L_7127: jng short L_712e
L_7129: mov word [bp-0x12],0x2
L_712e: mov ax,[bp+0xe]
L_7131: cmp [bp-0x8],ax
L_7134: jng short L_715b
L_7136: mov ax,[bp+0xc]
L_7139: cmp [bp-0x16],ax
L_713c: jng short L_715b
L_713e: mov ax,[bp+0xa]
L_7141: cmp_load dx,ax
L_7143: jnl short L_715b
L_7145: mov ax,[bp+0x8]
L_7148: cmp [bp-0x20],ax
L_714b: jnl short L_715b
L_714d: cmp word [window_state_7a94],0x0
L_7152: jz short L_715b
L_7154: mov word [bp-0x1c],0x0
L_7159: jmp short L_7160
L_715b: mov word [bp-0x1c],0x1
L_7160: cmp word [bp-0x1c],0x0
L_7164: jz short L_7181
L_7166: sub_load ax,ax
L_7168: push ax
L_7169: mov ah,[bp+0xe]
L_716c: sub_load al,al
L_716e: or ax,[bp+0xc]
L_7171: push ax
L_7172: mov ah,[bp+0xa]
L_7175: sub_load al,al
L_7177: or ax,[bp+0x8]
L_717a: push ax
L_717b: push word [bp+0x6]
L_717e: call window_scroll
L_7181: mov ax,[window_state_7a72]
L_7184: sub ax,strict word 0x3
L_7187: cmp ax,[bp+0x8]
L_718a: jng short L_71a2
L_718c: mov ax,[window_state_7a74]
L_718f: dec ax
L_7190: dec ax
L_7191: cmp ax,[bp+0xa]
L_7194: jng short L_71a2
L_7196: cmp word [window_state_7a66],0x0
L_719b: jnz short L_71a2
L_719d: mov dx,0x1
L_71a0: jmp short L_71a4
L_71a2: sub_load dx,dx
L_71a4: mov [bp-0x14],dx
L_71a7: mov di,[bp-0x6]
L_71aa: jmp near L_72ec
L_71ad: mov word [bp-0x1c],0x1
L_71b2: mov ah,[bp-0x8]
L_71b5: sub_load al,al
L_71b7: mov_load si,ax
L_71b9: or si,[bp-0x16]
L_71bc: mov ah,[bp-0xa]
L_71bf: or ax,[bp-0x20]
L_71c2: mov [bp-0x2],ax
L_71c5: push si
L_71c6: push ax
L_71c7: push word [bp+0x6]
L_71ca: push word [window_state_7ab2]
L_71ce: call window_frame
L_71d1: cmp word [bp-0x10],0x0
L_71d5: jz short L_71e3
L_71d7: mov ax,0x2
L_71da: push ax
L_71db: call window_pace
L_71de: dec word [bp-0x10]
L_71e1: jmp short L_725d
L_71e3: mov_load ax,si
L_71e5: mov cl,[bp-0x2]
L_71e8: mov_load ch,ah
L_71ea: mov [bp-0x4],cx
L_71ed: cmp word [bp-0x1e],0x0
L_71f1: jz short L_7212
L_71f3: push word [bp-0xe]
L_71f6: lea ax,[si+0x102]
L_71fa: push ax
L_71fb: push di
L_71fc: call window_vertical
L_71ff: push word [bp-0xe]
L_7202: mov ax,[bp-0x4]
L_7205: add ax,0xfe
L_7208: push ax
L_7209: push di
L_720a: call window_vertical
L_720d: mov word [bp-0x1e],0x0
L_7212: push word [bp-0xe]
L_7215: lea ax,[si+0x101]
L_7219: push ax
L_721a: push di
L_721b: call window_vertical
L_721e: push word [bp-0xe]
L_7221: mov ax,[bp-0x4]
L_7224: add ax,0xff
L_7227: push ax
L_7228: push di
L_7229: call window_vertical
L_722c: mov ax,[bp-0x1a]
L_722f: cmp [bp-0x18],ax
L_7232: jz short L_7242
L_7234: push ax
L_7235: push word [bp-0x18]
L_7238: push word [bp+0x6]
L_723b: push word [window_state_7ab4]
L_723f: call window_frame
L_7242: cmp word [bp-0x14],0x0
L_7246: jz short L_7257
L_7248: push word [bp-0x8]
L_724b: push word [bp-0x16]
L_724e: push word [bp-0xa]
L_7251: push word [bp-0x20]
L_7254: call window_shadow
L_7257: push word [bp-0xc]
L_725a: call window_pace
L_725d: mov [bp-0x1a],si
L_7260: mov ax,[bp-0x2]
L_7263: mov [bp-0x18],ax
L_7266: mov ax,[bp+0xe]
L_7269: cmp [bp-0x8],ax
L_726c: jng short L_7279
L_726e: dec word [bp-0x8]
L_7271: mov word [bp-0x1c],0x0
L_7276: inc di
L_7277: jmp short L_727d
L_7279: add byte [bp-0x19],0x1
L_727d: mov ax,[bp+0xc]
L_7280: cmp [bp-0x16],ax
L_7283: jng short L_72aa
L_7285: mov ax,[bp-0x16]
L_7288: sub ax,strict word 0x3
L_728b: cmp ax,[bp+0xc]
L_728e: jng short L_729d
L_7290: mov ax,[bp-0x12]
L_7293: sub [bp-0x16],ax
L_7296: mov word [bp-0x1e],0x1
L_729b: jmp short L_72a3
L_729d: mov ax,[bp+0xc]
L_72a0: mov [bp-0x16],ax
L_72a3: mov word [bp-0x1c],0x0
L_72a8: jmp short L_72ad
L_72aa: inc word [bp-0x1a]
L_72ad: mov ax,[bp+0xa]
L_72b0: cmp [bp-0xa],ax
L_72b3: jnl short L_72c0
L_72b5: inc word [bp-0xa]
L_72b8: inc di
L_72b9: mov word [bp-0x1c],0x0
L_72be: jmp short L_72c5
L_72c0: sub word [bp-0x18],0x100
L_72c5: mov ax,[bp+0x8]
L_72c8: cmp [bp-0x20],ax
L_72cb: jnl short L_72e9
L_72cd: mov cx,[bp-0x12]
L_72d0: add [bp-0x20],cx
L_72d3: cmp [bp-0x20],ax
L_72d6: jng short L_72dd
L_72d8: mov [bp-0x20],ax
L_72db: jmp short L_72e2
L_72dd: mov word [bp-0x1e],0x1
L_72e2: mov word [bp-0x1c],0x0
L_72e7: jmp short L_72ec
L_72e9: dec word [bp-0x18]
L_72ec: cmp word [bp-0x1c],0x0
L_72f0: jnz short L_72f5
L_72f2: jmp near L_71ad
L_72f5: mov ah,[bp+0xe]
L_72f8: sub_load al,al
L_72fa: or ax,[bp+0xc]
L_72fd: push ax
L_72fe: mov ah,[bp+0xa]
L_7301: sub_load al,al
L_7303: or ax,[bp+0x8]
L_7306: push ax
L_7307: push word [bp+0x6]
L_730a: push word [bp+0x4]
L_730d: call window_frame
L_7310: cmp word [bp-0x14],0x0
L_7314: jz short L_7325
L_7316: push word [bp+0xe]
L_7319: push word [bp+0xc]
L_731c: push word [bp+0xa]
L_731f: push word [bp+0x8]
L_7322: call window_shadow
L_7325: pop si
L_7326: pop di
L_7327: mov_load sp,bp
L_7329: pop bp
L_732a: ret word 0xc
