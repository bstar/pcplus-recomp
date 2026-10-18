#!/usr/bin/env python3
"""Pinned, loopback-only ENiGMA half BBS lab using the project's Nix Node."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'build/bbs-lab/enigma'
SOURCE=LAB/'source'
COMMIT='6c25317168b762f7d9088a54d3f8295438827a0e'
REPO='https://github.com/NuSkooler/enigma-bbs.git'
HOST='127.0.0.1'
PORT=23233
USERNAME='loclab'
PASSWORD='LoC-Lab-2026!'
LOCK_SHA256='8fcaecda3a4b1756ad295be95486cbdd5b9afea005949ac3da8822224c822d56'

def run(arguments,**options):
 return subprocess.run(arguments,cwd=SOURCE,check=True,**options)

def node(script):
 run(['node','-e',script])

def setup():
 executable=shutil.which('node')
 assert executable and '/nix/store/' in str(Path(executable).resolve()),'Run through the pinned Nix tools/dev shell'
 LAB.mkdir(parents=True,exist_ok=True)
 if not SOURCE.exists():
  subprocess.run(['git','clone','--no-checkout',REPO,str(SOURCE)],check=True)
 run(['git','fetch','--depth','1','origin',COMMIT])
 run(['git','checkout','--detach',COMMIT])
 assert hashlib.sha256((SOURCE/'package-lock.json').read_bytes()).hexdigest()==LOCK_SHA256
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()==COMMIT
 env=dict(os.environ,HUSKY='0')
 run(['npm','ci','--no-audit','--no-fund'],env=env)
 node('const D=require("better-sqlite3");let d=new D(":memory:");console.log(d.prepare("select sqlite_version() as sqlite").get());require("node-pty");')
 for directory in ['logs','db','db/mods','drop','file_base']:(SOURCE/directory).mkdir(parents=True,exist_ok=True)
 menus=SOURCE/'config/menus';menus.mkdir(parents=True,exist_ok=True)
 includes=[]
 for template in sorted((SOURCE/'misc/menu_templates').glob('*.in.hjson')):
  if template.name=='main.in.hjson':continue
  name='loc-'+template.name.replace('.in','');includes.append(name)
  shutil.copy2(template,menus/name)
 main=(SOURCE/'misc/menu_templates/main.in.hjson').read_text().replace('%INCLUDE_FILES%','\n        '.join(includes))
 (menus/'loc-main.hjson').write_text(main)
 config={'general':{'boardName':'LoC ENiGMA Lab','prettyBoardName':'LoC ENiGMA Lab','closedSystem':True,'menuFile':str(menus/'loc-main.hjson')},
  'loginServers':{'telnet':{'enabled':True,'address':HOST,'port':PORT},'ssh':{'enabled':False},'webSocket':{'ws':{'enabled':False},'wss':{'enabled':False}}},
  'contentServers':{'web':{'http':{'enabled':False},'https':{'enabled':False}},'gopher':{'enabled':False},'nntp':{'nntp':{'enabled':False},'nntps':{'enabled':False}}},
  'users':{'requireActivation':False,'preAuthIdleLogoutSeconds':600,'idleLogoutSeconds':900},
  'messageConferences':{'lab':{'name':'Lab','desc':'Private compatibility lab','default':True,'areas':{'general':{'name':'General','desc':'Synthetic local test messages only','default':True}}}},
  'logging':{'rotatingFile':{'level':'debug'}}}
 (SOURCE/'config/config.hjson').write_text(json.dumps(config,indent=2)+'\n')
 node(r'''const c=require('./core/oputil/oputil_common');c.initConfigAndDatabases(err=>{if(err)throw err;const U=require('./core/user');const P=require('./core/user_property');const users=[['locadmin','LoC-Admin-2026!'],['loclab','LoC-Lab-2026!']];function next(){if(!users.length)return process.exit(0);const [name,password]=users.shift();U.getUserIdAndName(name,(e,id)=>{if(!e&&id)return next();const u=new U();u.username=name;u.properties[P.RealName]='Local Test';u.properties[P.Location]='Loopback';u.properties[P.ThemeId]='luciano_blocktronics';u.properties[P.TermWidth]=80;u.properties[P.TermHeight]=25;u.create({password,sessionId:'pcplus-local-lab'},e=>{if(e)throw e;console.log('Created synthetic',name,u.userId);next();});});}next();});''')
 version=json.loads((SOURCE/'package.json').read_text())['version']
 metadata={'server':'ENiGMA½','repository':REPO,'commit':COMMIT,'version':version,'package_lock_sha256':hashlib.sha256((SOURCE/'package-lock.json').read_bytes()).hexdigest(),'node':subprocess.check_output(['node','--version'],text=True).strip(),'node_executable':str(Path(executable).resolve()),'endpoint':f'{HOST}:{PORT}','username':USERNAME,'password':PASSWORD,'theme':'luciano_blocktronics','scope':'Synthetic local BBS only; all runtime state under ignored build/bbs-lab/enigma.'}
 (LAB/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2))

def process_pid():
 try:
  pid=int((LAB/'server.pid').read_text())
  cmdline=Path(f'/proc/{pid}/cmdline').read_bytes()
  if b'main.js' in cmdline and str(SOURCE).encode() in cmdline:return pid
 except (FileNotFoundError,ValueError,ProcessLookupError):pass
 return None

def start():
 executable=shutil.which('node')
 assert executable and '/nix/store/' in str(Path(executable).resolve()),'Run through the pinned Nix bbs shell'
 if process_pid():return status()
 assert (SOURCE/'config/config.hjson').exists(),'Run setup first'
 with (LAB/'server.log').open('ab') as log:
  process=subprocess.Popen(['node',str(SOURCE/'main.js')],cwd=SOURCE,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
 (LAB/'server.pid').write_text(str(process.pid)+'\n')
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  if process.poll() is not None:raise RuntimeError('ENiGMA failed; see '+str(LAB/'server.log'))
  try:
   with socket.create_connection((HOST,PORT),timeout=.1):return status()
  except OSError:time.sleep(.1)
 raise TimeoutError('No loopback listener; see '+str(LAB/'server.log'))

def stop():
 pid=process_pid()
 if pid:
  os.kill(pid,signal.SIGTERM)
  for _ in range(50):
   if not process_pid():break
   time.sleep(.1)
  if process_pid():os.kill(pid,signal.SIGKILL)
 (LAB/'server.pid').unlink(missing_ok=True)
 print('Stopped owned ENiGMA lab server')

def status():
 result={'pid':process_pid(),'endpoint':f'{HOST}:{PORT}','username':USERNAME,'password':PASSWORD,'metadata':str(LAB/'metadata.json')}
 print(json.dumps(result,indent=2));return result

def probe():
 import re
 out=LAB/'probe';out.mkdir(exist_ok=True)
 s=socket.create_connection(('127.0.0.1',23233));s.settimeout(.1)
 raw=bytearray();plain=bytearray();sent=bytearray();buf=bytearray();events=[]
 def send(b):sent.extend(b);s.sendall(b)
 def process(b):
  buf.extend(b);text=bytearray()
  while buf:
   if buf[0]!=255:text.append(buf.pop(0));continue
   if len(buf)<2:break
   if buf[1]==255:text.append(255);del buf[:2];continue
   if buf[1] in [251,252,253,254]:
    if len(buf)<3:break
    _,cmd,opt=buf[:3];del buf[:3];events.append(['telnet',cmd,opt])
    if cmd==253:
     send(bytes([255,251 if opt in [0,3,24,31,39] else 252,opt]))
     if opt==31:send(b'\xff\xfa\x1f\x00\x50\x00\x19\xff\xf0')
    if cmd==251:send(bytes([255,253 if opt in [0,1,3] else 254,opt]))
    continue
   if buf[1]==250:
    end=buf.find(b'\xff\xf0',2)
    if end<0:break
    payload=bytes(buf[2:end]);del buf[:end+2];events.append(['subneg',payload.hex()])
    if payload[:2]==b'\x18\x01':send(b'\xff\xfa\x18\x00ANSI-BBS\xff\xf0')
    if payload[:2]==b'\x27\x01':send(b'\xff\xfa\x27\x00\x00TERM\x01ANSI-BBS\x00ROWS\x0125\x00COLUMNS\x0180\xff\xf0')
    continue
   del buf[:2]
  plain.extend(text)
  # Initial home-detection query follows ESC[H. Record all queries.
  n=text.count(b'\x1b[6n')
  for _ in range(n):events.append(['cpr','1;1']);send(b'\x1b[1;1R')
 def receive(duration):
  end=time.monotonic()+duration
  while time.monotonic()<end:
   try:
    b=s.recv(65536)
    if not b:break
    raw.extend(b);process(b)
   except socket.timeout:pass
 def phase(name,action=b'',delay=1):
  if action:send(action)
  start=len(plain);receive(delay)
  data=bytes(plain[start:]);(out/(name+'.bin')).write_bytes(data)
  text=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',data).decode('cp437',errors='replace')
  (out/(name+'.txt')).write_text(text)
  print(name,repr(text[-200:]),flush=True)
 phase('matrix',delay=4)
 def rows():
  return [json.loads(line) for line in (SOURCE/'logs/enigma-bbs.log').read_text().splitlines() if line.strip()]
 connected=[row for row in rows() if row.get('msg','').startswith('Client connected on node')]
 session_id=connected[-1]['sessionId']
 def current_menu():
  menus=[row['menuName'] for row in rows() if row.get('sessionId')==session_id and row.get('menuName')]
  return menus[-1] if menus else None
 phase('matrix-down',b'\x1b[B',.3);phase('matrix-up',b'\x1b[A',.3)
 phase('login',b'\r');phase('username',USERNAME.encode()+b'\r');phase('password',PASSWORD.encode()+b'\r',2)
 # Stock achievements/returning-caller screens make the pre-main count vary.
 # Drive the actual menus using their real server log state, never bypass them.
 for index in range(20):
  menu=current_menu()
  if menu=='mainMenu':break
  action=b'\x1b' if menu=='fullLoginSequenceOnelinerz' else b'N' if menu=='fullLoginSequenceNewScanConfirm' else b'\r'
  phase(f'advance-{index}-{menu}',action,1.2)
 assert current_menu()=='mainMenu',current_menu()
 phase('messages',b'M\r',1.5)
 assert current_menu()=='messageBaseMainMenu',current_menu()
 phase('return-main',b'Q\r',1.5);assert current_menu()=='mainMenu',current_menu()
 phase('files',b'F\r',1.5);assert current_menu()=='fileBaseMainMenu',current_menu()
 phase('return-main2',b'Q\r',1.5);assert current_menu()=='mainMenu',current_menu()
 phase('logoff-prompt',b'G\r',1);phase('logoff-confirm',b'Y',1)
 (out/'raw.bin').write_bytes(raw);(out/'plain.bin').write_bytes(plain);(out/'sent.bin').write_bytes(sent);(out/'events.json').write_text(json.dumps(events,indent=2))
 s.close()

 log=SOURCE/'logs/enigma-bbs.log'
 rows=[json.loads(line) for line in log.read_text().splitlines() if line.strip()]
 matching=[row for row in rows if row.get('msg')=='User "loclab" successfully logged in']
 session=matching[-1].get('sessionId') if matching else None
 menu_rows=[row for row in rows if row.get('sessionId')==session and row.get('menuName')]
 queries=sorted(set(seq.decode('ascii',errors='backslashreplace') for seq in re.findall(rb'\x1b\[[0-?]*[ -/]*[@-~]',plain) if seq[-1:] in [b'n',b'c'] or b' ' in seq))
 result={'server_commit':COMMIT,'authenticated':bool(matching),'session_id':session,'menus':[row['menuName'] for row in menu_rows],'queries':queries,'telnet_events':events,'scope':'Actual stock ENiGMA half login and menu workflow using independent Telnet baseline; fixedhome CPR response is not a DOS compatibility test.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['setup','start','stop','status','probe']);args=parser.parse_args()
 {'setup':setup,'start':start,'stop':stop,'status':status,'probe':probe}[args.command]()
if __name__=='__main__':main()
