#!/usr/bin/env python3
"""Optional original-required replay: inspect actual original CSI-X rectangle calls."""
from pathlib import Path
import hashlib,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_IP
ROOT=Path(__file__).resolve().parents[1]
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
def probe(count):
 image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
 assert hashlib.sha256(image).hexdigest()==EXPECTED
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
 u.mem_write(0x10000,image[0x1200:0xe2d0])
 u.mem_write(0x1d0d0,image[89472:89472+7168])
 for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_SS,0x4000),(UC_X86_REG_SP,0xe000)]:u.reg_write(reg,value)
 for offset,value in [(0xcd38,ord('X')),(0xcb3c,count or 0),(0xcb5c,0 if count is None else 1),(0x399c,9),(0x399e,19),(0x1f70,7)]:u.mem_write(0x40000+offset,struct.pack('<H',value))
 u.mem_write(0x4e000,struct.pack('<H',0xf000));calls=[];returned=[]
 def hook(uc,address,size,_):
  if address==0x1f000:returned.append(True);uc.emu_stop()
  if address==0x12530:
   sp=uc.reg_read(UC_X86_REG_SP);words=struct.unpack('<5H',uc.mem_read(0x40000+sp,10))
   calls.append({'attribute':words[1],'bottom':words[2],'top':words[3],'scroll':words[4]})
   uc.reg_write(UC_X86_REG_SP,sp+10);uc.reg_write(UC_X86_REG_IP,words[0])
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x1e4b2,0x20000,count=5000)
 assert returned and len(calls)==1
 return calls[0]
def main():
 cases=[]
 for count,want in [(None,18),(0,18),(65535,17),(999,0x0bf9),(61,79),(62,80)]:
  actual=probe(count);expected_bottom=want if count==999 else 0x0900|want
  assert actual=={'attribute':7,'bottom':expected_bottom,'top':0x0913,'scroll':0},(count,actual)
  cases.append({'count':count,'original_rectangle':actual})
 result={'source_sha256':EXPECTED,'cases':cases,'scope':'Actual original overlay12 dispatcher instructions, synthetic parser/screen state, rectangle call intercepted before rendering; this does not establish BIOS reaction to invalid rectangles.'}
 out=ROOT/'build/csi';out.mkdir(parents=True,exist_ok=True);(out/'csi-x-original.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Original CSI-X omitted/zero/overflow/boundary rectangle calls characterized in',len(cases),'cases')
if __name__=='__main__':main()
