#!/usr/bin/env python3
"""Optional original-vs-source CPU comparison; local original remains untracked."""
import argparse,hashlib,json,random,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_INS_IN,UC_X86_INS_OUT
from check_reports import Reports,ROOT
sys.path.insert(0,str(ROOT/'reconstruction'))
from check_ansi_freeze import load_image
STATE={'ansi_parameters':0xcb3c,'ansi_private':0xceac,'screen_cursor_row':0x399c,'screen_cursor_column':0x399e,'csi_origin_row':0xceb0,'csi_report_private_prefix':0x904c,'csi_printer_ready':0x3984,'csi_terminal_id':0x1d18}
def original_reply(image,state,attributes=False):
 uc=load_image(image)
 defaults={'ansi_parameters':5,'screen_cursor_row':9,'screen_cursor_column':19,'csi_terminal_id':2}
 defaults.update(state)
 for name,at in STATE.items():uc.mem_write(0x1fb70+at,struct.pack('<H',defaults.get(name,0)&0xffff))
 for at,value in [(0x900a,0x3fd),(0x9012,0x3f8),(0x8ffe,0x3fe),(0x3356,0),(0x39a6,0)]:uc.mem_write(0x1fb70+at,struct.pack('<H',value))
 uc.mem_write(0x1fb70+0xf2a0,struct.pack('<H',0xfff0))
 reply=bytearray();returned=[]
 def output(machine,port,size,value,_):
  if port==0x3f8:reply.append(value&255)
 def stop(machine,address,size,_):
  if address==0x1fff0:returned.append(True);machine.emu_stop()
 uc.hook_add(UC_HOOK_CODE,stop)
 uc.hook_add(UC_HOOK_INSN,lambda machine,port,size,_:{0x3fd:0x60,0x3fe:0xb0}.get(port,0),None,1,0,UC_X86_INS_IN)
 uc.hook_add(UC_HOOK_INSN,output,None,1,0,UC_X86_INS_OUT)
 uc.emu_start(0x1dd58 if attributes else 0x1de04,0,count=100000)
 assert returned,'Original reporter did not return'
 return bytes(reply)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--original',type=Path,required=True);args=parser.parse_args()
 image=args.original.read_bytes();digest=hashlib.sha256(image).hexdigest()
 assert digest=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 cases=[]
 def compare(state,attributes=False):
  original=original_reply(image,state,attributes)
  source=Reports(**state).reply('csi_primary_attributes' if attributes else 'csi_device_status')
  assert source==original,(state,source,original)
  cases.append({'state':state,'attributes':attributes,'reply_hex':source.hex(),'matched':True})
 for query in range(17):
  for flag in (0,1):compare({'ansi_parameters':query,'ansi_private':flag,'csi_report_private_prefix':flag,'csi_printer_ready':flag})
 for index in range(2,12):compare({'csi_terminal_id':index},True)
 rng=random.Random(201)
 coordinates=[(9,19,0),(0,0,0),(65535,32767,1),(32767,65535,0),(0,0,32768)]+[tuple(rng.randrange(65536) for _ in range(3)) for _ in range(64)]
 for row,column,origin in coordinates:
  for flag in (0,1):compare({'ansi_parameters':6,'ansi_private':flag,'csi_report_private_prefix':flag,'screen_cursor_row':row,'screen_cursor_column':column,'csi_origin_row':origin})
 result={'passed':True,'original_sha256':digest,'source_sha256':hashlib.sha256((ROOT/'build/reports/REPORTS.EXE').read_bytes()).hexdigest(),'case_count':len(cases),'scope':'Original resident/overlay instructions and UART writes compared with source-built reporting fixture; not full parser or hardware.','cases':cases}
 (ROOT/'build/reports/original-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(len(cases),'original/source reporting comparisons passed')
if __name__=='__main__':main()
