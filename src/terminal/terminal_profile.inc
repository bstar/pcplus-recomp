; Admitted display profiles; see src/config/terminal_profile.h for evidence.
; profile_gate reg,label: falls through for an admitted id, else jumps.
; Without TERMINAL_ANSI_PROFILES it emits the historical 4/6 sequence.
%macro profile_gate 2
%ifdef TERMINAL_ANSI_PROFILES
 cmp %1,2
 jb %2
 cmp %1,11
 ja %2
%else
 cmp %1,4
 je %%admitted
 cmp %1,6
 jne %2
%%admitted:
%endif
%endmacro
; active_profile_gate reg,label: the same test for the running csi_terminal_id.
; TERMINAL_VT52 also admits 1, entered at runtime by DECANM (ESC[?2l); VT52
; is never a configured profile, so configuration keeps profile_gate.
%macro active_profile_gate 2
%ifdef TERMINAL_VT52
 cmp %1,1
 je %%admitted
%endif
 profile_gate %1,%2
%ifdef TERMINAL_VT52
%%admitted:
%endif
%endmacro
