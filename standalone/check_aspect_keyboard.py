#!/usr/bin/env python3
"""Check every BIOS word through the production ASPECT reader, plus real DOS ABI."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_EFLAGS
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-keyboard'
PRODUCT=ROOT/'build/aspect-runner'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def expected(raw):
 low,high=raw&255,raw>>8
 signed=raw if raw<32768 else raw-65536
 if low in (0,224) or high==224:return raw
 if raw==0x3920:return low
 if raw in (0x0e08,0x0e7f) or signed>=0x372a:return raw
 return low
class Reader(DosImage):
 def __init__(self):
  super().__init__(PRODUCT/'ASPECT.EXE',PRODUCT/'ASPECT.map')
  h=struct.unpack_from('<14H',self.image)
  # Use the executable's actual initial stack rather than synthetic spare RAM.
  top=self.base+h[7]*16+h[8]
  assert self.data_base<top<=self.data_base+65536
  self.symbols['terminal_stack_top']=top
  self.raw=0;self.reads=0;self.mode=0;self.available=True
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,uc,number,_):
  assert number==0x16
  function=uc.reg_read(UC_X86_REG_AX)>>8
  if function==self.mode:
   assert self.available;self.available=False;self.reads+=1
  else:
   assert function==self.mode+1
   flags=uc.reg_read(UC_X86_REG_EFLAGS)
   uc.reg_write(UC_X86_REG_EFLAGS,flags&~64 if self.available else flags|64)
  # Empty BIOS result deliberately remains nonzero: the original uses ZF.
  uc.reg_write(UC_X86_REG_AX,self.raw)
BIOS=r'''BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS
extern _bios_raw,_bios_count,_bios_reads,_bios_peeks,_bios_bad
extern _runtime_keyboard_mode
global _test_bios
_test_bios:
 push bp
 mov bp,sp
 push ds
 push bx
 mov bx,DGROUP
 mov ds,bx
 sub ah,byte [_runtime_keyboard_mode]
 cmp ah,0
 je .read
 cmp ah,1
 je .peek
 inc word [_bios_bad]
 jmp .empty
.peek:
 inc word [_bios_peeks]
 cmp word [_bios_count],0
 je .empty
 and word [ss:bp+6],0xffbf
 mov ax,[_bios_raw]
 jmp .done
.empty:
 or word [ss:bp+6],0x40
 mov ax,0x1234
 jmp .done
.read:
 inc word [_bios_reads]
 cmp word [_bios_count],0
 jne .available
 inc word [_bios_bad]
 jmp .done
.available:
 dec word [_bios_count]
 mov ax,[_bios_raw]
.done:
 pop bx
 pop ds
 pop bp
 iret
SEGMENT _DATA public class=DATA use16
SEGMENT _BSS public class=BSS use16
'''
C=r'''#include <dos.h>
#include <stdio.h>
#include "runtime.h"
#include "when_runtime.h"
extern unsigned runtime_when_read_key(void);
extern unsigned runtime_when_key_ready(void);
extern void __interrupt __far test_bios(void);
volatile unsigned bios_raw,bios_count,bios_reads,bios_peeks,bios_bad;
static unsigned failures;
static unsigned test_mode;
static unsigned long checks;
static void ck(unsigned yes){++checks;if(!yes)++failures;}
static unsigned want(unsigned raw){
 unsigned low=raw&255,high=raw>>8;
 if(!low||low==224||high==224)return raw;
 if(raw==0x3920)return low;
 if(raw==0x0e08||raw==0x0e7f||(int)raw>=0x372a)return raw;
 return low;
}
static void stage(unsigned raw){runtime_error=0;runtime_when_reset();runtime_keyboard_mode=test_mode;bios_raw=raw;bios_count=1;}
int main(void){
 void (__interrupt __far *saved)(void);unsigned raw=0,i;
 static unsigned keys[]={0x1e61,0x0e08,0x0e7f,0x48e0,0xe02f,0x372a,0x3920,0x4800};
 saved=_dos_getvect(0x16);_dos_setvect(0x16,test_bios);
 for(test_mode=0;test_mode<=16;test_mode+=16){
 runtime_keyboard_mode=test_mode;bios_reads=0;
 do{bios_raw=raw;bios_count=1;
 ck(runtime_keyboard_peek()==(raw?raw:256));ck(bios_count==1);
 ck(runtime_when_read_key()==want(raw));ck(!bios_count);ck(!runtime_keyboard_peek());++raw;}while(raw);
 ck(!bios_reads); /* exactly65536 reads, modulo16bit */
 for(i=0;i<sizeof(keys)/sizeof(keys[0]);++i){
  stage(keys[i]);ck(runtime_when_poll()==1);ck(runtime_error==ASPECT_RUN_UNSUPPORTED);
  ck(runtime_when_last_key==want(keys[i]));ck(runtime_when_pending_key==65535U);ck(!bios_count);
 }
 stage(0x011b);ck(runtime_when_poll()==1);ck(runtime_error==ASPECT_RUN_CANCELLED);ck(runtime_when_last_key==27);ck(!bios_count);
 stage(0x48e0);runtime_when_keyboard_disabled=1;ck(!runtime_when_poll());ck(bios_count==1);ck(!runtime_when_last_key);
 stage(0x0e08);runtime_when_defer_begin();ck(!runtime_when_poll());ck(bios_count==1);ck(!runtime_when_last_key);runtime_when_defer_end();
 ck(runtime_when_poll()==1);ck(runtime_when_last_key==0x0e08);ck(runtime_error==ASPECT_RUN_UNSUPPORTED);ck(!bios_count);
 stage(0x011b);runtime_when_defer_begin();ck(runtime_when_poll()==1);ck(runtime_error==ASPECT_RUN_CANCELLED);ck(!bios_count);runtime_when_defer_end();
 stage(0);ck(runtime_when_key_ready()==256);ck(runtime_when_poll()==1);ck(runtime_error==ASPECT_RUN_UNSUPPORTED);ck(!runtime_when_last_key);ck(!bios_count);
 runtime_when_file_reset();ck(runtime_keyboard_mode==test_mode);
 stage(0x1e61);runtime_error=ASPECT_RUN_CANCELLED;ck(!runtime_when_key_ready());ck(bios_count==1);
 }
 ck(!bios_bad);_dos_setvect(0x16,saved);ck(_dos_getvect(0x16)==saved);
 printf("ASPECT_KEYBOARD 131072 words %lu checks %u failures\n",checks,failures);
 return failures?1:0;
}
'''
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((PRODUCT/'manifest.json').read_text())
 assert manifest['binary_sha256']==sha(PRODUCT/'ASPECT.EXE') and not manifest['original_inputs']
 for path,digest in manifest['sources'].items():assert sha(ROOT/path)==digest,path
 model=Reader();changed=0
 for flags in range(256):
  model.uc.mem_write(0x496,bytes([flags]));model.put('_runtime_keyboard_mode',65535)
  assert model.call('_runtime_keyboard_auto')==(16 if flags&16 else 0)
  assert model.get('_runtime_keyboard_mode')==(16 if flags&16 else 0)
  assert model.uc.mem_read(0x496,1)==bytes([flags])
 for mode in (0,16):
  model.mode=mode;model.put('_runtime_keyboard_mode',mode)
  for raw in range(65536):
   model.raw=raw;model.available=True
   assert model.call('_runtime_when_key_ready')==(raw or 256)
   assert model.available
   got=model.call('_runtime_when_read_key',limit=500)
   assert got==expected(raw),(hex(raw),hex(got),hex(expected(raw)))
   assert model.reads==raw+1+(65536 if mode else 0)
   assert model.uc.reg_read(UC_X86_REG_BP)==0xbabe
   assert model.uc.reg_read(UC_X86_REG_SI)==0x1234
   assert model.uc.reg_read(UC_X86_REG_DI)==0x5678
   assert not model.call('_runtime_when_key_ready')
   if not mode:changed+=got!=((raw&255) if raw&255 else raw)
 (OUT/'bios.asm').write_text(BIOS);(OUT/'harness.c').write_text(C)
 subprocess.run(['nasm','-f','obj',str(OUT/'bios.asm'),'-o',str(OUT/'bios.obj')],check=True)
 # Reuse exactly the product's compiled objects; replace only its CLI entry.
 objects=[PRODUCT/leaf for leaf in sorted(manifest['objects']) if leaf!='runner.o']
 for obj in objects:assert sha(obj)==manifest['objects'][obj.name],obj
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fm=KEYTEST.map','-fe=KEYTEST.EXE',str(OUT/'harness.c'),str(OUT/'bios.obj'),*[str(p) for p in objects]],cwd=OUT,check=True)
 config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nKEYTEST >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
 (OUT/'dosbox.conf').write_text(config)
 for leaf in ('PASS.TXT','FAIL.TXT','RESULT.TXT'):(OUT/leaf).unlink(missing_ok=True)
 with (OUT/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 result=(OUT/'RESULT.TXT').read_text().strip();print(result)
 assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),result
 assert result=='ASPECT_KEYBOARD 131072 words 655494 checks 0 failures'
 assert changed==19011
 assert sha(PRODUCT/'ASPECT.EXE')==manifest['binary_sha256']
 report=dict(passed=True,runner_sha256=manifest['binary_sha256'],checker_sha256=sha(Path(__file__)),manifest_sha256=sha(PRODUCT/'manifest.json'),CPU_words=131072,DOS_words=131072,BIOS_modes=[0,16],BDA_flag_cases=256,words_corrected_from_previous_reader=changed,DOS_summary=result,original_inputs=[],objects={p.name:sha(p) for p in objects},test_inputs={p.name:sha(p) for p in (OUT/'harness.c',OUT/'bios.asm',OUT/'KEYTEST.EXE')},scope='Exhaustive actual product reader CPU replay and8086 DOS execution in standard/enhanced modes with declared BIOS models. Both preserve occupiedAX0 versus emptyZF, read consumption and native normalization. CPU checks256 BDA flag patterns; DOS checks native WHEN state, disabled/deferred keyboard, file-reset retention and cancellation. No physical BIOS or full keyboard/UI dispatch claim.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Product BIOS key words corrected:',changed)
if __name__=='__main__':main()
