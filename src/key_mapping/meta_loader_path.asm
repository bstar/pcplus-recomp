; Direct far-cdecl entry to the parent's existing CONFIG near resolver.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
global _meta_loader_path
extern _resource_program_path
_meta_loader_path:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call _resource_program_path
 lea sp,[bp]
 pop bp
 retf
