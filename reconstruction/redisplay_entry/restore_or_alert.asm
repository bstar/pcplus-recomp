; Shared native screen restore wrapper; NULL takes an alert path, not copy/free.
BITS 16
CPU 8086
%ifdef REDISPLAY_ENTRY_OMF
SEGMENT _TEXT public class=CODE use16
global redisplay_restore_or_alert
extern display_restore,redisplay_snapshot_alert
%define short
%else
ORG 0x4870
%define display_restore 0x7558
%define redisplay_snapshot_alert 0x488f
%endif
%include "encodings.inc"
redisplay_restore_or_alert:
L_4870: push bp
L_4871: mov_load bp,sp
L_4873: mov ax,[bp+0x6]
L_4876: or ax,[bp+0x4]
L_4879: jz short L_4886
L_487b: push word [bp+0x6]
L_487e: push word [bp+0x4]
L_4881: call display_restore
L_4884: jmp short L_4889
L_4886: call redisplay_snapshot_alert
L_4889: mov_load sp,bp
L_488b: pop bp
L_488c: ret 0x4
