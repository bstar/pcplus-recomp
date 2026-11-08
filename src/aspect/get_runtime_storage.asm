; Far retained editor state, declared as a far external by get_runtime.c.
; Standalone segment deliberately excluded from DGROUP; layout200 bytes is
; checked by C and diagnostic linker-map admission. Contains no borrowed pointer.
BITS 16
CPU 8086
SEGMENT GET_RUNTIME_STORAGE public align=16 class=FAR_DATA use16
global _runtime_get_field_storage
_runtime_get_field_storage: times 200 db 0
