#!/usr/bin/env python3
"""Optional analyst replay: verified original instructions, synthetic command bytes.

Not used by source-only builds/tests. UART and time boundaries are explicitly
modeled; this never opens a PRM, modem or network endpoint.
"""
import argparse,hashlib,json,random,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_AX
from prm import expand_modem_command,modem_command_events
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
def main():
 p=argparse.ArgumentParser();p.add_argument('original',type=Path);p.add_argument('--output',type=Path,default=Path('build/modem-config/original-replay.json'));args=p.parse_args()
 image=args.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 uc=Uc(UC_ARCH_X86,UC_MODE_16);uc.mem_map(0,0x100000);uc.mem_write(0x10000,image[0x1200:0x1200+53456])
 for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x3000)]:uc.reg_write(reg,value)
 events=[]
 def hook(u,address,size,_):
  if address==0x1c000:u.emu_stop();return
  kind={0x1ab0b:'transmit',0x16b72:'character_delay_units',0x16b98:'pause_bios_tick_changes'}.get(address)
  if not kind:return
  sp=u.reg_read(UC_X86_REG_SP);ret,arg=struct.unpack('<2H',u.mem_read(0x30000+sp,4))
  events.append((kind,arg+1 if address==0x16b98 else arg));u.reg_write(UC_X86_REG_SP,sp+4);u.reg_write(UC_X86_REG_IP,ret)
 uc.hook_add(UC_HOOK_CODE,hook)
 def call(entry,params):
  uc.reg_write(UC_X86_REG_SP,0xf000);uc.mem_write(0x3f000,struct.pack('<'+str(1+len(params))+'H',0xc000,*params));uc.emu_start(0x10000+entry,0x20000,count=100000)
  assert uc.reg_read(UC_X86_REG_IP)==0xc000
 rng=random.Random(201);samples=[b'',b'AT^M',b'^^',b'^^^',b'A^`B']+[b'^'+bytes([i]) for i in range(1,256)]
 samples += [bytes(rng.randrange(1,256) for _ in range(rng.randrange(127)))+b'A' for _ in range(256)]
 count=0
 for data in samples:
  try:want=expand_modem_command(data)
  except ValueError:continue
  uc.mem_write(0x36000,data+b'\0');uc.mem_write(0x36200,b'\xa5'*130);call(0x4934,[0x6000,0x6200])
  actual=bytes(uc.mem_read(0x36200,len(want)+1));assert actual==want+b'\0',(data,actual,want);count+=1
 plans=0
 for pause in (0,13,126,255):
  for delay in (0,1,30,65535):
   for data in (b'AT^M',b'~~~+++^@^M',b'^^^',b'A^`B'):
    uc.mem_write(0x36000,data+b'\0');uc.mem_write(0x31d66,bytes([pause]));uc.mem_write(0x31d68,struct.pack('<H',delay));uc.mem_write(0x31d1a,b'\0\0');events.clear();call(0x48cc,[0x6000])
    assert tuple(events)==modem_command_events(data,pause,delay),(data,pause,delay,events);plans+=1
 result={'passed':True,'source_sha256':EXPECTED,'synthetic_expansion_cases':count,'sender_plan_cases':plans,'scope':'Actual original4934/48cc instructions with synthetic strings and modeled transmit/calibrated-delay/BIOS-delay boundaries. No original data/PRM or physical timing read.'}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
