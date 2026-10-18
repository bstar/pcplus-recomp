#!/usr/bin/env python3
"""Actual DOS AltG character snapshots, independent ANSI row/byte oracle.

Only synthetic owned media. Real BIOS keys, UART, renderer, DOS append and IRQ
cleanup; no product callbacks/replies mocked. Actual UART NUL does not render:
physical-NUL conversion belongs to separate native unit tests, not this proof.
"""
import argparse,fcntl,hashlib,json,os,socket,subprocess,time
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_transfer_dos import Peer as TerminalPeer
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE';OUT=ROOT/'build/terminal-snapshot-dos'
SEED=b'OLDER\x1aSCREEN RECORD\r\n';CURSOR=(7,13)
META=r'''bits 16
org 100h
mov ah,3
xor bh,bh
int 10h
mov [data],dx
mov [data+2],cx
mov ah,0fh
int 10h
mov [data+4],ax
mov [data+6],bh
mov dx,name
xor cx,cx
mov ah,3ch
int 21h
jc fail
mov bx,ax
mov dx,data
mov cx,7
mov ah,40h
int 21h
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
fail:
mov ax,4c01h
int 21h
name db 'BIOS.BIN',0
data times 7 db 0
'''
def layout(kind='layout'):
 rows=[b'']*25;colors={}
 if kind!='blank':
  rows[0]=b'   LEADING  INNER  SPACES   ';rows[2]=b'ANSI COLOR DOES NOT ENTER SNAPSHOT'
  rows[4]=(b'FULLWIDTH'+b'X'*71) if kind=='fullwidth' else b'RED ROW  '
  colors[4]=31
  rows[8]=b'CP437:\x82\xb3\xdb' if kind=='cp437' else b'SNAPSHOT TEST';rows[20]=b'END OF KNOWN VIEW   '
 return rows,colors
def wire_layout(rows,colors):
 data=bytearray(b'\x1b[0m\x1b[2J\x1b[H')
 for row,text in enumerate(rows):
  if text:data+=f'\x1b[{row+1};1H\x1b[{colors.get(row,0)}m'.encode()+text
 data+=f'\x1b[0m\x1b[{CURSOR[0]};{CURSOR[1]}H'.encode();return bytes(data)
def snapshot(rows):return b''.join(row.rstrip(b' ')+b'\r\n' for row in rows)
def recipes():
 return [dict(name='blank-25-records',kind='blank'),dict(name='leading-interior-trailing',kind='layout'),dict(name='fullwidth-80columns',kind='fullwidth'),dict(name='CP437-characters',kind='cp437'),dict(name='repeat-appends-preserve1A',repeat=True,seed=SEED),dict(name='prior-transient-status',notice=True),dict(name='capture-open-independent',capture='D:\\OTHER.LOG'),dict(name='capture-held-independent',capture='D:\\OTHER.LOG',hold=True),dict(name='capture-path-alias-conflict',capture='D:\\PCPLUS.SCR',conflict=True),dict(name='capture-held-alias-conflict',capture='D:\\PCPLUS.SCR',hold=True,conflict=True),dict(name='readonly-existing-preserved',readonly=True,seed=SEED)]
class SnapshotPeer(TerminalPeer):
 def __init__(self,recipe,output):self.output=output;self.cprs=[];super().__init__(recipe)
 def wait_marker(self,want):
  deadline=time.monotonic()+20
  while time.monotonic()<deadline and not self.stop.is_set():
   at=bytes(self.pending).find(want)
   if at>=0:del self.pending[:at+len(want)];self.log('actual-BIOS-marker',marker=want.decode());return
   self.receive()
  raise TimeoutError('Missing actual marker '+repr(want))
 def query(self):
  self.send(b'\x1b[6n\x1b[5n');expected=f'\x1b[{CURSOR[0]};{CURSOR[1]}R'.encode();deadline=time.monotonic()+5
  while time.monotonic()<deadline and not self.stop.is_set():
   data=bytes(self.pending);c=data.find(expected);d=data.find(b'\x1b[0n')
   if c>=0 and d>=0:
    del self.pending[:max(c+len(expected),d+4)];self.cprs.append(expected.decode());return
   self.receive()
  raise TimeoutError('Actual cursor/status reply missing or cursor changed')
 def run(self):
  r=self.recipe;rows,colors=layout(r.get('kind','layout'))
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready();self.wait_marker(b'm1');self.send(wire_layout(rows,colors));self.query();self.checks['actual_pre_snapshot_CPR_DSR']=True
    for ordinal in range(2 if r.get('repeat') else 1):
     self.wait_marker(b'm'+str(ordinal+2).encode());self.query();self.checks['actual_post_snapshot_CPR_DSR_unchanged']=True
     path=self.output/'PCPLUS.SCR'
     if not r.get('conflict') and not r.get('readonly'):
      expected=r.get('seed',b'')+snapshot(rows)*(ordinal+1)
      assert path.exists() and path.read_bytes()==expected,('Snapshot bytes not closed/exact before next key',ordinal)
      self.checks['snapshot_closed_exact_after_each_hotkey']=True
    if r.get('capture'):
     self.send(b'\x1b[15;1HPOSTSHOT\x1b[2K'+f'\x1b[{CURSOR[0]};{CURSOR[1]}H'.encode());self.query();self.checks['actual_post_snapshot_capture_probe']=True
    self.wait_marker(b'ready');self.query();self.checks['actual_later_keyboard_and_DSR']=True
  except EOFError:
   if not self.stop.is_set():self.errors.append('Unexpected serial EOF')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()
def run_case(r,a):
 out=OUT/a.label/r['name'];out.mkdir(parents=True,exist_ok=False);rows,colors=layout(r.get('kind','layout'));target=out/'PCPLUS.SCR'
 if r.get('seed') is not None:target.write_bytes(r['seed'])
 if r.get('readonly'):target.chmod(0o444)
 sampler=SAMPLER;base=(0x3f8,0x2f8,0x3e8,0x2e8)[a.com-1]
 for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(base+off))
 for stem,source in [('SNAP',sampler),('META',META)]:
  (out/(stem+'.asm')).write_text(source);subprocess.run(['nasm','-fbin',str(out/(stem+'.asm')),'-o',str(out/(stem+'.COM'))],check=True)
 peer=SnapshotPeer(r,out);peer.thread.start();keys=['p1500']
 if r.get('capture'):
  keys+=['a-f1','p300']+list(r['capture'])+['enter','p300']
  if r.get('hold'):keys+=['a-f2','p300']
 keys+=['m','1','p1200']
 if r.get('notice'):keys+=['a-f3','p300']
 keys+=['a-g','p500','m','2','p500']
 if r.get('repeat'):keys+=['a-g','p500','m','3','p500']
 if r.get('capture'):keys+=['a-f1','p500']
 keys+=['r','e','a','d','y','p500','a-x']
 serial='\n'.join('serial'+str(i)+'='+(f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1' if i==a.com else 'disabled') for i in range(1,5));command=f'C:\\TERMINAL COM{a.com} {a.baud} 8N1 {a.flow}'
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[serial]\n{serial}\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{out}"\nd:\nSNAP B\nADDKEY {' '.join(keys)}\n{command}\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto capture\n:fail\necho FAIL>FAIL.TXT\n:capture\nMETA\nSNAP S\nSNAP A\nexit\n'''
 (out/'dosbox.conf').write_text(conf);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Runtime changed';started=time.monotonic()
 with (out/'dosbox.log').open('w') as f:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=f,stderr=f,timeout=a.timeout).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.server.close();peer.thread.join(2)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 capture_expected=b'' if r.get('hold') else b''.join(rows)+(b'POSTSHOT' if r.get('capture') else b'')
 expected=(capture_expected if r.get('conflict') else r.get('seed',b'') if r.get('readonly') else r.get('seed',b'')+snapshot(rows)*(2 if r.get('repeat') else 1))
 checks=dict(peer.checks);checks.update(actual_initial_DSR=bool(checks.get('actual_terminal_ready')),required_pre_snapshot_cursor=bool(checks.get('actual_pre_snapshot_CPR_DSR')),required_post_snapshot_cursor=bool(checks.get('actual_post_snapshot_CPR_DSR_unchanged')),required_later_keyboard_DSR=bool(checks.get('actual_later_keyboard_and_DSR')),DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),no_peer_errors=not peer.errors,runtime_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,exact_snapshot_or_conflict_file=target.exists() and target.read_bytes()==expected)
 if r.get('capture') and not r.get('conflict'):checks['independent_capture_log_exact']=(out/'OTHER.LOG').exists() and (out/'OTHER.LOG').read_bytes()==capture_expected
 if r.get('readonly'):checks['readonly_flag_preserved']=target.stat().st_mode&0o222==0
 screen=read('SCREEN.BIN');grid=b''.join(row.ljust(80,b' ') for row in rows)
 checks['actual_video_top23rows_unchanged']=len(screen)==4000 and screen[:23*160:2]==grid[:23*80]
 meta=read('BIOS.BIN');checks['actual_BIOS_cursor_unchanged']=len(meta)==7 and meta[:2]==bytes([CURSOR[1]-1,CURSOR[0]-1]) and meta[4:]==bytes([3,80,0])
 if colors:checks['actual_color_attributes_preserved']=len(screen)==4000 and all(screen[4*160+i*2+1]&7==4 for i in range(len(rows[4])))
 allowed={'SNAP.asm','SNAP.COM','META.asm','META.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','BIOS.BIN','PCPLUS.SCR'}|({'OTHER.LOG'} if r.get('capture') and not r.get('conflict') else set());checks['no_other_files_created']=not [p for p in out.iterdir() if p.name not in allowed]
 (out/'serial.bin').write_bytes(peer.wire);(out/'peer.bin').write_bytes(peer.sent);(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n');(out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n');(out/'expected-snapshot.bin').write_bytes(expected)
 result=dict(passed=all(checks.values()),case=r['name'],checks=checks,errors=peer.errors,binary_sha256=a.sha256,seconds=round(time.monotonic()-started,3),keys=' '.join(keys),command=command,actual_CPRs=peer.cprs,expected_sha256=hashlib.sha256(expected).hexdigest(),actual_sha256=hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None,scope='ActualDOS AltG snapshots with independent ANSI rows/char-byte oracle, actualCPR/DSR/keyboard, B800sampling and BIOScursor/UART/IRQ restoration. Separate captureowner active/held and DOSpathalias conflicts. No physicalNUL injection,1A-in-row,physicalhardware or filesystemwrite-fault claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def self_check():
 assert len(snapshot(layout('blank')[0]))==50
 r,c=layout('fullwidth');assert len(r[4])==80 and len(snapshot(r).split(b'\r\n'))==26
 assert snapshot([b' A  B   ']+[b'']*24).startswith(b' A  B\r\n')
 assert b'\x82\xb3\xdb' in snapshot(layout('cp437')[0]);assert all('period' not in list(r.get('capture','')) for r in recipes())
 print('Independent25-row/trim/fullwidth/CP437 oracle self-check passed; no terminal executed')
def main():
 if '--self-check' in __import__('sys').argv:self_check();return 0
 p=argparse.ArgumentParser();p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--case',action='append',default=[]);p.add_argument('--com',type=int,choices=range(1,5),default=1);p.add_argument('--baud',type=int,default=38400);p.add_argument('--flow',choices=['HARD','NONE'],default='HARD');p.add_argument('--timeout',type=int,default=80);a=p.parse_args()
 assert a.label.replace('-','').replace('_','').isalnum();assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Explicit runtimefreeze required';OUT.mkdir(parents=True,exist_ok=True);selected=[r for r in recipes() if not a.case or r['name'] in a.case];assert selected
 with (OUT/'.lock').open('w') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);rows=[run_case(r,a) for r in selected]
 result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows);(OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
