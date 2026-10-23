; Maintained platform: atomic BIOS clock and exclusive quiet PIT2/speaker claim.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _speaker_owned,_speaker_generation_word
global _speaker_context,_speaker_claim,_speaker_release,_speaker_ticks
_speaker_context:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 and ax,0x200
 ret
.bad: xor ax,ax
 ret
_speaker_claim:
 push bp
 mov bp,sp
 mov cx,[bp+4]
 ; The C owner checked frequency >=19 before any hardware effect.
 mov dx,0x12
 mov ax,0x34de
 div cx
 mov cx,ax
 pushf
 cli
 in al,0x61
 test al,3
 jnz .busy
 ; Publish the cleanup owner before the first write.
 inc word [_speaker_generation_word]
 jnz .generation
 inc word [_speaker_generation_word]
.generation:
 mov word [_speaker_owned],1
 mov al,0xb6
 out 0x43,al
 mov ax,cx
 out 0x42,al
 mov al,ah
 out 0x42,al
 in al,0x61
 or al,3
 out 0x61,al
 popf
 xor ax,ax
 pop bp
 ret
.busy:
 popf
 mov ax,1
 pop bp
 ret
_speaker_release:
 pushf
 cli
 in al,0x61
 and al,0xfc
 out 0x61,al
 mov word [_speaker_owned],0
 popf
 ret
_speaker_ticks:
 push es
 mov ax,0x40
 mov es,ax
 pushf
 cli
 mov ax,[es:0x6c]
 mov dx,[es:0x6e]
 popf
 pop es
 ret
