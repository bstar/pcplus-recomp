#!/usr/bin/env python3
"""Production DOS remote filename selection -> X/YMODEM -> clipboard reuse.

Existing independent framing peers are reused; prompt/control boundaries are
strict. Test-only BIOS observers read keys/video, never product state or replies.
All file operations target fresh, owned synthetic fixture directories.
"""
import argparse,hashlib,json,os,socket,struct,subprocess,time
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_transfer_dos import Peer as ReceivePeer
from test_terminal_upload_dos import UploadPeer
from test_terminal_ymodem_dos import BatchPeer,file
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE';OUT=ROOT/'build/clipboard-transfer-dos'
def payload(n,seed=0):return bytes((i*37+seed)&255 for i in range(n))
def selection(names,mode,separator):
 return names[0].encode()+b'\r' if mode=='single' else b''.join(n.encode()+bytes([separator]) for n in names)+b'\r'
def recipes():
 rows=[]
 for protocol,direction,mode in [('XMODEM','rx','single'),('XMODEM','tx','single'),('YMODEM','rx','tagged'),('YMODEM','tx','all')]:
  catalog={'ONE.BIN':payload(12288,11),'TWO.BIN':payload(8197,73),'SKIP.BIN':payload(128,99)}
  if protocol=='YMODEM':catalog['ONE.BIN']=b''
  names=['ONE.BIN','TWO.BIN']+(['SKIP.BIN'] if mode=='tagged' else [])
  chosen=names[:1] if mode=='single' else names[:2];separator=32 if mode=='tagged' else 13
  rows.append(dict(name=protocol.lower()+'-'+direction+'-'+mode,protocol=protocol,direction=direction,mode=mode,separator=separator,names=names,chosen=chosen,catalog=catalog,post=selection(['TWO.BIN'] if mode=='single' else chosen,mode,separator)))
 for special in ['stale','prompt-cancel']:
  names=['OLD.ZIP','TWO.BIN'] if special=='stale' else ['ONE.BIN','TWO.BIN']
  rows.append(dict(name='xmodem-rx-'+special,protocol='XMODEM',direction='rx',mode='single',separator=13,names=names,chosen=['TWO.BIN'],catalog={'ONE.BIN':payload(12288,11),'TWO.BIN':payload(12288,73)},post=b'',special=special))
 return rows
class PromptMixin:
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.in_protocol=False;self.selections=[]
 def send(self,data):
  if self.in_protocol and self.recipe['direction']=='tx' and data==b'\x06':time.sleep(.35 if self.recipe['protocol']=='XMODEM' else .06)
  return super().send(data)
 def expect(self,data,timeout=25):
  got=bytearray();deadline=time.monotonic()+timeout
  while len(got)<len(data) and time.monotonic()<deadline and not self.stop.is_set():
   if not self.pending:self.receive();continue
   take=min(len(data)-len(got),len(self.pending));got.extend(self.pending[:take]);del self.pending[:take]
   assert data.startswith(got),('Unexpected prompt/response bytes',bytes(got),data)
  assert bytes(got)==data,('Missing exact prompt/response bytes',bytes(got),data)
  return bytes(got)
 def pick(self,names,mode,separator):
  packet=selection(names,mode,separator);at=len(self.wire)-len(self.pending);self.expect(packet)
  self.selections.append(dict(names=names,packet_hex=packet.hex(),wire_offset=at));self.log('remote-filename-packet',names=names,hex=packet.hex(),wire_offset=at)
  return names
 def ready(self):
  super().ready();r=self.recipe
  self.send(b'\x1b[2J\x1b[HFILE CATALOG\r\n '+b' '.join(n.lower().encode() for n in r['names'])+b'\r\nFile names: ')
  if r.get('special')=='stale':
   self.pick(['OLD.ZIP'],'single',13);self.send(b'\r\nNot found: OLD.ZIP\r\nFile names: ')
   self.checks['stale_remote_name_rejected_before_protocol']=True
  elif r.get('special')=='prompt-cancel':
   self.pick(['ONE.BIN'],'single',13)
   # One query sent during the local filename prompt must resume after Esc.
   # No transfer controls are tolerated before this actual application reply.
   time.sleep(.9);self.send(b'\x1b[5n');self.expect(b'\x1b[0n')
   self.checks['local_prompt_cancel_resumed_without_handshake']=True
   self.send(b'\r\nPrevious request canceled. File names: ')
  selected=self.pick(r['chosen'],r['mode'],r['separator'])
  items=[file(n,r['catalog'][n]) for n in selected]
  if r['protocol']=='XMODEM':
   data=items[0]['data'];r['data']=data;r['blocks']=[data[i:i+128] for i in range(0,len(data),128)];assert all(len(b)==128 for b in r['blocks'])
  else:r['files']=items
  self.checks['wire_selection_controls_payload']=True;self.in_protocol=True
 def control(self,expected,timeout=15):
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline and not self.stop.is_set():
   if not self.pending:self.receive();continue
   value=self.pending.pop(0);assert value in expected,('Unexpected protocol byte',value,expected)
   self.log('strict-DOS-control',value=value)
   if value==6 and self.recipe['direction']=='rx':time.sleep(.04)
   return value
  raise TimeoutError('Missing strict transfer control '+str(expected))
 def resume(self):
  self.in_protocol=False;self.log('protocol-complete')
  self.send(b'\x1b[2J\x1b[HAFTER TRANSFER\r\nFile names: \x1b[5n');self.expect(b'\x1b[0n')
  self.checks['posttransfer_actual_DSR']=True
  packet=self.recipe['post']
  if packet:
   at=len(self.wire)-len(self.pending);self.expect(packet);self.log('posttransfer-clipboard-packet',hex=packet.hex(),wire_offset=at)
   self.checks['retained_clipboard_reused']=True
  self.expect(b'ready');self.checks['posttransfer_keyboard']=True
  if not packet:self.checks['empty_clipboard_sent_no_bytes']=True
class PromptReceive(PromptMixin,ReceivePeer):pass
class PromptUpload(PromptMixin,UploadPeer):pass
class PromptBatch(PromptMixin,BatchPeer):pass

def keys(r):
 k=['p1500','a-=','p300','c','p250']
 for _ in r['names']:k+=['enter','p200']
 k+=['escape','p200']
 if r['mode']=='tagged':k+=['space','down','space','r','3','2','enter','p200']
 k+=[{'single':'s','all':'p','tagged':'t'}[r['mode']]]
 if r.get('special')=='stale':k+=['p600','s']
 # Alt-R while the clipboard owns keys must not start a nested transfer.
 k+=['p250','a-r','p250','escape','p300']
 if r.get('special')=='prompt-cancel':k+=['a-r','p300','a-=','c-pgup','p500','escape','p900','a-=','p250','s','p400','escape','p300']
 k+=['a-r' if r['direction']=='rx' else 'a-s','p300','a-=','c-pgup','p200']
 if r['protocol']=='YMODEM':k+=['f2','p200']
 target='RECV\\' if r['protocol']=='YMODEM' and r['direction']=='rx' else 'SEND\\*.BIN' if r['protocol']=='YMODEM' else ('RECV\\' if r['direction']=='rx' else 'SEND\\')+r['chosen'][0]
 for i,c in enumerate(target):
  if i and i%10==0:k+=['p100']
  k.append(c)
 k+=['enter','p1200','a-=','c-pgup','p','s','t','p9000','a-=','p350',{'single':'s','all':'p','tagged':'t'}[r['mode']],'p400','escape','p300','r','e','a','d','y','p600','a-x']
 return ' '.join(k)
def run_case(r,label,digest):
 out=OUT/label/r['name'];out.mkdir(parents=True,exist_ok=False);(out/'SEND').mkdir();(out/'RECV').mkdir()
 for n in ['SNAP','CLWATCH','KWATCH']:
  source=SAMPLER if n=='SNAP' else (ROOT/'standalone'/('clipboard_watch.asm' if n=='CLWATCH' else 'clipboard_transfer_keys.asm')).read_text()
  (out/(n+'.asm')).write_text(source);subprocess.run(['nasm','-fbin',str(out/(n+'.asm')),'-o',str(out/(n+'.COM'))],check=True)
 before_sources={}
 if r['direction']=='tx':
  for name in r['chosen']:
   p=out/'SEND'/name;p.write_bytes(r['catalog'][name]);st=p.stat();before_sources[name]=(st.st_ino,st.st_size,st.st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest())
 if r['protocol']=='YMODEM':peer=PromptBatch(r,out/'RECV')
 elif r['direction']=='rx':peer=PromptReceive(r,destination=out/'RECV'/r['chosen'][0])
 else:peer=PromptUpload(r)
 peer.thread.start();recipe=keys(r)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[serial]\nserial1=nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1\nserial2=disabled\nserial3=disabled\nserial4=disabled\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{out}"\nd:\nSNAP B\nCLWATCH T\nKWATCH T\nADDKEY {recipe}\nC:\\TERMINAL COM1 38400 8N1 HARD\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto capture\n:fail\necho FAIL>FAIL.TXT\n:capture\nSNAP S\nKWATCH\nif errorlevel 1 goto key_failed\ngoto key_done\n:key_failed\necho FAIL>FAIL.TXT\n:key_done\nCLWATCH\nif errorlevel 1 goto clip_failed\ngoto clip_done\n:clip_failed\necho FAIL>FAIL.TXT\n:clip_done\nSNAP A\nexit\n'''
 (out/'dosbox.conf').write_text(config);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest
 with (out/'dosbox.log').open('w') as log:
  result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=55)
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.server.close();peer.thread.join(2)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 raw=read('KWATCH.BIN');events=[]
 if len(raw)==5254:
  magic,count,overflow=struct.unpack_from('<3H',raw);assert magic==0x4b57 and count<=32 and not overflow
  for i in range(count):
   at=6+i*164;key,tick=struct.unpack_from('<2H',raw,at);events.append(dict(key=key,tick=tick,header=raw[at+4:at+84].decode('cp437'),footer=raw[at+84:at+164].decode('cp437')))
 active=[e for e in events if e['footer'].startswith((' Receiving',' Sending'))]
 probes={e['key'] for e in active};ascii_probes={e['key']&255 for e in active}
 before,after,screen=read('BEFORE.BIN'),read('AFTER.BIN'),read('SCREEN.BIN');checks=dict(peer.checks)
 checks.update(DOS_normal_exit=result.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(before)==42 and before==after,no_peer_errors=not peer.errors,actual_remote_selection=bool(peer.selections),binary_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest,BIOS_key_observer_collected=len(raw)==5254,active_protocol_received_both_local_hotkeys=0x8300 in probes and bool(probes&{0x8400,0x84e0}),active_protocol_received_paste_keys={ord('p'),ord('s'),ord('t')}<=ascii_probes,no_clipboard_window_on_active_key_reads=bool(active) and all('Filename Clipboard' not in e['header'] for e in active),clipboard_owns_nested_AltR=any(e['key']==0x1300 and 'Filename Clipboard' in e['header'] and i+1<len(events) and events[i+1]['key']&255==27 and 'Filename Clipboard' in events[i+1]['header'] and not events[i+1]['footer'].startswith((' Download:',' Upload:',' YMODEM')) for i,e in enumerate(events)),local_filename_prompt_ignored_clipboard_hotkeys=any(e['key']==0x8300 and e['footer'].startswith((' Download:',' Upload:',' YMODEM')) for e in events),posttransfer_DSR=bool(checks.get('posttransfer_actual_DSR')),posttransfer_keyboard=bool(checks.get('posttransfer_keyboard')),updated_live_screen_restored=len(screen)==4000 and screen[:28:2]==b'AFTER TRANSFER')
 if r['direction']=='rx':
  expected={n:r['catalog'][n] for n in r['chosen']};checks['exact_received_tree']={p.name:p.read_bytes() for p in (out/'RECV').iterdir()}==expected
 else:checks['unchanged_source_content_and_metadata']=set(p.name for p in (out/'SEND').iterdir())==set(before_sources) and all((p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest())==before_sources[p.name] for p in (out/'SEND').iterdir())
 checks['required_transfer_completion']=bool(checks.get('complete_EOT_handshake')) if r['protocol']=='XMODEM' and r['direction']=='rx' else bool(checks.get('exact_source_and_padding') and checks.get('EOT_NAK_then_ACK')) if r['protocol']=='XMODEM' else bool(checks.get('batch_end_ACK'))
 checks['no_transfer_staging_files']=not any(p.name.upper().startswith(('PCRX.','PCYM.')) for p in out.rglob('*'))
 clip=read('CWATCH.BIN');frames=[]
 if len(clip)==10246:
  magic,count,ticks=struct.unpack_from('<3H',clip);assert magic==0x434c and count<=32
  frames=[clip[6+i*320:6+(i+1)*320] for i in range(count)];checks['independent_clipboard_observer']=ticks>3
 else:checks['independent_clipboard_observer']=False
 if not r['post']:checks['empty_list_paste_attempt_observed']=any(b'No selected filenames' in f[240:] for f in frames)
 for name,data in [('serial.bin',peer.wire),('peer.bin',peer.sent)]:(out/name).write_bytes(data)
 for name,data in [('events.json',peer.events),('key-events.json',events),('selections.json',peer.selections)]: (out/name).write_text(json.dumps(data,indent=2)+'\n')
 result=dict(passed=all(checks.values()),case=r['name'],protocol=r['protocol'],direction=r['direction'],checks=checks,errors=peer.errors,binary_sha256=digest,keys=recipe,observed_keys=events,selections=peer.selections,scope='Actual DOS terminal/BIOS/UART/files; strict independent remote prompt + X/YMODEM peers. External BIOS key/video observers, no product callbacks/state reads or synthesized application replies. Owned fixtures; no physical modem or stock BBS proof.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--sha256',required=True);p.add_argument('--case',action='append',default=[]);a=p.parse_args();assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest==a.sha256,'Explicit frozen runtime does not match';rows=[]
 for r in recipes():
  if not a.case or r['name'] in a.case:rows.append(run_case(r,a.label,digest))
 assert rows
 result=dict(passed=all(r['passed'] for r in rows),binary_sha256=digest,cases=rows,sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'standalone/clipboard_transfer_keys.asm',ROOT/'standalone/clipboard_watch.asm',ROOT/'standalone/test_terminal_transfer_dos.py',ROOT/'standalone/test_terminal_upload_dos.py',ROOT/'standalone/test_terminal_ymodem_dos.py',ROOT/'standalone/test_terminal.py']})
 (OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']
if __name__=='__main__':main()
