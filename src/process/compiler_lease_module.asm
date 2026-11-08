; Source-linked matched-parent module metadata patched by compiler_lease_module.py.
BITS 16
CPU 8086
%ifdef COMPILER_LEASE_RETAINED
SEGMENT LEASE_MODULE_INFO public align=16 class=LEASE_MODULE use16
GROUP LEASE_INFO_GROUP LEASE_MODULE_INFO
%else
SEGMENT LEASE_MODULE_INFO public align=16 class=FARCODE use16
%endif
global _compiler_lease_expected
_compiler_lease_expected: dw 0x4342,1,0,0,0,0,0
