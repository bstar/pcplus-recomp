#!/usr/bin/env python3
"""Execute recovered CRT file code with explicit DOS-kernel fault model."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_DS,UC_X86_REG_EFLAGS,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_BP
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/transfer-files/FILES.EXE'
class Kernel:
 def kernel_setup(self,short=None,write_error=0,close_error=0):
  self.output=bytearray();self.writes=[];self.closes=[];self.short=short;self.write_error=write_error;self.close_error=close_error;self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,u,n,_):
  assert n==0x21,f'Unexpected interrupt{n:x}'
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;bx=u.reg_read(UC_X86_REG_BX);cx=u.reg_read(UC_X86_REG_CX);dx=u.reg_read(UC_X86_REG_DX);ds=u.reg_read(UC_X86_REG_DS)*16;error=0
  if ah==0x40:
   requested=bytes(u.mem_read(ds+dx,cx));count=cx if self.short is None else min(cx,self.short)
   self.writes.append(requested.hex());error=self.write_error
   if not error:self.output.extend(requested[:count]);ax=count
  elif ah==0x3e:self.closes.append(bx);error=self.close_error;ax=0
  elif ah==0x42:ax=len(self.output);u.reg_write(UC_X86_REG_DX,0)
  else:raise AssertionError(f'UnexpectedDOSservice{ax:04x}')
  u.reg_write(UC_X86_REG_AX,error or ax);flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags|1) if error else (flags&~1))
class Files(DosImage,Kernel):
 def __init__(self,buffered=0,text=0,**fault):
  super().__init__(BINARY,BINARY.parent/'transfer_files.map');self.kernel_setup(**fault);self.call('files_initialize',[5,buffered,text])
 def fwrite(self,data,size=1,count=None):
  self.uc.mem_write(self.symbols['files_source'],data)
  return self.call('files_fwrite',[self.offset('files_source'),size,len(data)//size if count is None else count,self.offset('files_stream_table')],limit=1000000)
 def flush(self):return self.call('files_fflush',[self.offset('files_stream_table')],limit=1000000)
 def close(self):return self.call('files_fclose',[self.offset('files_stream_table')],limit=1000000)
 def snapshot(self,returns):
  stream=bytes(self.uc.mem_read(self.symbols['files_stream_table'],8));p,remaining,base,flags,handle=struct.unpack('<3H2B',stream)
  return {'returns':returns,'output':self.output.hex(),'writes':self.writes,'closes':self.closes,'position':(p-base)&65535,'remaining':remaining,'flags':flags,'handle':handle,'errno':self.get('program_errno'),'dos_error':self.get('program_dos_error',1),'used':self.get('files_receive_used'),'status':self.get('files_status_code')}

def vectors():
 out=[]
 for buffered in [0,1]:
  for text in [0,1]:
   for n in [0,1,127,128,511,512,513,600,1024,4096]:out.append(('write-flush-close',buffered,text,n,{},1))
 for buffered in [0,1]:
  for fault in [{'short':1},{'short':0},{'write_error':5},{'close_error':6}]:out.append(('write-flush-close',buffered,0,600,fault,1))
 for size in [2,3,128]:out.append(('write-flush-close',0,0,768,{},size))
 for which in ['periodic','tail']:
  for fault in [{},{'short':1},{'short':0},{'write_error':5},{'close_error':6}]:out.append((which,0,0,600,fault,1))
 out.append(('multiply-overflow',0,0,0,{},256))
 return out

def run(m,v):
 kind,buffered,text,n,fault,size=v;data=bytes(i&255 for i in range(n));returns=[]
 if kind=='write-flush-close':returns=[m.fwrite(data,size),m.flush(),m.close()]
 elif kind=='multiply-overflow':returns=[m.fwrite(b'',256,256)]
 else:
  m.uc.mem_write(m.symbols['files_source'],data);returns=[m.call('files_probe_'+kind,limit=1000000)]
 return m.snapshot(returns)
def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();cases=[];v=vectors();answers=[]
 for i,vector in enumerate(v):
  kind,buffered,text,n,fault,size=vector;m=Files(buffered,text,**fault);got=run(m,vector);answers.append(got)
  if kind=='write-flush-close' and not fault:
   data=bytes(i&255 for i in range(n));want=data.replace(b'\n',b'\r\n') if text else data
   assert got['returns']==[n//size,0,0] and bytes.fromhex(got['output'])==want and got['flags']==0,(vector,got)
  elif kind=='multiply-overflow':assert got['returns']==[0] and not got['writes']
  elif kind=='periodic':
   assert got['returns']==([0] if fault.get('write_error') or 'short' in fault else [1]),(vector,got)
   if fault.get('short')==1:assert got['used']==600 and len(bytes.fromhex(got['output']))==1 and got['flags']==0
  elif kind=='tail':assert got['returns']==[1] and got['closes']==[5] and got['flags']==0,(vector,got)
  else:
   assert 65535 in got['returns'] or got['returns'][0]<n,(vector,got)
   assert got['flags']==0 and got['closes']==[5],(vector,got)
 for args in [(20,0,0),(5,2,0),(5,0,2)]:
  m=Files();before=bytes(m.uc.mem_read(m.symbols['files_stream_table'],320));assert m.call('files_initialize',args)==1 and bytes(m.uc.mem_read(m.symbols['files_stream_table'],320))==before and not m.writes and not m.closes
 cases.append({'case':'bounded-diagnostic-FILE-initialization-rejects-invalid-handle-and-modes','inputs':3,'passed':True})
 cases.append({'case':'native-binary-text-buffering-elementcounts-faults-receiver-shortwrite-finalerrors','inputs':len(v),'passed':True})
 if a.original:
  from check_directory_dial_original import Original,DATA,EXPECTED
  image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
  overlays=[x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==21]
  class OriginalFiles(Original,Kernel):
   def __init__(self,buffered,text,**fault):
    super().__init__(image,overlays);self.kernel_setup(**fault);self.symbols={'files_source':DATA+0x4000};self.uc.mem_write(DATA+0x7b56,image[153936+0x7b56:153936+0x7b56+20]);self.uc.mem_write(DATA+0x7b6a,b'\0'*320)
    for at,value in [(0x7b6a,0x6000),(0x7b6c,512 if buffered else 0),(0x7b6e,0x6000),(0x7c0c,512 if buffered else 1),(0x7b29,20),(0x8e24,0),(0x1d1e,0),(0x7b1c,0),(0x7dd6,0),(0x39c0,0x4000),(0xcbaa,0x7b6a),(0xcd34,600),(0x9006,0),(0x9008,0),(0x6200,0)]:self.put(at,value)
    self.uc.mem_write(DATA+0x7b70,bytes([2 if buffered else 6,5]));self.uc.mem_write(DATA+0x7c0a,bytes([1 if buffered else 0]));self.uc.mem_write(DATA+0x7b30,bytes([0x80 if text else 0]));self.uc.mem_write(DATA+0x7b24,b'\x03');self.uc.mem_write(DATA+0x7b27,b'\0')
   def hook(self,u,at,size,_):
    if at in (self.stop,0x1dc07,0x1d734,0x1da9e):u.emu_stop();return
    if at==0x1e498:
     sp=u.reg_read(UC_X86_REG_SP);ret,status=struct.unpack('<2H',u.mem_read(DATA+sp,4));self.put(0x6200,status);u.reg_write(UC_X86_REG_AX,status);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ret)
   def fwrite(self,data,size=1,count=None):
    self.uc.mem_write(DATA+0x4000,data);self.call(0x86ac,[0x4000,size,len(data)//size if count is None else count,0x7b6a]);return self.uc.reg_read(UC_X86_REG_AX)
   def flush(self):self.call(0x8c54,[0x7b6a]);return self.uc.reg_read(UC_X86_REG_AX)
   def close(self):self.call(0x8318,[0x7b6a]);return self.uc.reg_read(UC_X86_REG_AX)
   def call(self,entry,args=(),stop=0xf000,limit=0):
    if isinstance(entry,str):
     self.uc.reg_write(UC_X86_REG_SP,0xbf00);self.uc.reg_write(UC_X86_REG_BP,0xc000);self.uc.emu_start(0x1db2a if entry.endswith('periodic') else 0x1de20,0x20000,count=1000000);return 0 if self.uc.reg_read(UC_X86_REG_IP)==0xd734 else 1
    return super().call(entry,args,stop)
   def snapshot(self,returns):
    p,remaining,base,flags,handle=struct.unpack('<3H2B',self.uc.mem_read(DATA+0x7b6a,8))
    return {'returns':returns,'output':self.output.hex(),'writes':self.writes,'closes':self.closes,'position':(p-base)&65535,'remaining':remaining,'flags':flags,'handle':handle,'errno':self.get(0x7b1c),'dos_error':bytes(self.uc.mem_read(DATA+0x7b27,1))[0],'used':self.get(0xcd34),'status':self.get(0x6200)}
  for vector,want in zip(v,answers):
   _,buffered,text,_,fault,_=vector;o=OriginalFiles(buffered,text,**fault);got=run(o,vector);assert got==want,(vector,got,want)
  cases.append({'case':'genuine-original-CRT-and-receiver-file-fragments-against-source','inputs':len(v),'passed':True})
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Native CRT source and actual receiver file fragments; modeled DOSkernel faults, bounded synthetic FILE objects. No live UART/full session/transaction policy.'};(BINARY.parent/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',sum(x['inputs'] for x in cases),'native file cases')
if __name__=='__main__':main()
