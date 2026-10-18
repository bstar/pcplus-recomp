#!/usr/bin/env python3
"""Optional actual overlay5 dial-attempt replay with declared synthetic boundaries.

No PRM/user data/network reads. UI, keyboard, clock, command TX and baud setter
are explicitly modeled; original response matcher/dial decisions execute.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_AX
ROOT=Path(__file__).resolve().parents[1];EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
def replay(image,overlay,index=None,auto=0,baud=3,key=None,timeout=60):
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x10000,image[0x1200:0xe2d0]);start=overlay['relative_load_segment']*16;pos=overlay['source_file_offset'];u.mem_write(0x10000+start,image[pos:pos+overlay['initialized_bytes']])
 def word(at,value):u.mem_write(0x40000+at,struct.pack('<H',value))
 word(0x1b86,baud);word(0x1b92,auto);word(0x1b8e,timeout);word(0x1d1a,1);word(0x1d68,5)
 slots=[f'R{i:02}'.encode() for i in range(11)];u.mem_write(0x41c48,b''.join(x+b'\0'*13 for x in slots));rx=bytearray(slots[index] if index is not None else b'');word(0x8e20,0);u.mem_write(0x46000,b'5550100\0')
 for i,value in enumerate([300,1200,2400,4800,9600,19200,38400,57600,115200]):u.mem_write(0x43270+i*4,struct.pack('<I',value))
 for r,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_SS,0x4000),(UC_X86_REG_SP,0xe000)]:u.reg_write(r,value)
 u.mem_write(0x4e000,struct.pack('<2H',0xf000,0x6000));calls=[];seconds=0;released=False;returned=[]
 hooks={0xaa5c:('carrier',0),0x498b:('choice-text',0),0x6bf0:('draw-text',6),0xabca:('rx-flush-boundary',0),0x48cc:('command-send',0),0x3323:('seconds',0),0x6530:('key-pending',0),0x7878:('key-read',0),0xaad9:('read-byte',2),0x75e8:('draw-formatted',0),0x3616:('connected-ui',0),0xac27:('set-baud',0),0x6bb6:('abort-delay',0),0x8e6c:('format-wait',0),0x7880:('edit-wait',12),0x6e66:('cursor-ui',4),0x6dca:('cursor-refresh',0)}
 def hook(uc,at,length,_):
  nonlocal seconds,key,released
  if at==0x1f000:returned.append(True);uc.emu_stop();return
  info=hooks.get(at-0x10000)
  if info is None:return
  op,cleanup=info;sp=uc.reg_read(UC_X86_REG_SP);ret,a,b=struct.unpack('<3H',uc.mem_read(0x40000+sp,6));result=0
  if op=='seconds':
   if seconds and not released:word(0x8e20,len(rx));released=True
   result=seconds;seconds=(seconds+1)%60
  elif op=='key-pending':result=int(key is not None)
  elif op=='key-read':result=key;key=None
  elif op=='read-byte':result=rx.pop(0);word(0x8e20,len(rx))
  elif op=='format-wait':u.mem_write(0x40000+b,str(a).encode()+b'\0')
  elif op=='edit-wait':calls.append({'operation':op,'accepted':False})
  elif op=='set-baud':calls.append({'operation':op,'baud':a+(b<<16)})
  elif op=='command-send':calls.append({'operation':op,'source':a,'echo':struct.unpack('<H',uc.mem_read(0x41d1a,2))[0],'pacing_units':struct.unpack('<H',uc.mem_read(0x41d68,2))[0]})
  elif op in ('rx-flush-boundary','abort-delay','connected-ui'):calls.append({'operation':op})
  uc.reg_write(UC_X86_REG_AX,result);uc.reg_write(UC_X86_REG_SP,sp+2+cleanup);uc.reg_write(UC_X86_REG_IP,ret)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x1e8ad,0x20000,count=100000);assert returned,'Original attempt did not return within instruction bound';assert u.reg_read(UC_X86_REG_SP)==0xe002
 state={name:struct.unpack('<H',u.mem_read(0x40000+offset,2))[0] for name,offset in [('baud_index',0x1b86),('echo',0x1d1a),('pacing',0x1d68)]}
 return {'result':u.reg_read(UC_X86_REG_AX),'state':state,'calls':calls,'unconsumed_response_bytes':len(rx)}
def main():
 p=argparse.ArgumentParser();p.add_argument('original',type=Path);p.add_argument('--manifest',type=Path,default=ROOT/'analysis/pcplus-overlays/manifest.json');a=p.parse_args();image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest=json.loads(a.manifest.read_text());overlay=next(x for x in manifest['overlays'] if x['id']==5);cases=[]
 for index in range(11):
  for auto in (0,1):
   result=replay(image,overlay,index,auto);assert result['result']==(1 if index<7 else 0),(index,result)
   assert result['state']=={'baud_index':index if index<7 and auto else 3,'echo':1,'pacing':5}
   setters=[x['baud'] for x in result['calls'] if x['operation']=='set-baud'];assert setters==([ [300,1200,2400,4800,9600,19200,38400][index] ] if index<7 and auto and index!=3 else [])
   sends=[x for x in result['calls'] if x['operation']=='command-send'];assert len(sends)==3 and all(x['echo']==0 and x['pacing_units']==30 for x in sends)
   cases.append({'case':'response','slot':index,'autobaud':auto,**result})
 for key,want in [(None,0),(0x1b,0x1b),(0x20,2),(0x4f00,0),(0x5300,3)]:
  result=replay(image,overlay,key=key,timeout=0 if key is None else 60);assert result['result']==want,(key,result);cases.append({'case':'timeout-or-key','key':key,**result})
 output={'passed':True,'source_sha256':EXPECTED,'cases':cases,'scope':'Actual original overlay5 e8ad and resident4a1d with synthetic response slots. UI, command send, baud setting, clock, keyboard and UART-read boundaries are modeled; Synthetic response is made available by the clock boundary after command sending, not before RXflush. No real modem/PRM or complete calling application.'}
 out=ROOT/'build/modem-responses/original-attempt-results.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(output,indent=2)+'\n');print('Passed',len(cases),'original dial-attempt response/autobaud/timeout/key cases')
if __name__=='__main__':main()
