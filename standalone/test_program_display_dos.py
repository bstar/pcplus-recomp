#!/usr/bin/env python3
"""Real DOS PROGRAM scheduler/COMSPEC/EXEC child returns from graphics at four heights.
Diagnostic entry queues PROGRAM explicitly; return keys are actual BIOS input.
Synthetic serial peer only; no online BBS, ASPECT adoption, SIP/analog or hardware.
"""
import argparse,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_program_display_owner'] and m['diagnostic_row_geometry_probe'];assert sha(binary)==m['binary_sha256']
 with (out/'parent.log').open('w') as log:subprocess.run([sys.executable,str(ROOT/'standalone/test_large_view_dos.py'),'--terminal',str(binary),'--output',str(out/'views')],stdout=log,stderr=log,check=True,timeout=110)
 views=json.loads((out/'views/result.json').read_text());assert views['passed'] and len(views['cases'])==32
 cases=[];artifacts={}
 for label in ['normal','exclusive']:
  drive=out/'views/parent'/label/'drive';raw=(drive/'PROWS.BIN').read_bytes();words=struct.unpack('<35H',raw);assert words[:3]==(0x5052,2,4)
  assert (drive/'CHILD.LOG').read_bytes()==b'\x13'*4
  for r,rows in enumerate([25,28,43,50]):
   record=words[3+r*8:3+(r+1)*8];assert record==(rows,4,0,0,3,rows,rows-1,0),record
   before=(drive/f'PB{r}.BIN').read_bytes();after=(drive/f'PA{r}.BIN').read_bytes()
   assert len(before)==len(after)==8000 and before[:rows*160]==after[:rows*160]
   expected=b''.join(struct.pack('<H',0x0700+65+i%26) for i in range(rows*80));assert after[:rows*160]==expected
   cases.append(dict(run=label,rows=rows,passed=True,program_status=4,dos_child_status=0,ready=0,quit=0))
  for leaf in ['PROWS.BIN','CHILD.LOG','PCHILD.COM',*[f'P{phase}{r}.BIN' for phase in ['B','A'] for r in range(4)]]:
   p=drive/leaf;artifacts[str(p.relative_to(ROOT))]=sha(p)
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),cases=cases,shared_view_observations=32,diagnostic_package_rejected=views['diagnostic_package_rejected'],parent_result_sha256=sha(out/'views/result.json'),parent_log_sha256=sha(out/'parent.log'),artifacts=artifacts,checker_inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'standalone/test_large_view_dos.py',ROOT/'standalone/test_display_rows_terminal_dos.py',ROOT/'standalone/program_display_child.asm']},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS actual DOS:8 real PROGRAM/EXEC graphics-child returns,32 shared views, parent geometry/frame and hardware restoration')
if __name__=='__main__':main()
