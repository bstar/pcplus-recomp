; Shared CSI transition helper recovered through REA in overlay-14 context.
; Evidence ev_affa93fbfa603209be50ad0dfe0c499e94c70ee8819a6fab2f66b066eec914dc.
BITS 16
CPU 8086
%ifdef ANSI_OMF
SEGMENT _TEXT public class=CODE use16
global ansi_parameter_transition
extern ansi_command
%else
ORG 0xe4a2
%define ansi_command 0xcd38
%endif
ansi_parameter_transition:
 cmp word [ansi_command],byte ';'
 jnz .dispatch
 mov ax,'D'
 ret
 nop
.dispatch:
 mov ax,'L'
 ret
