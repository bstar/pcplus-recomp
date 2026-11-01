#!/usr/bin/env python3
"""Execute linked compiler lifecycle/EXEC guards without modeling a compiler."""
import argparse,hashlib,json,struct
from pathlib import Path
from check_directory_identity import Identity
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_directory_compile'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 for state in [0,1,2,3,4,5,65535]:
  for phase in (0,1,2):
   machine=Identity(binary);owner=machine.symbols['directory_compile_storage'];machine.uc.mem_write(owner,b'\xa5'*256)
   assert machine.bank('_directory_compile_exec_allowed')==1
   assert machine.bank('_directory_compile_initialize')==0 and bytes(machine.uc.mem_read(owner,256))==bytes(256)
   fixture=bytearray(256);struct.pack_into('<H',fixture,0,state);fixture[240]=phase;machine.uc.mem_write(owner,bytes(fixture))
   allowed=state<=4 and state!=2 and (state!=1 or phase==1)
   assert machine.bank('_directory_compile_exec_allowed')==allowed
   assert machine.bank('_directory_resources_exec_allowed',far=True)==allowed
   assert machine.bank('_directory_compile_initialize')==(2 if state in (1,2) or state>4 else 0)
   assert bytes(machine.uc.mem_read(owner,256))==fixture and not machine.calls
   cases.append(dict(case='state-'+str(state)+'-EXEC-phase-'+str(phase),passed=True))
 for name,args in [('zero-PSP',(0,1,1)),('null-bundle',(1,0,0)),('physical-wrap',(1,0xfff0,0xffff)),('owner-alias',(1,0,0))]:
  machine=Identity(binary);at=machine.symbols['directory_compile_storage'];machine.uc.mem_write(at,b'\xa5'*256)
  if name=='owner-alias':seg,off=machine.entries['directory_compile_storage'];args=(1,off,seg)
  assert machine.bank('_directory_compile_run',args)==1 and bytes(machine.uc.mem_read(at,256))==b'\xa5'*256 and not machine.calls
  cases.append(dict(case=name,passed=True))
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map')
 result=dict(passed=True,binary_sha256=sha(binary),inputs=len(cases),cases=cases,memory=memory,original_inputs=[],sources={n:sha(ROOT/n) for n in ['standalone/check_directory_compile.py','standalone/check_directory_identity.py','standalone/dos_image.py','standalone/terminal_memory.py']},scope=__doc__+' Explicit guard fixtures exercise actual linked instructions and ABI. No product instruction is patched or completed and no compile success is simulated. Actual parent/compiler execution has separate DOS receipts.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'linked compiler guard cases')
if __name__=='__main__':main()
