#!/usr/bin/env python3
"""Actual local BBS file transfer through DOS and the existing Hayes/Telnet modem.

This harness never simulates a transfer peer or injects a terminal response.
Only owned synthetic files under ignored build/ are accepted as payloads.
"""
import argparse,asyncio,binascii,fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from modem import Modem,Telnet
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'standalone'))
from test_terminal import SAMPLER
from terminal_config_fixtures import image as config_image,RATES
from modem_fixtures import fixture as modem_fixture
from directory_fixtures import directory as directory_image,prm as directory_prm
from directory_test_support import accounting_check
BINARY=ROOT/'build/terminal/TERMINAL.EXE'

def owned_file(value):
 p=Path(value).resolve();assert p.is_relative_to((ROOT/'build').resolve()),'Only owned ignored build/ fixtures permitted';return p
class ReadObserver:
 def __init__(self,reader,callback):self.reader,self.callback=reader,callback
 async def read(self,n):
  data=await self.reader.read(n)
  if data:self.callback(data)
  return data
class ObservedModem(Modem):
 """Observe real StreamReader chunks without changing parent modem behavior."""
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.trace=[];self.audit_codec=Telnet(self.baud);self.dos_offset=0;self.bbs_offset=0;self.clients=set()
 def observe_dos(self,data):
  self.trace.append(dict(seconds=time.monotonic()-self.start,direction='dos',offset=self.dos_offset,size=len(data)));self.dos_offset+=len(data)
 def observe_bbs(self,data):
  decoded,_=self.audit_codec.feed(data)
  self.trace.append(dict(seconds=time.monotonic()-self.start,direction='bbs',offset=self.bbs_offset,size=len(decoded)));self.bbs_offset+=len(decoded)
 async def accept(self,reader,writer):
  task=asyncio.current_task();pair=(task,writer);self.clients.add(pair)
  try:return await super().accept(ReadObserver(reader,self.observe_dos),writer)
  finally:self.clients.discard(pair)
 async def downstream(self,reader,upstream,serial):return await super().downstream(ReadObserver(reader,self.observe_bbs),upstream,serial)

def timestamp(trace,direction,offset):
 hits=[e for e in trace if e['direction']==direction and e['offset']<=offset<e['offset']+e['size']]
 assert hits,('No observed chunk for offset',direction,offset);return hits[0]['seconds']
def offset_after(trace,direction,seconds):
 hits=[e['offset'] for e in trace if e['direction']==direction and e['seconds']>=seconds]
 return min(hits) if hits else None

def packet_at(data,at,crc):
 if at>=len(data) or data[at] not in (1,2):return None
 size=128 if data[at]==1 else 1024;end=at+3+size+(2 if crc else 1)
 if end>len(data) or data[at+1]^data[at+2]!=255:return None
 body=data[at+3:at+3+size];trailer=data[at+3+size:end]
 expected=binascii.crc_hqx(body,0).to_bytes(2,'big') if crc else bytes([sum(body)&255])
 if trailer!=expected:return None
 return dict(offset=at,end=end,number=data[at+1],size=size,payload=body,crc=crc,sha256=hashlib.sha256(data[at:end]).hexdigest())
def audit_protocol(data,expected,*,minimum=0):
 """Locate a validated seq1 frame, then require strict frames through EOT.

No tail-size policy is assumed: the real sender chooses128/1024 and padding.
Retransmitted identical sequence numbers contribute payload only once.
"""
 first=None
 for at in range(minimum,min(len(data),minimum+1048576)):
  if data[at] not in (1,2):continue
  for crc in (True,False):
   candidate=packet_at(data,at,crc)
   if candidate and candidate['number']==1 and candidate['payload'][:min(len(expected),candidate['size'])]==expected[:candidate['size']]:first=candidate;break
  if first:break
 if first is None:raise AssertionError('No integrity-validated sequence1 frame matching fixture after start')
 frames=[];accepted=[];at=first['offset'];number=1;previous=None
 while at<len(data) and data[at] in (1,2):
  item=packet_at(data,at,first['crc']);assert item,('Malformed frame inside transfer',at)
  if item['number']==number&255:accepted.append(item);number+=1;previous=item
  else:assert previous and item['number']==previous['number'] and item['payload']==previous['payload'],'Bad sequence/retransmission'
  frames.append(item);at=item['end']
 assert at<len(data) and data[at]==4,('Missing EOT after valid frames',at)
 end=at
 while end<len(data) and data[end]==4:end+=1
 payload=b''.join(f['payload'] for f in accepted)
 assert payload[:len(expected)]==expected,'Transferred source prefix differs'
 assert payload[len(expected):]==b'\x1a'*(len(payload)-len(expected)),'Nonpadding bytes after source'
 assert len(payload)>=len(expected),'Truncated source'
 return dict(start=first['offset'],end=end,eot_start=at,eots=end-at,crc=first['crc'],frames=[{k:v for k,v in f.items() if k!='payload'} for f in frames],accepted_blocks=len(accepted),padded_payload=payload)

def audit_controls(audit,sender_stream,opposite,trace,sender,post_time,ack_timeout=11):
 """Match ACK/NAK to complete attempts/EOT before the next sender event.

Times are observed TCP-read chunks, not individual UART-byte timestamps.
Automatic menu text after the matched final ACK is outside protocol scope.
 """
 other='dos' if sender=='bbs' else 'bbs';cursor=0;records=[]
 def response(lower,upper,required):
  nonlocal cursor
  upper=min(upper,lower+ack_timeout);items=[]
  while cursor<len(opposite):
   t=timestamp(trace,other,cursor)
   if t<lower:
    assert opposite[cursor] in (6,0x15,0x18),('Unexpected intervening protocol byte',opposite[cursor],cursor)
    cursor+=1;continue
   if t>=upper:break
   value=opposite[cursor];items.append((cursor,value,t));cursor+=1
   # A response completes this attempt; later status/menu bytes belong after
   # finalACK only, never a substitute for a missing response.
   assert value in (6,0x15,0x18),('Unexpected byte before transfer response',value,items[-1][0])
   break
  if required:assert items and items[0][1]==6,'Missing required ACK before next frame/menu/deadline'
  return items
 frames=audit['frames'];first_complete=timestamp(trace,sender,frames[0]['end']-1)
 while cursor<len(opposite) and timestamp(trace,other,cursor)<first_complete:cursor+=1
 for i,frame in enumerate(frames):
  lower=timestamp(trace,sender,frame['end']-1)
  next_offset=frames[i+1]['offset'] if i+1<len(frames) else audit['eot_start']
  upper=timestamp(trace,sender,next_offset)
  retry=i+1<len(frames) and frames[i+1]['number']==frame['number']
  got=response(lower,upper,not retry)
  records.append(dict(kind='frame',number=frame['number'],response=got[0][1] if got else None,retry=retry))
 for offset in range(audit['eot_start'],audit['end']):
  lower=timestamp(trace,sender,offset)
  upper=timestamp(trace,sender,offset+1) if offset+1<audit['end'] else post_time
  got=response(lower,upper,offset+1==audit['end'])
  records.append(dict(kind='EOT',response=got[0][1] if got else None))
 return records

def self_check():
 from tempfile import TemporaryDirectory
 body=bytes(range(128));packet=b'\x01\x01\xfe'+body+binascii.crc_hqx(body,0).to_bytes(2,'big')
 # Deliberate chunk timings represent complete data, ACK, EOT and menu input.
 source=packet+b'\x04';audit=audit_protocol(source,body)
 art=b'ANSI art \x01\x01\xfeSAUCE00';assert audit_protocol(art+source,body)['start']==len(art)
 checksum=b'\x01\x01\xfe'+body+bytes([sum(body)&255])+b'\x04';assert audit_protocol(checksum,body)['crc'] is False
 def traces(other):return [dict(direction='bbs',offset=0,size=len(packet),seconds=1),dict(direction='bbs',offset=len(packet),size=1,seconds=3)]+[dict(direction='dos',offset=i,size=1,seconds=t) for i,(_,t) in enumerate(other)]
 good=[(6,2),(6,4)];assert audit_controls(audit,source,bytes(v for v,t in good),traces(good),'bbs',5)
 negatives=[[(6,2),(ord('x'),2.5),(6,4)],[(6,2)],[(6,2),(ord('M'),4),(6,4.5)],[(6,2),(6,6)],[(ord('x'),2),(6,2.5),(6,4)]]
 for events in negatives:
  try:audit_controls(audit,source,bytes(v for v,t in events),traces(events),'bbs',5)
  except AssertionError:pass
  else:raise AssertionError(('Invalid controls accepted',events))
 try:audit_protocol(packet+b'X\x04',body)
 except AssertionError:pass
 else:raise AssertionError('Unexpected intervening sender byte accepted')
 retrans=packet+packet+b'\x04';a=audit_protocol(retrans,body);assert a['accepted_blocks']==1 and len(a['frames'])==2
 t=[dict(direction='bbs',offset=0,size=len(packet),seconds=1),dict(direction='bbs',offset=len(packet),size=len(packet),seconds=3),dict(direction='bbs',offset=2*len(packet),size=1,seconds=5),dict(direction='dos',offset=0,size=1,seconds=2),dict(direction='dos',offset=1,size=1,seconds=4),dict(direction='dos',offset=2,size=1,seconds=6)]
 assert audit_controls(a,retrans,b'\x15\x06\x06',t,'bbs',7)
 print('Passive auditor:10 declared positive/negative regression groups passed')

def audit_enigma_server(output,mode,end_offset=None):
 """Retain bounded owned-server evidence for this one recorded DOS session."""
 output=Path(output);boundary=json.loads((output/'server-log-start.json').read_text());start=boundary['byte_offset']
 stock_log=ROOT/'build/bbs-lab/enigma/source/logs/enigma-bbs.log'
 log=owned_file(boundary.get('path',str(stock_log)))
 assert boundary.get('inode',log.stat().st_ino)==log.stat().st_ino,'Server log rotated during session'
 full=log.read_bytes();end=len(full) if end_offset is None else end_offset
 assert isinstance(end,int) and start<=end<=len(full),'Invalid recorded server log boundary'
 raw=full[start:end]
 (output/'server-session.jsonl').write_bytes(raw)
 rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
 connected=[r for r in rows if r.get('msg','').startswith('Client connected on node')]
 authenticated=[r for r in rows if r.get('msg')=='User "loclab" successfully logged in']
 sessions={r.get('sessionId') for r in connected};session=next(iter(sessions)) if len(sessions)==1 else None
 own=[r for r in rows if session is not None and r.get('sessionId')==session]
 menus=[r['menuName'] for r in own if r.get('menuName')]
 executions=[i for i,r in enumerate(own) if r.get('msg')=='Executing external protocol']
 exits=[i for i,r in enumerate(own) if r.get('msg')=='Process exited' and r.get('exitCode')==0]
 ordered=False
 if len(executions)==1 and len(exits)==1 and executions[0]<exits[0]:
  before=[r.get('menuName') for r in own[:executions[0]]]
  after=[r.get('menuName') for r in own[exits[0]+1:]]
  try:ordered='fileTransferProtocolSelection' in before and after.index('fileBaseMainMenu')<after.index('fileBaseListEntries')
  except ValueError:pass
 checks=dict(unique_new_connection=len(connected)==1 and len(sessions)==1,unique_authenticated_session=len(authenticated)==1 and authenticated[0].get('sessionId')==session,stock_external_protocol_success=len(executions)==1 and len(exits)==1,ordered_protocol_return_and_file_list=ordered)
 if log!=stock_log:
  checks['experimental_external_protocol_success']=checks.pop('stock_external_protocol_success')
 result=dict(passed=all(checks.values()),checks=checks,server_log=str(log),stock_server=log==stock_log,session_id=session,mode=mode,menus=menus,log_byte_start=start,log_byte_end=start+len(raw),scope='Owned real ENiGMA server log slice from recorded pre-run offset; one connection/login, external protocol exit, later file list; stock/experimental identity recorded separately. No additional connection created by this audit.')
 (output/'server-session-audit.json').write_text(json.dumps(result,indent=2)+'\n');return result

async def run(a):
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Runtime does not match freeze'
 assert a.label.replace('-','').replace('_','').isalnum() and a.name.replace('-','').isalnum()
 payload_path=owned_file(a.payload_file);payload=payload_path.read_bytes();payload_hash=hashlib.sha256(payload).hexdigest();assert payload,'This initial real-BBS audit requires a nonempty known fixture'
 output=ROOT/'build/bbs-lab/results'/a.name/a.label;output.mkdir(parents=True,exist_ok=True)
 assert not [p for p in output.iterdir() if p.name!='.lock'],'Use a fresh label; previous artifacts are preserved'
 server_path=owned_file(a.server_file) if a.server_file else None
 if a.mode=='upload' and server_path:assert not server_path.exists(),'Server upload destination must be fresh; use server preparation API'
 source=output/'SEND.BIN';target=output/'PCXTEST.BIN';assert not target.exists(),'Owned DOS target already exists'
 if a.mode=='upload':source.write_bytes(payload);source_stat=source.stat()
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
 checks=dict(DOS_normal_exit=code==0 and (output/'PASS.TXT').exists() and not (output/'FAIL.TXT').exists(),hardware_restored=len(before)==42 and before==after,screen_captured=len(screen)==4000,bbs_connected=any(e['kind']=='bbs-connected' for e in modem.events),binary_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,payload_fixture_unchanged=payload_path.read_bytes()==payload,observed_decoded_offsets_match=modem.bbs_offset==len(modem.display) and modem.dos_offset==len(modem.keyboard))
 if fixture is not None:checks['configuration_unchanged']=(output/'TEST.PRM').read_bytes()==fixture
 if directory_fixture is not None:checks['directory_accounting_exact']=accounting_check(directory_fixture,(output/'TEST.DIR').read_bytes(),a.entry)
 errors=[];audit=None
 try:
  direction='bbs' if a.mode=='download' else 'dos';stream=bytes(modem.display if direction=='bbs' else modem.keyboard);start_input=bytes.fromhex(a.start_input_hex)
  # Locate source-matching frames first, then corroborate a real DOS command
  # before those frames using the observed cross-direction chronology.
  audit=audit_protocol(stream,payload);first_time=timestamp(modem.trace,direction,audit['start']);serial_cut=offset_after(modem.trace,'dos',first_time)
  serial_prefix=bytes(modem.keyboard[:serial_cut]) if serial_cut is not None else bytes(modem.keyboard)
  if direction=='dos':serial_prefix=bytes(modem.keyboard[:audit['start']])
  request_at=serial_prefix.rfind(start_input);assert request_at>=0,'Actual BBS transfer-start input not observed before frames'
  request_time=timestamp(modem.trace,'dos',request_at);assert first_time>=request_time,'Frames predate transfer command'
  # Explicitly rescan only after the requested command, excluding prior art.
  minimum=offset_after(modem.trace,direction,request_time) or 0;audit=audit_protocol(stream,payload,minimum=minimum)
  end_time=timestamp(modem.trace,direction,audit['end']-1)
  # Menu commands must be after EOT, and server responses after those commands.
  dos_tail_offset=offset_after(modem.trace,'dos',end_time) or len(modem.keyboard);post_input=bytes.fromhex(a.post_input_hex);post_at=bytes(modem.keyboard).find(post_input,dos_tail_offset);assert post_at>=0,'No actual post-transfer menu input'
  post_time=timestamp(modem.trace,'dos',post_at)
  other=bytes(modem.keyboard if direction=='bbs' else modem.display)
  audit['controls']=audit_controls(audit,stream,other,modem.trace,direction,post_time)
  checks['actual_frame_and_final_EOT_ACKs']=True;checks['EOT_bounded']=1<=audit['eots']<=10
  bbs_tail_offset=offset_after(modem.trace,'bbs',post_time)
  assert bbs_tail_offset is not None,'No server response after post-transfer input';tail=bytes(modem.display[bbs_tail_offset:])
  pos=0
  for needle in a.post_menu:
   pos=tail.find(needle.encode('ascii'),pos);assert pos>=0,('Missing ordered post-transfer BBS response',needle);pos+=len(needle)
  checks['posttransfer_actual_menu_input_response']=True
  padded=audit.pop('padded_payload');checks['actual_validated_protocol']=True
  if a.mode=='download':checks['DOS_download_exact_accepted_blocks']=target.exists() and target.read_bytes()==padded
  else:
   st=source.stat();checks['DOS_source_unchanged']=source.read_bytes()==payload and (st.st_ino,st.st_size,st.st_mtime_ns)==(source_stat.st_ino,source_stat.st_size,source_stat.st_mtime_ns)
   if server_path:checks['server_uploaded_exact_accepted_blocks']=server_path.exists() and server_path.read_bytes()==padded
   else:checks['server_uploaded_exact_accepted_blocks']=False
  (output/'accepted-payload.bin').write_bytes(padded)
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
 checks['no_leftover_staging']=not (output/'PCRX.$$$').exists()
 (output/'screen.txt').write_text('\n'.join(screen[r*160:r*160+160:2].decode('cp437') for r in range(25))+'\n')
 if audit:
  # A failed acknowledgement/menu check can leave the raw payload attached.
  # Retain the failed audit without letting bytes serialization hide result.json.
  audit.pop('padded_payload',None)
  (output/'protocol.json').write_text(json.dumps(audit,indent=2)+'\n')
 result=dict(passed=all(checks.values()),name=a.name,label=a.label,mode=a.mode,binary_sha256=a.sha256,payload_sha256=payload_hash,checks=checks,errors=errors,seconds=round(time.monotonic()-start,3),keys=keys,command=command,serial=dict(com=a.com,baud=a.baud,flow=a.flow),scope='Actual local BBS protocol peer via unchanged Hayes/Telnet modem, real DOS AltR/AltS/files/UART. Passive frame/control audit, actual post-transfer menu interaction. Synthetic media; no physical CTS/DCD claim.')
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1

def main():
 if '--self-check' in sys.argv:self_check();return 0
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('name');p.add_argument('--port',type=int,required=True);p.add_argument('--label',required=True);p.add_argument('--sha256',required=True);p.add_argument('--mode',choices=['upload','download'],required=True);p.add_argument('--payload-file',required=True);p.add_argument('--keys',required=True);p.add_argument('--start-input-hex',required=True);p.add_argument('--post-input-hex',required=True);p.add_argument('--post-menu',action='append',required=True);p.add_argument('--server-file');p.add_argument('--server-audit-command-json');p.add_argument('--wait',type=int,default=3);p.add_argument('--timeout',type=int,default=150);p.add_argument('--com',type=int,choices=range(1,5),default=2);p.add_argument('--baud',type=int,choices=RATES,default=19200);p.add_argument('--flow',choices=['HARD','NONE'],default='HARD');p.add_argument('--config-fixture',action='store_true');p.add_argument('--dial-fixture',action='store_true');p.add_argument('--directory-fixture',action='store_true');p.add_argument('--directory-browser',action='store_true');p.add_argument('--entry',type=int,choices=range(1,201),default=3);a=p.parse_args()
 assert bytes.fromhex(a.start_input_hex) and bytes.fromhex(a.post_input_hex);output=ROOT/'build/bbs-lab/results'/a.name/a.label;output.mkdir(parents=True,exist_ok=True)
 with (output/'.lock').open('w') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);return asyncio.run(run(a))
if __name__=='__main__':raise SystemExit(main())
