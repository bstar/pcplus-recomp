#!/usr/bin/env python3
"""Independently verify captured DOS modem reconnect sessions at larger heights."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 records=[];reports=[]
 policy=re.findall(r'X\((\w+)\)',(ROOT/'src/aspect/renderer_policy.h').read_text())+['terminal_program_status']
 history_at=916+(len(policy)+3)*2+sum([2000,25,948,4,1,96,96,96,96,32,16,20,108])+256+512
 for run in a.run:
  run=run.resolve();assert run.is_relative_to(ROOT/'build');report=json.loads((run/'result.json').read_text());assert report['passed']
  for name,h in report['sources'].items():assert sha(ROOT/name)==h,name
  for name,h in report['inputs'].items():assert sha(ROOT/name)==h,name
  folder=run/'run'
  for name,h in report['captures'].items():assert sha(folder/name)==h,name
  assert sha(run/'observer.asm')==report['observer_source_sha256'] and sha(run/'RENDER.COM')==report['observer_sha256']
  rows,profile,flow=report['physical_rows'],report['profile'],report['flow'];logical=rows-1
  assert rows in (25,28,43,50) and profile in (4,6) and flow in ('soft','both')
  events=json.loads((folder/'peer-events.json').read_text());assert [e['session'] for e in events if e['kind']=='connected']==[1,2]
  assert sum(e['kind']=='first-hangup' for e in events)==sum(e['kind']=='completed-hangup' for e in events)==1
  assert sum(e['kind']=='xoff' for e in events)==1
  streams=[b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and e['session']==n) for n in (1,2)]
  assert (folder/'serial.bin').read_bytes()==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
  for wire in streams:
   assert b'\x1b[1;16R' in wire and (b'\x1b[?62;2c' if profile==4 else b'\x1b[?1;2c') in wire
   assert b'\x1b'+f'[{logical};{len("LOWER-"+str(rows))+1}R'.encode() in wire
  clean=[bytes(c for c in wire if c not in (17,19)) for wire in streams]
  assert b'KEYREADY' in clean[0] and b'SECONDOK' not in clean[0]
  assert b'KEYREADY' in clean[1] and b'SECONDOKready\x1b[1;25R' in clean[1]
  common=b'\x1b[1;16R'+(b'\x1b[?62;2c' if profile==4 else b'\x1b[?1;2c')+b'\x1b'+f'[{logical};{len("LOWER-"+str(rows))+1}R'.encode()+b'\x1b[1;16RKEYREADY'
  assert clean==[common,common+b'\x1b[1;22RSECONDOKready\x1b[1;25R'],clean
  assert (folder/'SECOND.OK').read_bytes()==b'RECONNECTED'
  log=(folder/'dosbox.log').read_text();dial=(folder/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
  commands=re.findall(r'Command sent to modem: ->(.*?)<-',log)
  assert commands in (['ATZ','ATD'+dial]*2,['ATZ','ATD'+dial,'','ATZ','ATD'+dial])
  assert log.count('Modem response: NO CARRIER')==2 and 'Modem response: ERROR' not in log
  config=(folder/'dosbox.conf').read_text();assert 'cputype=8086' in config and 'serial3=modem listenport:0 irq:5' in config
  assert (folder/'PASS.TXT').is_file() and not (folder/'FAIL.TXT').exists()
  assert len((folder/'BEFORE.BIN').read_bytes())==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  raw=(folder/'RENDER.BIN').read_bytes();h=struct.unpack_from('<7H',raw);assert h[:4]==(0x524e,1,1,1) and h[6]==14
  assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
  # Fixed independent layout of the appended second-EXEC/event sample.
  extra=raw[-(48+40+832):];v=struct.unpack_from('<24H',extra)
  assert v[:4]==(1,1,1,0) and v[4]>=36 and v[5]==0 and v[6]>=36 and v[7]>=36 and v[8:12]==(1,1,1,1)
  assert v[12:]==(1,0,6,0,0,0,0,rows,0,logical,rows,14 if rows==28 else 8 if rows in (43,50) else 16)
  assert extra[48:68]==extra[68:88] and extra[88:504]==extra[504:920]
  history=[raw[history_at+i*72:history_at+(i+1)*72] for i in range(3)];states=[struct.unpack_from('<4H',x) for x in history]
  parent=next(ROOT/n for n in report['inputs'] if n.endswith('/TERMINAL.EXE'));manifest=json.loads((parent.parent/'manifest.json').read_text());segment=h[5]+16+manifest['memory_layout']['history_relative_segment']
  assert history[0]!=history[1] and history[1]==history[2]
  assert all(start<=pointer<end and end-start==63000 and seg==segment for start,end,pointer,seg in states)
  screen=(folder/'SCREEN.BIN').read_bytes();expected=bytearray(b' \x07'*(logical*80))
  for at,text in [(0,b'FIRST BYTE SAFELOGIN:END'),(160,b'NO CARRIER'),((logical-1)*160,('LOWER-'+str(rows)).encode())]:
   for i,c in enumerate(text):expected[at+2*i]=c
  assert len(screen)==8000 and screen[:logical*160]==expected
  assert screen[logical*160:(logical+1)*160:2].startswith(b' Carrier lost')
  assert b'OFF-LINE' in screen[logical*160:(logical+1)*160:2]
  assert all(report['checks'].values())
  records.append(dict(rows=rows,profile=profile,flow=flow,parent_psp=h[5],child_exits=[14,0],first_history_segment=segment,same_process_connections=2,final_parent_owners_released=True,logical_cells_exact=True,result_sha256=sha(run/'result.json'),raw_capture_sha256=sha(folder/'RENDER.BIN')))
  reports.append(dict(path=str((run/'result.json').relative_to(ROOT)),sha256=sha(run/'result.json')))
 result=dict(passed=True,cases=records,actual_DOS_workflows=len(records),actual_modem_connections=2*len(records),reports=reports,checker_sha256=sha(Path(__file__)),scope=__doc__+' Actual raw EXEC/JFT/owner/event samples, source bindings, modem log, peer wire, frame and first-child far history. Real physical UART/SIP/BBS and transfer acceptance are separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS independent modem reconnect artifacts',len(records),'DOS workflows')
if __name__=='__main__':main()
