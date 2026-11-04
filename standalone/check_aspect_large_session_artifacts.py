#!/usr/bin/env python3
"""Independently verify actual DOS session captures and retained far-history state."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 policy=re.findall(r'X\((\w+)\)',(ROOT/'src/aspect/renderer_policy.h').read_text())+['terminal_program_status']
 history_at=916+(len(policy)+3)*2+sum([2000,25,948,4,1,96,96,96,96,32,16,20,108])+256+512
 records=[];identities=[]
 for run in a.run:
  run=run.resolve();assert run.is_relative_to(ROOT/'build');rp=run/'result.json';report=json.loads(rp.read_text());assert report['passed'] and report['diagnostic_package_rejected']
  assert (len(report['cases'])==3 and {c['kind'] for c in report['cases']}=={'queries','RIS','window'}) or (len(report['cases'])==1 and report['cases'][0].get('nested') in ('save','noclear-text','noclear-graphics'))
  for n,h in report['sources'].items():assert sha(ROOT/n)==h,n
  for case in report['cases']:
   rows,profile,kind=case['physical_rows'],case['profile'],case['kind'];nested=case.get('nested');folder=run/(f'{rows}-{profile}-{kind}'+('-'+nested if nested else ''))/'run'
   for n,h in case['artifacts'].items():assert sha(folder/n)==h,n
   raw=(folder/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw);assert header[:4]==(0x524e,1,1,1) and header[6]==0
   history=[raw[history_at+i*72:history_at+(i+1)*72] for i in range(3)];states=[struct.unpack_from('<4H',h) for h in history]
   assert all(len(h)==72 for h in history) and history[1]==history[2] and history[0]!=history[1]
   image=report['images'][str(rows)];binary=ROOT/image['path'];manifest=json.loads((binary.parent/'manifest.json').read_text())
   expected_segment=header[5]+16+manifest['memory_layout']['history_relative_segment']
   assert all(start<=pointer<end and end-start==63000 and segment==expected_segment for start,end,pointer,segment in states)
   state=struct.unpack_from('<10H',raw,886);assert state[5]==profile and state[6:8]==((rows-2,10) if kind=='window' else (0,21)),state
   if nested:
    logical=rows-1;expected=bytearray(b' \x07'*(logical*80))
    if nested!='noclear-graphics':
     for offset,text in [(0,b'FIRST BYTE SAFELOGIN:'),((logical-1)*160,('LOWER-'+str(rows)).encode())]:
      for i,value in enumerate(text):expected[offset+2*i]=value
    if nested=='noclear-text':expected[20*160:20*160+2]=b'C\x4f'
    assert (folder/'SCREEN.BIN').read_bytes()[:logical*160]==expected,(rows,profile,nested,'complete logical frame')
   else:
    logical=rows-1;expected=bytearray(b' \x07'*(logical*80))
    bottom=b'UPDATEDEND' if kind=='window' else b'' if kind=='RIS' else ('LOWER-'+str(rows)).encode()
    for offset,text in [(0,b'FIRST BYTE SAFELOGIN:'),((logical-1)*160,bottom)]:
     for i,value in enumerate(text):expected[offset+2*i]=value
    assert (folder/'SCREEN.BIN').read_bytes()[:logical*160]==expected,(rows,profile,kind,'complete logical frame')
   assert case['cpu']=='8086' and case['serial_irq']==5 and all(case['checks'].values())
   records.append(dict(rows=rows,profile=profile,kind=kind,nested=nested,child_exit=0,far_history_retained=True,far_history_segment=expected_segment,history_states=states,exit_cursor=state[6:8],result_sha256=sha(folder/'result.json'),observer_capture_sha256=sha(folder/'RENDER.BIN')))
  identities.append(dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp)))
 result=dict(passed=True,cases=records,actual_DOS_cases=len(records),reports=identities,checker_sha256=sha(Path(__file__)),policy_header_sha256=sha(ROOT/'src/aspect/renderer_policy.h'),scope=__doc__+' Checks immutable actual parent/ASPECT captures, real child exit, cursor and independent far-history relocation/bounds/content across EXEC. No new runtime, original executable or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS independent session artifacts',len(records),'actual DOS cases')
if __name__=='__main__':main()
