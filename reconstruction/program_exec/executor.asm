; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_execute
extern program_validate_name
extern program_system
extern program_spawnl
extern program_service_6b5a
extern program_service_76b4
extern program_service_6bbe
extern program_service_6f60
extern program_service_6e78
extern program_service_6dca
extern program_service_758a
extern program_service_40c9
extern program_service_3745
extern program_service_03a7
extern program_service_7508
extern program_service_40df
extern program_service_6d1a
extern program_service_4870
extern program_service_6b42
extern program_service_427f
extern program_service_85fc
extern program_service_1c66
extern program_service_2eaa
extern program_service_76ea
extern program_service_82b6
extern program_service_6e5a
extern program_busy
extern program_errno
extern program_state_7a6c
extern program_state_7a88
extern program_state_7a8a
extern program_state_7a74
extern program_state_7a72
extern program_state_2b8a
extern program_state_3252
extern program_state_2c12
extern program_state_cee6
extern program_state_2bae
extern program_state_1d4c
extern program_state_2068
extern program_state_206a
extern program_state_42cc
extern program_state_42c6
extern program_state_42c4
extern program_state_42c8
extern program_state_42ca
extern program_state_42ce
%define short
%else
ORG 0x433d
%define program_validate_name 0x4748
%define program_system 0x896a
%define program_spawnl 0x8d34
%define program_service_6b5a 0x6b5a
%define program_service_76b4 0x76b4
%define program_service_6bbe 0x6bbe
%define program_service_6f60 0x6f60
%define program_service_6e78 0x6e78
%define program_service_6dca 0x6dca
%define program_service_758a 0x758a
%define program_service_40c9 0x40c9
%define program_service_3745 0x3745
%define program_service_03a7 0x3a7
%define program_service_7508 0x7508
%define program_service_40df 0x40df
%define program_service_6d1a 0x6d1a
%define program_service_4870 0x4870
%define program_service_6b42 0x6b42
%define program_service_427f 0x427f
%define program_service_85fc 0x85fc
%define program_service_1c66 0x1c66
%define program_service_2eaa 0x2eaa
%define program_service_76ea 0x76ea
%define program_service_82b6 0x82b6
%define program_service_6e5a 0x6e5a
%define program_busy 0x333c
%define program_errno 0x7b1c
%define program_state_7a6c 0x7a6c
%define program_state_7a88 0x7a88
%define program_state_7a8a 0x7a8a
%define program_state_7a74 0x7a74
%define program_state_7a72 0x7a72
%define program_state_2b8a 0x2b8a
%define program_state_3252 0x3252
%define program_state_2c12 0x2c12
%define program_state_cee6 0xcee6
%define program_state_2bae 0x2bae
%define program_state_1d4c 0x1d4c
%define program_state_2068 0x2068
%define program_state_206a 0x206a
%define program_state_42cc 0x42cc
%define program_state_42c6 0x42c6
%define program_state_42c4 0x42c4
%define program_state_42c8 0x42c8
%define program_state_42ca 0x42ca
%define program_state_42ce 0x42ce
%endif
%include "encodings.inc"
program_execute:
L_433d: push bp
L_433e: mov_load bp,sp
L_4340: sub sp,0x4c
L_4343: push si
L_4344: push word [bp+0x4]
L_4347: call program_validate_name
L_434a: pop bx
L_434b: or_load ax,ax
L_434d: jz short L_4355
L_434f: mov ax,0x1
L_4352: jmp near L_4565
L_4355: cmp byte [program_busy],0x0
L_435a: jz short L_4362
L_435c: mov ax,0xffff
L_435f: jmp near L_4565
L_4362: mov byte [program_busy],0x1
L_4367: mov ax,[program_state_7a6c]
L_436a: mov [bp-0x2],ax
L_436d: or_load ax,ax
L_436f: jnz short L_4391
L_4371: cmp [program_state_7a88],ax
L_4375: jz short L_438e
L_4377: mov ax,[program_state_7a8a]
L_437a: cwd
L_437b: sub_load ax,dx
L_437d: sar ax,1
L_437f: sub ax,[program_state_7a88]
L_4383: inc ax
L_4384: jnz short L_438b
L_4386: mov ax,0x2
L_4389: jmp short L_438e
L_438b: mov ax,0x1
L_438e: mov [bp-0x4],ax
L_4391: call program_service_6b5a
L_4394: mov ax,0x1
L_4397: push ax
L_4398: call program_service_76b4
L_439b: mov ax,[program_state_7a74]
L_439e: mov [bp-0x6],ax
L_43a1: mov ax,[program_state_7a72]
L_43a4: mov [bp-0x8],ax
L_43a7: cmp word [bp+0xc],0x0
L_43ab: jz short L_43cd
L_43ad: call program_service_6bbe
L_43b0: mov [bp-0x10],ax
L_43b3: mov [bp-0xe],dx
L_43b6: mov ax,0x7
L_43b9: push ax
L_43ba: call program_service_6f60
L_43bd: mov ax,0x100
L_43c0: push ax
L_43c1: call program_service_6e78
L_43c4: call program_service_6dca
L_43c7: call program_service_758a
L_43ca: call program_service_40c9
L_43cd: mov word [program_errno],0x0
L_43d3: cmp word [bp+0x8],0x0
L_43d7: jz short L_43e2
L_43d9: push word [bp+0x4]
L_43dc: call program_system
L_43df: pop bx
L_43e0: jmp short L_43f5
L_43e2: sub_load ax,ax
L_43e4: push ax
L_43e5: push word [bp+0x6]
L_43e8: push word [bp+0x4]
L_43eb: push word [bp+0x4]
L_43ee: push ax
L_43ef: call program_spawnl
L_43f2: add sp,0xa
L_43f5: mov_load si,ax
L_43f7: cmp word [bp+0xa],0x0
L_43fb: jz short L_4400
L_43fd: call program_service_3745
L_4400: call program_service_03a7
L_4403: cmp word [bp+0xc],0x0
L_4407: jz short L_4413
L_4409: mov ax,0x1
L_440c: push ax
L_440d: call program_service_7508
L_4410: call program_service_40df
L_4413: call program_service_6d1a
L_4416: mov ax,[bp-0x6]
L_4419: cmp [program_state_7a74],ax
L_441d: jnz short L_443c
L_441f: mov ax,[bp-0x8]
L_4422: cmp [program_state_7a72],ax
L_4426: jnz short L_443c
L_4428: cmp word [bp+0xc],0x0
L_442c: jz short L_4437
L_442e: push word [bp-0xe]
L_4431: push word [bp-0x10]
L_4434: call program_service_4870
L_4437: call program_service_6b42
L_443a: jmp short L_44a1
L_443c: lea bx,[program_state_2b8a]
L_4440: call program_service_427f
L_4443: cmp word [bp+0xc],0x0
L_4447: jz short L_4454
L_4449: push word [bp-0xe]
L_444c: push word [bp-0x10]
L_444f: call program_service_85fc
L_4452: pop bx
L_4453: pop bx
L_4454: call program_service_1c66
L_4457: cmp word [program_state_7a74],0x19
L_445c: jl short L_4486
L_445e: cmp word [program_state_7a72],0x50
L_4463: jl short L_4486
L_4465: sub_load ax,ax
L_4467: push ax
L_4468: push ax
L_4469: push ax
L_446a: call program_service_2eaa
L_446d: add sp,0x6
L_4470: cmp word [program_state_7a74],0x19
L_4475: jnz short L_449b
L_4477: cmp word [program_state_7a72],0x50
L_447c: jnz short L_449b
L_447e: mov word [program_state_3252],0x1
L_4484: jmp short L_449b
L_4486: lea bx,[program_state_2c12]
L_448a: call program_service_427f
L_448d: sub_load ax,ax
L_448f: push ax
L_4490: push ax
L_4491: mov ax,0x1
L_4494: push ax
L_4495: call program_service_2eaa
L_4498: add sp,0x6
L_449b: mov ax,[program_state_3252]
L_449e: mov [program_state_cee6],ax
L_44a1: cmp si,0xf7
L_44a5: jnz short L_44c5
L_44a7: cmp word [bp+0xc],0x0
L_44ab: jnz short L_44c5
L_44ad: lea bx,[program_state_2bae]
L_44b1: call program_service_427f
L_44b4: sub_load ax,ax
L_44b6: push ax
L_44b7: push word [program_state_1d4c]
L_44bb: push word [program_state_cee6]
L_44bf: call program_service_2eaa
L_44c2: add sp,0x6
L_44c5: mov ax,0x1
L_44c8: push ax
L_44c9: push word [program_state_2068]
L_44cd: push word [program_state_206a]
L_44d1: call program_service_76ea
L_44d4: cmp si,0xffffffffffffffff
L_44d7: jnz short L_4527
L_44d9: cmp word [program_errno],0x0
L_44de: jz short L_4527
L_44e0: mov ax,[program_errno]
L_44e3: cmp ax,strict word 0xc
L_44e6: jz short L_450e
L_44e8: ja short L_44f6
L_44ea: sub al,0x2
L_44ec: jz short L_44fc
L_44ee: sub al,0x5
L_44f0: jz short L_4502
L_44f2: dec al
L_44f4: jz short L_4508
L_44f6: mov dx,[program_state_42cc]
L_44fa: jmp short L_4512
L_44fc: mov dx,[program_state_42c6]
L_4500: jmp short L_4512
L_4502: mov dx,[program_state_42c4]
L_4506: jmp short L_4512
L_4508: mov dx,[program_state_42c8]
L_450c: jmp short L_4512
L_450e: mov dx,[program_state_42ca]
L_4512: push dx
L_4513: push word [program_state_42ce]
L_4517: lea ax,[bp-0x4c]
L_451a: push ax
L_451b: call program_service_82b6
L_451e: add sp,0x6
L_4521: lea bx,[bp-0x4c]
L_4524: call program_service_427f
L_4527: cmp word [bp-0x2],0x0
L_452b: jz short L_4532
L_452d: call program_service_6dca
L_4530: jmp short L_455e
L_4532: mov ax,[bp-0x4]
L_4535: or_load ax,ax
L_4537: jz short L_4541
L_4539: dec ax
L_453a: jz short L_4549
L_453c: dec ax
L_453d: jz short L_454f
L_453f: jmp short L_455b
L_4541: mov word [program_state_7a88],0x0
L_4547: jmp short L_455b
L_4549: mov ax,[program_state_7a8a]
L_454c: dec ax
L_454d: jmp short L_4558
L_454f: mov ax,[program_state_7a8a]
L_4552: cwd
L_4553: sub_load ax,dx
L_4555: sar ax,1
L_4557: inc ax
L_4558: mov [program_state_7a88],ax
L_455b: call program_service_6e5a
L_455e: mov byte [program_busy],0x0
L_4563: mov_load ax,si
L_4565: pop si
L_4566: mov_load sp,bp
L_4568: pop bp
L_4569: ret
