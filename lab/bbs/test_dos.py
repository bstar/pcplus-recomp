#!/usr/bin/env python3
"""Exercise real loopback BBS servers through the DOS executable and modem model."""
import argparse,asyncio,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
from modem import Modem
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from test_terminal import SAMPLER
from terminal_config_fixtures import image as config_image, RATES
from modem_fixtures import fixture as modem_fixture
from directory_fixtures import directory as directory_image,prm as directory_prm
from directory_test_support import accounting_check

async def run(args):
 binary=ROOT/'build/terminal/TERMINAL.EXE'
 if getattr(args,'binary',None):binary=args.binary.resolve()
 digest=hashlib.sha256(binary.read_bytes()).hexdigest()
 output=ROOT/'build/bbs-lab/results'/args.name/args.label
 output.mkdir(parents=True,exist_ok=True)
 for name in ('PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN'):(output/name).unlink(missing_ok=True)
 fixture=None;directory_fixture=None
 automatic=args.dial_fixture or args.directory_fixture
 command=f'TERMINAL COM{args.com} {args.baud} {args.flow}'
 if args.config_fixture or automatic:
  fixture=config_image(port=args.com,baud=RATES.index(args.baud),soft=int(args.flow=='SOFT'),hard=int(args.flow=='HARD'),normal=7)
  if automatic:
   modem=bytearray(modem_fixture(timeout=45))
   for at,size in ((0,10),(0x174,32),(0x194,12),(0x1ae,10)):modem[at:at+size]=fixture[at:at+size]
   fixture=bytes(modem)
  if args.directory_fixture:
   # The record overrides a different PRM port/rate; both UART tables are real.
   fixture=directory_prm(port=1,baud=6,soft=int(args.flow=='SOFT'),hard=int(args.flow=='HARD'))
   directory_fixture=directory_image(entry=args.entry,target=f'lab.local:{args.port}'.encode('ascii'),port=args.com,baud=RATES.index(args.baud))
   binding=getattr(args,'directory_key_binding',None)
   if binding:
    assert re.fullmatch(r'[A-Za-z0-9_-]{1,8}',binding)
    directory_fixture=bytearray(directory_fixture);at=250+(args.entry-1)*114+0x56
    directory_fixture[at:at+9]=binding.encode().ljust(9,b'\0');directory_fixture=bytes(directory_fixture)
   (output/'TEST.DIR').write_bytes(directory_fixture)
  (output/'TEST.PRM').write_bytes(fixture)
  command='TERMINAL @D:\\TEST.PRM'
  if args.directory_fixture:
   command+=' /E:D:\\TEST.DIR'
   if not args.directory_browser:command+=f' /N:{args.entry}'
  elif args.dial_fixture:command+=f' /D:lab.local:{args.port}'
  if getattr(args,'mouse_scales',None):
   import struct
   sx,sy=args.mouse_scales
   assert 1<=sx<=999 and 1<=sy<=999
   fixture=bytearray(fixture);struct.pack_into('<HH',fixture,0x4e4,sx,sy)
   fixture=bytes(fixture);(output/'TEST.PRM').write_bytes(fixture)
 program_sound=getattr(args,'program_sound',None)
 if program_sound is not None:
  assert fixture is not None and program_sound in (0,1,65535)
  import struct
  fixture=bytearray(fixture);struct.pack_into('<H',fixture,0x1bc,program_sound)
  fixture=bytes(fixture);(output/'TEST.PRM').write_bytes(fixture)
 init_wait=getattr(args,'init_wait',None)
 if init_wait is not None:
  assert 0<=init_wait<=32767
  command+=f' /I:{init_wait}'
 keymap=None
 if args.keymap_fixture:
  keymap=args.keymap_fixture.read_bytes()
  assert keymap and len(keymap)%948==0,'Whole native KBD profile blocks required'
  (output/'BOARD.KBD').write_bytes(keymap)
  command+=' /K:D:\\BOARD.KBD'
 meta=None
 meta_path=getattr(args,'meta_fixture',None)
 if meta_path:
  meta=meta_path.read_bytes();assert len(meta)==540,'Whole ten-record KEY fixture required'
  (output/'ACTIONS.KEY').write_bytes(meta)
  command+=' /T:D:\\ACTIONS.KEY'
 base=[0x3f8,0x2f8,0x3e8,0x2e8][args.com-1]
 sampler=SAMPLER
 for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(base+offset))
 (output/'sampler.asm').write_text(sampler)
 subprocess.run(['nasm','-f','bin',str(output/'sampler.asm'),'-o',str(output/'SNAP.COM')],check=True)
 modem=Modem('127.0.0.1',args.port,output,soft=args.flow=='SOFT',baud=args.baud,packet_delay_ms=args.packet_delay_ms)
 server=await asyncio.start_server(modem.accept,'127.0.0.1',0)
 port=server.sockets[0].getsockname()[1]
 prefix=('p1000 ' if automatic else 'p1000 a t d enter ')
 if args.directory_browser:
  assert args.directory_fixture and args.entry<=10,'Browser lab recipe supports first-page selection'
  prefix='p500 '+('down p100 '*(args.entry-1))+'enter p1000 '
 keys=prefix+args.keys+f' p{args.wait*1000} a-x'
 serial='\n'.join(f'serial{i}='+ (f'nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1' if i==args.com else 'disabled') for i in range(1,5))
 config=f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
{serial}
[autoexec]
@echo off
mount c "{binary.parent}"
mount d "{output}"
c:
D:\\SNAP B
ADDKEY {keys}
{command}
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
D:\\SNAP S
D:\\SNAP A
exit
'''
 cpu=getattr(args,'cpu','386')
 assert cpu in ('8086','286','386','486')
 if cpu!='386':config=config.replace('cputype=386','cputype='+cpu)
 (output/'dosbox.conf').write_text(config)
 server_log=None
 if args.server_log:
  assert args.name=='enigma','Explicit server log is for owned ENiGMA fixtures'
  server_log=args.server_log.resolve()
  assert server_log.is_relative_to(ROOT/'build') and server_log.is_file(),'Only owned build/ server logs'
 elif args.name=='enigma' and args.port==23233:
  server_log=ROOT/'build/bbs-lab/enigma/source/logs/enigma-bbs.log'
 if server_log is not None:
  stat=server_log.stat()
  (output/'server-log-start.json').write_text(json.dumps({'byte_offset':stat.st_size,'path':str(server_log),'inode':stat.st_ino})+'\n')
 start=time.monotonic()
 with (output/'dosbox.log').open('w') as log:
  process=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(output/'dosbox.conf'),cwd=output,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log)
  try:code=await asyncio.wait_for(process.wait(),args.timeout)
  except asyncio.TimeoutError:
   process.terminate()
   try:await asyncio.wait_for(process.wait(),5)
   except asyncio.TimeoutError:process.kill();await process.wait()
   code=-1
 server.close()
 # Python3.14 waits for accepted clients as well as the listening socket.
 # A timed-out DOS process can leave its nullmodem transport accepted here.
 if hasattr(server,'close_clients'):server.close_clients()
 try:await asyncio.wait_for(server.wait_closed(),3)
 except asyncio.TimeoutError:pass
 try:await asyncio.wait_for(modem.done.wait(),2)
 except asyncio.TimeoutError:pass
 modem.save()
 screen=(output/'SCREEN.BIN').read_bytes() if (output/'SCREEN.BIN').exists() else b''
 text='\n'.join(screen[row*160:row*160+160:2].decode('cp437') for row in range(25)) if len(screen)==4000 else ''
 (output/'screen.txt').write_text(text+'\n')
 before=(output/'BEFORE.BIN').read_bytes() if (output/'BEFORE.BIN').exists() else b''
 after=(output/'AFTER.BIN').read_bytes() if (output/'AFTER.BIN').exists() else b''
 checks={'dos_normal_exit':code==0 and (output/'PASS.TXT').exists(),'hardware_restored':len(before)==42 and before==after,'screen_captured':len(screen)==4000,'bbs_connected':any(e['kind']=='bbs-connected' for e in modem.events),'bbs_display_received':bool(modem.display)}
 if fixture is not None:checks['configuration_unchanged']=(output/'TEST.PRM').read_bytes()==fixture
 if meta is not None:checks['meta_actions_unchanged']=(output/'ACTIONS.KEY').read_bytes()==meta
 if keymap is not None:checks['keyboard_profile_unchanged']=(output/'BOARD.KBD').read_bytes()==keymap
 if directory_fixture is not None:checks['directory_accounting_exact']=accounting_check(directory_fixture,(output/'TEST.DIR').read_bytes(),args.entry)
 checks['binary_unchanged_during_run']=hashlib.sha256(binary.read_bytes()).hexdigest()==digest
 result={'name':args.name,'label':args.label,'checks':checks,'passed':all(checks.values()),'seconds':round(time.monotonic()-start,3),'binary_sha256':digest,'keyboard':keys,'keyboard_input':args.keys,'serial':{'com':args.com,'baud':args.baud,'line':'8N1','flow':args.flow,'hardware_scope':'DOSBox-X nullmodem holds CTS ready; physical handshake timing is not represented.'},'scope':'Actual local BBS via modeled Hayes/Telnet modem, DOSBox-X UART and source-built DOS terminal. Normal exit alone does not establish successful menu interaction.'}
 result['initialization_wait_seconds']=init_wait
 result['cpu']=next(line.split('=',1)[1] for line in config.splitlines() if line.startswith('cputype='))
 result['server_log']=str(server_log) if server_log is not None else None
 result['server_endpoint']={'address':'127.0.0.1','port':args.port}
 result['modem_packet_delay_ms']=args.packet_delay_ms
 result['meta_actions']={'sha256':hashlib.sha256(meta).hexdigest(),'file':'ACTIONS.KEY'} if meta is not None else None
 result['keyboard_profile']={'sha256':hashlib.sha256(keymap).hexdigest(),'file':'BOARD.KBD'} if keymap is not None else None
 result['configuration']={'automatic_dial':automatic,'mode':'explicit synthetic partial PRM' if fixture is not None else 'CLI serial options','command':command,'sha256':hashlib.sha256(fixture).hexdigest() if fixture is not None else None,'directory_entry':args.entry if directory_fixture is not None else None,'directory_browser':args.directory_browser,'directory_sha256':hashlib.sha256(directory_fixture).hexdigest() if directory_fixture is not None else None}
 if program_sound is not None:result['configuration']['program_sound_word']=program_sound
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));print(text)
 return 0 if result['passed'] else 1

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('name');p.add_argument('--port',type=int,required=True);p.add_argument('--label',default='probe');p.add_argument('--keys',default='');p.add_argument('--wait',type=int,default=12);p.add_argument('--timeout',type=int,default=70)
 p.add_argument('--server-log',type=Path,help='Explicit owned ENiGMA log for a separate test server; default stock fixture')
 p.add_argument('--init-wait',type=int,choices=range(32768),help='Explicit /I initialization acknowledgement deadline in seconds')
 p.add_argument('--dial-fixture',action='store_true',help='Exercise configured automatic modem initialization/dialing inside DOS')
 p.add_argument('--directory-key-binding',help='Bind the selected synthetic directory entry to a KEY basename')
 p.add_argument('--meta-fixture',type=Path,help='Load an explicit source-owned ten-record KEY fixture with /T')
 p.add_argument('--keymap-fixture',type=Path,help='Copy an explicit source-owned KBD fixture to the owned DOS test drive and load with /K')
 p.add_argument('--packet-delay-ms',type=int,choices=range(101),default=0,help='Explicit byte-transparent modem buffering experiment, NONE/HARD only; default immediate')
 p.add_argument('--directory-fixture',action='store_true',help='Load an actual synthetic directory record and dial it inside DOS')
 p.add_argument('--directory-browser',action='store_true',help='Choose the fixture entry through native DOS browser keys')
 p.add_argument('--entry',type=int,choices=range(1,201),default=3)
 p.add_argument('--program-sound',type=int,choices=[0,1,65535],help='Set only the sound word in the explicit synthetic PRM fixture')
 p.add_argument('--config-fixture',action='store_true',help='Read synthetic PRM in DOS; no serial CLI overrides or private configuration')
 p.add_argument('--mouse-scales',type=int,nargs=2,metavar=('X','Y'),help='Explicit valid mouse scales in the synthetic PRM')
 p.add_argument('--cpu',choices=['8086','286','386','486'],default='386')
 p.add_argument('--com',type=int,choices=range(1,5),default=1);p.add_argument('--baud',type=int,choices=[300,1200,2400,4800,9600,19200,38400,57600,115200],default=38400);p.add_argument('--flow',choices=['NONE','SOFT','HARD'],default='SOFT')
 raise SystemExit(asyncio.run(run(p.parse_args())))
