#!/usr/bin/env python3
"""Pinned, loopback-only Mystic vendor lab and wire-recording reference client."""
from __future__ import annotations
import argparse,hashlib,json,os,re,select,socket,struct,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'build/bbs-lab/mystic'
SYSTEM=BASE/'system'
URL='https://mysticbbs.com/downloads/mys112a48_l64.rar'
SHA256='fb427b57d9627ef93008c561df807991bdd288b4a1fc1757dfb5bb5434f286a3'
HOST='127.0.0.1';PORT=23232

def setup():
 BASE.mkdir(parents=True,exist_ok=True)
 archive=BASE/'mys112a48_l64.rar'
 if not archive.exists():
  req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'en-US,en;q=0.9','Referer':'https://www.mysticbbs.com/'})
  with urllib.request.urlopen(req,timeout=30) as response:archive.write_bytes(response.read())
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==SHA256,'Vendor archive hash mismatch'
 vendor=BASE/'vendor';vendor.mkdir(exist_ok=True)
 if not (vendor/'install').exists():subprocess.run(['bsdtar','-xf',str(archive),'-C',str(vendor)],check=True)
 (vendor/'install').chmod(0o700)
 if not (SYSTEM/'mystic.dat').exists():subprocess.run([str(vendor/'install'),'auto',str(SYSTEM)],cwd=vendor,check=True)
 configure()
 meta={'version':'Mystic 1.12 A48 Linux64','source':URL,'archive_sha256':SHA256,'endpoint':f'{HOST}:{PORT}','vendor_release':'2023-01-15','server_configuration':'Only first TELNET record active, IPV4 only,127.0.0.1:23232; other seven inactive','runtime_root_alias':str(Path('/tmp')/f'pcplus-mystic-lab-{os.getuid()}'),'runtime':'native vendor ELF, no Docker or system services'}
 (BASE/'installation.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))

def short_paths():
 alias=Path('/tmp')/f'pcplus-mystic-lab-{os.getuid()}'
 if alias.is_symlink():
  assert alias.resolve()==SYSTEM.resolve(),'Unexpected existing lab alias'
 elif alias.exists():raise RuntimeError('Refusing to replace existing lab alias')
 else:alias.symlink_to(SYSTEM)
 path=SYSTEM/'mystic.dat';data=bytearray(path.read_bytes())
 old=(str(SYSTEM)+'/').encode();new=(str(alias)+'/').encode();position=0;changed=0
 while (at:=data.find(old,position))!=-1:
  length=data[at-1];value=bytes(data[at:at+length]);assert value.startswith(old)
  replacement=new+value[len(old):];assert len(replacement)<=length
  data[at-1]=len(replacement);data[at:at+length]=replacement+bytes(length-len(replacement))
  position=at+length;changed+=1
 if changed:path.write_bytes(data)
 return str(alias)

def configure():
 short_paths()
 # Offsets corroborated by performing these exact edits in vendor mystic -cfg.
 # This is deliberately pinned to A48's eight384-byte record layout.
 path=SYSTEM/'data/servers.dat';data=bytearray(path.read_bytes())
 assert len(data)==8*384 and data[66:73]==b'\x06TELNET','Unexpected A48 server record format'
 for index in range(8):data[index*384]=int(index==0)
 data[1:21]=bytes([len(HOST)])+HOST.encode()+bytes(19-len(HOST))
 data[61]=0 # Vendor UI adapter type IPV4, rather than dual-stack.
 struct.pack_into('<H',data,75,PORT)
 path.write_bytes(data)
 allow=SYSTEM/'data/allowlist.txt';text=allow.read_text()
 if HOST not in text.splitlines():allow.write_text(text.rstrip()+'\n'+HOST+'\n')
 assert data[1:11]==b'\x09127.0.0.1' and data[61]==0 and struct.unpack_from('<H',data,75)[0]==PORT
 assert [data[i*384] for i in range(8)]==[1,0,0,0,0,0,0,0]

def start():
 pidfile=BASE/'server.pid'
 if pidfile.exists():
  pid=int(pidfile.read_text())
  try:
   if (Path('/proc')/str(pid)/'exe').resolve(strict=True)==(SYSTEM/'mis').resolve():
    print(json.dumps({'pid':pid,'endpoint':f'{HOST}:{PORT}','already_running':True}));return
  except FileNotFoundError:pass
 configure()
 logfile=BASE/'server-console.log'
 with logfile.open('ab') as log:
  proc=subprocess.Popen([str(SYSTEM/'mis'),'server'],cwd=SYSTEM,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
 (BASE/'server.pid').write_text(str(proc.pid)+'\n')
 time.sleep(.5)
 if proc.poll() is not None:raise RuntimeError('MIS exited; inspect server-console.log')
 print(json.dumps({'pid':proc.pid,'endpoint':f'{HOST}:{PORT}','log':str(logfile)}))

def stop():
 subprocess.run([str(SYSTEM/'mis'),'shutdown'],cwd=SYSTEM,check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

class Reference:
 """Reference socket client; responses model80x25 detection, not the DOS program."""
 def __init__(self,label='reference'):
  self.label=re.sub('[^a-zA-Z0-9_-]','_',label)
  self.directory=BASE/self.label;self.directory.mkdir(parents=True,exist_ok=True)
  self.sock=socket.create_connection((HOST,PORT),timeout=5)
  self.sock.settimeout(.2);self.events=[];self.raw_in=bytearray();self.raw_out=bytearray();self.application=bytearray()
  self.cursor=0;self.telnet=bytearray();self.state='data';self.command=0;self.sub=bytearray();self.answered=set()
 def send(self,data,reason='input'):
  self.sock.sendall(data);self.raw_out.extend(data);self.events.append({'direction':'client-to-server','reason':reason,'monotonic':time.monotonic(),'hex':data.hex()})
 def decode(self,data):
  output=bytearray()
  for value in data:
   if self.state=='data':
    if value==255:self.state='iac'
    else:output.append(value)
   elif self.state=='iac':
    if value==255:output.append(255);self.state='data'
    elif value in (251,252,253,254):self.command=value;self.state='option'
    elif value==250:self.sub.clear();self.state='sub'
    else:self.state='data'
   elif self.state=='option':
    if self.command==253:
     accepted=value in (0,3,24,31)
     self.send(bytes([255,251 if accepted else 252,value]),'telnet-negotiation')
     if value==31 and accepted:self.send(b'\xff\xfa\x1f\x00\x50\x00\x19\xff\xf0','NAWS80x25')
    elif self.command==251:self.send(bytes([255,253 if value in (0,1,3) else 254,value]),'telnet-negotiation')
    self.state='data'
   elif self.state=='sub':
    if value==255:self.state='sub-iac'
    else:self.sub.append(value)
   elif self.state=='sub-iac':
    if value==240:
     if self.sub[:2]==b'\x18\x01':self.send(b'\xff\xfa\x18\x00ANSI-BBS\xff\xf0','terminal-type')
     self.state='data'
    elif value==255:self.sub.append(value);self.state='sub'
    else:self.state='sub'
  start=len(self.application);self.application.extend(output)
  for match in re.finditer(rb'\x1b\[6n|\x1b\[5n|\x1b\[c|\x1b\[>c|\x1bZ',self.application[max(0,start-8):]):
   position=max(0,start-8)+match.start()
   if position in self.answered:continue
   self.answered.add(position);query=match[0]
   reply={b'\x1b[6n':b'\x1b[25;80R',b'\x1b[5n':b'\x1b[0n',b'\x1b[c':b'\x1b[?62;2c',b'\x1b[>c':b'\x1b[>1;10;0c',b'\x1bZ':b'\x1b[?62;2c'}[query]
   self.send(reply,'reference-detection-reply')
  return bytes(output)
 def expect(self,cues,timeout=15):
  if isinstance(cues,str):cues=[cues]
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline:
   text=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',self.application[self.cursor:]).decode('cp437',errors='replace')
   for cue in cues:
    if cue in text:self.cursor=len(self.application);return cue
   try:
    if self.receive() is None:raise RuntimeError('Mystic disconnected before '+repr(cues))
   except socket.timeout:pass
  raise TimeoutError('Mystic prompt deadline: '+repr(cues))
 def receive(self):
  data=self.sock.recv(65536)
  if not data:return None
  self.raw_in.extend(data);self.events.append({'direction':'server-to-client','monotonic':time.monotonic(),'hex':data.hex()})
  return self.decode(data)
 def save(self):
  (self.directory/'server.bin').write_bytes(self.raw_in);(self.directory/'client.bin').write_bytes(self.raw_out)
  (self.directory/'application.bin').write_bytes(self.application)
  (self.directory/'application.txt').write_text(re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',self.application).decode('cp437',errors='replace'))
  (self.directory/'wire.json').write_text(json.dumps(self.events,indent=2)+'\n')
 def close(self):self.save();self.sock.close()

def bootstrap():
 """Create/login the local synthetic fixture; never contacts an external BBS."""
 new=(SYSTEM/'data/users.dat').stat().st_size==0
 client=Reference('bootstrap')
 try:
  client.expect('Enter your user name:')
  if new:
   client.send(b'new\r');client.expect('Create an account with this BBS?');client.send(b'y')
   for cue,value in [('Enter your alias/handle',b'PCPLUSLAB\r'),('Enter your full REAL name',b'PCPlus Test\r'),
                     ('[U]ndisclosed',b'u'),('Enter your e-mail address',b'pcplus@example.invalid\r'),
                     ('How did you hear of this BBS',b'Local compatibility lab\r'),
                     ('Password ->',b'LoCtest42\r'),('Again ->',b'LoCtest42\r')]:
    client.expect(cue);client.send(value)
  else:
   client.send(b'PCPLUSLAB\r');client.expect('Enter your password:');client.send(b'LoCtest42\r')
  cue=client.expect(['Add to the one liners?','Command ->'])
  if cue!='Command ->':
   client.send(b'n');cue=client.expect(['Read them now?','Command ->'])
   if cue!='Command ->':client.send(b'n');client.expect('Command ->')
  result={'passed':True,'created':new,'username':'PCPLUSLAB','password':'LoCtest42','scope':'Synthetic local reference-client account fixture, not DOS compatibility proof.'}
  (BASE/'fixture.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 finally:client.close()

def audit(label):
 """Assert actual DOS/vendor menu evidence beyond the generic transport exit gate."""
 directory=ROOT/'build/bbs-lab/results/mystic'/label
 run=json.loads((directory/'result.json').read_text())
 display=(directory/'display.bin').read_bytes();sent=(directory/'serial-received.bin').read_bytes()
 plain=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display)
 screen=(directory/'screen.txt').read_text()
 markers=[b'Indexed File Lister',b'File Base Listings',b'Indexed Message Reader',b'Message Base Listings']
 positions=[plain.find(marker) for marker in markers]
 reports=[part.decode('ascii') for part in re.findall(rb'\x1b\[[0-9]+;[0-9]+R',sent)]
 checks={'generic_DOS_hardware_and_connection_checks':run['passed'],
  'actual_vendor_banner':b'Mystic BBS Version 1.12 A48' in plain,
  'actual_DOS_CPR_response':b'\x1b[6n' in display and '\x1b[25;80R' in reports,
  'authenticated_input_and_prompts':b'pcpluslab\rLoCtest42\r' in sent and b'Add to the one liners?' in plain,
  'file_and_message_indexed_screens_in_order':all(v>=0 for v in positions) and positions==sorted(positions),
  'actual_DOS_arrow_pairs':sent.count(b'\x1b[B')>=2 and sent.count(b'\x1b[A')>=2,
  'escape_return_to_message_menu':sent.endswith(b'\x1b') and 'Indexed Message Reader' in screen and 'Command ->' in screen and 'General Messages' in screen,
  'no_unsupported_terminal_failure':'Unsupported terminal function' not in screen}
 result={'passed':all(checks.values()),'checks':checks,'DOS_binary_sha256':run['binary_sha256'],'vendor_archive_sha256':SHA256,
  'endpoint':f'{HOST}:{PORT}','terminal_reports':reports,'menu_markers':{m.decode():p for m,p in zip(markers,positions)},
  'scope':'Actual vendor Mystic login and read-only file/message indexed-menu navigation through source-built DOS executable; no public BBS or physical modem.'}
 (directory/'mystic-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not result['passed']:raise SystemExit(1)

def probe(label):
 client=Reference(label)
 print('Reference client connected; input lines become CR-terminated bytes; ~quit ends.',flush=True)
 try:
  while True:
   ready,_,_=select.select([client.sock,sys.stdin],[],[],.2)
   if client.sock in ready:
    try:out=client.receive()
    except socket.timeout:continue
    if out is None:break
    text=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',out).decode('cp437',errors='replace')
    print(text,end='',flush=True)
   if sys.stdin in ready:
    line=sys.stdin.readline()
    if not line or line.rstrip()=='~quit':break
    value=line.rstrip('\r\n')
    client.send(bytes.fromhex(value[5:]) if value.startswith('~hex ') else value.encode('ascii')+b'\r')
 finally:client.close()

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['setup','configure','start','stop','bootstrap','probe','audit']);p.add_argument('--label',default='reference');args=p.parse_args()
 {'setup':setup,'configure':configure,'start':start,'stop':stop,'bootstrap':bootstrap,'probe':lambda:probe(args.label),'audit':lambda:audit(args.label)}[args.command]()
if __name__=='__main__':main()
