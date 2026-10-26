; Explicit small-model cdecl FS adapters; the reader preserves DS=SS and passes
; near DOS buffers. No implicit stack forwarding or serial/UI ownership.
BITS 16
CPU 8086
%include "far_bridge.inc"
SEGMENT _TEXT public class=CODE use16
NEAR_CDECL_SERVICE _directory_reader_bank_open,_directory_reader_fs_open,2
NEAR_CDECL_SERVICE _directory_reader_bank_read,_directory_reader_fs_read,4
NEAR_CDECL_SERVICE _directory_reader_bank_close,_directory_reader_fs_close,1
SEGMENT DIRECTORY_CODE public align=16 class=FARCODE use16
GROUP DIRECTORY_GROUP DIRECTORY_CODE
FAR_CDECL_SERVICE _directory_reader_bank_open,_directory_reader_fs_open,2
FAR_CDECL_SERVICE _directory_reader_bank_read,_directory_reader_fs_read,4
FAR_CDECL_SERVICE _directory_reader_bank_close,_directory_reader_fs_close,1
