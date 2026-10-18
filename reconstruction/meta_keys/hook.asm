; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_hook
extern meta_keys_validate_name
extern meta_keys_get_ds
extern meta_keys_decimal32
extern meta_keys_decimal16
extern meta_keys_strcpy
extern meta_keys_strcat
extern meta_keys_program_service
extern meta_keys_resolve_program
extern meta_hook_result
extern meta_hook_exchange_a
extern meta_hook_exchange_b
extern meta_prm_image
extern meta_hook_prefix
extern meta_hook_space_a
extern meta_hook_space_b
extern meta_hook_space_c
extern meta_hook_space_d
%define short
%else
ORG 0x414c
%define meta_keys_validate_name 0x4748
%define meta_keys_get_ds 0x76b0
%define meta_keys_decimal32 0x89fa
%define meta_keys_decimal16 0x8e6c
%define meta_keys_strcpy 0x8268
%define meta_keys_strcat 0x8bea
%define meta_keys_program_service 0x433d
%define meta_keys_resolve_program 0x353d
%define meta_hook_result 0xd124
%define meta_hook_exchange_a 0xd126
%define meta_hook_exchange_b 0xd13a
%define meta_prm_image 0x1b84
%define meta_hook_prefix 0x4765
%define meta_hook_space_a 0x476e
%define meta_hook_space_b 0x4770
%define meta_hook_space_c 0x4772
%define meta_hook_space_d 0x4774
%endif
%include "encodings.inc"
meta_keys_hook:
L_414c: push bp
L_414d: mov_load bp,sp
L_414f: sub sp,0x9c
L_4153: push si
L_4154: mov si,[bp+0xa]
L_4157: push si
L_4158: call meta_keys_validate_name
L_415b: pop bx
L_415c: or_load ax,ax
L_415e: jz short L_4166
L_4160: mov ax,0x1
L_4163: jmp near L_4275
L_4166: call meta_keys_get_ds
L_4169: mov [bp-0x2],ax
L_416c: mov word [bp-0x4],meta_prm_image
L_4171: mov ax,0xa
L_4174: push ax
L_4175: lea ax,[bp-0x18]
L_4178: push ax
L_4179: push word [bp-0x2]
L_417c: push word [bp-0x4]
L_417f: call meta_keys_decimal32
L_4182: add sp,0x8
L_4185: mov ax,meta_hook_prefix
L_4188: push ax
L_4189: lea ax,[bp-0x9c]
L_418d: push ax
L_418e: call meta_keys_strcpy
L_4191: pop bx
L_4192: pop bx
L_4193: cmp word [bp+0x4],0x0
L_4197: jz short L_4203
L_4199: mov word [bp-0x4],meta_hook_exchange_a
L_419e: mov ax,0xa
L_41a1: push ax
L_41a2: lea cx,[bp-0x28]
L_41a5: push cx
L_41a6: push word [bp-0x2]
L_41a9: push word [bp-0x4]
L_41ac: call meta_keys_decimal32
L_41af: add sp,0x8
L_41b2: mov word [bp-0x4],meta_hook_exchange_b
L_41b7: mov ax,0xa
L_41ba: push ax
L_41bb: lea ax,[bp-0x38]
L_41be: push ax
L_41bf: push word [bp-0x2]
L_41c2: push word [bp-0x4]
L_41c5: call meta_keys_decimal32
L_41c8: add sp,0x8
L_41cb: lea ax,[bp-0x28]
L_41ce: push ax
L_41cf: lea ax,[bp-0x9c]
L_41d3: push ax
L_41d4: call meta_keys_strcat
L_41d7: pop bx
L_41d8: pop bx
L_41d9: mov ax,meta_hook_space_a
L_41dc: push ax
L_41dd: lea ax,[bp-0x9c]
L_41e1: push ax
L_41e2: call meta_keys_strcat
L_41e5: pop bx
L_41e6: pop bx
L_41e7: lea ax,[bp-0x38]
L_41ea: push ax
L_41eb: lea ax,[bp-0x9c]
L_41ef: push ax
L_41f0: call meta_keys_strcat
L_41f3: pop bx
L_41f4: pop bx
L_41f5: mov ax,meta_hook_space_b
L_41f8: push ax
L_41f9: lea ax,[bp-0x9c]
L_41fd: push ax
L_41fe: call meta_keys_strcat
L_4201: pop bx
L_4202: pop bx
L_4203: lea ax,[bp-0x18]
L_4206: push ax
L_4207: lea ax,[bp-0x9c]
L_420b: push ax
L_420c: call meta_keys_strcat
L_420f: pop bx
L_4210: pop bx
L_4211: mov ax,0xa
L_4214: push ax
L_4215: lea ax,[bp-0x8]
L_4218: push ax
L_4219: push word [bp+0x8]
L_421c: call meta_keys_decimal16
L_421f: add sp,0x6
L_4222: mov ax,meta_hook_space_c
L_4225: push ax
L_4226: lea ax,[bp-0x9c]
L_422a: push ax
L_422b: call meta_keys_strcat
L_422e: pop bx
L_422f: pop bx
L_4230: lea ax,[bp-0x8]
L_4233: push ax
L_4234: lea ax,[bp-0x9c]
L_4238: push ax
L_4239: call meta_keys_strcat
L_423c: pop bx
L_423d: pop bx
L_423e: cmp word [bp+0x4],0x0
L_4242: jnz short L_425f
L_4244: mov ax,meta_hook_space_d
L_4247: push ax
L_4248: lea ax,[bp-0x9c]
L_424c: push ax
L_424d: call meta_keys_strcat
L_4250: pop bx
L_4251: pop bx
L_4252: push word [bp+0x6]
L_4255: lea ax,[bp-0x9c]
L_4259: push ax
L_425a: call meta_keys_strcat
L_425d: pop bx
L_425e: pop bx
L_425f: sub_load ax,ax
L_4261: push ax
L_4262: push ax
L_4263: push ax
L_4264: lea ax,[bp-0x9c]
L_4268: push ax
L_4269: push si
L_426a: call meta_keys_resolve_program
L_426d: pop bx
L_426e: push ax
L_426f: call meta_keys_program_service
L_4272: add sp,0xa
L_4275: mov [meta_hook_result],ax
L_4278: pop si
L_4279: mov_load sp,bp
L_427b: pop bp
L_427c: ret word 0x8
