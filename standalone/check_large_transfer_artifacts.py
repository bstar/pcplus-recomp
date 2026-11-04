#!/usr/bin/env python3
"""Independently verify actual DOS transfer row captures and known file vectors."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
NAMES={'x-rx-binary','x-rx-badCRC-retry','x-rx-local-Escape','x-tx-binary','x-tx-NAK-retry','x-tx-peer-CAN','y-rx-binary','y-tx-binary','y-rx-local-Escape','y-rx-cancel-retry','y-rx-retained-first','y-tx-NAK-retry','z-rx-default','z-rx-crc16','z-tx-default','z-tx-escape'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 binary=bytes(range(256))*4+b'\x00\x1a\xff\x11\x13';batch={'EMPTY.BIN':b'','ODD.BIN':b'A','ALL.BIN':binary};records=[];reports=[]
 for run in a.run:
  run=run.resolve();assert run.is_relative_to(ROOT/'build');report=json.loads((run/'result.json').read_text());assert report['passed'] and {c['case'] for c in report['cases']}==NAMES
  rows=report['physical_rows'];assert rows in (25,28,43,50)
  for n,h in report['sources'].items():assert sha(ROOT/n)==h,n
  for c in report['cases']:
   name=c['case'];folder=run/name;assert c['passed'] and all(c['checks'].values())
   for n,h in c['captures'].items():assert sha(folder/n)==h,n
   config=(folder/'dosbox.conf').read_text();parent=Path(re.search(r'^mount c "([^"]+)"$',config,re.M)[1])/'TERMINAL.EXE';assert parent.is_relative_to(ROOT/'build')
   assert sha(parent)==report['terminal_sha256']==c['terminal_sha256']
   manifest=json.loads((parent.parent/'manifest.json').read_text());assert sha(parent.parent/'manifest.json')==report['manifest_sha256'] and manifest['diagnostic_session_rows_probe']==rows
   for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
   assert 'cputype=8086' in config and 'transparent:1 irq:5' in config
   assert len((folder/'BEFORE.BIN').read_bytes())==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
   assert len((folder/'SCREEN.BIN').read_bytes())==8000 and (folder/'SCREEN.BIN').read_bytes()[:28:2]==b'AFTER TRANSFER'
   wire=(folder/'serial.bin').read_bytes();assert b'\x1b[0n' in wire and b'ready' in wire and b'\x1b'+f'[{rows-1};9R'.encode() in wire
   raw=(folder/'TRWATCH.BIN').read_bytes();assert len(raw)==1988
   magic,version,before,after,s1,s2=struct.unpack_from('<6H',raw);count=2 if name=='y-rx-cancel-retry' else 1
   assert (magic,version,before,after)==(0x5254,1,count,count) and [s1,s2][:count]==[1]*count
   for i in range(count):
    old=raw[12+i*334:12+(i+1)*334];restored=raw[680+i*334:680+(i+1)*334];overlay=raw[1348+i*320:1348+(i+1)*320]
    assert old==restored
    r,font,cursor,shape,mode,columns,page=struct.unpack_from('<7H',old,320)
    assert (r,font,mode,columns,page)==(rows,14 if rows==28 else 8 if rows in (43,50) else 16,3,80,0)
    assert cursor>>8<rows and cursor&255<80
    assert overlay[1::2]==bytes([31])*160 and {'x':b'XMODEM','y':b'YMODEM','z':b'ZMODEM'}[name[0]] in overlay[:160:2]
   incoming='-rx-' in name;expected={}
   if incoming:
    if name=='x-rx-binary':expected={'ONE.BIN':bytes(range(128))+bytes(range(256))*4+bytes(range(128,256))}
    elif name=='x-rx-badCRC-retry':expected={'ONE.BIN':bytes(range(128))}
    elif name in ('y-rx-binary','y-rx-cancel-retry','z-rx-default','z-rx-crc16'):expected=batch
    elif name=='y-rx-retained-first':expected={'ALL.BIN':binary}
    assert {p.name:p.read_bytes() for p in (folder/'RECV').iterdir()}==expected,(rows,name,'known receive vectors')
   else:
    expected={'ONE.BIN':binary} if name.startswith('x-') else {'ALL.BIN':binary} if name=='y-tx-NAK-retry' else batch
    assert {p.name:p.read_bytes() for p in (folder/'SEND').iterdir()}==expected,(rows,name,'known source vectors')
    if name.startswith('z-'):assert {p.name:p.read_bytes() for p in (folder/'PEER').iterdir()}==batch
   assert not any(p.name.upper().startswith(('PCRX.','PCZRX.','PCYM.')) for p in folder.rglob('*'))
   records.append(dict(rows=rows,case=name,leases=count,exact_underlay_and_BIOS_metadata=True,known_binary_files=True,result_sha256=sha(folder/'result.json'),raw_capture_sha256=sha(folder/'TRWATCH.BIN')))
  reports.append(dict(path=str((run/'result.json').relative_to(ROOT)),sha256=sha(run/'result.json')))
 result=dict(passed=True,cases=records,actual_DOS_workflows=len(records),actual_UI_leases=sum(c['leases'] for c in records),reports=reports,checker_sha256=sha(Path(__file__)),scope=__doc__+' Independently checks immutable BIOS two-row/cursor/shape/height captures, overlay placement, known binary files, scratch cleanup and hardware snapshots. Existing independent peers/lrzsz own protocol validation. No modem DCD, SIP, BBS or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS independent transfer captures',len(records),'DOS workflows')
if __name__=='__main__':main()
