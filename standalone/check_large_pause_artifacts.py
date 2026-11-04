#!/usr/bin/env python3
"""Independent raw Pause frames, modem commands, file records and wire checks.
Does not establish physical Boca/SPA2102/SIP or BBS acceptance.
"""
import argparse,datetime as dt,hashlib,json,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
HEADING=b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
OLD=b'\r\n'+b'PREVIOUS CALL'.ljust(22)+b' '+b'5550100'.rjust(20)+b' 01/02/95 03:04:05 03:05:06 00:01:01'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--direct',type=Path,action='append',required=True);p.add_argument('--carrier',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[];artifacts={};images={};reports={}
 for label in ('ordinary','25','28','43','50'):
  parent=(a.build/label).resolve();manifest=json.loads((parent/'manifest.json').read_text());assert sha(parent/'TERMINAL.EXE')==manifest['binary_sha256']
  for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
  images[manifest['binary_sha256']]=dict(label=label,manifest=manifest)
 def frames(folder,rows):
  raw=(folder/'PAUSE.BIN').read_bytes();size=rows*160;assert len(raw)==size*2 and raw[:size]==raw[size:]
  assert raw[:30:2]==b'FIRST BYTE SAFE'
  row=raw[size-160:size];message=b'Screen paused.  Press any key to continue...'
  assert row[36:36+len(message)*2:2]==message and row[1::2]==b'\x70'*80
  assert f'LOWER-{rows}'.encode() in raw[(rows-2)*160:(rows-1)*160:2] and b'QUEUED' not in raw[::2]
  watcher=out/f'watch-{rows}.com'
  if not watcher.exists():subprocess.run(['nasm','-fbin','-DPAUSE_ROWS='+str(rows),str(ROOT/'standalone/pause_watch.asm'),'-o',str(watcher)],check=True)
  assert sha(watcher)==sha(folder/'PAUSEW.COM')
  assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
  assert len((folder/'BEFORE.BIN').read_bytes())==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  assert 'cputype=8086' in (folder/'dosbox.conf').read_text()
  for f in folder.rglob('*'):
   if f.is_file():artifacts[str(f.relative_to(ROOT))]=sha(f)
 for path in a.direct:
  path=path.resolve();r=json.loads(path.read_text());assert r['passed'] and {c['case'] for c in r['cases']}=={'direct','reference','partial-parser'}
  rows=r['rows'];image=images[r['terminal_sha256']];assert (image['manifest'].get('diagnostic_session_rows_probe') or 25)==rows
  for c in r['cases']:
   result=ROOT/c['result'];case=json.loads(result.read_text());assert case['passed'] and all(case['checks'].values()) and case['binary_sha256']==r['terminal_sha256']
   folder=result.parent;frames(folder,rows);wire=(folder/'serial.bin').read_bytes();lower=b'\x1b'+f'[{rows-1};9R'.encode()
   assert wire.count(b'\x13')==wire.count(b'\x11')==1 and wire.index(b'\x11')<wire.index(b'\x1b[8;7R')
   assert re.findall(rb'\x1b\[\d+;\d+R',wire)==[b'\x1b[1;16R',lower,b'\x1b[8;7R',b'\x1b[1;16R',lower]
   assert wire.count(b'ready\r')==1 and b'x' not in wire
   cases.append(dict(kind='direct',rows=rows,image=image['label'],case=c['case'],passed=True))
  reports[str(path.relative_to(ROOT))]=sha(path)
 assert {c['rows'] for c in cases}=={25,28,43,50} and any(c['image']=='ordinary' for c in cases)
 n=0
 for path in a.carrier:
  path=path.resolve();r=json.loads(path.read_text());assert r['passed'] and {c['soft'] for c in r['cases']}=={0,1};rows=r['rows'];image=images[r['terminal_sha256']]
  assert image['manifest']['diagnostic_session_rows_probe']==rows
  for name,h in r['sources'].items():assert sha(ROOT/name)==h,name
  for c in r['cases']:
   folder=path.parent/c['case'];assert c['passed'] and all(c['checks'].values()) and len(c['sessions'])==2 and all(not s['errors'] for s in c['sessions'])
   for name,h in c['artifacts'].items():assert sha(ROOT/name)==h,name
   frames(folder,rows);first=(folder/'connection-1.bin').read_bytes();second=(folder/'connection-2.bin').read_bytes()
   assert first.count(b'\x13')==1 and b'\x11' not in first and b'x' not in first+second
   lower=b'\x1b'+f'[{rows-1};9R'.encode();assert all(lower in b and b'\x1b[1;16R' in b and b'\x1b[?1;2c' in b for b in (first,second))
   assert b'\x1b[2;10R' in second and b'ready' in second and b'\x1b[3;6R' in second
   log=(folder/'dosbox.log').read_text();commands=[s for s in re.findall(r'Command sent to modem: ->(.*?)<-',log) if s]
   dial=(folder/'TEST.DIR').read_bytes()[275:296].split(b'\0',1)[0];init='AT&K4' if c['soft'] else 'AT&K3';expected=[init,'ATD'+dial.decode()]*2
   assert commands in (expected,expected+['ATH']) and 'Modem response: ERROR' not in log and log.count('Modem response: CONNECT')==2 and 'Modem response: NO CARRIER' in log
   starts=list(re.finditer(re.escape('Command sent to modem: ->'+init+'<-'),log));assert len(starts)==2
   for at in starts:assert 'Modem response: OK' in log[at.end():log.index('Command sent to modem: ->ATD',at.end())]
   raw=(folder/'PLSTATE.BIN').read_bytes();assert len(raw)==9798;header=struct.unpack_from('<10H',raw);assert header[0]==0x4c45 and header[3]==1 and header[9]==0 and 1<=header[2]<=8
   final=raw[20+(header[2]-1)*722:20+header[2]*722];assert struct.unpack_from('<3H',final,716)==(4,0,0)
   fon=(folder/'PCPLUS.FON').read_bytes();seed=HEADING+OLD;assert fon.startswith(seed) and len(fon)==len(seed)+162
   for i in range(2):
    rec=fon[len(seed)+i*81:len(seed)+(i+1)*81];assert rec[:46]==b'\r\n'+b'LAB NODE 001'.ljust(22)+b' '+dial.rjust(20)+b' '
    start=dt.datetime.strptime(rec[46:63].decode(),'%m/%d/%y %H:%M:%S');hh,mm,ss=map(int,rec[73:81].split(b':'));assert mm<60 and ss<60
    assert (start+dt.timedelta(hours=hh,minutes=mm,seconds=ss)).strftime('%H:%M:%S').encode()==rec[64:72]
   assert len((folder/'SCREEN.BIN').read_bytes())==8000
   cases.append(dict(kind='carrier',rows=rows,soft=c['soft'],connections=2,passed=True));n+=1
  reports[str(path.relative_to(ROOT))]=sha(path)
 assert n==8 and {c['rows'] for c in cases if c['kind']=='carrier'}=={25,28,43,50}
 sources={name:sha(ROOT/name) for name in ['standalone/check_large_pause_artifacts.py','standalone/test_screen_pause_dos.py','standalone/test_large_pause_carrier_dos.py','standalone/test_connection_dos.py','standalone/test_phone_log_carrier_terminal.py','standalone/pause_watch.asm']}
 report=dict(passed=True,cases=cases,DOS_workflows=len(cases),virtual_modem_connections=n*2,pause_frames=len(cases)*2,artifacts=artifacts,reports=reports,sources=sources,scope=__doc__+' Independent complete paused frames, lower-row CPR, queued query/XON order, raw call records, clean initialization and same-parent redial. Exact post-resume underlay and transient DCD timing remain linked-model evidence.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS independent Pause captures',len(cases),'DOS workflows')
if __name__=='__main__':main()
