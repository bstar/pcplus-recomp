; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_timestamp
global session_at_f0d7
global session_at_f0da
global session_at_f0de
extern session_clock
extern session_started_high
extern session_started_low
%else
ORG 0xf0d4
%define session_clock 0x77fe
%define session_started_high 0xce08
%define session_started_low 0xce06
%endif
%include "encodings.inc"
session_timestamp: call session_clock
session_at_f0d7: mov [session_started_low],ax
session_at_f0da: mov [session_started_high],dx
session_at_f0de: ret
