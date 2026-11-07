; Near Watcom register calls from the transient bank use existing resident
; callbacks. Never encode a near call to the parent's different code segment.
BITS 16
CPU 8086
SEGMENT LINE_PORT_CODE public align=16 class=FARCODE use16
%macro service 1
global line_%1_service_
extern config_%1_service__resident
line_%1_service_:
 call far config_%1_service__resident
 ret
%endmacro
service memcpy
service memset
service memcmp
; Explicit near-cdecl service frames match CONFIG_CDECL's resident adapters:
; caller's near return plus our far return precede their argument words.
global _line_overlay_paths,_line_overlay_prm_read
extern _config_line_paths_resident,_config_prm_read_resident
_line_overlay_paths:
 call far _config_line_paths_resident
 ret
_line_overlay_prm_read:
 call far _config_prm_read_resident
 ret
