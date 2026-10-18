; Exact original screen snapshot instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef SNAPSHOT_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global snapshot_video_end
global snapshot_at_77b2
global snapshot_at_77b5
global snapshot_at_77b7
global snapshot_at_77b9
global snapshot_at_77bb
global snapshot_at_77bc
extern snapshot_cga_status_port
%else
ORG 0x77ae
%define snapshot_cga_status_port 0x7a8e
%endif
%include "encodings.inc"
snapshot_video_end: mov dx,[snapshot_cga_status_port]
snapshot_at_77b2: cmp dx,0x0
snapshot_at_77b5: jz short snapshot_at_77bc
snapshot_at_77b7: mov al,0x2d
snapshot_at_77b9: mov dl,0xd8
snapshot_at_77bb: out dx,al
snapshot_at_77bc: ret
