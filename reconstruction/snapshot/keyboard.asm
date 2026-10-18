; Exact original screen snapshot instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef SNAPSHOT_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global snapshot_keyboard_original
global snapshot_at_1313
global snapshot_at_1314
global snapshot_at_1317
global snapshot_at_131a
global snapshot_at_131d
global snapshot_at_131e
global snapshot_at_1321
global snapshot_at_1324
global snapshot_at_1326
global snapshot_at_1327
global snapshot_at_132a
global snapshot_at_132d
extern snapshot_keyboard_state
extern snapshot_write_original
%else
ORG 0x1310
%define snapshot_keyboard_state 0xdae
%define snapshot_write_original 0x3496
%endif
%include "encodings.inc"
snapshot_keyboard_original: mov ax,0x1
snapshot_at_1313: push ax
snapshot_at_1314: call snapshot_keyboard_state
snapshot_at_1317: add sp,0x2
snapshot_at_131a: mov ax,0x1
snapshot_at_131d: push ax
snapshot_at_131e: call snapshot_write_original
snapshot_at_1321: add sp,0x2
snapshot_at_1324: sub_load ax,ax
snapshot_at_1326: push ax
snapshot_at_1327: call snapshot_keyboard_state
snapshot_at_132a: add sp,0x2
snapshot_at_132d: ret
