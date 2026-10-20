"""Record RX notices through video reads only; no UART reads or key insertion."""
from zmodem_label_watch import SAMPLER as BASE
SAMPLER=BASE.replace(''' cmp word [es:3840],0x1f52
 jne .done
 cmp word [es:3842],0x1f65
 jne .done
 cmp word [es:3844],0x1f6d
 jne .done
''',''' cmp byte [es:3842],'R'
 jne .carrier
 cmp byte [es:3844],'X'
 je .observed
.carrier:
 cmp byte [es:3842],'C'
 jne .done
 cmp byte [es:3844],'a'
 jne .done
 cmp byte [es:3846],'r'
 jne .done
.observed:
''')
assert SAMPLER!=BASE
