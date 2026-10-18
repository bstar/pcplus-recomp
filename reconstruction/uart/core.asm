; Recovered assembly, not original source. Source image SHA-256: 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904
; Resident UART block [0xaa5c, 0xaea7); original relocation sites retained.
; Names are analyst annotations. Flat mode retains original addresses; OMF mode links symbols.
; Code corroboration: analysis/pcplus-main/functions and pcplus-uart-entry/evidence.
BITS 16
CPU 8086
%ifdef UART_OMF
SEGMENT _TEXT public class=CODE use16
; Let NASM expand branches when maintained-code fixes change distances.
%define short
%else
ORG 0xaa5c
%endif
%include "layout.inc"
%include "encodings.inc"
%ifdef UART_OMF
global uart_carrier_detect
global uart_receive_byte
global uart_available
global uart_transmit_byte
global uart_transmit_buffer
global uart_transmit_string
global uart_clear_to_send
global uart_clear_receive_buffer
global uart_unreceive_byte
global uart_set_rts
global uart_set_baud_divisor
global uart_set_line_control
global uart_saved_ds
global uart_previous_irq_offset
global uart_previous_irq_segment
global uart_receive_interrupt
global uart_install_interrupt
global uart_transmit_cl
global uart_restore_interrupt
global uart_disable
global uart_mask_irq
global uart_enable
global uart_wait_transmitter_empty
global uart_save_hardware_state
global uart_restore_hardware_state
%endif


uart_carrier_detect:
L_aa5c: mov dx,[uart_port_msr]                               ; original aa5c: mov dx,[0x8ffe]
L_aa60: in al,dx                                      ; original aa60: in al,dx
L_aa61: and ax,0x80                                   ; original aa61: and ax,0x80
L_aa64: ret                                           ; original aa64: ret

uart_receive_byte:
L_aa65: cmp word [uart_rx_count],0x0                         ; original aa65: cmp word [0x8e20],0x0
L_aa6a: jz short L_aad5                               ; original aa6a: jz 0xaad5
L_aa6c: mov bx,[uart_rx_read]                               ; original aa6c: mov bx,[0x7e1b]
L_aa70: mov al,[bx]                                   ; original aa70: mov al,[bx]
L_aa72: and ax,[uart_rx_mask]                               ; original aa72: and ax,[0x8e22]
L_aa76: dec word [uart_rx_count]                             ; original aa76: dec word [0x8e20]
L_aa7a: cmp bx,[uart_rx_last]                               ; original aa7a: cmp bx,[0x7e1d]
L_aa7e: jz short L_aa94                               ; original aa7e: jz 0xaa94
L_aa80: inc bx                                        ; original aa80: inc bx
L_aa81: mov [uart_rx_read],bx                               ; original aa81: mov [0x7e1b],bx
L_aa85: cmp word [uart_software_flow],0x0                         ; original aa85: cmp word [0x3354],0x0
L_aa8a: jnz short L_aa99                              ; original aa8a: jnz 0xaa99
L_aa8c: cmp word [uart_hardware_flow],0x0                         ; original aa8c: cmp word [0x3356],0x0
L_aa91: jnz short L_aab5                              ; original aa91: jnz 0xaab5
L_aa93: ret                                           ; original aa93: ret
L_aa94: mov bx,uart_rx_buffer                                 ; original aa94: mov bx,0x7e20
L_aa97: jmp short L_aa81                              ; original aa97: jmp 0xaa81
L_aa99: cmp byte [uart_xoff_sent],0x1                         ; original aa99: cmp byte [0x7e17],0x1
L_aa9e: jnz short L_aa93                              ; original aa9e: jnz 0xaa93
L_aaa0: cmp word [uart_rx_count],0x80                        ; original aaa0: cmp word [0x8e20],0x80
L_aaa6: jg short L_aa93                               ; original aaa6: jg 0xaa93
L_aaa8: mov byte [uart_xoff_sent],0x0                         ; original aaa8: mov byte [0x7e17],0x0
L_aaad: push ax                                       ; original aaad: push ax
L_aaae: mov cl,0x11                                   ; original aaae: mov cl,0x11
%ifdef UART_OMF
    mov byte [uart_flow_pending],0x11
%else
L_aab0: call L_ad93                                   ; original aab0: call 0xad93
%endif
L_aab3: pop ax                                        ; original aab3: pop ax
L_aab4: ret                                           ; original aab4: ret
L_aab5: cmp byte [uart_rts_lowered],0x0                         ; original aab5: cmp byte [0x7e18],0x0
L_aaba: jz short L_aa93                               ; original aaba: jz 0xaa93
L_aabc: cmp word [uart_rx_count],0x80                        ; original aabc: cmp word [0x8e20],0x80
L_aac2: jg short L_aa93                               ; original aac2: jg 0xaa93
L_aac4: mov_load cl,al                                ; original aac4: mov cl,al
L_aac6: mov al,0xb                                    ; original aac6: mov al,0xb
L_aac8: mov dx,[uart_port_mcr]                               ; original aac8: mov dx,[0x8ff4]
L_aacc: out dx,al                                     ; original aacc: out dx,al
L_aacd: mov_load al,cl                                ; original aacd: mov al,cl
L_aacf: mov byte [uart_rts_lowered],0x0                         ; original aacf: mov byte [0x7e18],0x0
L_aad4: ret                                           ; original aad4: ret
L_aad5: mov ax,0xffff                                 ; original aad5: mov ax,0xffff
L_aad8: ret                                           ; original aad8: ret

uart_available:
L_aad9: mov_load bx,sp                                ; original aad9: mov bx,sp
L_aadb: push di                                       ; original aadb: push di
L_aadc: push si                                       ; original aadc: push si
L_aadd: mov si,[bx+0x2]                               ; original aadd: mov si,[bx+0x2]
L_aae0: cmp word [uart_rx_count],0x0                         ; original aae0: cmp word [0x8e20],0x0
L_aae5: jz short L_aaef                               ; original aae5: jz 0xaaef
L_aae7: call L_aa65                                   ; original aae7: call 0xaa65
L_aaea: pop si                                        ; original aaea: pop si
L_aaeb: pop di                                        ; original aaeb: pop di
L_aaec: ret word 0x2                                  ; original aaec: ret word 0x2
L_aaef: call pcplus_seconds                                   ; original aaef: call 0x3323
L_aaf2: mov_load di,ax                                ; original aaf2: mov di,ax
L_aaf4: or_load si,si                                 ; original aaf4: or si,si
L_aaf6: jz short L_aae7                               ; original aaf6: jz 0xaae7
L_aaf8: cmp word [uart_rx_count],0x0                         ; original aaf8: cmp word [0x8e20],0x0
L_aafd: jnz short L_aae7                              ; original aafd: jnz 0xaae7
L_aaff: call pcplus_seconds                                   ; original aaff: call 0x3323
L_ab02: cmp_load ax,di                                ; original ab02: cmp ax,di
L_ab04: jz short L_aaf4                               ; original ab04: jz 0xaaf4
L_ab06: mov_load di,ax                                ; original ab06: mov di,ax
L_ab08: dec si                                        ; original ab08: dec si
L_ab09: jmp short L_aaf4                              ; original ab09: jmp 0xaaf4

uart_transmit_byte:
L_ab0b: mov_load bx,sp                                ; original ab0b: mov bx,sp
L_ab0d: mov cx,[bx+0x2]                               ; original ab0d: mov cx,[bx+0x2]
L_ab10: cmp word [uart_tx_paused],0x1                         ; original ab10: cmp word [0x39a6],0x1
L_ab15: jz short L_ab31                               ; original ab15: jz 0xab31
L_ab17: cmp word [uart_hardware_flow],0x1                         ; original ab17: cmp word [0x3356],0x1
L_ab1c: jz short L_ab80                               ; original ab1c: jz 0xab80
L_ab1e: mov dx,[uart_port_lsr]                               ; original ab1e: mov dx,[0x900a]
L_ab22: in al,dx                                      ; original ab22: in al,dx
L_ab23: and al,0x20                                   ; original ab23: and al,0x20
L_ab25: jz short L_ab22                               ; original ab25: jz 0xab22
L_ab27: mov_load al,cl                                ; original ab27: mov al,cl
L_ab29: mov dx,[uart_port_thr]                               ; original ab29: mov dx,[0x9012]
L_ab2d: out dx,al                                     ; original ab2d: out dx,al
L_ab2e: ret word 0x2                                  ; original ab2e: ret word 0x2
L_ab31: push cx                                       ; original ab31: push cx
L_ab32: push di                                       ; original ab32: push di
L_ab33: push si                                       ; original ab33: push si
L_ab34: mov si,0x14                                   ; original ab34: mov si,0x14
L_ab37: call pcplus_seconds                                   ; original ab37: call 0x3323
L_ab3a: mov_load di,ax                                ; original ab3a: mov di,ax
L_ab3c: mov ax,0x1                                    ; original ab3c: mov ax,0x1
L_ab3f: call L_ac0e                                   ; original ab3f: call 0xac0e
L_ab42: call pcplus_flow_bell                                   ; original ab42: call 0x3778
L_ab45: sub_load ax,ax                                ; original ab45: sub ax,ax
L_ab47: push ax                                       ; original ab47: push ax
L_ab48: mov ax,uart_flow_message                                 ; original ab48: mov ax,0x7deb
L_ab4b: push ax                                       ; original ab4b: push ax
L_ab4c: call pcplus_flow_message                                   ; original ab4c: call 0x31bb
L_ab4f: add sp,0x4                                    ; original ab4f: add sp,0x4
L_ab52: cmp word [uart_tx_paused],0x0                         ; original ab52: cmp word [0x39a6],0x0
L_ab57: jz short L_ab70                               ; original ab57: jz 0xab70
L_ab59: or_load si,si                                 ; original ab59: or si,si
L_ab5b: jz short L_ab70                               ; original ab5b: jz 0xab70
L_ab5d: call pcplus_escape_pressed                                   ; original ab5d: call 0x3f4b
L_ab60: or_load ax,ax                                 ; original ab60: or ax,ax
L_ab62: jnz short L_ab70                              ; original ab62: jnz 0xab70
L_ab64: call pcplus_seconds                                   ; original ab64: call 0x3323
L_ab67: cmp_load ax,di                                ; original ab67: cmp ax,di
L_ab69: jz short L_ab52                               ; original ab69: jz 0xab52
L_ab6b: mov_load di,ax                                ; original ab6b: mov di,ax
L_ab6d: dec si                                        ; original ab6d: dec si
L_ab6e: jmp short L_ab52                              ; original ab6e: jmp 0xab52
L_ab70: mov word [uart_tx_paused],0x0                         ; original ab70: mov word [0x39a6],0x0
L_ab76: xor_load ax,ax                                ; original ab76: xor ax,ax
L_ab78: call L_ac0e                                   ; original ab78: call 0xac0e
L_ab7b: pop si                                        ; original ab7b: pop si
L_ab7c: pop di                                        ; original ab7c: pop di
L_ab7d: pop cx                                        ; original ab7d: pop cx
L_ab7e: jmp short L_ab17                              ; original ab7e: jmp 0xab17
L_ab80: push cx                                       ; original ab80: push cx
L_ab81: call L_abc1                                   ; original ab81: call 0xabc1
L_ab84: or_load ax,ax                                 ; original ab84: or ax,ax
L_ab86: jnz short L_ab8f                              ; original ab86: jnz 0xab8f
L_ab88: call pcplus_escape_pressed                                   ; original ab88: call 0x3f4b
L_ab8b: or_load ax,ax                                 ; original ab8b: or ax,ax
L_ab8d: jz short L_ab81                               ; original ab8d: jz 0xab81
L_ab8f: pop cx                                        ; original ab8f: pop cx
L_ab90: jmp short L_ab1e                              ; original ab90: jmp 0xab1e

uart_transmit_buffer:
L_ab92: mov_load bx,sp                                ; original ab92: mov bx,sp
L_ab94: push di                                       ; original ab94: push di
L_ab95: push si                                       ; original ab95: push si
L_ab96: mov si,[bx+0x4]                               ; original ab96: mov si,[bx+0x4]
L_ab99: mov di,[bx+0x2]                               ; original ab99: mov di,[bx+0x2]
L_ab9c: dec si                                        ; original ab9c: dec si
L_ab9d: inc si                                        ; original ab9d: inc si
L_ab9e: mov al,[si]                                   ; original ab9e: mov al,[si]
L_aba0: push ax                                       ; original aba0: push ax
L_aba1: call L_ab0b                                   ; original aba1: call 0xab0b
L_aba4: dec di                                        ; original aba4: dec di
L_aba5: jnz short L_ab9d                              ; original aba5: jnz 0xab9d
L_aba7: pop si                                        ; original aba7: pop si
L_aba8: pop di                                        ; original aba8: pop di
L_aba9: ret word 0x4                                  ; original aba9: ret word 0x4

uart_transmit_string:
L_abac: mov_load bx,sp                                ; original abac: mov bx,sp
L_abae: push si                                       ; original abae: push si
L_abaf: mov si,[bx+0x2]                               ; original abaf: mov si,[bx+0x2]
L_abb2: jmp short L_abb8                              ; original abb2: jmp 0xabb8
L_abb4: push ax                                       ; original abb4: push ax
L_abb5: call L_ab0b                                   ; original abb5: call 0xab0b
L_abb8: lodsb                                         ; original abb8: lodsb
L_abb9: cmp al,0x0                                    ; original abb9: cmp al,0x0
L_abbb: jnz short L_abb4                              ; original abbb: jnz 0xabb4
L_abbd: pop si                                        ; original abbd: pop si
L_abbe: ret word 0x2                                  ; original abbe: ret word 0x2

uart_clear_to_send:
L_abc1: mov dx,[uart_port_msr]                               ; original abc1: mov dx,[0x8ffe]
L_abc5: in al,dx                                      ; original abc5: in al,dx
L_abc6: and ax,strict word 0x10                       ; original abc6: and ax,0x10
L_abc9: ret                                           ; original abc9: ret

uart_clear_receive_buffer:
L_abca: mov bx,uart_rx_buffer                                 ; original abca: mov bx,0x7e20
L_abcd: cli                                           ; original abcd: cli
L_abce: mov [uart_rx_write],bx                               ; original abce: mov [0x7e19],bx
L_abd2: mov [uart_rx_read],bx                               ; original abd2: mov [0x7e1b],bx
L_abd6: mov word [uart_rx_count],0x0                         ; original abd6: mov word [0x8e20],0x0
L_abdc: sti                                           ; original abdc: sti
L_abdd: ret                                           ; original abdd: ret

uart_unreceive_byte:
L_abde: mov ax,uart_rx_buffer                                 ; original abde: mov ax,0x7e20
L_abe1: cli                                           ; original abe1: cli
L_abe2: cmp ax,[uart_rx_read]                               ; original abe2: cmp ax,[0x7e1b]
L_abe6: jz short L_abf2                               ; original abe6: jz 0xabf2
L_abe8: dec word [uart_rx_read]                             ; original abe8: dec word [0x7e1b]
L_abec: inc word [uart_rx_count]                             ; original abec: inc word [0x8e20]
L_abf0: sti                                           ; original abf0: sti
L_abf1: ret                                           ; original abf1: ret
L_abf2: mov ax,[uart_rx_last]                               ; original abf2: mov ax,[0x7e1d]
L_abf5: mov [uart_rx_read],ax                               ; original abf5: mov [0x7e1b],ax
L_abf8: jmp short L_abec                              ; original abf8: jmp 0xabec

uart_set_rts:
L_abfa: mov_load bx,sp                                ; original abfa: mov bx,sp
L_abfc: mov cx,[bx+0x2]                               ; original abfc: mov cx,[bx+0x2]
L_abff: mov al,0xb                                    ; original abff: mov al,0xb
L_ac01: cmp cx,0x1                                    ; original ac01: cmp cx,0x1
L_ac04: jz short L_ac08                               ; original ac04: jz 0xac08
L_ac06: mov al,0x9                                    ; original ac06: mov al,0x9
L_ac08: mov dx,[uart_port_mcr]                               ; original ac08: mov dx,[0x8ff4]
L_ac0c: out dx,al                                     ; original ac0c: out dx,al
L_ac0d: ret                                           ; original ac0d: ret
L_ac0e: mov bx,uart_flow_screen_save                                 ; original ac0e: mov bx,0x7df9
L_ac11: push bx                                       ; original ac11: push bx
L_ac12: mov bx,0xf00                                  ; original ac12: mov bx,0xf00
L_ac15: push bx                                       ; original ac15: push bx
L_ac16: mov bx,0xf                                    ; original ac16: mov bx,0xf
L_ac19: push bx                                       ; original ac19: push bx
L_ac1a: cmp ax,strict word 0x0                        ; original ac1a: cmp ax,0x0
L_ac1d: jnz short L_ac23                              ; original ac1d: jnz 0xac23
L_ac1f: call pcplus_screen_restore                                   ; original ac1f: call 0x7682
L_ac22: ret                                           ; original ac22: ret
L_ac23: call pcplus_screen_save                                   ; original ac23: call 0x765c
L_ac26: ret                                           ; original ac26: ret

uart_set_baud_divisor:
L_ac27: mov_load bx,sp                                ; original ac27: mov bx,sp
L_ac29: mov cx,0x1                                    ; original ac29: mov cx,0x1
L_ac2c: cmp word [bx+0x4],0x1                         ; original ac2c: cmp word [bx+0x4],0x1
L_ac30: jz short L_ac3f                               ; original ac30: jz 0xac3f
L_ac32: mov bx,[bx+0x2]                               ; original ac32: mov bx,[bx+0x2]
L_ac35: mov dx,0x1                                    ; original ac35: mov dx,0x1
L_ac38: mov ax,0xc200                                 ; original ac38: mov ax,0xc200
L_ac3b: div bx                                        ; original ac3b: div bx
L_ac3d: mov_load cx,ax                                ; original ac3d: mov cx,ax
L_ac3f: mov dx,[uart_port_lcr]                               ; original ac3f: mov dx,[0x8fee]
L_ac43: in al,dx                                      ; original ac43: in al,dx
L_ac44: mov_load bl,al                                ; original ac44: mov bl,al
L_ac46: or ax,0x80                                    ; original ac46: or ax,0x80
L_ac49: out dx,al                                     ; original ac49: out dx,al
L_ac4a: mov dx,[uart_port_thr]                               ; original ac4a: mov dx,[0x9012]
L_ac4e: mov_load ax,cx                                ; original ac4e: mov ax,cx
L_ac50: out dx,al                                     ; original ac50: out dx,al
L_ac51: inc dx                                        ; original ac51: inc dx
L_ac52: mov_load al,ah                                ; original ac52: mov al,ah
L_ac54: out dx,al                                     ; original ac54: out dx,al
L_ac55: mov dx,[uart_port_lcr]                               ; original ac55: mov dx,[0x8fee]
L_ac59: mov_load al,bl                                ; original ac59: mov al,bl
L_ac5b: out dx,al                                     ; original ac5b: out dx,al
L_ac5c: ret                                           ; original ac5c: ret

uart_set_line_control:
L_ac5d: push bp                                       ; original ac5d: push bp
L_ac5e: mov_load bp,sp                                ; original ac5e: mov bp,sp
L_ac60: mov bx,[bp+0x4]                               ; original ac60: mov bx,[bp+0x4]
L_ac63: cmp bx,0x0                                    ; original ac63: cmp bx,0x0
L_ac66: jnz short L_ac6c                              ; original ac66: jnz 0xac6c
L_ac68: xor_load al,al                                ; original ac68: xor al,al
L_ac6a: jmp short L_ac8d                              ; original ac6a: jmp 0xac8d
L_ac6c: mov al,0x8                                    ; original ac6c: mov al,0x8
L_ac6e: cmp bx,0x1                                    ; original ac6e: cmp bx,0x1
L_ac71: jnz short L_ac77                              ; original ac71: jnz 0xac77
L_ac73: and al,0xef                                   ; original ac73: and al,0xef
L_ac75: jmp short L_ac8d                              ; original ac75: jmp 0xac8d
L_ac77: cmp bx,0x2                                    ; original ac77: cmp bx,0x2
L_ac7a: jnz short L_ac80                              ; original ac7a: jnz 0xac80
L_ac7c: or al,0x18                                    ; original ac7c: or al,0x18
L_ac7e: jmp short L_ac8d                              ; original ac7e: jmp 0xac8d
L_ac80: or al,0x20                                    ; original ac80: or al,0x20
L_ac82: cmp bx,0x3                                    ; original ac82: cmp bx,0x3
L_ac85: jnz short L_ac8b                              ; original ac85: jnz 0xac8b
L_ac87: and al,0xef                                   ; original ac87: and al,0xef
L_ac89: jmp short L_ac8d                              ; original ac89: jmp 0xac8d
L_ac8b: or al,0x38                                    ; original ac8b: or al,0x38
L_ac8d: or al,0x2                                     ; original ac8d: or al,0x2
L_ac8f: mov bx,[bp+0x6]                               ; original ac8f: mov bx,[bp+0x6]
L_ac92: cmp bx,0x7                                    ; original ac92: cmp bx,0x7
L_ac95: jnz short L_ac9b                              ; original ac95: jnz 0xac9b
L_ac97: and al,0xfe                                   ; original ac97: and al,0xfe
L_ac99: jmp short L_ac9d                              ; original ac99: jmp 0xac9d
L_ac9b: or al,0x3                                     ; original ac9b: or al,0x3
L_ac9d: mov bx,[bp+0x8]                               ; original ac9d: mov bx,[bp+0x8]
L_aca0: cmp bx,0x1                                    ; original aca0: cmp bx,0x1
L_aca3: jnz short L_aca9                              ; original aca3: jnz 0xaca9
L_aca5: and al,0xfb                                   ; original aca5: and al,0xfb
L_aca7: jmp short L_acab                              ; original aca7: jmp 0xacab
L_aca9: or al,0x4                                     ; original aca9: or al,0x4
L_acab: mov dx,[uart_port_lcr]                               ; original acab: mov dx,[0x8fee]
L_acaf: out dx,al                                     ; original acaf: out dx,al
L_acb0: pop bp                                        ; original acb0: pop bp
L_acb1: ret                                           ; original acb1: ret
uart_saved_ds: dw 0
uart_previous_irq_offset: dw 0
uart_previous_irq_segment: dw 0


uart_receive_interrupt:
L_acb8: push ax                                       ; original acb8: push ax
L_acb9: push dx                                       ; original acb9: push dx
L_acba: push ds                                       ; original acba: push ds
%ifdef UART_OMF
L_acbb: mov ax,seg uart_rx_count ; Linker supplies the data segment.
%else
L_acbb: mov ax,0xfb7                                  ; original acbb: mov ax,0xfb7
%endif
L_acbe: mov ds,ax                                     ; original acbe: mov ds,ax
L_acc0: mov dx,[uart_port_rbr]                               ; original acc0: mov dx,[0x9022]
L_acc4: in al,dx                                      ; original acc4: in al,dx
L_acc5: push bx                                       ; original acc5: push bx
L_acc6: push cx                                       ; original acc6: push cx
L_acc7: mov bx,[uart_rx_write]                               ; original acc7: mov bx,[0x7e19]
L_accb: cmp word [uart_software_flow],0x0                         ; original accb: cmp word [0x3354],0x0
L_acd0: jnz short L_ad09                              ; original acd0: jnz 0xad09
L_acd2: cmp word [uart_hardware_flow],0x0                         ; original acd2: cmp word [0x3356],0x0
L_acd7: jnz short L_ad42                              ; original acd7: jnz 0xad42
L_acd9: cmp word [uart_rx_count],0x1000                      ; original acd9: cmp word [0x8e20],0x1000
%ifdef UART_OMF
L_acdf: jz short L_ace1 ; Use the maintained overflow guard and counter.
%else
L_acdf: jz short L_acfa                               ; original acdf: jz 0xacfa
%endif
L_ace1:
%ifdef UART_OMF
    ; Source-build fix: RTS is advisory; never overwrite unread ring data.
    cmp word [uart_rx_count],4096
    jb omf_rx_store
    cmp word [uart_rx_dropped],0xffff
    je L_acf2
    inc word [uart_rx_dropped]
    jmp L_acf2
omf_rx_store:
%endif
         mov [bx],al                                   ; original ace1: mov [bx],al
L_ace3: inc word [uart_rx_count]                             ; original ace3: inc word [0x8e20]
L_ace7: cmp bx,[uart_rx_last]                               ; original ace7: cmp bx,[0x7e1d]
L_aceb: jz short L_ad04                               ; original aceb: jz 0xad04
L_aced: inc bx                                        ; original aced: inc bx
L_acee: mov [uart_rx_write],bx                               ; original acee: mov [0x7e19],bx
L_acf2: add dx,0x2                                    ; original acf2: add dx,0x2
L_acf5: in al,dx                                      ; original acf5: in al,dx
L_acf6: and al,0x4                                    ; original acf6: and al,0x4
L_acf8: jnz short L_ad5e                              ; original acf8: jnz 0xad5e
L_acfa: pop cx                                        ; original acfa: pop cx
L_acfb: pop bx                                        ; original acfb: pop bx
L_acfc: pop ds                                        ; original acfc: pop ds
L_acfd: pop dx                                        ; original acfd: pop dx
L_acfe: mov al,0x20                                   ; original acfe: mov al,0x20
L_ad00: out byte 0x20,al                              ; original ad00: out byte 0x20,al
L_ad02: pop ax                                        ; original ad02: pop ax
L_ad03: iret                                          ; original ad03: iret
L_ad04: mov bx,uart_rx_buffer                                 ; original ad04: mov bx,0x7e20
L_ad07: jmp short L_acee                              ; original ad07: jmp 0xacee
L_ad09: mov_load cl,al                                ; original ad09: mov cl,al
L_ad0b: cmp cl,0x13                                   ; original ad0b: cmp cl,0x13
L_ad0e: jz short L_ad32                               ; original ad0e: jz 0xad32
L_ad10: cmp cl,0x11                                   ; original ad10: cmp cl,0x11
L_ad13: jz short L_ad3a                               ; original ad13: jz 0xad3a
L_ad15: test byte [uart_xoff_sent],0x1                        ; original ad15: test byte [0x7e17],0x1
L_ad1a: jnz short L_acd9                              ; original ad1a: jnz 0xacd9
L_ad1c: cmp word [uart_rx_count],0xc00                       ; original ad1c: cmp word [0x8e20],0xc00
L_ad22: jc short L_ace1                               ; original ad22: jc 0xace1
L_ad24: push ax                                       ; original ad24: push ax
L_ad25: mov byte [uart_xoff_sent],0x1                         ; original ad25: mov byte [0x7e17],0x1
L_ad2a: mov cl,0x13                                   ; original ad2a: mov cl,0x13
%ifdef UART_OMF
    mov byte [uart_flow_pending],0x13
%else
L_ad2c: call L_ad93                                   ; original ad2c: call 0xad93
%endif
L_ad2f: pop ax                                        ; original ad2f: pop ax
L_ad30: jmp short L_ace1                              ; original ad30: jmp 0xace1
L_ad32: mov word [uart_tx_paused],0x1                         ; original ad32: mov word [0x39a6],0x1
L_ad38: jmp short L_acfa                              ; original ad38: jmp 0xacfa
L_ad3a: mov word [uart_tx_paused],0x0                         ; original ad3a: mov word [0x39a6],0x0
L_ad40: jmp short L_acfa                              ; original ad40: jmp 0xacfa
L_ad42: cmp word [uart_rx_count],0xc00                       ; original ad42: cmp word [0x8e20],0xc00
L_ad48: jc short L_ace1                               ; original ad48: jc 0xace1
L_ad4a: mov_load cl,al                                ; original ad4a: mov cl,al
L_ad4c: mov al,0x9                                    ; original ad4c: mov al,0x9
L_ad4e: push dx                                       ; original ad4e: push dx
L_ad4f: mov dx,[uart_port_mcr]                               ; original ad4f: mov dx,[0x8ff4]
L_ad53: out dx,al                                     ; original ad53: out dx,al
L_ad54: pop dx                                        ; original ad54: pop dx
L_ad55: mov_load al,cl                                ; original ad55: mov al,cl
L_ad57: mov byte [uart_rts_lowered],0x1                         ; original ad57: mov byte [0x7e18],0x1
L_ad5c: jmp short L_ace1                              ; original ad5c: jmp 0xace1
L_ad5e: sub dx,0x2                                    ; original ad5e: sub dx,0x2
L_ad61: in al,dx                                      ; original ad61: in al,dx
L_ad62: jmp near L_accb                               ; original ad62: jmp 0xaccb

uart_install_interrupt:
L_ad65: push bp                                       ; original ad65: push bp
L_ad66: mov_load bp,sp                                ; original ad66: mov bp,sp
L_ad68: push ds                                       ; original ad68: push ds
L_ad69: push es                                       ; original ad69: push es
L_ad6a: mov ax,ds                                     ; original ad6a: mov ax,ds
L_ad6c: mov [cs:uart_saved_ds],ax                            ; original ad6c: mov [cs:0xacb2],ax
L_ad70: mov ax,[bp+0x4]                               ; original ad70: mov ax,[bp+0x4]
L_ad73: mov ah,0x35                                   ; original ad73: mov ah,0x35
L_ad75: int byte 0x21                                 ; original ad75: int byte 0x21
L_ad77: mov [cs:uart_previous_irq_offset],bx                            ; original ad77: mov [cs:0xacb4],bx
L_ad7c: mov word [cs:uart_previous_irq_segment],es                       ; original ad7c: mov word [cs:0xacb6],es
L_ad81: mov ax,cs                                     ; original ad81: mov ax,cs
L_ad83: mov ds,ax                                     ; original ad83: mov ds,ax
L_ad85: mov dx,uart_receive_interrupt                                 ; original ad85: mov dx,0xacb8
L_ad88: mov ax,[bp+0x4]                               ; original ad88: mov ax,[bp+0x4]
L_ad8b: mov ah,0x25                                   ; original ad8b: mov ah,0x25
L_ad8d: int byte 0x21                                 ; original ad8d: int byte 0x21
L_ad8f: pop es                                        ; original ad8f: pop es
L_ad90: pop ds                                        ; original ad90: pop ds
L_ad91: pop bp                                        ; original ad91: pop bp
L_ad92: ret                                           ; original ad92: ret

uart_transmit_cl:
L_ad93: mov dx,[uart_port_lsr]                               ; original ad93: mov dx,[0x900a]
L_ad97: in al,dx                                      ; original ad97: in al,dx
L_ad98: and al,0x20                                   ; original ad98: and al,0x20
L_ad9a: jz short L_ad97                               ; original ad9a: jz 0xad97
L_ad9c: mov_load al,cl                                ; original ad9c: mov al,cl
L_ad9e: mov dx,[uart_port_thr]                               ; original ad9e: mov dx,[0x9012]
L_ada2: out dx,al                                     ; original ada2: out dx,al
L_ada3: ret                                           ; original ada3: ret

uart_restore_interrupt:
L_ada4: mov_load bx,sp                                ; original ada4: mov bx,sp
L_ada6: mov ax,[bx+0x2]                               ; original ada6: mov ax,[bx+0x2]
L_ada9: push ds                                       ; original ada9: push ds
L_adaa: mov dx,[cs:uart_previous_irq_offset]                            ; original adaa: mov dx,[cs:0xacb4]
L_adaf: mov ds,word [cs:uart_previous_irq_segment]                       ; original adaf: mov ds,word [cs:0xacb6]
L_adb4: mov ah,0x25                                   ; original adb4: mov ah,0x25
L_adb6: int byte 0x21                                 ; original adb6: int byte 0x21
L_adb8: pop ds                                        ; original adb8: pop ds
L_adb9: ret                                           ; original adb9: ret

uart_disable:
L_adba: cli                                           ; original adba: cli
L_adbb: call L_add6                                   ; original adbb: call 0xadd6
L_adbe: mov dx,[uart_port_lcr]                               ; original adbe: mov dx,[0x8fee]
L_adc2: in al,dx                                      ; original adc2: in al,dx
L_adc3: and al,0x7f                                   ; original adc3: and al,0x7f
L_adc5: out dx,al                                     ; original adc5: out dx,al
L_adc6: mov dx,[uart_port_ier]                               ; original adc6: mov dx,[0x901a]
L_adca: mov al,0x0                                    ; original adca: mov al,0x0
L_adcc: out dx,al                                     ; original adcc: out dx,al
L_adcd: mov dx,[uart_port_mcr]                               ; original adcd: mov dx,[0x8ff4]
L_add1: mov al,0x0                                    ; original add1: mov al,0x0
L_add3: out dx,al                                     ; original add3: out dx,al
L_add4: sti                                           ; original add4: sti
L_add5: ret                                           ; original add5: ret

uart_mask_irq:
L_add6: in al,byte 0x21                               ; original add6: in al,byte 0x21
L_add8: mov bx,[uart_port_index]                               ; original add8: mov bx,[0x1b84]
L_addc: shl bx,1                                      ; original addc: shl bx,1
L_adde: mov bx,[bx+uart_irq_indices]                            ; original adde: mov bx,[bx+0x1d08]
L_ade2: shl bx,1                                      ; original ade2: shl bx,1
L_ade4: or ax,[bx+uart_irq_disable_masks]                             ; original ade4: or ax,[bx+0x3368]
L_ade8: out byte 0x21,al                              ; original ade8: out byte 0x21,al
L_adea: ret                                           ; original adea: ret

uart_enable:
L_adeb: mov al,0xb                                    ; original adeb: mov al,0xb
L_aded: mov dx,[uart_port_mcr]                               ; original aded: mov dx,[0x8ff4]
L_adf1: out dx,al                                     ; original adf1: out dx,al
L_adf2: mov dx,[uart_port_msr]                               ; original adf2: mov dx,[0x8ffe]
L_adf6: in al,dx                                      ; original adf6: in al,dx
L_adf7: mov dx,[uart_port_lsr]                               ; original adf7: mov dx,[0x900a]
L_adfb: in al,dx                                      ; original adfb: in al,dx
L_adfc: mov dx,[uart_port_thr]                               ; original adfc: mov dx,[0x9012]
L_ae00: in al,dx                                      ; original ae00: in al,dx
L_ae01: mov dx,[uart_port_lcr]                               ; original ae01: mov dx,[0x8fee]
L_ae05: in al,dx                                      ; original ae05: in al,dx
L_ae06: and al,0x7f                                   ; original ae06: and al,0x7f
L_ae08: out dx,al                                     ; original ae08: out dx,al
L_ae09: mov al,0x1                                    ; original ae09: mov al,0x1
L_ae0b: mov dx,[uart_port_ier]                               ; original ae0b: mov dx,[0x901a]
L_ae0f: out dx,al                                     ; original ae0f: out dx,al
L_ae10: in al,byte 0x21                               ; original ae10: in al,byte 0x21
L_ae12: mov bx,[uart_port_index]                               ; original ae12: mov bx,[0x1b84]
L_ae16: shl bx,1                                      ; original ae16: shl bx,1
L_ae18: mov bx,[bx+uart_irq_indices]                            ; original ae18: mov bx,[bx+0x1d08]
L_ae1c: shl bx,1                                      ; original ae1c: shl bx,1
L_ae1e: and ax,[bx+uart_irq_enable_masks]                            ; original ae1e: and ax,[bx+0x3358]
L_ae22: out byte 0x21,al                              ; original ae22: out byte 0x21,al
L_ae24: ret                                           ; original ae24: ret

uart_wait_transmitter_empty:
L_ae25: mov dx,[uart_port_lsr]                               ; original ae25: mov dx,[0x900a]
L_ae29: in al,dx                                      ; original ae29: in al,dx
L_ae2a: and al,0x60                                   ; original ae2a: and al,0x60
L_ae2c: cmp al,0x60                                   ; original ae2c: cmp al,0x60
L_ae2e: jnz short L_ae29                              ; original ae2e: jnz 0xae29
L_ae30: ret                                           ; original ae30: ret
db 0 ; original alignment byte at 0xae31

uart_save_hardware_state:
L_ae32: in al,byte 0x21                               ; original ae32: in al,byte 0x21
L_ae34: mov [uart_saved_pic],al                               ; original ae34: mov [0x9024],al
L_ae37: mov dx,[uart_port_lcr]                               ; original ae37: mov dx,[0x8fee]
L_ae3b: in al,dx                                      ; original ae3b: in al,dx
L_ae3c: mov [uart_saved_lcr],al                               ; original ae3c: mov [0x902c],al
L_ae3f: and al,0x7f                                   ; original ae3f: and al,0x7f
L_ae41: out dx,al                                     ; original ae41: out dx,al
L_ae42: mov dx,[uart_port_mcr]                               ; original ae42: mov dx,[0x8ff4]
L_ae46: in al,dx                                      ; original ae46: in al,dx
L_ae47: mov [uart_saved_mcr],al                               ; original ae47: mov [0x9034],al
L_ae4a: mov dx,[uart_port_ier]                               ; original ae4a: mov dx,[0x901a]
L_ae4e: in al,dx                                      ; original ae4e: in al,dx
L_ae4f: mov [uart_saved_ier],al                               ; original ae4f: mov [0x9040],al
L_ae52: mov dx,[uart_port_lcr]                               ; original ae52: mov dx,[0x8fee]
L_ae56: in al,dx                                      ; original ae56: in al,dx
L_ae57: or ax,0x80                                    ; original ae57: or ax,0x80
L_ae5a: out dx,al                                     ; original ae5a: out dx,al
L_ae5b: mov dx,[uart_port_thr]                               ; original ae5b: mov dx,[0x9012]
L_ae5f: in al,dx                                      ; original ae5f: in al,dx
L_ae60: mov [uart_saved_dll],al                               ; original ae60: mov [0x9044],al
L_ae63: inc dx                                        ; original ae63: inc dx
L_ae64: in al,dx                                      ; original ae64: in al,dx
L_ae65: mov [uart_saved_dlm],al                               ; original ae65: mov [0x904b],al
L_ae68: ret                                           ; original ae68: ret

uart_restore_hardware_state:
L_ae69: mov al,[uart_saved_pic]                               ; original ae69: mov al,[0x9024]
L_ae6c: out byte 0x21,al                              ; original ae6c: out byte 0x21,al
L_ae6e: mov dx,[uart_port_lcr]                               ; original ae6e: mov dx,[0x8fee]
L_ae72: in al,dx                                      ; original ae72: in al,dx
L_ae73: mov_load bl,al                                ; original ae73: mov bl,al
L_ae75: or ax,0x80                                    ; original ae75: or ax,0x80
L_ae78: out dx,al                                     ; original ae78: out dx,al
L_ae79: mov dx,[uart_port_thr]                               ; original ae79: mov dx,[0x9012]
L_ae7d: mov al,[uart_saved_dll]                               ; original ae7d: mov al,[0x9044]
L_ae80: out dx,al                                     ; original ae80: out dx,al
L_ae81: inc dx                                        ; original ae81: inc dx
L_ae82: mov al,[uart_saved_dlm]                               ; original ae82: mov al,[0x904b]
L_ae85: out dx,al                                     ; original ae85: out dx,al
L_ae86: mov dx,[uart_port_lcr]                               ; original ae86: mov dx,[0x8fee]
L_ae8a: in al,dx                                      ; original ae8a: in al,dx
L_ae8b: and al,0x7f                                   ; original ae8b: and al,0x7f
L_ae8d: out dx,al                                     ; original ae8d: out dx,al
L_ae8e: mov dx,[uart_port_mcr]                               ; original ae8e: mov dx,[0x8ff4]
L_ae92: mov al,[uart_saved_mcr]                               ; original ae92: mov al,[0x9034]
L_ae95: out dx,al                                     ; original ae95: out dx,al
L_ae96: mov dx,[uart_port_ier]                               ; original ae96: mov dx,[0x901a]
L_ae9a: mov al,[uart_saved_ier]                               ; original ae9a: mov al,[0x9040]
L_ae9d: out dx,al                                     ; original ae9d: out dx,al
L_ae9e: mov dx,[uart_port_lcr]                               ; original ae9e: mov dx,[0x8fee]
L_aea2: mov al,[uart_saved_lcr]                               ; original aea2: mov al,[0x902c]
L_aea5: out dx,al                                     ; original aea5: out dx,al
L_aea6: ret                                           ; original aea6: ret
