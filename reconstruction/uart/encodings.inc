; Keep the original register/register direction encodings when exact rebuilding
; matters. These macros encode named x86 operations, not opaque byte blocks.
%macro regcode 3
 %ifidni %3,al
  %assign %1 0
  %assign %2 0
 %elifidni %3,cl
  %assign %1 1
  %assign %2 0
 %elifidni %3,dl
  %assign %1 2
  %assign %2 0
 %elifidni %3,bl
  %assign %1 3
  %assign %2 0
 %elifidni %3,ah
  %assign %1 4
  %assign %2 0
 %elifidni %3,ch
  %assign %1 5
  %assign %2 0
 %elifidni %3,dh
  %assign %1 6
  %assign %2 0
 %elifidni %3,bh
  %assign %1 7
  %assign %2 0
 %elifidni %3,ax
  %assign %1 0
  %assign %2 1
 %elifidni %3,cx
  %assign %1 1
  %assign %2 1
 %elifidni %3,dx
  %assign %1 2
  %assign %2 1
 %elifidni %3,bx
  %assign %1 3
  %assign %2 1
 %elifidni %3,sp
  %assign %1 4
  %assign %2 1
 %elifidni %3,bp
  %assign %1 5
  %assign %2 1
 %elifidni %3,si
  %assign %1 6
  %assign %2 1
 %elifidni %3,di
  %assign %1 7
  %assign %2 1
 %else
  %error Unsupported register
 %endif
%endmacro

%macro load_rr 3
 regcode %%d, %%dw, %2
 regcode %%s, %%sw, %3
 %if %%dw != %%sw
  %error Register widths differ
 %endif
 db %1 + %%dw, 0xc0 + (%%d << 3) + %%s
%endmacro
%imacro add_load 2
 load_rr 0x02, %1, %2
%endmacro
%imacro or_load 2
 load_rr 0x0a, %1, %2
%endmacro
%imacro adc_load 2
 load_rr 0x12, %1, %2
%endmacro
%imacro sbb_load 2
 load_rr 0x1a, %1, %2
%endmacro
%imacro and_load 2
 load_rr 0x22, %1, %2
%endmacro
%imacro sub_load 2
 load_rr 0x2a, %1, %2
%endmacro
%imacro xor_load 2
 load_rr 0x32, %1, %2
%endmacro
%imacro cmp_load 2
 load_rr 0x3a, %1, %2
%endmacro
%imacro mov_load 2
 load_rr 0x8a, %1, %2
%endmacro
