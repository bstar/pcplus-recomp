; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_putc
global files_at_91a7
global files_at_91a9
global files_at_91aa
global files_at_91ab
global files_at_91ae
global files_at_91b1
global files_at_91b3
global files_at_91b5
global files_at_91b7
global files_at_91b9
global files_at_91be
global files_at_91c0
global files_at_91c2
global files_at_91c4
global files_at_91c6
global files_at_91c9
global files_at_91cb
global files_at_91cd
global files_at_91cf
global files_at_91d1
global files_at_91d4
global files_at_91d6
global files_at_91da
global files_at_91de
global files_at_91e0
global files_at_91e3
global files_at_91e5
global files_at_91e7
global files_at_91e9
global files_at_91eb
global files_at_91ee
global files_at_91f0
global files_at_91f4
global files_at_91f6
global files_at_91fa
global files_at_91fc
global files_at_9200
global files_at_9202
global files_at_9207
global files_at_9209
global files_at_920c
global files_at_920d
global files_at_9210
global files_at_9211
global files_at_9212
global files_at_9215
global files_at_9218
global files_at_921b
global files_at_921d
global files_at_9220
global files_at_9224
global files_at_9226
global files_at_9227
global files_at_9228
global files_at_922b
global files_at_922c
global files_at_922d
global files_at_9231
global files_at_9233
global files_at_9235
global files_at_9238
global files_at_923a
global files_at_923b
global files_at_923d
global files_at_9240
global files_at_9241
global files_at_9244
global files_at_9246
global files_at_9247
global files_at_9248
global files_at_924b
global files_at_924c
global files_at_924f
global files_at_9252
global files_at_9253
global files_at_9256
global files_at_9259
global files_at_925b
global files_at_925d
global files_at_925f
global files_at_9261
global files_at_9264
global files_at_9266
global files_at_9268
global files_at_926d
global files_at_926f
global files_at_9272
global files_at_9273
global files_at_9274
global files_at_9275
global files_at_9276
global files_at_9279
global files_at_927c
global files_at_927e
global files_at_9280
global files_at_9282
global files_at_9283
global files_at_9284
global files_at_9285
extern files_handle_flags
extern files_stream_table
extern files_stdout
extern files_stderr
extern files_aux
extern files_extra_table
extern files_seek
extern files_write
extern files_allocate_buffer
%else
ORG 0x91a6
%define files_handle_flags 0x7b2b
%define files_stream_table 0x7b6a
%define files_stdout 0x7b72
%define files_stderr 0x7b7a
%define files_aux 0x7b8a
%define files_extra_table 0x7c0a
%define files_seek 0xa22e
%define files_write 0xa368
%define files_allocate_buffer 0xa71a
%endif
%include "encodings.inc"
files_putc: push bp
files_at_91a7: mov_load bp,sp
files_at_91a9: push si
files_at_91aa: push di
files_at_91ab: mov si,[bp+0x6]
files_at_91ae: mov al,[si+0x6]
files_at_91b1: test al,0x82
files_at_91b3: jz short files_at_921d
files_at_91b5: test al,0x40
files_at_91b7: jnz short files_at_921d
files_at_91b9: mov word [si+0x2],0x0
files_at_91be: test al,0x1
files_at_91c0: jz short files_at_91cd
files_at_91c2: test al,0x10
files_at_91c4: jz short files_at_921d
files_at_91c6: mov cx,[si+0x4]
files_at_91c9: mov [si],cx
files_at_91cb: and al,0xfe
files_at_91cd: or al,0x2
files_at_91cf: and al,0xef
files_at_91d1: mov [si+0x6],al
files_at_91d4: mov_load di,si
files_at_91d6: sub di,files_stream_table
files_at_91da: add di,files_extra_table
files_at_91de: xor_load bx,bx
files_at_91e0: mov bl,[si+0x7]
files_at_91e3: test al,0x8
files_at_91e5: jnz short files_at_9233
files_at_91e7: test al,0x4
files_at_91e9: jnz short files_at_9209
files_at_91eb: test byte [di],0x1
files_at_91ee: jnz short files_at_9233
files_at_91f0: cmp si,files_stdout
files_at_91f4: jz short files_at_9202
files_at_91f6: cmp si,files_stderr
files_at_91fa: jz short files_at_9202
files_at_91fc: cmp si,files_aux
files_at_9200: jnz short files_at_9226
files_at_9202: test byte [bx+files_handle_flags],0x40
files_at_9207: jz short files_at_9226
files_at_9209: mov cx,0x1
files_at_920c: push cx
files_at_920d: lea di,[bp+0x4]
files_at_9210: push di
files_at_9211: push bx
files_at_9212: call files_write
files_at_9215: add sp,0x6
files_at_9218: mov cx,0x1
files_at_921b: jmp short files_at_925b
files_at_921d: mov ax,0xffff
files_at_9220: or byte [si+0x6],0x20
files_at_9224: jmp short files_at_9282
files_at_9226: push bx
files_at_9227: push si
files_at_9228: call files_allocate_buffer
files_at_922b: pop bx
files_at_922c: pop bx
files_at_922d: test byte [si+0x6],0x8
files_at_9231: jz short files_at_9209
files_at_9233: mov cx,[si]
files_at_9235: mov dx,[si+0x4]
files_at_9238: sub_load cx,dx
files_at_923a: inc dx
files_at_923b: mov [si],dx
files_at_923d: mov dx,[di+0x2]
files_at_9240: dec dx
files_at_9241: mov [si+0x2],dx
files_at_9244: jcxz files_at_9266
files_at_9246: push cx
files_at_9247: push cx
files_at_9248: push word [si+0x4]
files_at_924b: push bx
files_at_924c: call files_write
files_at_924f: add sp,0x6
files_at_9252: pop cx
files_at_9253: mov di,[si+0x4]
files_at_9256: mov dx,[bp+0x4]
files_at_9259: mov [di],dl
files_at_925b: cmp_load ax,cx
files_at_925d: jnz short files_at_921d
files_at_925f: xor_load ax,ax
files_at_9261: mov al,[bp+0x4]
files_at_9264: jmp short files_at_9282
files_at_9266: xor_load ax,ax
files_at_9268: test byte [bx+files_handle_flags],0x20
files_at_926d: jz short files_at_9253
files_at_926f: mov cx,0x2
files_at_9272: push cx
files_at_9273: push ax
files_at_9274: push ax
files_at_9275: push bx
files_at_9276: call files_seek
files_at_9279: add sp,0x8
files_at_927c: xor_load ax,ax
files_at_927e: mov_load cx,ax
files_at_9280: jmp short files_at_9253
files_at_9282: pop di
files_at_9283: pop si
files_at_9284: pop bp
files_at_9285: ret
