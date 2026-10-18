#!/usr/bin/env python3
"""Build and test actual DOS16 modem importer; entirely synthetic source inputs."""
import hashlib,json,os,random,re,struct,subprocess
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_REG_ES,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_INS_IN,UC_X86_INS_OUT
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/modem-import'
COMMANDS=[(0x18,47),(0x47,25),(0x60,25),(0x79,25),(0x92,25),(0xab,25)]
OFFSETS={'MI_TIMEOUT':0,'MI_REDIAL_PAUSE':2,'MI_AUTOBAUD':4,'MI_ABORT_DTR':6,'MI_INITIALIZE_CONNECTED':8,'MI_CYCLE_LIMIT':10,'MI_CHARACTER_DELAY':12,'MI_PAUSE_CHARACTER':14,'MI_ABORT_CHARACTER':16,'MI_INITIALIZATION':18,'MI_DIAL_PREFIX':65,'MI_DIAL_SUFFIX':90,'MI_HANGUP':115,'MI_ANSWER_ON':140,'MI_ANSWER_OFF':165,'MI_RESPONSES':190,'MI_BREAK_DELAY':366,'MI_SIZE':368}
def fixture():
 image=bytearray(random.Random(201).randbytes(1264))
 for at,value in [(0x0a,45),(0x0c,2),(0x0e,1),(0x10,1),(0x14,0),(0x16,3),(0x1e4,30)]:struct.pack_into('<H',image,at,value)
 image[0x1e2]=ord('~');image[0x12]=13
 for (at,size),text in zip(COMMANDS,[b'ATZ^M',b'ATDT',b'^M',b'~~~+++~~~ATH^M',b'ATS0=1^M',b'ATS0=0^M']):image[at:at+len(text)+1]=text+b'\0'
 for index in range(11):
  text=b'R'+str(index).encode();at=0xc4+index*16;image[at:at+len(text)+1]=text+b'\0'
 return bytes(image)
def changed(image,at,value):
 data=bytearray(image);struct.pack_into('<H',data,at,value);return bytes(data)
def expected(image):
 return struct.pack('<9H',*(struct.unpack_from('<H',image,at)[0] for at in [0x0a,0x0c,0x0e,0x10,0x14,0x16,0x1e4]),image[0x1e2],image[0x12])+image[0x18:0x174]+image[0x1a4:0x1a6]
def build():
 OUT.mkdir(parents=True,exist_ok=True)
 host=r'''#include "modem_import.h"
#include <string.h>
#include <stdio.h>
prm_dos_image synthetic_input;
modem_import_settings synthetic_output;
prm_dos_result synthetic_io;
int main(void)
{
 modem_import_settings before;
 memset(&synthetic_output,0xcc,sizeof(synthetic_output));
 if(modem_import_read("VALID.PRM",&synthetic_output,&synthetic_io)!=MODEM_IMPORT_OK)return 1;
 if(synthetic_io.status!=PRM_DOS_OK || synthetic_io.bytes_processed!=1264)return 2;
 if(synthetic_output.dial_timeout_seconds!=45 || synthetic_output.redial_pause_seconds!=2 ||
  synthetic_output.autobaud!=1 || synthetic_output.abort_drop_dtr!=1 ||
  synthetic_output.initialize_while_connected!=0 || synthetic_output.dial_cycle_limit!=3 ||
  synthetic_output.command_character_delay_units!=30 || synthetic_output.command_pause_character!='~' ||
  synthetic_output.dial_abort_character!=13 || strcmp((char *)synthetic_output.initialization,"ATZ^M") ||
  strcmp((char *)synthetic_output.responses[10],"R10"))return 3;
 memcpy(&before,&synthetic_output,sizeof(before));
 if(modem_import_read("ABSENT.PRM",&synthetic_output,&synthetic_io)!=MODEM_IMPORT_IO ||
  memcmp(&before,&synthetic_output,sizeof(before)))return 4;
 if(modem_import_read("SHORT.PRM",&synthetic_output,&synthetic_io)!=MODEM_IMPORT_IO ||
  memcmp(&before,&synthetic_output,sizeof(before)))return 5;
 if(modem_import_read("BAD.PRM",&synthetic_output,&synthetic_io)!=MODEM_IMPORT_COMMAND ||
  synthetic_io.status!=PRM_DOS_OK || memcmp(&before,&synthetic_output,sizeof(before)))return 6;
 if(modem_import_read("",&synthetic_output,&synthetic_io)!=MODEM_IMPORT_ARGUMENT ||
  memcmp(&before,&synthetic_output,sizeof(before)))return 7;
 if(modem_import_read("VALID.PRM",&synthetic_output,0)!=MODEM_IMPORT_OK)return 8;
 if(modem_import_decode(0,&synthetic_output)!=MODEM_IMPORT_ARGUMENT)return 9;
 puts("MODEM IMPORT PASS");return 0;
}
'''
 (OUT/'host.c').write_text(host)
 sources=[ROOT/'src/config/modem_import.c',ROOT/'src/config/prm_dos.c',OUT/'host.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/config'),'-fm=modem.map','-fe=MODEM.EXE',*map(str,sources)],cwd=OUT,check=True)
 return OUT/'MODEM.EXE',OUT/'modem.map'
class Model(DosImage):
 def __init__(self,binary,mapfile):
  super().__init__(binary,mapfile);self.input=self.offset('_synthetic_input');self.output=self.offset('_synthetic_output')
  self.uc.hook_add(UC_HOOK_INTR,self.io)
  for instruction in (UC_X86_INS_IN,UC_X86_INS_OUT):self.uc.hook_add(UC_HOOK_INSN,self.io,None,1,0,instruction)
 def io(self,*args):raise AssertionError('Pure decoder attempted interrupt/UART/DOS IO')
 def decode(self,image,input_pointer=None,output_pointer=None):
  self.uc.mem_write(self.data_base+self.input,image)
  self.uc.mem_write(self.data_base+self.output,b'\xcc'*368)
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  status=self.call('_modem_import_decode',[self.input if input_pointer is None else input_pointer,self.output if output_pointer is None else output_pointer],limit=300000)
  assert bytes(self.uc.mem_read(self.data_base+self.input,1264))==image
  for reg,want in ((UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)):assert self.uc.reg_read(reg)==want
  result=bytes(self.uc.mem_read(self.data_base+self.output,368))
  if status:assert result==b'\xcc'*368
  return status,result

def main():
 binary,mapfile=build();data=fixture();cases=[];inputs=0
 def check(name,count):
  nonlocal inputs
  cases.append({'case':name,'inputs':count,'passed':True});inputs+=count;print(name,'passed',count,flush=True)
 macros={k:int(v) for k,v in re.findall(r'^%define (MI_\w+) (\d+)$',(ROOT/'src/config/modem_import.inc').read_text(),re.M)}
 assert all(macros[k]==v for k,v in OFFSETS.items());assert macros['MI_RESPONSE_COUNT']==11 and macros['MI_RESPONSE_SIZE']==16
 model=Model(binary,mapfile);assert model.decode(data)==(0,expected(data));check('C-sizeof-and-offset-assertions-plus-NASM-layout-agreement',1)
 count=0
 for at,size in COMMANDS:
  for text in (b'',b'A'*(size-1),b'^@^M^^^',b'^^',b'^^^',b'^`',b'\xff'):
   raw=bytearray(data);raw[at:at+size]=text+b'\0'+bytes([0xa5])*(size-len(text)-1)
   assert Model(binary,mapfile).decode(bytes(raw))==(0,expected(raw));count+=1
  for text in (b'A'*size,b'AT^\0',b'^^^^\0'):
   raw=bytearray(data);raw[at:at+len(text)]=text
   assert Model(binary,mapfile).decode(bytes(raw))[0]==4;count+=1
 check('all-six-command-capacities-and-real-caret-boundaries',count)
 count=0
 for index in range(11):
  for text in (b'',b'A'*15,b'^',b'\xff\x01\x13\x1b'):
   raw=bytearray(data);at=0xc4+index*16;raw[at:at+16]=text+b'\0'+bytes([0xa5])*(15-len(text))
   assert Model(binary,mapfile).decode(bytes(raw))==(0,expected(raw));count+=1
  raw=bytearray(data);raw[0xc4+index*16:0xc4+(index+1)*16]=b'X'*16
  assert Model(binary,mapfile).decode(bytes(raw))[0]==5;count+=1
 check('all11-raw-response-slots-not-reexpanded',count)
 count=0
 for at in (0x0e,0x10,0x14):
  for value in (0,1,2,65535):
   raw=changed(data,at,value);status,result=Model(binary,mapfile).decode(raw)
   assert status==(0 if value<2 else 2)
   if not status:assert result==expected(raw)
   count+=1
 for at in (0x0a,0x0c,0x16,0x1e4):
  for value in (0,1,32766,32767,32768,65535):
   raw=changed(data,at,value);status,result=Model(binary,mapfile).decode(raw)
   assert status==(3 if value>32767 or (at==0x0a and value==0) else 0),(at,value,status)
   if not status:assert result==expected(raw)
   count+=1
 for value in (0,1,54,55,56,350,65535):
  raw=changed(data,0x1a4,value);assert Model(binary,mapfile).decode(raw)==(0,expected(raw));count+=1
 check('Boolean-and-maintained-numeric-policy-boundaries-atomic',count)
 count=0
 for inp,out in ((0,model.output),(model.input,0),(0xfc00,model.output),(model.input,0xff00),(model.input,model.input),(model.input,model.input+1263)):
  assert Model(binary,mapfile).decode(data,inp,out)[0]==1;count+=1
 check('null-wraparound-and-overlap-arguments-atomic',count)
 # Real DOS read-only loader tests, with generated local fixtures and preserved hashes.
 (OUT/'VALID.PRM').write_bytes(data);(OUT/'SHORT.PRM').write_bytes(data[:-1])
 bad=bytearray(data);bad[0x18:0x18+47]=b'X'*47;(OUT/'BAD.PRM').write_bytes(bad)
 before={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ('VALID.PRM','SHORT.PRM','BAD.PRM')}
 for name in ('PASS.TXT','FAIL.TXT','LOG.TXT'):(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nMODEM >LOG.TXT\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=35)
 assert (OUT/'PASS.TXT').exists() and b'MODEM IMPORT PASS' in (OUT/'LOG.TXT').read_bytes()
 assert before=={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in before}
 check('real-DOS-loader-valid-missing-short-invalid-argument-noresult-and-no-rewrites',7)
 result={'passed':True,'inputs':inputs,'cases':cases,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'settings_bytes':368,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/config/modem_import.c',ROOT/'src/config/modem_import.h',ROOT/'src/config/modem_import.inc',ROOT/'src/config/prm_dos.c',ROOT/'src/config/prm_dos.h',Path(__file__).resolve()]},'scope':'Source-built DOS8086 C decoder/loader, synthetic PRMs only. CPU tests forbid all interrupts and port IO during decode; separate DOS run executes read-only loader. No modem defaults, dialing, live UART, original executable or private config inputs.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
