#!/usr/bin/env python3
"""Optional real-original flow-message comparison, including its full call chain."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INSN,UC_HOOK_MEM_READ
from unicorn.x86_const import *
from check_ui_flow import Flow,ROOT,BINARY

def replay(image,video,duration,suppressed,cga,bottom):
 uc=Uc(UC_ARCH_X86,UC_MODE_16);uc.mem_map(0,0x100000)
 header=struct.unpack_from('<14H',image);size=(header[2]-1)*512+(header[1] or 512)
 uc.mem_write(0x10000,image[header[4]*16:size])
 for i in range(header[3]):
  off,seg=struct.unpack_from('<HH',image,header[12]+i*4);at=0x10000+seg*16+off
  value=struct.unpack('<H',uc.mem_read(at,2))[0];uc.mem_write(at,struct.pack('<H',(value+0x1000)&65535))
 base=0x1fb70
 for at,value in [(0x7a78,0xb800),(0x7a8e,0x3da if cga else 0),(0x3250,80),(0x7a82,3840 if bottom else 0),(0x7a84,0x1800 if bottom else 0),(0x1d46,int(suppressed)),(0x1f6e,0x2f),(0x7a72,80)]:uc.mem_write(base+at,struct.pack('<H',value))
 uc.mem_write(base+0x9000,b'123456789ABCDE\0');uc.mem_write(0xb8000,video)
 uc.mem_write(base+0xf2a0,struct.pack('<3H',0xfff0,0x9000,duration))
 for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x1fb7),(UC_X86_REG_SS,0x1fb7),(UC_X86_REG_SP,0xf2a0),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:uc.reg_write(reg,value)
 returned=[];reads=[];ticks=[];outputs=[]
 def stop(machine,address,size,_):
  if address==0x1fff0:returned.append(True);machine.emu_stop()
 def status(machine,port,size,_):
  assert (port,size)==(0x3da,1);value=9 if len(reads)%2 else 0;reads.append(value);return value
 def output(machine,port,size,value,_):
  assert (port,size)==(0x3d8,1);outputs.append(value)
 def clock(machine,access,address,size,value,_):
  assert address==0x46c and size==2
  machine.mem_write(0x46c,((0xfffe+len(ticks)//3)&65535).to_bytes(2,'little'));ticks.append(True)
 uc.hook_add(UC_HOOK_CODE,stop);uc.hook_add(UC_HOOK_INSN,status,None,1,0,UC_X86_INS_IN)
 uc.hook_add(UC_HOOK_INSN,output,None,1,0,UC_X86_INS_OUT);uc.hook_add(UC_HOOK_MEM_READ,clock,None,0x46c,0x46d)
 uc.emu_start(0x131bb,0,count=500000)
 assert returned and uc.reg_read(UC_X86_REG_SP)==0xf2a2
 for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert uc.reg_read(reg)==value
 return bytes(uc.mem_read(0xb8000,4000)),len(reads),len(ticks),outputs

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--original',type=Path,required=True);args=parser.parse_args()
 image=args.original.read_bytes();proof=json.loads((ROOT/'reconstruction/ui_windows/provenance.json').read_text());digest=hashlib.sha256(image).hexdigest();assert digest==proof['source_sha256']
 video=bytes(i%256 for i in range(4000));cases=[]
 for cga in (False,True):
  for bottom in (False,True):
   for suppressed in (False,True):
    for duration in (0,1,3,65535):
     expected=replay(image,video,duration,suppressed,cga,bottom)
     a=Flow();a.uc.mem_write(a.video,video);a.put('text_cga_status_port',0x3da if cga else 0);a.put('ui_flow_attribute',0x2f);a.put('ui_flow_suppressed',int(suppressed));a.put('ui_flow_video_base',3840 if bottom else 0);a.put('ui_flow_coordinate_base',0x1800 if bottom else 0)
     a.message(duration,b'123456789ABCDE')
     assert (a.memory(),a.reads,a.tick_reads,a.outputs)==expected,(cga,bottom,suppressed,duration)
     cases.append({'cga':cga,'bottom_row':bottom,'suppressed':suppressed,'duration':duration,'matched':True})
 result={'passed':True,'case_count':len(cases),'original_sha256':digest,'source_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual resident original flow message+complete original dependencies compared with linked recovery. Text video,stack ABI,preserved registers,BDA read counts,CGA IN/OUT match. Explicit synthetic clock/port fixtures on both sides.'}
 (ROOT/'build/ui-windows/flow-original-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(len(cases),'original/source full-chain flow-message comparisons passed')
if __name__=='__main__':main()
