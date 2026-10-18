#!/usr/bin/env python3
"""Optional runtime comparison of real original resident helpers and linked source."""
from pathlib import Path
import argparse,hashlib,json,random,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INSN
from unicorn.x86_const import *
from check_ui_windows import Windows,ROOT,BINARY

def replay(image,entry,video,buffer,offset,count,cga):
 uc=Uc(UC_ARCH_X86,UC_MODE_16);uc.mem_map(0,0x100000)
 header=struct.unpack_from('<14H',image);size=(header[2]-1)*512+(header[1] or 512)
 uc.mem_write(0x10000,image[header[4]*16:size])
 for i in range(header[3]):
  off,seg=struct.unpack_from('<HH',image,header[12]+i*4);at=0x10000+seg*16+off
  value=struct.unpack('<H',uc.mem_read(at,2))[0];uc.mem_write(at,struct.pack('<H',(value+0x1000)&65535))
 ds=0x1fb7;base=ds*16
 uc.mem_write(base+0x7a78,struct.pack('<H',0xb800));uc.mem_write(base+0x7a8e,struct.pack('<H',0x3da if cga else 0))
 uc.mem_write(0xb8000,video);uc.mem_write(base+0x9000,buffer)
 uc.mem_write(base+0xf2a0,struct.pack('<4H',0xfff0,count,offset,0x9000))
 for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,ds),(UC_X86_REG_SS,ds),(UC_X86_REG_SP,0xf2a0),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:uc.reg_write(reg,value)
 returned=[];reads=[]
 def stop(machine,address,size,_):
  if address==0x1fff0:returned.append(True);machine.emu_stop()
 def status(machine,port,size,_):
  assert (port,size)==(0x3da,1);value=len(reads)%2;reads.append(value);return value
 uc.hook_add(UC_HOOK_CODE,stop);uc.hook_add(UC_HOOK_INSN,status,None,1,0,UC_X86_INS_IN)
 uc.emu_start(entry,0,count=500000);assert returned and uc.reg_read(UC_X86_REG_SP)==0xf2a8
 for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert uc.reg_read(reg)==value
 return bytes(uc.mem_read(0xb8000,4000)),bytes(uc.mem_read(base+0x9000,4096)),len(reads)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--original',type=Path,required=True);args=parser.parse_args()
 image=args.original.read_bytes();proof=json.loads((ROOT/'reconstruction/ui_windows/provenance.json').read_text());digest=hashlib.sha256(image).hexdigest();assert digest==proof['source_sha256']
 rng=random.Random(201);cases=[]
 for name,entry in [('pcplus_screen_save',0x1765c),('pcplus_screen_restore',0x17682)]:
  for cga in (False,True):
   for offset,count in [(0,0),(0,1),(2,15),(160,80),(3998,1),(0,1999),(0,2000)]:
    video=bytes(rng.randrange(256) for _ in range(4000));buffer=bytes(rng.randrange(256) for _ in range(4096))
    expected=replay(image,entry,video,buffer,offset,count,cga)
    a=Windows();a.put('text_cga_status_port',0x3da if cga else 0);a.uc.mem_write(a.video,video);a.uc.mem_write(a.symbols['window_buffer'],buffer)
    a.invoke(name,[count,offset,a.offset('window_buffer')])
    assert (a.memory(),a.data(),a.reads)==expected,(name,cga,offset,count)
    cases.append({'routine':name,'cga':cga,'offset':offset,'count':count,'matched':True})
 result={'passed':True,'case_count':len(cases),'original_sha256':digest,'source_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual original resident save/restore/read and packed writer versus linked source; video,buffer,ABI and alternating CGA-port read counts compared. No synthetic analysis executable or overlay execution.'}
 (ROOT/'build/ui-windows/original-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(len(cases),'original/source window snapshot comparisons passed')
if __name__=='__main__':main()
