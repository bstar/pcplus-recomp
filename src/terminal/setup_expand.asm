; C status adapter for the recovered expander: AX0 success, original error
; otherwise. Caller removes four argument words; DS=SS. No I/O or output on
; expansion failure. Native CF/length are intentionally translated here.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _live_modem_expand
extern modem_expand_bounded
_live_modem_expand:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call modem_expand_bounded
 lea sp,[bp]
 jc .done
 xor ax,ax
.done:
 pop bp
 ret
