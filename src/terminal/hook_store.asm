BITS 16
CPU 8086
%ifdef TERMINAL_HOOK_EXECUTE
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
global _terminal_hook_owner
_terminal_hook_owner: times 84 db 0
global _terminal_hook_phase,_terminal_hook_proposal
_terminal_hook_phase: dw 0
_terminal_hook_proposal: times 2584 db 0
global _terminal_hook_before
_terminal_hook_before: times 1264 db 0
%endif
