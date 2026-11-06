; Exact native fallback. Tone/screen service semantics remain external here.
BITS 16
CPU 8086
%ifdef REDISPLAY_ENTRY_OMF
SEGMENT _TEXT public class=CODE use16
global redisplay_snapshot_alert
extern redisplay_alert_376d,redisplay_tone_7722
%else
ORG 0x488f
%define redisplay_alert_376d 0x376d
%define redisplay_tone_7722 0x7722
%endif
redisplay_snapshot_alert:
L_488f: call redisplay_alert_376d
L_4892: mov ax,0x1b8
L_4895: push ax
L_4896: mov ax,0x64
L_4899: push ax
L_489a: call redisplay_tone_7722
L_489d: call redisplay_alert_376d
L_48a0: ret
