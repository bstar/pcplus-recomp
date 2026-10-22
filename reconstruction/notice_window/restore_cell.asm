; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_restore_cell
extern window_copy_cell
extern window_state_8fdc
extern window_state_8fda
%define short
%else
ORG 29939
%define window_copy_cell 32630
%define window_state_8fdc 36828
%define window_state_8fda 36826
%endif
%include "encodings.inc"
window_restore_cell:
L_74f3: push word [window_state_8fdc]
L_74f7: push word [window_state_8fda]
L_74fb: push ax
L_74fc: call window_copy_cell
L_74ff: ret
