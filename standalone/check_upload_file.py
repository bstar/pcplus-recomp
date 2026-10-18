#!/usr/bin/env python3
"""Actual linked upload C ownership/bounds with explicit mocked DOS backend."""
import hashlib,json,struct
from pathlib import Path
from dos_image import DosImage
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/upload-file'
def main():
 cases=[]
 for name,argc,argument in [('fault-matrix',1,None),('ambiguous-close-no-repeat',2,b'9\0')]:
  m=DosImage(OUT/'UPFAULT.EXE',OUT/'upfault.map')
  if argument:
   m.uc.mem_write(m.data_base+0xf100,argument);m.uc.mem_write(m.data_base+0xf000,struct.pack('<3H',0,0xf100,0));argv=0xf000
  else:argv=0
  m.uc.reg_write(UC_X86_REG_AX,argc);m.uc.reg_write(UC_X86_REG_DX,argv)
  answer=m.call('main_',limit=5000000);assert answer==0,(name,answer)
  cases.append({'case':name,'passed':True})
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'UPFAULT.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked maintained upload_file.c and C filesystem-fault driver; no source ownership helper substituted. Mocked FS only; physical DOSIO is separately executed in test_upload_file_dos.py. Compile-time 16bitword/92bytes/offsetof assertions included.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(cases),'linked fault groups')
if __name__=='__main__':main()
