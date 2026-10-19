#!/usr/bin/env python3
"""Source-only bounded ASPECT child UART owner diagnostic, no originals."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-serial';OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'src/aspect/serial_backend.asm',ROOT/'reconstruction/uart/core.asm',ROOT/'src/uart/api.asm']
objects=[]
for i,p in enumerate(sources):
 o=OUT/f'{i}.obj';objects.append(str(o));subprocess.run(['nasm','-fobj','-DUART_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(p),'-o',str(o)],check=True)
(OUT/'main.c').write_text(r'''#include "serial.h"
#include <conio.h>
#include <stdio.h>
static unsigned finish(unsigned result){printf("status=%u count=%u\n",result,aspect_serial_rx_count);return result;}
unsigned char aspect_serial_test_buffer[128];
static unsigned elapsed(unsigned long first){unsigned long n=aspect_serial_ticks();if(n<first)n+=1573040UL;return n-first>=72UL;}
static unsigned send(unsigned c){unsigned long first=aspect_serial_ticks();while(aspect_serial_try_write(c)){if(aspect_serial_poll()||elapsed(first))return 1;}return 0;}
int main(int argc,char **argv){
 unsigned status,i=0,c;unsigned long first;static unsigned char expected[]={0,0x1a,0x80,0xff};
 if(argc==1)return aspect_serial_open("BAD")!=ASPECT_SERIAL_ARGUMENT;
 status=aspect_serial_open(argv[1]);if(status)return finish(status);
 if(send('D')){aspect_serial_close();return finish(20);}
 first=aspect_serial_ticks();
 while(i<4 && !elapsed(first)){
  if(aspect_serial_poll()){aspect_serial_close();return finish(21);}
  if(kbhit() && getch()==27){status=aspect_serial_close();return finish(status);}
  c=aspect_serial_read();if(c==0xffff)continue;
  if(c!=expected[i++]){aspect_serial_close();return finish(22);}
 }
 if(i!=4){aspect_serial_close();return finish(23);}
 if(send('R')){aspect_serial_close();return finish(24);}
 return finish(aspect_serial_close());
}
''')
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-os','-k8192','-I'+str(ROOT/'src/aspect'),'-fm=serial.map','-fe=SERIAL.EXE',str(OUT/'main.c'),str(ROOT/'src/aspect/serial.c'),*objects],cwd=OUT,check=True)
sources += [ROOT/'src/aspect/serial.c',ROOT/'src/aspect/serial.h',ROOT/'src/aspect/serial_handoff.h',Path(__file__).resolve()]
(OUT/'manifest.json').write_text(json.dumps(dict(binary_sha256=hashlib.sha256((OUT/'SERIAL.EXE').read_bytes()).hexdigest(),original_inputs=[],sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
