; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_collapse_delay
extern window_pace
extern window_state_8fde
%define short
%else
ORG 29952
%define window_pace 27506
%define window_state_8fde 36830
%endif
%include "encodings.inc"
window_collapse_delay:
L_7500: push word [window_state_8fde]
L_7504: call window_pace
L_7507: ret
