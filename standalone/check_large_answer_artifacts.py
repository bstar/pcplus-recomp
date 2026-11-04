#!/usr/bin/env python3
"""Independent full-height Auto Answer frames, serial ordering and modem logs.
Owned DOS/emulator captures only; no physical/SIP/BBS acceptance.
"""
import argparse,datetime as dt,hashlib,json,re,struct
from pathlib import Path
from answer_notice_watch import build as build_watcher
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
HEADING=b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
OLD=b'\r\n'+b'PREVIOUS CALL'.ljust(22)+b' '+b'5550100'.rjust(20)+b' 01/02/95 03:04:05 03:05:06 00:01:01'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--direct',type=Path,action='append',required=True);p.add_argument('--carrier',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);images={};cases=[];artifacts={};reports={}
 for label in ('ordinary','25','28','43','50'):
  parent=(a.build/label).resolve();m=json.loads((parent/'manifest.json').read_text());assert sha(parent/'TERMINAL.EXE')==m['binary_sha256']
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
  images[m['binary_sha256']]=(label,m)
 def capture(folder,rows):
  frames=(folder/'PAUSE.BIN').read_bytes();size=rows*160;assert len(frames)==size*2
  for at in (0,size):
   assert frames[at+size-160:at+size-130:2]==b' AUTO ANSWER...'
   assert f'LOWER-{rows}'.encode() in frames[at+(rows-2)*160:at+(rows-1)*160:2]
  watch=out/str(rows)
  if not watch.exists():watch.mkdir();build_watcher(watch,rows)
  assert sha(folder/'ANSWERW.COM')==sha(watch/'ANSWERW.COM')
  assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
  assert len((folder/'BEFORE.BIN').read_bytes())==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  assert 'cputype=8086' in (folder/'dosbox.conf').read_text()
  for f in folder.rglob('*'):
   if f.is_file():artifacts[str(f.relative_to(ROOT))]=sha(f)
 def report(path):
  path=path.resolve();r=json.loads(path.read_text());assert r['passed'] and r['terminal_sha256'] in images
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
  reports[str(path.relative_to(ROOT))]=sha(path);return path,r
 for path in a.direct:
  path,r=report(path);rows=r['rows'];label,m=images[r['terminal_sha256']];assert (m.get('diagnostic_session_rows_probe') or 25)==rows
  assert {c['case'] for c in r['cases']}=={'direct-quiet','reference-echo-sound'}
  for c in r['cases']:
   result=ROOT/c['result'];v=json.loads(result.read_text());assert v['passed'] and all(v['checks'].values()) and v['binary_sha256']==r['terminal_sha256'];folder=result.parent;capture(folder,rows)
   wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes();assert len(screen)==4000 and b'AUTO ANSWER...' not in screen[::2]
   assert wire.count(b'ATZ\r')==wire.count(b'ATDCaseTest:23\r')==wire.count(b'ATS0=1\r\n')==wire.count(b'ready\r')==1
   at=wire.index(b'ATS0=1\r\n');assert wire.index(b'x',at+8)>=at+8 and b'~' not in wire
   assert b'\x1b[2;10R' in wire and b'\x1b'+f'[{rows-1};9R'.encode() in wire
   enabled=c['case']=='reference-echo-sound';assert (b'ATS0=1' in screen[::2])==enabled
   assert (folder/'TEST.PRM').read_bytes()[0x92:0xab]==b'ATS0=1~~^M^J\0'.ljust(25,b'\0')
   cases.append(dict(kind='direct',image=label,rows=rows,case=c['case'],passed=True))
 assert len(cases)==10 and {c['image'] for c in cases}=={'ordinary','25','28','43','50'}
 for path in a.carrier:
  path,r=report(path);rows=r['rows'];label,m=images[r['terminal_sha256']];assert m['diagnostic_session_rows_probe']==rows and {c['soft'] for c in r['cases']}=={0,1}
  for c in r['cases']:
   assert c['passed'] and all(c['checks'].values()) and len(c['sessions'])==2 and all(not s['errors'] for s in c['sessions']);folder=path.parent/c['case'];capture(folder,rows)
   for n,h in c['artifacts'].items():assert sha(ROOT/n)==h,n
   first=(folder/'connection-1.bin').read_bytes();second=(folder/'connection-2.bin').read_bytes();assert b'ATS' in first and b'ATS0=1\r' not in first and b'ready' in second and b'\x1b[3;6R' in second
   assert all(b'\x1b'+f'[{rows-1};9R'.encode() in data and b'\x1b[1;16R' in data and b'\x1b[?1;2c' in data for data in (first,second))
   dial=(folder/'TEST.DIR').read_bytes()[275:296].split(b'\0',1)[0];init='AT&K4' if c['soft'] else 'AT&K3';expected=[init,'ATD'+dial.decode()]*2;log=(folder/'dosbox.log').read_text();cmd=[s for s in re.findall(r'Command sent to modem: ->(.*?)<-',log) if s]
   assert cmd in (expected,expected+['ATH']) and 'Modem response: ERROR' not in log and log.count('Modem response: CONNECT')==2 and 'Modem response: NO CARRIER' in log
   starts=list(re.finditer(re.escape('Command sent to modem: ->'+init+'<-'),log));assert len(starts)==2
   for at in starts:assert 'Modem response: OK' in log[at.end():log.index('Command sent to modem: ->ATD',at.end())]
   raw=(folder/'PLSTATE.BIN').read_bytes();assert len(raw)==9798;h=struct.unpack_from('<10H',raw);assert h[0]==0x4c45 and h[3]==1 and h[9]==0 and 1<=h[2]<=8
   final=raw[20+(h[2]-1)*722:20+h[2]*722];assert struct.unpack_from('<3H',final,716)==(4,0,0)
   fon=(folder/'PCPLUS.FON').read_bytes();seed=HEADING+OLD;assert fon.startswith(seed) and len(fon)==len(seed)+162
   for i in range(2):
    rec=fon[len(seed)+i*81:len(seed)+(i+1)*81];assert rec[:46]==b'\r\n'+b'LAB NODE 001'.ljust(22)+b' '+dial.rjust(20)+b' '
    start=dt.datetime.strptime(rec[46:63].decode(),'%m/%d/%y %H:%M:%S');hh,mm,ss=map(int,rec[73:81].split(b':'));assert mm<60 and ss<60
    assert (start+dt.timedelta(hours=hh,minutes=mm,seconds=ss)).strftime('%H:%M:%S').encode()==rec[64:72]
   screen=(folder/'SCREEN.BIN').read_bytes();assert len(screen)==8000 and b'AUTO ANSWER...' not in screen[::2]
   assert (folder/'TEST.PRM').read_bytes()[0x92:0xab]==b'~ATS0=1^M\0'.ljust(25,b'\0')
   cases.append(dict(kind='carrier',rows=rows,soft=c['soft'],connections=2,passed=True))
 assert len(cases)==18 and {c['rows'] for c in cases if c['kind']=='carrier'}=={25,28,43,50}
 sources=['standalone/check_large_answer_artifacts.py','standalone/test_auto_answer_dos.py','standalone/test_large_answer_carrier_dos.py','standalone/answer_notice_watch.py','standalone/pause_watch.asm']
 r=dict(passed=True,DOS_workflows=len(cases),virtual_modem_connections=16,full_notice_frames=2*len(cases),cases=cases,reports=reports,artifacts=artifacts,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Rebuilds passive observer and independently checks raw frames, emitted data/command phases, typed order, call records and hardware. Transient/ABI/tone/fault timing remains model evidence.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS independent Auto Answer captures',len(cases),'DOS workflows')
if __name__=='__main__':main()
