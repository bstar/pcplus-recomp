#!/usr/bin/env python3
"""Differential status string bridge clipping with real native text writes.
CPU replay of CONFIG/resident stack forwarding; synthetic width/video fixtures.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[];images={}
 for label,binary in [('baseline',a.baseline.resolve()),('candidate',a.terminal.resolve())]:
  manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
  if label=='baseline':assert sha(binary)==json.loads((ROOT/'docs/validation/large-auto-answer.json').read_text())['images']['ordinary']['sha256']
  else:
   for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
  images[label]=dict(path=str(binary.relative_to(ROOT)),sha256=sha(binary))
  entries={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(binary.parent/'terminal.map').read_text(),re.M|re.I)}
  for columns in (80,132):
   for row in (24,49):
    for col in (0,columns-1,columns):
     for payload in (b'',bytes(1+i%255 for i in range(200))):
      m=DosImage(binary,binary.parent/'terminal.map');m.put('screen_columns',columns);m.put('text_cga_status_port',0);m.put('status_error',0)
      ptr=m.stage_near(payload+b'\0');before=b'\xcc'*16384;m.uc.mem_write(0xb8000,before)
      seg,_=entries['status_write_string'];cs=m.base_segment+seg;sentinel=0xfffe;sp=m.offset('terminal_stack_top')-8
      m.uc.mem_write(m.data_base+sp,struct.pack('<4H',sentinel,ptr,0x1f,row*256+col));kept={UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x6789}
      for r,v in {**kept,UC_X86_REG_CS:cs,UC_X86_REG_DS:m.ds,UC_X86_REG_SS:m.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:0x202}.items():m.uc.reg_write(r,v)
      returned=[]
      def stop(u,at,size,d):
       if at==cs*16+sentinel:returned.append(True);u.emu_stop()
      m.uc.hook_add(UC_HOOK_CODE,stop);m.uc.emu_start(m.symbols['status_write_string'],0,count=100000)
      assert returned and m.uc.reg_read(UC_X86_REG_SP)==sp+8 and m.uc.reg_read(UC_X86_REG_DS)==m.uc.reg_read(UC_X86_REG_SS)==m.ds
      for r,v in kept.items():assert m.uc.reg_read(r)==v,r
      assert m.uc.reg_read(UC_X86_REG_EFLAGS)&0x600==0x200
      count=len(payload) if label=='baseline' else min(len(payload),max(0,columns-col));wanted=bytearray(before);at=(row*columns+col)*2
      for i,byte in enumerate(payload[:count]):wanted[at+i*2:at+i*2+2]=bytes([byte,31])
      assert bytes(m.uc.mem_read(0xb8000,16384))==bytes(wanted),(label,columns,row,col,len(payload))
      assert m.get('status_error')==(3 if label=='candidate' and col==columns else 0)
      cases.append(dict(image=label,columns=columns,row=row,column=col,source_bytes=len(payload),written_cells=count,stack_and_canaries_exact=True,passed=True))
 for n,h in json.loads((a.terminal.parent/'manifest.json').read_text())['sources'].items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,inputs=len(cases),cases=cases,images=images,sources={n:sha(ROOT/n) for n in ['standalone/check_status_string_bounds.py','standalone/dos_image.py']},scope=__doc__+' Baseline intentionally crosses row bounds; candidate clips or refuses column outside width, retaining native visible bytes and callee-cleaned ABI. Synthetic132-column addressing is not actual BIOS mode support.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS status string bounds',len(cases),'baseline/candidate inputs')
if __name__=='__main__':main()
