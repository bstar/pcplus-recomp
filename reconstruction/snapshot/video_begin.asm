; Exact original screen snapshot instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef SNAPSHOT_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global snapshot_video_begin
global snapshot_at_77c2
global snapshot_at_77c5
global snapshot_at_77c7
global snapshot_at_77c8
global snapshot_at_77ca
global snapshot_at_77cc
global snapshot_at_77ce
global snapshot_at_77d0
global snapshot_at_77d1
extern snapshot_cga_status_port
%else
ORG 0x77be
%define snapshot_cga_status_port 0x7a8e
%endif
%include "encodings.inc"
snapshot_video_begin: mov dx,[snapshot_cga_status_port]
snapshot_at_77c2: cmp dx,0x0
snapshot_at_77c5: jz short snapshot_at_77d1
snapshot_at_77c7: in al,dx
snapshot_at_77c8: test al,0x8
snapshot_at_77ca: jz short snapshot_at_77c7
snapshot_at_77cc: mov al,0x25
snapshot_at_77ce: mov dl,0xd8
snapshot_at_77d0: out dx,al
snapshot_at_77d1: ret
