#!/usr/bin/env python3
"""Native snapshot CPU checks; --original explicitly adds SHA-bound comparisons."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/snapshot'
PROOF=json.loads((ROOT/'reconstruction/snapshot/provenance.json').read_text())
class Original:
 def __init__(self):
  data=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(data).hexdigest()==PROOF['source_sha256']
  self.uc=Uc(UC_ARCH_X86,UC_MODE_16);self.uc.mem_map(0,0x100000);self.uc.mem_write(0x10000,data[0x1200:0xe2d0]);self.base=0x10000;self.base_segment=0x1000;self.ds=0x4000;self.data_base=0x40000
  self.symbols={name:self.data_base+int(at,16) for at,name in PROOF['state'].items()}
  self.symbols.update({name:self.base+int(at,16) for at,name in PROOF['boundaries'].items()})
  # State entries and code boundaries can share names only for actual entries.
  for at,name in PROOF['state'].items():self.symbols[name]=self.data_base+int(at,16)
  for i,name in enumerate(['fixture_output','fixture_output_count','fixture_open_calls','fixture_close_calls','fixture_write_calls','fixture_prepare_calls','fixture_status_calls','fixture_error_calls','fixture_wait_calls','fixture_refresh_calls','fixture_keyboard_calls','fixture_open_result','fixture_close_result','fixture_write_failure']):self.symbols[name]=self.data_base+(0x9000 if i==0 else 0xa100+2*i)
  self.put('fixture_open_result',1)
  for name,value in [('snapshot_filename',b'PCPLUS.SCR\0'),('snapshot_append_mode',b'ab\0'),('snapshot_newline',b'\r\n\0')]:self.uc.mem_write(self.symbols[name],value)
  self.uc.hook_add(UC_HOOK_CODE,self.boundary)
 def get(self,name):return int.from_bytes(self.uc.mem_read(self.symbols[name],2),'little')
 def put(self,name,n):self.uc.mem_write(self.symbols[name],struct.pack('<H',n))
 def boundary(self,u,address,size,_):
  names={'snapshot_open':'fixture_open_calls','snapshot_close':'fixture_close_calls','snapshot_puts':'fixture_write_calls','snapshot_prepare_screen':'fixture_prepare_calls','snapshot_status':'fixture_status_calls','snapshot_error':'fixture_error_calls','snapshot_wait_key':'fixture_wait_calls','snapshot_refresh':'fixture_refresh_calls','snapshot_keyboard_state':'fixture_keyboard_calls'}
  for name,counter in names.items():
   if address!=self.symbols[name]:continue
   self.put(counter,self.get(counter)+1);sp=u.reg_read(UC_X86_REG_SP);at=self.data_base+sp;ret=int.from_bytes(u.mem_read(at,2),'little');result=0
   if name=='snapshot_open':result=self.get('fixture_open_result')
   elif name=='snapshot_close':result=self.get('fixture_close_result')
   elif name=='snapshot_puts':
    if self.get('fixture_write_failure'):result=0xffff
    else:
     pointer=int.from_bytes(u.mem_read(at+2,2),'little');row=bytearray()
     while u.mem_read(self.data_base+pointer,1)!=b'\0':row.extend(u.mem_read(self.data_base+pointer,1));pointer+=1;assert len(row)<256
     count=self.get('fixture_output_count');u.mem_write(self.symbols['fixture_output']+count,bytes(row));self.put('fixture_output_count',count+len(row))
   u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ret);return

def call(m,name,args=(),cleanup=0):
 u=m.uc;returned=[]
 def stop(u,address,size,_):
  if address==0x1f000:returned.append(True);u.emu_stop()
 hook=u.hook_add(UC_HOOK_CODE,stop)
 for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_ES,0x1234),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1111),(UC_X86_REG_DI,0x2222),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
 m.returned=False
 sp=0xe000;u.mem_write(m.data_base+sp,struct.pack('<'+'H'*(len(args)+1),0xf000,*args));u.reg_write(UC_X86_REG_SP,sp)
 u.emu_start(m.symbols[name],0x20000,count=1000000);u.hook_del(hook)
 assert (returned or m.returned) and u.reg_read(UC_X86_REG_SP)==sp+2+cleanup,(name,'stack')
 assert u.reg_read(UC_X86_REG_DS)==m.ds and not(u.reg_read(UC_X86_REG_EFLAGS)&0x400),'DS/DF'
 return u.reg_read(UC_X86_REG_AX)
def fresh(original):return Original() if original else DosImage(OUT/'SNAPSHOT.EXE',OUT/'snapshot.map')
def initialize(m):
 for name,n in [('snapshot_shadow_enabled',1),('snapshot_shadow_columns',5),('snapshot_shadow_offset',0x6000),('snapshot_shadow_segment',m.ds),('snapshot_video_columns',5),('snapshot_video_stride',10),('snapshot_video_segment',0x8000),('snapshot_cga_status_port',0),('snapshot_rows',3),('snapshot_special_row',2)]:m.put(name,n)

def run(original=False):
 results=[]
 for width in [0,1,5,80,132]:
  for content in [b' '*width,bytes((i*37)&255 for i in range(width)),(b' A\0B'+b' '*width)[:width]]:
   m=fresh(original);initialize(m);u=m.uc;source=0x80000;out=m.data_base+0x7000
   cells=b''.join(bytes([c,(i*17)&255]) for i,c in enumerate(content));u.mem_write(source,cells or b'X');u.mem_write(out,b'\xa5'*(width+3))
   n=call(m,'snapshot_copy_original',(width,0,0x8000,0x7000),8);expected=content.replace(b'\0',b' ')
   assert n==len(expected.rstrip(b' '));assert bytes(u.mem_read(out,width+1))==expected+b'\0';assert bytes(u.mem_read(out+width+1,2))==b'\xa5\xa5'
   assert u.reg_read(UC_X86_REG_SI)==0x1111 and u.reg_read(UC_X86_REG_DI)==0x2222
   results.append({'case':'copy','width':width,'length':n,'output':bytes(u.mem_read(out,width+3)).hex()})
 for shadow in [0,1]:
  m=fresh(original);initialize(m);m.put('snapshot_shadow_enabled',shadow);content=b'ROW  ';cells=b''.join(bytes([c,7]) for c in content)
  m.uc.mem_write((m.data_base+0x6000 if shadow else 0x80000)+10,cells)
  n=call(m,'snapshot_row_original',(1,0x7000));assert n==3 and bytes(m.uc.mem_read(m.data_base+0x7000,6))==b'ROW  \0'
  results.append({'case':'row','shadow':shadow,'length':n})
 for interactive,failedopen,failedwrite,failedclose,special in [(0,0,0,0,2),(1,0,0,0,2),(1,1,0,0,2),(0,0,1,0,2),(0,0,0,1,2),(0,0,0,0,3)]:
  m=fresh(original);initialize(m);m.put('snapshot_special_row',special);m.put('fixture_open_result',not failedopen);m.put('fixture_write_failure',failedwrite);m.put('fixture_close_result',0xffff if failedclose else 0)
  rows=[b' A\0B ',b' '*5,b'Z\x1a   '];m.uc.mem_write(m.data_base+0x6000,b''.join(bytes([c,7]) for row in rows for c in row))
  call(m,'snapshot_write_original',(interactive,));count=m.get('fixture_output_count');data=bytes(m.uc.mem_read(m.symbols['fixture_output'],count))
  expected=b'' if failedopen or failedwrite else b' A B\r\n\r\nZ'+(b' ' if special==2 else b'\x1a')+b'\r\n'
  assert data==expected,(data,expected)
  assert m.get('fixture_close_calls')==(not failedopen)
  assert m.get('fixture_error_calls')==failedopen
  assert m.get('fixture_write_calls')==(0 if failedopen else 3)
  assert m.get('fixture_wait_calls')==(interactive and not failedopen)
  results.append({'case':'writer','interactive':interactive,'openfail':failedopen,'writefail':failedwrite,'closefail':failedclose,'specialrow':special,'output':data.hex()})
 # Actual native CGA register instructions, model only IN/OUT ports.
 m=fresh(original);initialize(m);m.put('snapshot_shadow_enabled',0);m.put('snapshot_cga_status_port',0x3da);m.uc.mem_write(0x80000,b'A\x07'*5);ports=[]
 m.uc.hook_add(UC_HOOK_INSN,lambda u,port,size,_:8,None,1,0,UC_X86_INS_IN)
 m.uc.hook_add(UC_HOOK_INSN,lambda u,port,size,value,_:ports.append([port,value]),None,1,0,UC_X86_INS_OUT)
 assert call(m,'snapshot_row_original',(0,0x7000))==5 and ports==[[0x3d8,0x25],[0x3d8,0x2d]]
 results.append({'case':'CGA-native-bracket','ports':ports})
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');a=p.parse_args();cases=run();compared=0
 if a.original:other=run(True);assert cases==other;compared=len(other)
 m=DosImage(OUT/'SNAPSHOT.EXE',OUT/'snapshot.map');assert m.call('main_',limit=1000000)==0
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'SNAPSHOT.EXE').read_bytes()).hexdigest(),'cases':cases,'original_comparisons':compared,'scope':'Actual native snapshot/copy/row/CGA and reused string code; declared memory-FILE/UI boundaries. Optional original uses digest-verified original instructions with identical synthetic data, not installed files.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'snapshot cases;',compared,'original comparisons')
if __name__=='__main__':
 try:main()
 except Exception as error:
  OUT.mkdir(parents=True,exist_ok=True)
  result={'passed':False,'error':type(error).__name__+': '+str(error)}
  (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
  raise
