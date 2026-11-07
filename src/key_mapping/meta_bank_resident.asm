; New resident services for Meta builds. The selected Line/Port parent omits
; the optional directory callbacks, so bind these names independently.
; Exactly44 _TEXT bytes, no DGROUP; DS=SS, existing near helper code reused.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
NEAR_CDECL_SERVICE _meta_bank_paths,_directory_replace_paths,3
NEAR_CDECL_SERVICE _meta_bank_actions,_key_actions_dos_read,3
NEAR_NAMED_SERVICE meta_bank_attributes_service_,capture_fs_attributes_
