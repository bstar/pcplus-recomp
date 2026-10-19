#!/usr/bin/env python3
"""Actual owned BBS ZMODEM batch through DOS; never fabricates protocol replies.

Prepare the stock server protocol/helper and fresh upload area separately with
the owned lab setup tools. --file NAME=build/... is repeatable, including empty files.
DOS upload pattern D:\\SEND\\*.BIN; receive directory D:\\RECV. Supply paced
ADDKEY --keys including local F2 inside the AltR/AltS filename prompt; no sessions start on import.
"""
import argparse,asyncio,fcntl,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
from test_transfer_dos import (ROOT,BINARY,owned_file,ObservedModem,timestamp,
 offset_after,audit_enigma_server,SAMPLER,config_image,RATES,modem_fixture,
 directory_image,directory_prm,accounting_check)
from audit_zmodem import audit_batch,audit_controls,self_check

def parse_files(values):
 result={}
 for value in values:
  name,sep,path=value.partition('=');name=name.upper()
  assert sep and re.fullmatch(r'[A-Z0-9_]{1,8}\.BIN',name),'Use unique explicit DOS83 BIN filenames'
  assert name not in result,'Duplicate fixture filename'
  stem=name.split('.')[0];assert stem not in ('CON','AUX','PRN','NUL') and not re.fullmatch(r'(COM|LPT)[1-9]',stem)
  result[name]=owned_file(path);assert result[name].is_file()
 assert result,'At least one owned source, empty files allowed'
 return result

async def run(a):
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Runtime does not match freeze'
 assert a.label.replace('-','').replace('_','').isalnum() and a.name.replace('-','').isalnum()
 fixtures=parse_files(a.file);expected={name:path.read_bytes() for name,path in fixtures.items()};payload_hash={name:hashlib.sha256(data).hexdigest() for name,data in expected.items()}
 output=ROOT/'build/bbs-lab/results'/a.name/a.label;output.mkdir(parents=True,exist_ok=True)
 assert not [p for p in output.iterdir() if p.name!='.lock'],'Use a fresh label; previous artifacts are preserved'
 send=output/'SEND';target=output/'RECV';send.mkdir();target.mkdir()
 source_stats={}
 if a.mode=='upload':
  assert a.server_directory and a.server_audit_command_json,'Upload requires owned server directory and official metadata audit command'
  directory=owned_file(a.server_directory)
  for name,data in expected.items():
   assert not (directory/name).exists(),'Server target collision: '+name
   source=send/name;source.write_bytes(data);st=source.stat();source_stats[name]=(st.st_ino,st.st_size,st.st_mtime_ns)
 assert a.keys.lower().split().count('f2')>=2,'Keys must explicitly select DOS ZMODEM with F2'
 fixture=None;directory_fixture=None;automatic=a.dial_fixture or a.directory_fixture
 command=f'TERMINAL COM{a.com} {a.baud} {a.flow}'
 if a.config_fixture or automatic:
  fixture=config_image(port=a.com,baud=RATES.index(a.baud),soft=0,hard=int(a.flow=='HARD'),normal=7)
  if automatic:
   modem=bytearray(modem_fixture(timeout=45))
   for at,size in ((0,10),(0x174,32),(0x194,12),(0x1ae,10)):modem[at:at+size]=fixture[at:at+size]
   fixture=bytes(modem)
  if a.directory_fixture:
   fixture=directory_prm(port=1,baud=6,soft=0,hard=int(a.flow=='HARD'));directory_fixture=directory_image(entry=a.entry,target=f'lab.local:{a.port}'.encode(),port=a.com,baud=RATES.index(a.baud));(output/'TEST.DIR').write_bytes(directory_fixture)
  (output/'TEST.PRM').write_bytes(fixture);command='TERMINAL @D:\\TEST.PRM'
  if a.directory_fixture:command+=' /E:D:\\TEST.DIR'+('' if a.directory_browser else f' /N:{a.entry}')
  elif a.dial_fixture:command+=f' /D:lab.local:{a.port}'
 command='C:\\'+command
 sampler=SAMPLER;base=(0x3f8,0x2f8,0x3e8,0x2e8)[a.com-1]
 for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(base+off))
 (output/'sampler.asm').write_text(sampler);subprocess.run(['nasm','-fbin',str(output/'sampler.asm'),'-o',str(output/'SNAP.COM')],check=True)
 modem=ObservedModem('127.0.0.1',a.port,output,soft=False,baud=a.baud);server=await asyncio.start_server(modem.accept,'127.0.0.1',0);port=server.sockets[0].getsockname()[1]
 prefix='p1000 ' if automatic else 'p1000 a t d enter '
 if a.directory_browser:
  assert a.directory_fixture and a.entry<=10;prefix='p500 '+('down p100 '*(a.entry-1))+'enter p1000 '
 keys=prefix+a.keys+f' p{a.wait*1000} a-x'
 serial='\n'.join('serial'+str(i)+'='+(f'nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1' if i==a.com else 'disabled') for i in range(1,5))
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
mount c "{BINARY.parent}"
mount d "{output}"
d:
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
 (output/'dosbox.conf').write_text(config)
 if a.name=='enigma':
  server_log=ROOT/'build/bbs-lab/enigma/source/logs/enigma-bbs.log'
  if server_log.exists():(output/'server-log-start.json').write_text(json.dumps({'byte_offset':server_log.stat().st_size})+'\n')
 start=time.monotonic()
 with (output/'dosbox.log').open('w') as log:
  process=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(output/'dosbox.conf'),cwd=output,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log)
  try:code=await asyncio.wait_for(process.wait(),a.timeout)
  except asyncio.TimeoutError:
   process.terminate()
   try:await asyncio.wait_for(process.wait(),5)
   except asyncio.TimeoutError:process.kill();await process.wait()
   code=-1
 server.close()
 for task,writer in list(modem.clients):writer.close();task.cancel()
 if modem.clients:
  try:await asyncio.wait_for(asyncio.gather(*(task for task,writer in list(modem.clients)),return_exceptions=True),3)
  except asyncio.TimeoutError:pass
 # Python3.14 waits for accepted clients here; DOSBox abnormal exits can leave
 # its connection tracked. Close only this owned listener's clients first.
 if hasattr(server,'close_clients'):server.close_clients()
 try:await asyncio.wait_for(server.wait_closed(),3)
 except asyncio.TimeoutError:pass
 try:await asyncio.wait_for(modem.done.wait(),2)
 except asyncio.TimeoutError:pass
 modem.save();(output/'trace.json').write_text(json.dumps(modem.trace,indent=2)+'\n')
 before=(output/'BEFORE.BIN').read_bytes() if (output/'BEFORE.BIN').exists() else b'';after=(output/'AFTER.BIN').read_bytes() if (output/'AFTER.BIN').exists() else b'';screen=(output/'SCREEN.BIN').read_bytes() if (output/'SCREEN.BIN').exists() else b''
 checks=dict(DOS_normal_exit=code==0 and (output/'PASS.TXT').exists() and not (output/'FAIL.TXT').exists(),hardware_restored=len(before)==42 and before==after,screen_captured=len(screen)==4000,bbs_connected=any(e['kind']=='bbs-connected' for e in modem.events),binary_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,payload_fixture_unchanged=all(path.read_bytes()==expected[name] for name,path in fixtures.items()),observed_decoded_offsets_match=modem.bbs_offset==len(modem.display) and modem.dos_offset==len(modem.keyboard))
 if fixture is not None:checks['configuration_unchanged']=(output/'TEST.PRM').read_bytes()==fixture
 if directory_fixture is not None:checks['directory_accounting_exact']=accounting_check(directory_fixture,(output/'TEST.DIR').read_bytes(),a.entry)
 errors=[];audit=None
 try:
  direction='bbs' if a.mode=='download' else 'dos';stream=bytes(modem.display if direction=='bbs' else modem.keyboard);start_input=bytes.fromhex(a.start_input_hex)
  # Locate source-matching frames first, then corroborate a real DOS command
  # before those frames using the observed cross-direction chronology.
  audit=audit_batch(stream,expected);first_time=timestamp(modem.trace,direction,audit['start']);serial_cut=offset_after(modem.trace,'dos',first_time)
  serial_prefix=bytes(modem.keyboard[:serial_cut]) if serial_cut is not None else bytes(modem.keyboard)
  if direction=='dos':serial_prefix=bytes(modem.keyboard[:audit['start']])
  request_at=serial_prefix.rfind(start_input);assert request_at>=0,'No actual BBS transfer command before ZFILE'
  request_time=timestamp(modem.trace,'dos',request_at);assert first_time>=request_time
  minimum=offset_after(modem.trace,direction,request_time) or 0;audit=audit_batch(stream,expected,minimum)
  end_time=timestamp(modem.trace,direction,audit['end']-1)
  dos_tail_offset=offset_after(modem.trace,'dos',end_time) or len(modem.keyboard)
  post_input=bytes.fromhex(a.post_input_hex);post_at=bytes(modem.keyboard).find(post_input,dos_tail_offset);assert post_at>=0,'No actual post-batch menu input'
  post_time=timestamp(modem.trace,'dos',post_at)
  other=bytes(modem.keyboard if direction=='bbs' else modem.display)
  audit['controls']=audit_controls(audit,other,modem.trace,direction,post_time,False)
  checks['ZFILE_data_CRC_ZEOF_ZFIN_OO_confirmed']=True
  bbs_tail_offset=offset_after(modem.trace,'bbs',post_time);assert bbs_tail_offset is not None
  tail=bytes(modem.display[bbs_tail_offset:]);pos=0
  for needle in a.post_menu:
   pos=tail.find(needle.encode('ascii'),pos);assert pos>=0,('Missing ordered postbatch response',needle);pos+=len(needle)
  checks['posttransfer_actual_menu_input_response']=True
  checks['actual_validated_protocol']=True
  for item in audit['files']:
   name=item['name'];data=item.pop('source')
   if a.mode=='download':checks['DOS_exact_length_'+name]=(target/name).is_file() and (target/name).read_bytes()==data
   else:
    source=send/name;st=source.stat()
    checks['DOS_immutable_'+name]=source.read_bytes()==data and (st.st_ino,st.st_size,st.st_mtime_ns)==source_stats[name]
    destination=owned_file(a.server_directory)/name
    checks['server_exact_length_'+name]=destination.is_file() and destination.read_bytes()==data
  if a.mode=='download':checks['only_expected_received_files']={p.name.upper() for p in target.iterdir()}==set(expected)
 except Exception as error:errors.append(str(error));checks['actual_validated_protocol']=False
 if a.server_audit_command_json:
  argv=json.loads(a.server_audit_command_json);assert isinstance(argv,list) and argv and all(isinstance(s,str) for s in argv)
  result=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True);(output/'server-audit.stdout').write_text(result.stdout);(output/'server-audit.stderr').write_text(result.stderr)
  try:metadata=json.loads(result.stdout);checks['server_metadata_audit']=result.returncode==0 and metadata.get('passed') is True
  except ValueError:checks['server_metadata_audit']=False
 elif a.mode=='upload':checks['server_metadata_audit']=False
 if a.name=='enigma':
  try:checks['unique_server_session_and_ordered_menus']=audit_enigma_server(output,a.mode)['passed']
  except Exception as error:errors.append('Server session audit: '+str(error));checks['unique_server_session_and_ordered_menus']=False
 checks['no_leftover_staging']=not list(output.rglob('PCRX.$$$'))
 (output/'screen.txt').write_text('\n'.join(screen[r*160:r*160+160:2].decode('cp437') for r in range(25))+'\n')
 if audit:
  # A failed acknowledgement/menu check can leave the raw payload attached.
  # Retain the failed audit without letting bytes serialization hide result.json.
  for item in audit.get('files',[]):item.pop('source',None)
  (output/'protocol.json').write_text(json.dumps(audit,indent=2)+'\n')
 confirmed=bool(audit and audit.get('controls') and audit.get('finish'))
 result=dict(passed=all(checks.values()),standard_completion=confirmed,name=a.name,label=a.label,mode=a.mode,binary_sha256=a.sha256,payload_sha256=payload_hash,checks=checks,errors=errors,seconds=round(time.monotonic()-start,3),keys=keys,command=command,serial=dict(com=a.com,baud=a.baud,flow=a.flow),scope='Actual local BBS ZMODEM via unchanged observed Hayes/Telnet bridge and production DOS F2/AltR/AltS/UART/files. Independent passive header/data CRC, verified offsets, ZEOF and ZFIN/OO, opposite headers and post-transfer menu input/response. Synthetic media, no injected protocol replies or physical modem claim.')
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1

def main():
 if '--self-check' in sys.argv:self_check();return 0
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('name',choices=['synchronet','enigma']);p.add_argument('--port',type=int,required=True)
 p.add_argument('--label',required=True);p.add_argument('--sha256',required=True)
 p.add_argument('--mode',choices=['upload','download'],required=True)
 p.add_argument('--file',action='append',required=True,help='DOSNAME.BIN=owned build/fixture path')
 p.add_argument('--keys',required=True);p.add_argument('--start-input-hex',required=True)
 p.add_argument('--post-input-hex',required=True);p.add_argument('--post-menu',action='append',required=True)
 p.add_argument('--server-directory');p.add_argument('--server-audit-command-json')
 p.add_argument('--wait',type=int,default=3);p.add_argument('--timeout',type=int,default=180)
 p.add_argument('--com',type=int,choices=range(1,5),default=2);p.add_argument('--baud',type=int,choices=RATES,default=19200)
 p.add_argument('--flow',choices=['HARD','NONE'],default='HARD')
 p.add_argument('--config-fixture',action='store_true');p.add_argument('--dial-fixture',action='store_true')
 p.add_argument('--directory-fixture',action='store_true');p.add_argument('--directory-browser',action='store_true')
 p.add_argument('--entry',type=int,choices=range(1,201),default=3);a=p.parse_args()
 assert bytes.fromhex(a.start_input_hex) and bytes.fromhex(a.post_input_hex)
 assert a.port=={'synchronet':23231,'enigma':23233}[a.name],'Only the matching owned loopback BBS endpoint'
 output=ROOT/'build/bbs-lab/results'/a.name/a.label;output.mkdir(parents=True,exist_ok=True)
 with (output/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not [item for item in output.iterdir() if item.name!='.lock'],'Use a fresh label; existing evidence is never overwritten'
  try:return asyncio.run(run(a))
  except Exception as error:
   result=dict(passed=False,error=type(error).__name__+': '+str(error),label=a.label,mode=a.mode,binary_sha256=a.sha256)
   (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 1
if __name__=='__main__':raise SystemExit(main())
