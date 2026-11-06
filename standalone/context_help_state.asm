; Diagnostic ABI bindings. Original resolver/formatter/PROGRAM UI controller
; are explicit maintained boundaries; only descriptor producer is recovered.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern context_help_native,_help_probe_resolve,_help_probe_execute,_help_probe_format
global _help_probe_invoke,help_resolve,help_format_tail,help_execute
_help_probe_invoke:
 push es
 call context_help_native
 pop es
 ret
help_resolve: jmp _help_probe_resolve
help_format_tail: jmp _help_probe_format
help_execute: jmp _help_probe_execute
SEGMENT _DATA public class=DATA use16
global help_path_key,help_title,help_program_key,help_tail_format,_help_probe_title
help_path_key: db 'PCPLUS.HLP',0
help_title:
_help_probe_title: db 'LoC // PCPlus Help',0
help_program_key: db 'PCHELP.RTE',0
help_tail_format: db ' PCHELP %lu',0
%macro wordfield 2
 global %1,%2
 %1:
 %2: dw 0
%endmacro
wordfield help_topic,_help_probe_topic
wordfield help_ui_1d3e,_help_probe_ui0
wordfield help_normal,_help_probe_ui1
wordfield help_bold,_help_probe_ui2
wordfield help_reverse,_help_probe_ui3
wordfield help_mouse_x,_help_probe_ui4
wordfield help_mouse_y,_help_probe_ui5
