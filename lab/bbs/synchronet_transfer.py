#!/usr/bin/env python3
"""Real owned Synchronet/sexyz transfer lab, loopback only; no server patches."""
import argparse,binascii,hashlib,json,os,re,socket,struct,subprocess,time
from pathlib import Path
from synchronet import Peer,LAB,RUNTIME,COMMIT,ENV
ROOT=Path(__file__).resolve().parents[2];OUT=LAB/'transfers';CODE='pcplab';AREA=RUNTIME/'data/dirs/pcplab'
PAYLOAD=bytes((i*37+13)%256 for i in range(11521))
assert all(bytes([x]) in PAYLOAD for x in (0,0x1a,0xff,0x11,0x13))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def js(program,label,quiet=False):
 OUT.mkdir(parents=True,exist_ok=True);path=OUT/(label+'.js');path.write_text(program)
 result=subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(path)],env=ENV(),capture_output=True,text=True,check=True)
 (OUT/(label+'.stdout')).write_text(result.stdout);(OUT/(label+'.stderr')).write_text(result.stderr)
 if not quiet:print(result.stdout,flush=True)
 return result.stdout

def setup():
 OUT.mkdir(parents=True,exist_ok=True);config=RUNTIME/'ctrl/file.ini';before=config.read_bytes();marker=b'[dir:Main:PCPLAB]'
 if marker not in before:
  backup=OUT/'file.ini.before';assert not backup.exists(),'Unreviewed existing backup'
  backup.write_bytes(before)
  settings=1|8|16|32|1024|4096|8192|262144|524288
  extra=f'''\n[dir:Main:PCPLAB]\n description=PCPlus Transfer Lab\n name=PCPlus Lab\n ars=LEVEL 50\n upload_ars=LEVEL 50\n download_ars=LEVEL 50\n operator_ars=SYSOP\n exempt_ars=\n area_tag=\n path=pcplab/\n vdir=\n vshortcut=\n data_dir=\n upload_sem=\n extensions=BIN\n settings={hex(settings)}\n seq_dev=0\n sort=0\n max_age=0\n max_files=100\n upload_credit_pct=0\n download_credit_pct=0\n'''.encode()
  config.write_bytes(before+extra)
  assert config.read_bytes()[:len(before)]==before
 AREA.mkdir(parents=True,exist_ok=True);payload=AREA/'PCXTEST.BIN'
 if payload.exists():assert payload.read_bytes()==PAYLOAD
 else:payload.write_bytes(PAYLOAD)
 js("var f=new FileBase('pcplab'); if(!f.open()) throw Error(f.last_error);\nif(!f.get('PCXTEST.BIN')) {if(!f.add({name:'PCXTEST.BIN',desc:'Synthetic PCPlus binary transfer fixture',from:'Lab Sysop',cost:0},false)) throw Error(f.last_error);}\nprint(JSON.stringify({dir:file_area.dir.pcplab,file:f.get('PCXTEST.BIN')},null,2)); f.close();\n",'seed-filebase')
 # Official terminal server semaphore; parent verified no active lab sessions.
 owners=[]
 for process in Path('/proc').iterdir():
  if not process.name.isdigit():continue
  try:command=(process/'cmdline').read_bytes()
  except OSError:continue
  if command.split(b'\x00',1)[0]==str(RUNTIME/'exec/sbbs').encode():owners.append(process)
 assert len(owners)==1,'Expected one owned Synchronet process'
 assert '127.0.0.1:23231' in subprocess.check_output(['ss','-lntp'],text=True), 'Loopback listener missing'
 (RUNTIME/'ctrl/recycle').touch();time.sleep(3)
 record={'server_commit':COMMIT,'endpoint':['127.0.0.1',23231],'file_ini_before_sha256':digest(OUT/'file.ini.before'),'file_ini_after_sha256':digest(config),'appended_directory':CODE,'existing_configuration_prefix_unchanged':config.read_bytes().startswith((OUT/'file.ini.before').read_bytes()),'payload':{'path':str(payload),'bytes':len(PAYLOAD),'sha256':digest(payload)},'helpers':{n:{'path':str(RUNTIME/'exec'/n),'sha256':digest(RUNTIME/'exec'/n)} for n in ['sexyz','jsexec','sbbs']},'official_api_source':'src/sbbs3/js_filebase.cpp FileBase.add/get; exec/addfiles.js','flags_source':'exec/load/sbbsdefs.js DIR_FCHK|DIR_DUPES|DIR_FREE|DIR_TFREE|DIR_ULDATE|DIR_NOSCAN|DIR_NOAUTO|DIR_QUIET|DIR_NOSTAT','recycle_source':'src/sbbs3/main.cpp semfile_list_init(ctrl_dir,recycle,server_abbrev)','limitations':['Dedicated synthetic local file area only; original message/file menu defaults and users retained.','Stock XMODEM has no exact original-length field; payload padding is recorded separately.']}
 (OUT/'setup.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
def login(p,out):
 steps=[]
 def step(label,data=b'',needle=None,delay=.8):
  p.text.clear();p.scan_from=0
  if data:p.send(data,label)
  if needle:p.wait(needle,25)
  else:p.pump(delay)
  out.mkdir(parents=True,exist_ok=True);(out/(label+'.txt')).write_text(p.clean);(out/(label+'.bin')).write_bytes(p.text)
  steps.append({'step':label,'sent':data.hex(),'received':len(p.text)});print(label,repr(p.clean[-1500:]),flush=True)
  return p.clean
 p.wait('Login:');step('login',b'LABUSER\r','Password:');step('password',b'LABPASS42\r','[Hit a key]');step('welcome',b' ','Enter number of bulletin or [Quit]');step('bulletins',b'Q','Search all groups for new messages?');step('scan',b'n\r','[Hit a key]');step('main',b' ','Read/Post Messages');return step,steps

def explore():
 out=OUT/'explore'
 with Peer() as p:
  try:
   step,steps=login(p,out);step('files',b'T',delay=1);step('join',b'J',delay=1);step('area',b'11\r',delay=1);step('download',b'D',delay=1);step('filename',b'PCXTEST.BIN\r',delay=1);step('protocol',b'1',delay=2)
  finally:
   out.mkdir(parents=True,exist_ok=True);(out/'transcript.txt').write_text(p.cleaned(p.history));(out/'server-wire.bin').write_bytes(p.rx);(out/'client-wire.bin').write_bytes(p.tx)
class BinaryPeer(Peer):
 binary=False
 def plain(self,data):
  if self.binary:self.text.extend(data);self.history.extend(data)
  else:super().plain(data)
 def octets(self,data):self.send(data.replace(b'\xff',b'\xff\xff'),'protocol')
 def take(self,n,timeout=30):
  end=time.monotonic()+timeout
  while len(self.text)<n and time.monotonic()<end:
   if not self.pump(.05):break
  if len(self.text)<n:raise TimeoutError(f'Need {n} bytes, have {len(self.text)}: {bytes(self.text[:200])!r}')
  result=bytes(self.text[:n]);del self.text[:n];return result

def reference(protocol='1',upload=False,name=None):
 out=OUT/('reference-'+('upload' if upload else 'download')+'-'+protocol+('-'+name if name else ''));out.mkdir(parents=True,exist_ok=True);result={'passed':False,'protocol':protocol}
 with BinaryPeer() as p:
  try:
   step,steps=login(p,out);step('files',b'T',delay=.6);step('join',b'J','Which, Quit');step('area',b'11\r',delay=.7)
   if upload:
    payload=PAYLOAD[:-1]+bytes([ord(protocol)]);(out/'source.bin').write_bytes(payload)
    name=name or 'PCXUP'+protocol+'.BIN';assert re.fullmatch(r'PCXUP[A-Z0-9]{1,2}\.BIN',name);assert not (AREA/name).exists(),'Owned upload already exists; retain evidence, choose a new label'
    step('upload',b'U','Filename:');step('upload-name',name.encode()+b'\r','[Yes] No');step('upload-confirm',b'y','Enter a description now.');step('description',b'Synthetic local transfer fixture\r','Protocol, Batch or Quit:');step('upload-protocol',protocol.encode(),'Hang up after transfer?')
    p.binary=True;p.text.clear();p.octets(b'n');handshake=bytearray()
    while True:
     lead=p.take(1)[0];handshake.append(lead)
     if lead==21:break
     if lead==67:
      p.pump(.1)
      if not p.text or set(p.text)=={67}:break
    crc=lead==67;frames=[];offset=0;seq=1
    while offset<len(payload):
     size=1024 if protocol=='1' and len(payload)-offset>=1024 else 128
     block=payload[offset:offset+size].ljust(size,b'\x1a');packet=bytes([2 if size==1024 else 1,seq%256,255-seq%256])+block
     packet+=(binascii.crc_hqx(block,0).to_bytes(2,'big') if crc else bytes([sum(block)&255]));p.octets(packet);answer=p.take(1)[0];assert answer==6,(offset,answer)
     frames.append({'sequence':seq%256,'bytes':size});seq+=1;offset+=size
    p.octets(b'\x04');eot_answer=p.take(1);eots=1
    if eot_answer==b'\x15':p.octets(b'\x04');eot_answer=p.take(1);eots+=1
    assert eot_answer==b'\x06',eot_answer
    p.binary=False;p.wait('[Hit a key]',20);(out/'completion.txt').write_text(p.clean);p.send(b' ','transfer pause');p.text.clear();p.wait('■ File ■',15);(out/'post-transfer.txt').write_text(p.clean)
    installed=(AREA/name).read_bytes();assert installed[:len(payload)]==payload;assert len(installed)==offset;assert set(installed[len(payload):])<={26}
    meta=js("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);var x=f.get('"+name+"');if(!x)throw Error('missing metadata');print(JSON.stringify(x,null,2));f.close();",'metadata-'+name)
    result={'passed':True,'direction':'upload','protocol':protocol,'frames':frames,'crc':crc,'payload_bytes':len(payload),'installed_bytes':len(installed),'padding_bytes':len(installed)-len(payload),'installed_sha256':digest(AREA/name),'metadata_verified':True,'eots':eots,'returned_file_prompt':'■ File ■' in p.clean,'handshake_hex':handshake.hex(),'scope':'Actual unmodified Synchronet/sexyz receives independently framed binary payload and adds FileBase metadata; local synthetic reference peer, not DOS proof.'};return
   step('download',b'D','Filespec');step('filename',b'PCXTEST.BIN\r','Protocol, Batch');step('protocol',protocol.encode(),'Hang up after transfer?')
   p.binary=True;p.text.clear();p.octets(b'n');p.pump(.5)
   # Stock helper output before SOH/STX is status text; handshake starts peer.
   p.text.clear();p.octets(b'C' if protocol=='1' else b'\x15');data=bytearray();frames=[];expected=1;discard=bytearray()
   while True:
    leader=p.take(1)[0]
    if leader==4:p.octets(b'\x06');break
    if leader not in (1,2):discard.append(leader);continue
    size=128 if leader==1 else 1024;frame=p.take(2+size+(2 if protocol=='1' else 1));seq,comp=frame[:2];block=frame[2:2+size];check=frame[2+size:]
    assert seq==expected%256 and comp==255-seq,(seq,expected)
    assert check==(binascii.crc_hqx(block,0).to_bytes(2,'big') if protocol=='1' else bytes([sum(block)&255]))
    frames.append({'sequence':seq,'bytes':size});data.extend(block);expected+=1;p.octets(b'\x06')
   (out/'received.bin').write_bytes(data);assert data[:len(PAYLOAD)]==PAYLOAD;assert set(data[len(PAYLOAD):])<={0x1a}
   p.binary=False;p.wait('[Hit a key]',15);p.send(b' ','transfer pause');p.text.clear();p.wait('■ File ■',15);p.pump(.3);(out/'post-transfer.txt').write_text(p.clean)
   result={'passed':True,'protocol':protocol,'frames':frames,'payload_bytes':len(PAYLOAD),'received_bytes':len(data),'padding_bytes':len(data)-len(PAYLOAD),'padding_value':26,'sha256_payload':hashlib.sha256(data[:len(PAYLOAD)]).hexdigest(),'returned_file_prompt':'■ File ■' in p.clean,'preframe_status':discard.decode('cp437',errors='replace'),'scope':'Actual stock Synchronet/sexyz over loopback Telnet; independently verified frames and payload, reference peer rather than DOS.'}
  finally:
   (out/'server-wire.bin').write_bytes(p.rx);(out/'client-wire.bin').write_bytes(p.tx);(out/'transcript.txt').write_text(p.cleaned(p.history));(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

def audit(name,expected=None):
 assert re.fullmatch(r'[A-Z0-9_]{1,8}\.BIN',name),'Synthetic BIN basename required'
 raw=js("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);print('PCPLAB_JSON:'+JSON.stringify(f.get('"+name+"')));f.close();",'audit-'+name,quiet=True)
 metadata=json.loads(raw.split('PCPLAB_JSON:',1)[1].splitlines()[0]);path=AREA/name
 data=path.read_bytes();assert metadata and metadata['name'].upper()==name and metadata['size']==len(data)
 assert metadata['crc16']==binascii.crc_hqx(data,0)
 assert metadata['sha1']==hashlib.sha1(data).hexdigest() and metadata['md5']==hashlib.md5(data).hexdigest() and metadata['crc32']==binascii.crc32(data)&0xffffffff
 source=Path(expected).read_bytes() if expected else (PAYLOAD if name=='PCXTEST.BIN' else None)
 if source is not None:
  assert data[:len(source)]==source and set(data[len(source):])<={26}
  assert len(data) in {len(source),((len(source)+127)//128)*128,((len(source)+1023)//1024)*1024}
 result={'passed':True,'metadata_matches_physical_bytes':True,'expected_payload_verified':source is not None,'padding_bytes':len(data)-len(source) if source is not None else None,'server_commit':COMMIT,'directory_code':CODE,'name':name,'exists':path.exists(),'bytes':path.stat().st_size if path.exists() else None,'sha256':digest(path) if path.exists() else None,'metadata':metadata}
 (OUT/('audit-'+name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['setup','explore','reference','audit']);p.add_argument('--protocol',choices=['X','1'],default='1');p.add_argument('--upload',action='store_true');p.add_argument('--name');p.add_argument('--expected',help='Synthetic source file; verify exact prefix and only protocol SUB padding up to one128/1024byte frame');a=p.parse_args()
 if a.action=='reference':reference(a.protocol,a.upload,a.name)
 elif a.action=='audit':audit(a.name or 'PCXTEST.BIN',a.expected)
 else:globals()[a.action]()
