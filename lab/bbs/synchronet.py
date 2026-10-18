#!/usr/bin/env python3
"""Pinned official Synchronet loopback-only compatibility laboratory.

Run through nix develop ./nix#bbs --command python3 lab/bbs/synchronet.py ...
Downloaded code/default data and captures stay in ignored build/bbs-lab.
"""
import argparse,hashlib,json,os,re,shutil,socket,subprocess,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'build/bbs-lab/synchronet';RUNTIME=LAB/'runtime'
HOST='127.0.0.1';PORT=23231
COMMIT='9de2c48d0265b07e1a8406d8a55d31df4fad7ee8'
ARTIFACTS={'sbbs_dev.tgz':'e2d2d763c2913281fa5b40f12d9d82d5d4972b78f8676a618eabde112fd99b89','sbbs_run.tgz':'ef12ec76ebe4bf64eac2fc4fb098c5b4f4b30f33c96ace46dffd75eba5fb4e54','sbbs_src.tgz':'b6c1ccc4a6b0eaeb38acd2c3e8f02a7e8cfaaaade6bc7ccf72e85aa1161f94a4'}
ENV=lambda:dict(os.environ,SBBSCTRL=str(RUNTIME/'ctrl'))

def setup():
 LAB.mkdir(parents=True,exist_ok=True)
 for name,digest in ARTIFACTS.items():
  p=LAB/name
  if not p.exists():urllib.request.urlretrieve('https://www.synchro.net/Synchronet/'+name,p)
  if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise RuntimeError('Rolling upstream archive changed; refusing unreviewed artifact '+name)
 if not (RUNTIME/'ctrl/main.ini').exists():
  RUNTIME.mkdir(parents=True,exist_ok=True)
  subprocess.run(['tar','xzf',str(LAB/'sbbs_run.tgz'),'-C',str(RUNTIME)],check=True)
 subprocess.run(['tar','xzf',str(LAB/'sbbs_dev.tgz'),'-C',str(RUNTIME/'exec')],check=True)
 config=f'''[Global]\nInterface=127.0.0.1\nHostname=localhost\nCtrlDirectory={RUNTIME}/ctrl\nTempDirectory={RUNTIME}/temp\nLogLevel=Debug\nLoginAttemptDelay=0\nLoginAttemptThrottle=0\n[BBS]\nAutoStart=true\nTelnetInterface=127.0.0.1\nTelnetPort={PORT}\nFirstNode=1\nLastNode=2\nOptions=NO_HOST_LOOKUP|NO_EVENTS\nDefaultTermWidth=80\nDefaultTermHeight=25\n[FTP]\nAutoStart=false\n[Mail]\nAutoStart=false\n[Web]\nAutoStart=false\n[Services]\nAutoStart=false\n[Unix]\nDaemonize=false\n'''
 (RUNTIME/'ctrl/sbbs.ini').write_text(config)
 p=RUNTIME/'ctrl/main.ini';s=p.read_text().replace('name=My BBS','name=LoC Protocol Lab',1).replace('operator=Sysop','operator=Lab Sysop',1).replace('new_install=true','new_install=false',1).replace('password=SYSPASS','password=LOCALONLY42',1);p.write_text(s)
 for name in ['data/user','data/subs','data/dirs','data/msgs','data/logs','temp','mods','node1/temp','node2/temp']:(RUNTIME/name).mkdir(parents=True,exist_ok=True)
 subprocess.run([str(RUNTIME/'exec/jsexec'),'-n','makeuser.js','LABUSER','-P','LABPASS42','-R','Local Tester','-L','Local Lab','-S','50'],env=ENV(),check=True)
 script=RUNTIME/'exec/lab_setup.js'
 script.write_text("require('userdefs.js','USER_ANSI');\nvar u=new User(system.matchuser('LABUSER'));\nu.handle='LABUSER';u.name='Local Tester';u.address='Local Test';u.location='Local Lab';u.zipcode='00000';u.phone='0000000000';u.birthdate='19900101';u.gender='M';u.netmail='labuser@example.invalid';u.security.password='LABPASS42';u.security.level=50;\nu.settings |= USER_ANSI|USER_COLOR|USER_AUTOTERM;\n")
 subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(script)],env=ENV(),check=True)
 provenance()

def provenance():
 for name,digest in ARTIFACTS.items():
  if hashlib.sha256((LAB/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Archive digest mismatch: '+name)
 version=subprocess.check_output([str(RUNTIME/'exec/sbbs'),'version'],env=ENV(),text=True)
 provenance={'server':'Synchronet3.22a development snapshot','source_commit':COMMIT,'artifacts':{n:{'url':'https://www.synchro.net/Synchronet/'+n,'sha256':d} for n,d in ARTIFACTS.items()},'version_output':version,'endpoint':[HOST,PORT],'account':{'name':'LABUSER','password':'LABPASS42','security_level':50,'synthetic':True},'runtime_dependencies':'Pinned repository nix#bbs shell; original official ELF snapshot compiler GCC14.2.0','limitations':['Not a stable release; upstream archives are rolling and digest changes fail closed.','No public board, network messages, or private configuration used.']}
 (LAB/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 print(json.dumps(provenance,indent=2))

class Peer:
 def __init__(self):
  self.sock=socket.create_connection((HOST,PORT),5);self.sock.settimeout(.2)
  self.rx=bytearray();self.tx=bytearray();self.text=bytearray();self.history=bytearray();self.pending=bytearray();self.events=[];self.probes=[];self.cpr_number=0
 def send(self,data,label='terminal'):
  self.sock.sendall(data);self.tx.extend(data);self.events.append({'time':time.monotonic(),'direction':'out','label':label,'hex':data.hex()})
 def plain(self,data):
  self.text.extend(data);self.history.extend(data)
  # Initial ANSI probe is intentionally declared, not a screen implementation.
  # A reference ANSI peer reports the far edge for the initial size detection.
  while b'\x1b[6n' in self.text[self.scan_from:]:
   i=self.text.find(b'\x1b[6n',self.scan_from);self.scan_from=i+4;self.cpr_number+=1
   self.probes.append({'kind':'CPR','offset':i});self.send(b'\x1b[25;80R','CPR25x80')
 def feed(self,data):
  self.pending.extend(data);out=bytearray();i=0
  while i<len(self.pending):
   if self.pending[i]!=255:out.append(self.pending[i]);i+=1;continue
   if i+1>=len(self.pending):break
   cmd=self.pending[i+1]
   if cmd==255:out.append(255);i+=2;continue
   if cmd in (251,252,253,254):
    if i+2>=len(self.pending):break
    option=self.pending[i+2]
    if cmd==251:self.send(bytes([255,253 if option in (0,1,3) else 254,option]),'telnet')
    elif cmd==253:
     yes=option in (0,3,24,31);self.send(bytes([255,251 if yes else 252,option]),'telnet')
     if option==31:self.send(b'\xff\xfa\x1f\x00P\x00\x19\xff\xf0','NAWS80x25')
    i+=3;continue
   if cmd==250:
    end=self.pending.find(b'\xff\xf0',i+2)
    if end<0:break
    payload=bytes(self.pending[i+2:end])
    if payload==b'\x18\x01':self.send(b'\xff\xfa\x18\x00ANSI\xff\xf0','TTYPEANSI')
    i=end+2;continue
   i+=2
  del self.pending[:i]
  self.plain(out)
 def pump(self,seconds=.5):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   try:data=self.sock.recv(65536)
   except TimeoutError:continue
   if not data:return False
   self.rx.extend(data);self.events.append({'time':time.monotonic(),'direction':'in','hex':data.hex()});self.feed(data)
  return True
 @staticmethod
 def cleaned(data):
  b=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',bytes(data))
  b=re.sub(rb'\x1b_.*?\x1b\\',b'',b,flags=re.S)
  return b.decode('cp437',errors='replace')
 @property
 def clean(self):return self.cleaned(self.text)
 def wait(self,needle,timeout=15):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   if needle.lower() in self.clean.lower():return
   if not self.pump(.2):break
  raise RuntimeError('Prompt not reached: '+needle+'\n'+self.clean[-1800:])
 def save(self,name):
  path=LAB/'captures'/name;path.mkdir(parents=True,exist_ok=True)
  (path/'server-wire.bin').write_bytes(self.rx);(path/'client-wire.bin').write_bytes(self.tx)
  (path/'transcript.txt').write_text(self.cleaned(self.history));(path/'events.json').write_text(json.dumps(self.events,indent=2)+'\n')
  (path/'capabilities.json').write_text(json.dumps({'cpr_count':self.cpr_number,'probes':self.probes,'ansi_sequences':sorted({m.group().hex() for m in re.finditer(rb'\x1b\[[0-?]*[ -/]*[@-~]',self.history)})},indent=2)+'\n')
 def __enter__(self):self.scan_from=0;return self
 def __exit__(self,*_):self.sock.close()

def probe():
 with Peer() as peer:
  steps=[]
  def phase():peer.text.clear();peer.scan_from=0
  def reached(prompt):peer.wait(prompt,25);steps.append(prompt)
  try:
   reached('Login:');peer.send(b'LABUSER\r','username');phase()
   reached('Password:');peer.send(b'LABPASS42\r','synthetic password');phase()
   reached('[Hit a key]');peer.send(b' ','welcome pause');phase()
   reached('Enter number of bulletin or [Quit]');peer.send(b'1\r','read-only bulletin1');phase()
   reached('Enter number of bulletin or [Quit]');assert 'System Totals:' in peer.clean
   steps.append('System Totals:');peer.send(b'Q','leave bulletins');phase()
   reached('Search all groups for new messages?');peer.send(b'n\r','decline message scan');phase()
   reached('[Hit a key]');peer.send(b' ','logon pause');phase()
   reached('Main');assert 'Read/Post Messages' in peer.clean
   steps.append('stock main menu');print(peer.clean[-6000:])
   result={'passed':True,'steps':steps,'scope':'Actual local Synchronet login, read-only bulletin1 and stock main menu with declared reference Telnet peer, not DOS renderer proof.'}
  except Exception:
   result={'passed':False,'steps':steps};raise
  finally:
   peer.save('reference-navigation')
   path=LAB/'captures/reference-navigation/result.json';path.write_text(json.dumps(result,indent=2)+'\n')

def check_dos(label):
 path=ROOT/'build/bbs-lab/results/synchronet'/label
 result=json.loads((path/'result.json').read_text());text=Peer.cleaned((path/'display.bin').read_bytes());sent=(path/'serial-received.bin').read_bytes()
 file_at=text.index('■ File ■');message_at=text.index('No messages have been posted on Local Notices',file_at)
 checks={'run_and_hardware_checks':result['passed'],'real_ansi_device_attributes':b'\x1b[?1;2c' in sent,'input_commands_reached_wire':b'TQRQ' in sent,'file_section_reached':'List Files in dir' in text[:message_at] and 'Q Main/Message Section' in text[:message_at],'returned_then_read_empty_message_area':'■ Main ■' in text[file_at:message_at],'returned_to_main_after_message_pause':'■ Main ■' in text[message_at:],'final_dos_video_is_main_menu':'■ Main ■' in (path/'screen.txt').read_text(),'no_unrecognized_command':'Unrecognized command' not in text}
 output={'passed':all(checks.values()),'checks':checks,'binary_sha256':result['binary_sha256'],'serial':result.get('serial'),'scope':'Actual DOS ANSI profile login, file section, return, read empty message area, dismiss pause and final main menu. No transfer/message writes or physical modem claim.'}
 (path/'navigation-checks.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2));assert output['passed']

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['setup','serve','probe','provenance','check-dos']);p.add_argument('--label',default='ansi-navigation');a=p.parse_args()
 if a.action=='setup':setup()
 elif a.action=='provenance':provenance()
 elif a.action=='check-dos':check_dos(a.label)
 elif a.action=='serve':
  os.environ.update(ENV());os.execv(str(RUNTIME/'exec/sbbs'),['sbbs','nd','t!','ne','nh',str(RUNTIME/'ctrl')])
 else:probe()
if __name__=='__main__':main()
