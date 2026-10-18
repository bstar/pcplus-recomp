#!/usr/bin/env python3
"""Owned loopback ENiGMA native file-transfer compatibility fixture."""
import argparse,binascii,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
import enigma,synchronet
ROOT=Path(__file__).resolve().parents[2];SOURCE=enigma.SOURCE;LAB=enigma.LAB;OUT=ROOT/'build/bbs-lab/results/enigma/transfers'
AREA='pcplus_transfer';STORAGE=SOURCE/'file_base/pcplus_transfer';HELPER=LAB/'helpers/sexyz';SHA='7aa339b40482a99a6854253d9e0c336a7bec3ed55a2072f7fe5ce7a72323893b'
def upload_payload():return bytes(b^0x5a for b in payload())
def payload():return bytes(((i*73+(i>>8)*19)&255) for i in range(11521))
def setup():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()==enigma.COMMIT
 original=SOURCE/'docker/bin/sexyz-amd64';assert hashlib.sha256(original.read_bytes()).hexdigest()==SHA
 OUT.mkdir(parents=True,exist_ok=True);HELPER.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(original,HELPER);HELPER.chmod(0o755)
 loader=subprocess.check_output(['patchelf','--print-interpreter',shutil.which('node')],text=True).strip();assert loader.startswith('/nix/store/')
 subprocess.run(['patchelf','--set-interpreter',loader,'--set-rpath',str(Path(loader).parent),str(HELPER)],check=True)
 config=SOURCE/'config/config.hjson';old=config.read_bytes();backup=OUT/('config-before-'+hashlib.sha256(old).hexdigest()+'.json');backup.write_bytes(old)
 c=json.loads(old);fb=c.setdefault('fileBase',{});fb.setdefault('storageTags',{})[AREA]=str(STORAGE)
 fb.setdefault('areas',{})[AREA]={'name':'PCPlus Transfer Lab','desc':'Owned binary protocol fixtures','storageTags':[AREA],'acs':{'read':'GM[users]','write':'GM[users]','download':'GM[users]'}}
 p=c.setdefault('fileTransferProtocols',{}).setdefault('xmodemSexyz',{});p.update({'sort':0,'external':{'sendCmd':str(HELPER),'recvCmd':str(HELPER),'sendArgs':['-telnet','sX','@{fileListPath}'],'recvArgsNonBatch':['-telnet','rC','{fileName}'],'recvArgs':['-telnet','rC','PCXUP.BIN']}})
 config.write_text(json.dumps(c,indent=2)+'\n');STORAGE.mkdir(parents=True,exist_ok=True);(STORAGE/'PCXTEST.BIN').write_bytes(payload())
 subprocess.run(['node','oputil.js','fb','scan',AREA,'--no-prompt'],cwd=SOURCE,check=True)
 version=subprocess.run([str(HELPER),'v'],capture_output=True,text=True)
 metadata={'server_commit':enigma.COMMIT,'helper_original_sha256':SHA,'helper_patched_sha256':hashlib.sha256(HELPER.read_bytes()).hexdigest(),'helper_manifest':json.loads((SOURCE/'docker/sexyz/manifest.json').read_text()),'loader':loader,'config_backup':str(backup),'config_before_sha256':hashlib.sha256(old).hexdigest(),'config_after_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),'area':AREA,'storage':str(STORAGE),'file_bytes':len(payload()),'file_sha256':hashlib.sha256(payload()).hexdigest(),'helper_version':version.stdout+version.stderr}
 (OUT/'setup.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2))
def metadata(name):
 assert name in ('PCXTEST.BIN','PCXUP.BIN')
 js="""const c=require('./core/oputil/oputil_common');c.initConfigAndDatabases(e=>{if(e)throw e;const F=require('./core/file_entry');F.findByFileNameWildcard(process.argv[1],(e,entries)=>{if(e&&e.code!==-33002)throw e;if(e)entries=[];console.log(JSON.stringify(entries.map(f=>({fileId:f.fileId,fileName:f.fileName,areaTag:f.areaTag,storageTag:f.storageTag,filePath:f.filePath,fileSha256:f.fileSha256,meta:f.meta,desc:f.desc})),null,2));process.exit(0);});});"""
 raw=subprocess.check_output(['node','-e',js,name],cwd=SOURCE,text=True)
 result=json.loads(raw);OUT.mkdir(parents=True,exist_ok=True);(OUT/(name+'-metadata.json')).write_text(json.dumps(result,indent=2)+'\n');return result
def audit_upload():
 try:
  entries=metadata('PCXUP.BIN');expected=upload_payload()+b'\x1a'*127
  checks={'exactly_one_entry':len(entries)==1}
  if len(entries)==1:
   e=entries[0];path=Path(e['filePath'])
   checks.update({'owned_area':e['areaTag']==AREA and e['storageTag']==AREA,
    'owned_filename':e['fileName']=='PCXUP.BIN','owned_physical_parent':path.resolve().parent==STORAGE.resolve(),
    'metadata_size':e['meta'].get('byte_size')==len(expected),
    'metadata_sha256':e['fileSha256']==hashlib.sha256(expected).hexdigest(),
    'physical_exact_padded_bytes':path.is_file() and path.read_bytes()==expected,
    'synthetic_upload_user':e['meta'].get('upload_by_username')=='loclab'})
  result={'passed':all(checks.values()),'checks':checks,'server_commit':enigma.COMMIT,'expected_source_bytes':11521,'expected_stored_bytes':len(expected),'expected_stored_sha256':hashlib.sha256(expected).hexdigest(),'metadata':entries,'scope':'Official FileEntry API plus exact owned physical padded bytes; no direct invented SQL'}
 except Exception as error:result={'passed':False,'error':str(error)}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'upload-server-audit.json').write_text(json.dumps(result,indent=2)+'\n');return result
def audit_download(minimum_downloads=2):
 try:
  entries=metadata('PCXTEST.BIN');expected=payload();digest=hashlib.sha256(expected).hexdigest()
  checks={'exactly_one_entry':len(entries)==1}
  if len(entries)==1:
   e=entries[0];path=Path(e['filePath']);count=e['meta'].get('dl_count')
   checks.update({'owned_area':e['areaTag']==AREA and e['storageTag']==AREA,
    'owned_filename':e['fileName']=='PCXTEST.BIN','owned_physical_parent':path.resolve().parent==STORAGE.resolve(),
    'metadata_size':e['meta'].get('byte_size')==len(expected),'metadata_sha256':e['fileSha256']==digest,
    'physical_exact_source_bytes':path.is_file() and path.read_bytes()==expected,
    'download_count_incremented':isinstance(count,int) and count>=minimum_downloads})
  result={'passed':all(checks.values()),'checks':checks,'server_commit':enigma.COMMIT,
   'expected_source_bytes':len(expected),'expected_source_sha256':digest,
   'reference_download_count':1,'minimum_downloads':minimum_downloads,'metadata':entries,
   'scope':'Official FileEntry API and unchanged owned physical source; download count was 1 after the independent reference transfer. DOS destination padding is checked separately by the DOS harness.'}
 except Exception as error:result={'passed':False,'error':str(error)}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'download-server-audit.json').write_text(json.dumps(result,indent=2)+'\n');return result
def clear_owned_upload():
 entries=metadata('PCXUP.BIN')
 if not entries:return {'removed':False,'reason':'No owned reference upload'}
 expected=upload_payload()+b'\x1a'*127
 assert len(entries)==1 and entries[0]['areaTag']==AREA and entries[0]['fileSha256']==hashlib.sha256(expected).hexdigest()
 entry=entries[0];path=Path(entry['filePath']);assert path.resolve().parent==STORAGE.resolve() and path.read_bytes()==expected
 backup=OUT/('owned-upload-'+entry['fileSha256']+'.bin');backup.write_bytes(expected)
 result=subprocess.run(['node','oputil.js','fb','rm',str(entry['fileId']),'--phys-file'],cwd=SOURCE,capture_output=True,text=True,check=True)
 assert not metadata('PCXUP.BIN') and not path.exists()
 record={'removed':True,'entry':entry,'preserved_payload':str(backup),'official_cli_stdout':result.stdout}
 (OUT/'owned-upload-cleanup.json').write_text(json.dumps(record,indent=2)+'\n');return record
def reference(steps,download=False,upload=False):
 OUT.mkdir(parents=True,exist_ok=True);log=SOURCE/'logs/enigma-bbs.log';start=log.stat().st_size;synchronet.PORT=enigma.PORT
 with synchronet.Peer() as p:
  def plain(data):
   p.text.extend(data);p.history.extend(data)
   while b'\x1b[6n' in p.text[p.scan_from:]:
    i=p.text.find(b'\x1b[6n',p.scan_from);p.scan_from=i+4;p.send(b'\x1b[1;1R','CPRhome')
  p.plain=plain
  def menu():
   with log.open('rb') as f:f.seek(start);rows=[json.loads(r) for r in f if r.strip()]
   names=[r['menuName'] for r in rows if r.get('menuName')];return names[-1] if names else None
  def step(name,data=b'',delay=1):
   if data:p.send(data,name)
   p.pump(delay);print(name,menu(),repr(p.cleaned(p.text)[-500:]),flush=True)
  step('matrix',delay=3);step('login',b'\r');step('name',b'loclab\r');step('password',b'LoC-Lab-2026!\r',2)
  for i in range(20):
   m=menu()
   if m=='mainMenu':break
   step('advance'+str(i),b'\x1b' if m=='fullLoginSequenceOnelinerz' else b'N' if m=='fullLoginSequenceNewScanConfirm' else b'\r')
  assert menu()=='mainMenu',menu()
  if download:steps=['460d','4c0d','74','71','440d','61']
  if upload:steps=['460d','550d','09','09','09','0d']
  for i,s in enumerate(steps):step('step'+str(i),bytes.fromhex(s))
  if download:
   assert menu()=='fileTransferProtocolSelection'
   buffer=bytearray();received=bytearray();frames=[];eots=0;done=False
   def transfer_plain(data):buffer.extend(data);p.history.extend(data)
   p.plain=transfer_plain;p.send(b'\r','XMODEMselect');p.pump(1);p.send(b'C','CRCrequest')
   deadline=time.monotonic()+45
   while time.monotonic()<deadline and not done:
    p.pump(.05)
    while buffer:
     if buffer[0] not in (1,2,4):del buffer[0];continue
     if buffer[0]==4:
      del buffer[0];eots+=1;p.send(b'\x15' if eots==1 else b'\x06','EOTresponse');done=eots>1;break
     size=128 if buffer[0]==1 else 1024;count=size+5
     if len(buffer)<count:break
     frame=bytes(buffer[:count]);del buffer[:count];number=(len(frames)+1)&255
     assert frame[1:3]==bytes([number,255-number]),frame[:3]
     data=frame[3:-2];assert frame[-2:]==binascii.crc_hqx(data,0).to_bytes(2,'big')
     frames.append({'size':size,'number':number,'sha256':hashlib.sha256(frame).hexdigest()});received.extend(data);p.send(b'\x06','blockACK')
   assert done,'DownloadEOTtimeout'
   expected=payload();assert received[:len(expected)]==expected and all(b==26 for b in received[len(expected):])
   p.plain=plain;p.pump(2);step('return',b'\r',1)
   result={'passed':True,'direction':'download','server_commit':enigma.COMMIT,'payload_bytes':len(expected),'wire_payload_bytes':len(received),'padding_bytes':len(received)-len(expected),'frames':frames,'eots':eots,'return_menu':menu(),'payload_sha256':hashlib.sha256(expected).hexdigest()}
   (OUT/'download-reference.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'download-payload.bin').write_bytes(received)

  if upload:
   assert menu()=='fileTransferProtocolSelection',menu()
   buffer=bytearray();wireframes=[];source=upload_payload();(OUT/'SEND.BIN').write_bytes(source)
   def transfer_plain(data):buffer.extend(data);p.history.extend(data)
   def wait_control(choices,timeout=15):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
     p.pump(.05)
     while buffer:
      value=buffer.pop(0)
      if value in choices:return value
    raise TimeoutError(('No protocol control',choices,bytes(buffer)))
   p.plain=transfer_plain;p.send(b'\r','XMODEMselect');assert wait_control([67])==67
   offset=0;number=1
   while offset<len(source):
    size=1024 if len(source)-offset>=897 else 128
    body=source[offset:offset+size];body+=b'\x1a'*(size-len(body))
    frame=bytes([2 if size==1024 else 1,number,255-number])+body+binascii.crc_hqx(body,0).to_bytes(2,'big')
    p.send(frame.replace(b'\xff',b'\xff\xff'),'XMODEMframe')
    assert wait_control([6,21,24])==6,('Upload block rejected',number)
    wireframes.append({'size':size,'number':number,'sha256':hashlib.sha256(frame).hexdigest()});offset+=size;number=(number+1)&255
   p.send(b'\x04','EOT');reply=wait_control([6,21,24])
   if reply==21:p.send(b'\x04','EOTrepeat');reply=wait_control([6,24])
   assert reply==6
   p.plain=plain;step('after-upload',delay=3)
   for i in range(3):step('details-tab'+str(i),b'\t',.7)
   step('details-submit',b'\r',3)
   step('achievement-return',b'\r',1);step('file-list-return',b'L\r',1)
   assert menu()=='fileBaseListEntries',menu()
   expected=source+b'\x1a'*(offset-len(source));entries=metadata('PCXUP.BIN')
   assert len(entries)==1 and entries[0]['areaTag']==AREA and entries[0]['meta']['byte_size']==len(expected),entries
   assert Path(entries[0]['filePath']).read_bytes()==expected
   assert entries[0]['fileSha256']==hashlib.sha256(expected).hexdigest()
   result={'passed':True,'direction':'upload','server_commit':enigma.COMMIT,'source_bytes':len(source),'installed_bytes':len(expected),'padding_bytes':len(expected)-len(source),'source_sha256':hashlib.sha256(source).hexdigest(),'installed_sha256':hashlib.sha256(expected).hexdigest(),'frames':wireframes,'metadata':entries,'return_menu':menu()}
   (OUT/'upload-reference.json').write_text(json.dumps(result,indent=2)+'\n')
   (OUT/'upload-server-wire.bin').write_bytes(p.rx);(OUT/'upload-client-wire.bin').write_bytes(p.tx);(OUT/'upload-transcript.txt').write_text(p.cleaned(p.history))
  (OUT/'reference-server.bin').write_bytes(p.rx);(OUT/'reference-client.bin').write_bytes(p.tx);(OUT/'reference.txt').write_text(p.cleaned(p.history))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['setup','reference','metadata','clear-owned-upload','audit-upload','audit-download']);parser.add_argument('--step',action='append',default=[]);parser.add_argument('--download',action='store_true');parser.add_argument('--upload',action='store_true');parser.add_argument('--minimum-downloads',type=int,default=2);a=parser.parse_args()
 if a.action=='setup':setup()
 elif a.action=='audit-download':
  if a.minimum_downloads<2:parser.error('--minimum-downloads must be at least 2 (reference count was 1)')
  result=audit_download(a.minimum_downloads);print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
 elif a.action=='audit-upload':
  result=audit_upload();print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
 elif a.action=='clear-owned-upload':print(json.dumps(clear_owned_upload(),indent=2))
 elif a.action=='metadata':print(json.dumps({n:metadata(n) for n in ['PCXTEST.BIN','PCXUP.BIN']},indent=2))
 else:reference(a.step,a.download,a.upload)
if __name__=='__main__':raise SystemExit(main())
