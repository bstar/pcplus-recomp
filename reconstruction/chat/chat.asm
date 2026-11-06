; Recovered2.01 Chat controller and duplex log/history helper.
; Flat bytes retain original instruction choices. DS=SS, DFclear.
; Native blocking behavior is evidence, not a live integration policy.
BITS 16
CPU 8086
%ifdef RECON_FLAT
ORG 0xe828
%define chat_service_3fb0 0x3fb0
%define chat_service_6edc 0x6edc
%define chat_service_6bf0 0x6bf0
%define chat_service_6e78 0x6e78
%define chat_service_6e5a 0x6e5a
%define chat_service_6e66 0x6e66
%define chat_service_aa65 0xaa65
%define chat_service_3d94 0x3d94
%define chat_service_5832 0x5832
%define chat_service_9b6 0x9b6
%define chat_service_798e 0x798e
%define chat_service_6dca 0x6dca
%define chat_service_6530 0x6530
%define chat_service_64fe 0x64fe
%define chat_service_a62 0xa62
%define chat_service_ab0b 0xab0b
%define chat_service_6b5a 0x6b5a
%define chat_service_d830 0xd830
%define chat_service_6b42 0x6b42
%define chat_service_48cc 0x48cc
%define chat_service_1bbe 0x1bbe
%define chat_data_7a74 0x7a74
%define chat_data_8fd4 0x8fd4
%define chat_data_8fd6 0x8fd6
%define chat_data_1d38 0x1d38
%define chat_data_7a84 0x7a84
%define chat_data_207a 0x207a
%define chat_data_207c 0x207c
%define chat_data_207e 0x207e
%define chat_data_397a 0x397a
%define chat_data_8fd5 0x8fd5
%define chat_data_399c 0x399c
%define chat_data_399e 0x399e
%define chat_data_8e20 0x8e20
%define chat_data_8fd7 0x8fd7
%define chat_data_334a 0x334a
%define chat_data_1d76 0x1d76
%define chat_data_1d1a 0x1d1a
%define chat_data_3986 0x3986
%define chat_data_3758 0x3758
%define chat_data_378e 0x378e
%define chat_data_37c4 0x37c4
%define chat_data_37fa 0x37fa
%define chat_data_3830 0x3830
%define chat_data_3866 0x3866
%define chat_data_389c 0x389c
%define chat_data_38d2 0x38d2
%define chat_data_3908 0x3908
%define chat_data_393e 0x393e
%define chat_data_7746 0x7746
%define chat_data_d00a 0xd00a
%else
SEGMENT _TEXT public class=CODE use16
global chat_native,chat_echo_string
extern chat_service_3fb0
extern chat_service_6edc
extern chat_service_6bf0
extern chat_service_6e78
extern chat_service_6e5a
extern chat_service_6e66
extern chat_service_aa65
extern chat_service_3d94
extern chat_service_5832
extern chat_service_9b6
extern chat_service_798e
extern chat_service_6dca
extern chat_service_6530
extern chat_service_64fe
extern chat_service_a62
extern chat_service_ab0b
extern chat_service_6b5a
extern chat_service_d830
extern chat_service_6b42
extern chat_service_48cc
extern chat_service_1bbe
extern chat_data_7a74
extern chat_data_8fd4
extern chat_data_8fd6
extern chat_data_1d38
extern chat_data_7a84
extern chat_data_207a
extern chat_data_207c
extern chat_data_207e
extern chat_data_397a
extern chat_data_8fd5
extern chat_data_399c
extern chat_data_399e
extern chat_data_8e20
extern chat_data_8fd7
extern chat_data_334a
extern chat_data_1d76
extern chat_data_1d1a
extern chat_data_3986
extern chat_data_3758
extern chat_data_378e
extern chat_data_37c4
extern chat_data_37fa
extern chat_data_3830
extern chat_data_3866
extern chat_data_389c
extern chat_data_38d2
extern chat_data_3908
extern chat_data_393e
extern chat_data_7746
extern chat_data_d00a
%endif
chat_native:
 push bp
Le829:
 db 0x8B,0xEC ; mov bp,sp
Le82b:
 sub sp,0x132
Le82f:
 push di
Le830:
 push si
Le831:
 call chat_service_3fb0
Le834:
 cmp word [chat_data_7a74],0x1c
Le839:
 jng short Le854
Le83b:
 mov word [chat_data_8fd4],0x2000
Le841:
 mov di,0x20
Le844:
 mov si,0x2100
Le847:
 mov word [chat_data_8fd6],0x2200
Le84d:
 mov word [bp-0x4],0x22
Le852:
 jmp short Le86b
Le854:
 mov word [chat_data_8fd4],0x1200
Le85a:
 mov di,0x12
Le85d:
 mov si,0x1300
Le860:
 mov word [chat_data_8fd6],0x1400
Le866:
 mov word [bp-0x4],0x14
Le86b:
 db 0x2B,0xC0 ; sub ax,ax
Le86d:
 push ax
Le86e:
 db 0x2B,0xC9 ; sub cx,cx
Le870:
 push cx
Le871:
 mov cx,0x4f
Le874:
 push cx
Le875:
 push word [chat_data_1d38]
Le879:
 call chat_service_6edc
Le87c:
 db 0x2B,0xC0 ; sub ax,ax
Le87e:
 push ax
Le87f:
 push si
Le880:
 db 0x8B,0xCE ; mov cx,si
Le882:
 or si,0x4f
Le885:
 push si
Le886:
 push word [chat_data_1d38]
Le88a:
 db 0x8B,0xF1 ; mov si,cx
Le88c:
 call chat_service_6edc
Le88f:
 db 0x2B,0xC0 ; sub ax,ax
Le891:
 push ax
Le892:
 push word [chat_data_7a84]
Le896:
 mov ax,[chat_data_7a84]
Le899:
 or al,0x4f
Le89b:
 push ax
Le89c:
 push word [chat_data_1d38]
Le8a0:
 call chat_service_6edc
Le8a3:
 mov ax,0x24
Le8a6:
 push ax
Le8a7:
 push word [chat_data_1d38]
Le8ab:
 push word [chat_data_207a]
Le8af:
 call chat_service_6bf0
Le8b2:
 or si,0x25
Le8b5:
 push si
Le8b6:
 push word [chat_data_1d38]
Le8ba:
 push word [chat_data_207c]
Le8be:
 call chat_service_6bf0
Le8c1:
 mov ax,[chat_data_7a84]
Le8c4:
 or al,0x19
Le8c6:
 push ax
Le8c7:
 push word [chat_data_1d38]
Le8cb:
 push word [chat_data_207e]
Le8cf:
 call chat_service_6bf0
Le8d2:
 push word [chat_data_8fd6]
Le8d6:
 call chat_service_6e78
Le8d9:
 lea ax,[bp-0x132]
Le8dd:
 mov [bp-0x2],ax
Le8e0:
 mov [bp-0x6],di
Le8e3:
 db 0x8B,0xF8 ; mov di,ax
Le8e5:
 mov word [chat_data_397a],0x3
Le8eb:
 mov [bp-0x2],di
Le8ee:
 jmp short Le936
Le8f0:
 call chat_service_6e5a
Le8f3:
 mov al,[chat_data_8fd5]
Le8f6:
 db 0x2a,0xe4 ; SUB AH,AH, original direction-bit encoding.
Le8f8:
 mov [chat_data_399c],ax
Le8fb:
 push ax
Le8fc:
 mov al,[chat_data_8fd4]
Le8ff:
 mov [chat_data_399e],ax
Le902:
 push ax
Le903:
 call chat_service_6e66
Le906:
 call chat_service_aa65
Le909:
 db 0x8B,0xD8 ; mov bx,ax
Le90b:
 mov al,[bx-0x2ff6]
Le90f:
 db 0x2a,0xe4 ; SUB AH,AH, original direction-bit encoding.
Le911:
 db 0x8B,0xF0 ; mov si,ax
Le913:
 db 0x0B,0xF6 ; or si,si
Le915:
 jz short Le936
Le917:
 push word [bp-0x6]
Le91a:
 mov ax,0x1
Le91d:
 push ax
Le91e:
 db 0x8B,0xC6 ; mov ax,si
Le920:
 push ax
Le921:
 call chat_service_3d94
Le924:
 add sp,0x6
Le927:
 push si
Le928:
 call chat_service_5832
Le92b:
 push si
Le92c:
 call chat_service_9b6
Le92f:
 pop bx
Le930:
 call chat_service_798e
Le933:
 mov [chat_data_8fd4],ax
Le936:
 cmp word [chat_data_8e20],0x0
Le93b:
 jnz short Le8f0
Le93d:
 mov al,[chat_data_8fd7]
Le940:
 db 0x2a,0xe4 ; SUB AH,AH, original direction-bit encoding.
Le942:
 mov [chat_data_399c],ax
Le945:
 push ax
Le946:
 mov al,[chat_data_8fd6]
Le949:
 mov [chat_data_399e],ax
Le94c:
 push ax
Le94d:
 call chat_service_6e66
Le950:
 call chat_service_6dca
Le953:
 mov di,[bp-0x2]
Le956:
 call chat_service_6530
Le959:
 db 0x0B,0xC0 ; or ax,ax
Le95b:
 jz short Le8e5
Le95d:
 mov al,[chat_data_8fd7]
Le960:
 db 0x2a,0xe4 ; SUB AH,AH, original direction-bit encoding.
Le962:
 mov [chat_data_399c],ax
Le965:
 push ax
Le966:
 mov al,[chat_data_8fd6]
Le969:
 mov [chat_data_399e],ax
Le96c:
 push ax
Le96d:
 call chat_service_6e66
Le970:
 call chat_service_64fe
Le973:
 db 0x8B,0xF0 ; mov si,ax
Le975:
 sub ax,strict word 0x11
Le978:
 jz short Le97e
Le97a:
 dec ax
Le97b:
 dec ax
Le97c:
 jnz short Le981
Le97e:
 jmp near Lea5e
Le981:
 sub ax,strict word 0x8
Le984:
 jnz short Le989
Le986:
 jmp near Leae3
Le989:
 sub ax,0x6ce5
Le98c:
 jnz short Le991
Le98e:
 jmp near Lea65
Le991:
 sub ax,0xb00
Le994:
 jnz short Le999
Le996:
 jmp near Lea74
Le999:
 sub ax,0x100
Le99c:
 jnz short Le9a1
Le99e:
 jmp near Lea7f
Le9a1:
 sub ax,0x100
Le9a4:
 jnz short Le9a9
Le9a6:
 jmp near Lea84
Le9a9:
 sub ax,0x100
Le9ac:
 jnz short Le9b1
Le9ae:
 jmp near Lea89
Le9b1:
 sub ax,0x100
Le9b4:
 jnz short Le9b9
Le9b6:
 jmp near Lea8e
Le9b9:
 sub ax,0x100
Le9bc:
 jnz short Le9c1
Le9be:
 jmp near Lea93
Le9c1:
 sub ax,0x100
Le9c4:
 jnz short Le9c9
Le9c6:
 jmp near Lea98
Le9c9:
 sub ax,0x100
Le9cc:
 jnz short Le9d1
Le9ce:
 jmp near Lea9d
Le9d1:
 sub ax,0x100
Le9d4:
 jnz short Le9d9
Le9d6:
 jmp near Leaa2
Le9d9:
 sub ax,0x100
Le9dc:
 jnz short Le9e1
Le9de:
 jmp near Leaa7
Le9e1:
 push word [chat_data_334a]
Le9e5:
 push word [bp-0x4]
Le9e8:
 db 0x8B,0xC6 ; mov ax,si
Le9ea:
 push ax
Le9eb:
 call chat_service_3d94
Le9ee:
 add sp,0x6
Le9f1:
 call chat_service_798e
Le9f4:
 mov [chat_data_8fd6],ax
Le9f7:
 cmp byte [chat_data_1d76],0x0
Le9fc:
 jz short Lea44
Le9fe:
 db 0x8B,0xC6 ; mov ax,si
Lea00:
 inc di
Lea01:
 mov [di-0x1],al
Lea04:
 cmp si,0xe08
Lea08:
 jnz short Lea18
Lea0a:
 dec di
Lea0b:
 dec di
Lea0c:
 lea ax,[bp-0x132]
Lea10:
 db 0x3B,0xF8 ; cmp di,ax
Lea12:
 jnc short Lea18
Lea14:
 lea di,[bp-0x132]
Lea18:
 cmp si,0xd
Lea1b:
 jnz short Lea20
Lea1d:
 jmp near Leaac
Lea20:
 cmp si,0xe00d
Lea24:
 jnz short Lea29
Lea26:
 jmp near Leaac
Lea29:
 lea ax,[bp-0x8]
Lea2c:
 db 0x3B,0xF8 ; cmp di,ax
Lea2e:
 jz short Lea33
Lea30:
 jmp near Le956
Lea33:
 mov byte [di],0x0
Lea36:
 lea bx,[bp-0x132]
Lea3a:
 call chat_service_a62
Lea3d:
 lea ax,[bp-0x132]
Lea41:
 jmp near Lead7
Lea44:
 push si
Lea45:
 call chat_service_ab0b
Lea48:
 cmp word [chat_data_1d1a],0x0
Lea4d:
 jnz short Lea52
Lea4f:
 jmp near Le956
Lea52:
 push si
Lea53:
 call chat_service_9b6
Lea56:
 pop bx
Lea57:
 push si
Lea58:
 call chat_service_5832
Lea5b:
 jmp near Le956
Lea5e:
 push si
Lea5f:
 call chat_service_ab0b
Lea62:
 jmp near Le956
Lea65:
 call chat_service_6b5a
Lea68:
 call chat_service_d830
Lea6b:
 call chat_service_6b42
Lea6e:
 call chat_service_6dca
Lea71:
 jmp near Le956
Lea74:
 mov ax,chat_data_3758
Lea77:
 push ax
Lea78:
 call chat_service_48cc
Lea7b:
 pop bx
Lea7c:
 jmp near Le956
Lea7f:
 mov ax,chat_data_378e
Lea82:
 jmp short Lea77
Lea84:
 mov ax,chat_data_37c4
Lea87:
 jmp short Lea77
Lea89:
 mov ax,chat_data_37fa
Lea8c:
 jmp short Lea77
Lea8e:
 mov ax,chat_data_3830
Lea91:
 jmp short Lea77
Lea93:
 mov ax,chat_data_3866
Lea96:
 jmp short Lea77
Lea98:
 mov ax,chat_data_389c
Lea9b:
 jmp short Lea77
Lea9d:
 mov ax,chat_data_38d2
Leaa0:
 jmp short Lea77
Leaa2:
 mov ax,chat_data_3908
Leaa5:
 jmp short Lea77
Leaa7:
 mov ax,chat_data_393e
Leaaa:
 jmp short Lea77
Leaac:
 mov byte [di],0x0
Leaaf:
 lea bx,[bp-0x132]
Leab3:
 call chat_service_a62
Leab6:
 lea ax,[bp-0x132]
Leaba:
 push ax
Leabb:
 call chat_echo_string
Leabe:
 pop bx
Leabf:
 cmp word [chat_data_3986],0x0
Leac4:
 jnz short Leacd
Leac6:
 cmp word [chat_data_1d1a],0x0
Leacb:
 jz short Leadc
Leacd:
 mov ax,0xa
Lead0:
 push ax
Lead1:
 call chat_service_ab0b
Lead4:
 mov ax,chat_data_7746
Lead7:
 push ax
Lead8:
 call chat_echo_string
Leadb:
 pop bx
Leadc:
 lea di,[bp-0x132]
Leae0:
 jmp near Le8e5
Leae3:
 call chat_service_3fb0
Leae6:
 db 0x2B,0xC0 ; sub ax,ax
Leae8:
 cwd
Leae9:
 call chat_service_1bbe
Leaec:
 pop si
Leaed:
 pop di
Leaee:
 db 0x8B,0xE5 ; mov sp,bp
Leaf0:
 pop bp
Leaf1:
 ret
chat_echo_string:
 push bp
Leaf3:
 db 0x8B,0xEC ; mov bp,sp
Leaf5:
 push di
Leaf6:
 push si
Leaf7:
 cmp word [chat_data_1d1a],0x0
Leafc:
 jz short Leb1a
Leafe:
 mov si,[bp+0x4]
Leb01:
 jmp short Leb15
Leb03:
 mov al,[si]
Leb05:
 cbw
Leb06:
 push ax
Leb07:
 call chat_service_9b6
Leb0a:
 pop bx
Leb0b:
 db 0x8B,0xFE ; mov di,si
Leb0d:
 inc si
Leb0e:
 mov al,[di]
Leb10:
 cbw
Leb11:
 push ax
Leb12:
 call chat_service_5832
Leb15:
 cmp byte [si],0x0
Leb18:
 jnz short Leb03
Leb1a:
 pop si
Leb1b:
 pop di
Leb1c:
 db 0x8B,0xE5 ; mov sp,bp
Leb1e:
 pop bp
Leb1f:
 ret
