; Native PCPlus2.01 ASPECT receive policy: resident4C3C and reused4C74.
; OriginalSHA6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; 4C74 is reused verbatim from reconstruction/translation/receive.asm. Its
; historical translation_script_* aliases refer to the E2F8 pattern/event
; monitor and534E callback; these are not file capture or logging services.
; DS=SS,DF=0. Direct adapter takes delayed word RET2; character takes
; (echo,delayed) RET4. Raw/delayed reads return AX byte or negativeword.
; Pattern callback consumes word RET2; console emission is caller-clean.
; Pattern runs before display; both see the translated byte. Negative words
; bypass translation and both services. Nonnegative values above255 retain
; native unchecked table indexing and are outside the raw byte contract.
; The live owner supplies one immutable256-byte XLT snapshot; no second
; translation belongs in raw read or pattern/display callback adapters.
BITS 16
CPU 8086
%ifdef ASPECT_RECEIVE_POLICY_FLAT
%if ASPECT_RECEIVE_POLICY_UNIT=1
%include "encodings.inc"
%endif
%endif
%ifdef ASPECT_RECEIVE_POLICY_FLAT
%if ASPECT_RECEIVE_POLICY_UNIT=1
ORG 0x4c3c
%define aspect_receive_policy_display 0xe37e
%define aspect_receive_policy_read 0x4c74
%elif ASPECT_RECEIVE_POLICY_UNIT!=2
%error Select ASPECT_RECEIVE_POLICY_UNIT1..2
%endif
%else
%define ASPECT_RECEIVE_POLICY_UNIT 0
global aspect_receive_policy_displayed
extern aspect_receive_policy_display
%endif
%if ASPECT_RECEIVE_POLICY_UNIT=0 || ASPECT_RECEIVE_POLICY_UNIT=2
%define translation_receive_original aspect_receive_policy_read
%ifndef ASPECT_RECEIVE_POLICY_FLAT
%define TRANSLATION_OMF
%define translation_table aspect_receive_policy_table
%define translation_script_enabled aspect_receive_policy_pattern_count
%define translation_read aspect_receive_policy_raw
%define translation_wait aspect_receive_policy_delayed
%define translation_script aspect_receive_policy_pattern_byte
%define translation_dispatch aspect_receive_policy_emit_byte
%endif
; Shared NASM encodings include path also resolves ../translation/receive.asm.
%include "../translation/receive.asm"
%endif
%if ASPECT_RECEIVE_POLICY_UNIT=0 || ASPECT_RECEIVE_POLICY_UNIT=1
aspect_receive_policy_displayed:
policy_loc_4c3c:
 push bp
policy_loc_4c3d:
 mov_load bp,sp
policy_loc_4c3f:
 push word [bp+4]
policy_loc_4c42:
 push word [aspect_receive_policy_display]
policy_loc_4c46:
 call aspect_receive_policy_read
policy_loc_4c49:
 mov_load sp,bp
policy_loc_4c4b:
 pop bp
policy_loc_4c4c:
 ret 2
%endif
