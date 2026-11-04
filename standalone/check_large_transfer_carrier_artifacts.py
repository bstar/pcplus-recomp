#!/usr/bin/env python3
"""Independent immutable DOS carrier/transfer/BIOS/file/log capture checks."""
import argparse,datetime as dt,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
NAMES={'receive-negotiation','receive-partial','upload-unacked','upload-partial'}|{f'{p}-{k}' for p in ['ymodem','zmodem'] for k in ['receive-metadata','receive-partial','receive-retained','upload-metadata','upload-partial']}|{f'{p}-fragment-{m}' for p in ['ymodem','zmodem'] for m in ['legacy','strict']}
HEADING=b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
OLD=b'\r\n'+b'PREVIOUS CALL'.ljust(22)+b' '+b'5550100'.rjust(20)+b' 01/02/95 03:04:05 03:05:06 00:01:01'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[];reports=[]
 for run in a.run:
  run=run.resolve();assert run.is_relative_to(ROOT/'build');report=json.loads((run/'result.json').read_text());assert report['passed'] and {c['case'] for c in report['cases']}==NAMES
  rows=report['physical_rows'];assert rows in (25,28,43,50)
  for n,h in report['sources'].items():assert sha(ROOT/n)==h,n
  parent=ROOT/report['terminal_path'];assert sha(parent)==report['terminal_sha256'];manifest=json.loads((parent.parent/'manifest.json').read_text())
  assert sha(parent.parent/'manifest.json')==report['manifest_sha256'] and manifest['diagnostic_session_rows_probe']==rows
  for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
  for c in report['cases']:
   name=c['case'];folder=run/name;assert c['passed'] and all(c['checks'].values())
   for n,h in c['artifacts'].items():assert sha(ROOT/n)==h,n
   protocol=1 if name.startswith('ymodem') else 2 if name.startswith('zmodem') else 0
   upload=name.startswith('upload') or '-upload-' in name or '-fragment-' in name
   partial=name.endswith(('partial','retained'));retained=name.endswith('retained');fragment='-fragment-' in name
   assert len(c['sessions'])==2 and all(not s['errors'] for s in c['sessions'])
   e=[x['kind'] for x in c['sessions'][0]['events']];assert e.count('carrier-drop')==1 and e[-1]=='closed'
   first=(folder/'connection-1.bin').read_bytes();second=(folder/'connection-2.bin').read_bytes()
   reply=b'\x1b'+f'[{rows-1};9R'.encode()
   assert all(b'\x1b[1;16R' in w and b'\x1b[?1;2c' in w and reply in w for w in [first,second])
   assert b'\x1b[2;10R' in second and b'ready' in second and b'\x1b[3;6R' in second
   cfg=(folder/'dosbox.conf').read_text();assert 'cputype=8086' in cfg and 'serial3=modem irq:5 listenport:0' in cfg
   assert (folder/'PASS.TXT').is_file() and not (folder/'FAIL.TXT').exists()
   assert len((folder/'BEFORE.BIN').read_bytes())==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
   assert len((folder/'SCREEN.BIN').read_bytes())==8000
   dial=(folder/'TEST.DIR').read_bytes()[275:296].split(b'\0',1)[0]
   log=(folder/'dosbox.log').read_text();cmd=re.findall(r'Command sent to modem: ->(.*?)<-',log);cmd=[x for x in cmd if x]
   wanted=['AT&K3','ATD'+dial.decode()]*2
   retired=name.startswith('zmodem-fragment-') and 'IN' in cmd
   if retired:wanted.insert(2,'IN')
   assert cmd in (wanted,wanted+['ATH']) and log.count('Modem response: CONNECT')==2
   initializations=list(re.finditer(re.escape('Command sent to modem: ->AT&K3<-'),log));errors=list(re.finditer('Modem response: ERROR',log));assert len(initializations)==2
   for at in initializations:
    response=log[at.end():log.index('Command sent to modem: ->ATD',at.end())];assert 'Modem response: OK' in response and 'Modem response: ERROR' not in response
   if retired:assert len(errors)==1 and log.index('Modem response: NO CARRIER')<errors[0].start()<initializations[1].start()
   else:assert not errors
   assert 'Modem response: NO CARRIER' in log
   raw=(folder/'PLSTATE.BIN').read_bytes();assert len(raw)==(9922 if protocol else 9862)
   h=struct.unpack_from('<10H',raw);assert h[0]==0x4c45 and h[3]==1 and h[9]==0 and 1<=h[2]<=8
   watch=struct.unpack_from('<32H',raw,9798);assert watch[0]>0 and watch[2:8]==(4,0,0,int(upload),0,0)
   down=watch[8:18];up=watch[18:32];assert down[5:8]==(0,0,0) and up[4:8]==(0,0,0,0)
   if upload:
    assert up[0]==6 and (folder/'SEND.BIN').read_bytes()==bytes(range(256))*16
   else:
    assert down[0]==4 and (down[8]|down[9]<<16)==(9216 if protocol and partial else 10240 if partial else 0)
   if protocol:
    b=struct.unpack_from('<30H',raw,9862);assert b[0]==protocol and b[15 if upload else 1]==4
    if not upload:assert b[13]|b[14]<<16==int(retained)
    expected={'FIRST.BIN':b'FIRST COMPLETE FILE\r\n'} if retained else {}
    assert {p.name:p.read_bytes() for p in (folder/'RECV').iterdir()}==expected
   else:assert not (folder/'RECV.BIN').exists()
   assert not any(p.name.upper().startswith(('PCRX.','PCZRX.','PCYM.')) for p in folder.rglob('*'))
   if fragment:
    prefix=c['sessions'][0]['batch']['metadata_prefix'];assert prefix['bytes']==16 and len(bytes.fromhex(prefix['hex']))==16 and not prefix['complete']
    assert not c['sessions'][0]['batch']['metadata']
   elif upload and partial:
    assert ('batch-upload-ACK-1' if protocol else 'upload-ACK-1') in e and ('batch-upload-frame-2' if protocol else 'upload-frame-2') in e
   elif not upload and partial:
    assert ('batch-download-ACK-9' if protocol else 'download-ACK-11') in e
   bios=(folder/'TRWATCH.BIN').read_bytes();assert len(bios)==1988 and struct.unpack_from('<6H',bios)==(0x5254,1,1,1,1,0)
   old=bios[12:346];new=bios[680:1014];overlay=bios[1348:1668];assert old==new and overlay[1::2]==bytes([31])*160
   r,font,cursor,shape,mode,cols,page=struct.unpack_from('<7H',old,320)
   assert (r,font,mode,cols,page)==(rows,14 if rows==28 else 8 if rows in (43,50) else 16,3,80,0)
   assert [b'XMODEM',b'YMODEM',b'ZMODEM'][protocol] in overlay[:160:2]
   data=(folder/'PCPLUS.FON').read_bytes();seed=HEADING+OLD;assert data.startswith(seed) and len(data)==len(seed)+162
   for i in range(2):
    record=data[len(seed)+i*81:len(seed)+(i+1)*81];assert record[:46]==b'\r\n'+b'LAB NODE 001'.ljust(22)+b' '+dial.rjust(20)+b' '
    start=dt.datetime.strptime(record[46:63].decode(),'%m/%d/%y %H:%M:%S');hh,mm,ss=map(int,record[73:81].split(b':'));assert mm<60 and ss<60
    finish=start+dt.timedelta(hours=hh,minutes=mm,seconds=ss);assert finish.strftime('%H:%M:%S').encode()==record[64:72]
   final=raw[20+(h[2]-1)*722:20+h[2]*722];assert struct.unpack_from('<3H',final,716)==(4,0,0)
   cases.append(dict(rows=rows,case=name,protocol=protocol,upload=upload,carrier_fault=4,closed_file_owners=True,retained_file=retained,metadata_fragment=fragment,connections=2,exact_BIOS_row_return=True,logged_call_pairs=2,result_sha256=sha(folder/'checks.json'),storage_capture_sha256=sha(folder/'PLSTATE.BIN'),BIOS_capture_sha256=sha(folder/'TRWATCH.BIN')))
  reports.append(dict(path=str((run/'result.json').relative_to(ROOT)),sha256=sha(run/'result.json')))
 result=dict(passed=True,cases=cases,actual_DOS_workflows=len(cases),virtual_modem_connections=2*len(cases),BIOS_UI_leases=len(cases),reports=reports,checker_sha256=sha(Path(__file__)),scope=__doc__+' Raw owner/BIOS snapshots, exact file trees/source vectors, call pairs and clean modem commands. Independent primary peers validate frame CRC/data and staged prefixes before deletion. Virtual modem/socket lifecycle only; no physical/SIP/BBS/full-parity acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS independent transfer carrier captures',len(cases),'DOS workflows')
if __name__=='__main__':main()
