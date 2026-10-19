#!/usr/bin/env python3
"""Build recovered resident long arithmetic without original inputs."""
import hashlib,json,random,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-long'
UNITS=[('multiply_value',0x9950,0x9982),('divide_value',0x9a1a,0x9ab4),('shift_left_value',0x9ab4,0x9abf),('divide',0x9af2,0x9b11),('modulo',0x9b12,0x9b31),('multiply',0x9b90,0x9baf),('shift_left',0x9bb0,0x9bcc),('shift_right',0x9bcc,0x9be8),('modulo_value',0x9c7c,0x9d1c),('shift_right_value',0x9d1c,0x9d27)]
MASK=0xffffffff
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def signed(n):return n-0x100000000 if n&0x80000000 else n
def expected(op,a,b):
 if op=='multiply':return a*b&MASK
 if op in ['divide','modulo']:
  x,y=signed(a),signed(b);q=abs(x)//abs(y)
  if (x<0)!=(y<0):q=-q
  return (q if op=='divide' else x-q*y)&MASK
 count=b&255
 return ((a<<count) if op=='shift_left' else signed(a)>>count)&MASK

def vectors():
 values=[0,1,2,3,7,0x7fff,0x8000,0xffff,0x10000,0x10001,0x7ffffffe,0x7fffffff,0x80000000,0x80000001,0xffff0000,0xfffffffe,0xffffffff]
 rng=random.Random(0x9a1a);pairs=[(a,b) for a in values for b in values]+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(300)]
 result=[]
 for op in ['multiply','divide','modulo']:
  for a,b in pairs:
   if b or op=='multiply':result.append((op,a,b,expected(op,a,b)))
 for op in ['shift_left','shift_right']:
  for a in values:
   for b in [0,1,7,15,16,17,30,31,32,33,63,127,128,255,256,257,65535]:result.append((op,a,b,expected(op,a,b)))
 return result

ASM='''BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _long_probe
extern _long_value,_abi_bad
'''+ '\n'.join('extern aspect_long_'+name for name,_,_ in UNITS)+'''
_long_probe:
 push bp
 mov bp,sp
 push si
 push di
 push bx
 push es
 mov si,0x1234
 mov di,0x5678
 mov bx,[bp+4]
 shl bx,1
 call word [cs:ops+bx]
 cmp si,0x1234
 jne .bad
 cmp di,0x5678
 jne .bad
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 je .done
.bad: inc word [_abi_bad]
.done:
 pop es
 pop bx
 pop di
 pop si
 pop bp
 ret
ops:
'''
for name,_,_ in UNITS:ASM+=' dw op_'+name+'\n'
for name,_,_ in UNITS:
 ASM+='op_'+name+':\n'
 if name.endswith('_value') and 'shift' not in name:
  ASM+=' push word [bp+12]\n push word [bp+10]\n push word [bp+8]\n push word [bp+6]\n'
 elif name.endswith('_value'):
  ASM+=' mov ax,[bp+6]\n mov dx,[bp+8]\n mov cx,[bp+10]\n'
 else:
  if 'shift' not in name:ASM+=' push word [bp+12]\n'
  ASM+=' push word [bp+10]\n mov ax,_long_value\n push ax\n'
 ASM+=' call aspect_long_'+name+'\n'
 if name.endswith('_value'):ASM+=' mov [_long_value],ax\n mov [_long_value+2],dx\n'
 ASM+=' ret\n'
C='''#include <stdio.h>
#include <string.h>
unsigned long long_value;
unsigned abi_bad;
extern void long_probe(unsigned,unsigned long,unsigned long);
static unsigned long checks;
static unsigned failures;
static void run(unsigned op,unsigned long a,unsigned long b,unsigned long expected){long_value=a;abi_bad=0;long_probe(op,a,b);++checks;if(long_value!=expected||abi_bad){++failures;printf("FAIL %u %08lx %08lx got %08lx expected %08lx ABI%u\\n",op,a,b,long_value,expected,abi_bad);}}
int main(void){FILE *done,*input;unsigned char row[13];unsigned long a,b,value;
 input=fopen("VECTORS.BIN","rb");if(!input)return 2;
 while(fread(row,1,13,input)==13){memcpy(&a,row+1,4);memcpy(&b,row+5,4);memcpy(&value,row+9,4);run(row[0],a,b,value);}
 if(ferror(input)){fclose(input);return 2;}fclose(input);
'''
def main():
 OUT.mkdir(parents=True,exist_ok=True);source=ROOT/'src/aspect/long_arithmetic.asm';units=[]
 for i,(name,start,end) in enumerate(UNITS,1):
  path=OUT/(name+'.bin');subprocess.run(['nasm','-f','bin','-DASPECT_LONG_FLAT',f'-DASPECT_LONG_UNIT={i}','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(path)],check=True)
  assert path.stat().st_size==end-start
  units.append(dict(name=name,start=start,end_exclusive=end,bytes=end-start,sha256=sha(path),source_file_start=0x1200+start))
 subprocess.run(['nasm','-f','obj','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(OUT/'long.obj')],check=True)
 (OUT/'bridge.asm').write_text(ASM);subprocess.run(['nasm','-f','obj',str(OUT/'bridge.asm'),'-o',str(OUT/'bridge.obj')],check=True)
 program=C;data=bytearray()
 for op,a,b,value in vectors():
  for name in [op,op+'_value']:
   index=[n for n,_,_ in UNITS].index(name)
   data+=struct.pack('<BIII',index,a,b,value)
 program+='done=fopen("DONE.TXT","w");if(!done)return 2;fprintf(done,"ASPECT_LONG %lu checks %u failures\\n",checks,failures);fclose(done);return failures?1:0;}\n'
 (OUT/'VECTORS.BIN').write_bytes(data)
 (OUT/'diagnostic.c').write_text(program)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-fm=LONG.map','-fe=LONG.EXE',str(OUT/'diagnostic.c'),str(OUT/'bridge.obj'),str(OUT/'long.obj')],cwd=OUT,check=True)
 sources=[source,Path(__file__).resolve(),ROOT/'reconstruction/uart/encodings.inc']
 report=dict(binary_sha256=sha(OUT/'LONG.EXE'),original_inputs=[],sources={str(p.relative_to(ROOT)):sha(p) for p in sources},units=units,bytes=sum(u['bytes'] for u in units),vector_count=len(vectors()),DOS_checks=2*len(vectors()),vectors_sha256=sha(OUT/'VECTORS.BIN'))
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
