#!/usr/bin/env python3
"""Independent actual DOS CSI5i raw printer-controller verification.

Real UART/BIOS/PRN APIs; synthetic file-only virtual parallel output. No original
application, physical printer, substituted terminal callbacks or fake replies.
"""
import argparse,fcntl,hashlib,json,os,socket,subprocess,time
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_snapshot_dos import META,CURSOR,wire_layout,SnapshotPeer
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-print-controller-dos';BINARY=ROOT/'build/terminal/TERMINAL.EXE'
RAW=b'A\x00B\x7f\r\n\x0c\x1a\x14\xffEND'
def layout():
 rows=[b'']*25;rows[0]=b'BEFORE PRINT CONTROLLER';rows[3]=b'   SCREEN AND CURSOR MUST STAY   ';rows[8]=b'UNCHANGED RAW VIEW';return rows,{3:31}
def filtered(data):return bytes(c for c in data if c not in (0,127))
def recipes():
 return [dict(name='binary-NUL-DEL-FF-SUB-DC4-once',data=RAW),dict(name='all256-raw-values',data=bytes(range(256))),dict(name='fragmented-stop-followed-ANSI',data=b'FRAGMENTED',fragment=True),dict(name='digit4-native-grammar',data=b'DIGIT4',terminator=b'\x1b[14i'),dict(name='suppress0-5-and-unknown-replay',data=b'A\x1b[5iB\x1b[0iC\x1b[31mD',expected=b'ABC\x1b[31mD'),dict(name='bounded-prefix-overflow-replay',data=b'\x1b['+b'1'*40+b'X'),dict(name='first-byte-timeout-replays-literal-ESC',data=b'\x1b[12',timeout=True,expected=b'\x1b[12X'),dict(name='active-copy-borrowed-owner',data=RAW,active=True),dict(name='capture-active-bypass',data=RAW,capture=True),dict(name='capture-held-bypass',data=RAW,capture=True,hold=True),dict(name='disabled-PRN-nonfatal',disabled=True),dict(name='keyboard-double-Escape',data=RAW,keyboard='escape'),dict(name='AltX-closes-controller',data=RAW,keyboard='exit'),dict(name='ordinary-key-and-nested-owner-denials',data=RAW,keyboard='ordinary')]
class ControllerPeer(SnapshotPeer):
 def marker(self,value):return self.wait_marker(value)
 def run(self):
  r=self.recipe;rows,colors=layout()
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready();self.marker(b'm1');self.send(wire_layout(rows,colors));self.query();self.checks['actual_precontroller_cursor_DSR']=True
    self.marker(b'm2');wire_start=len(self.wire);self.send(b'\x1b[5i')
    if not r.get('disabled'):
     self.send(r.get('data',RAW));self.log('controller-raw-payload',size=len(r.get('data',RAW)))
     if r.get('timeout'):time.sleep(2.3);self.send(b'X')
     if r.get('keyboard')=='exit':
      while not self.stop.is_set():self.receive()
     if r.get('keyboard')=='escape':
      self.marker(b'\x1b');self.checks['first_keyboard_Escape_forwarded']=True;time.sleep(.6)
     else:
      if r.get('keyboard')=='ordinary':
       self.marker(b'z0');self.checks['only_ordinary_keys_forwarded_while_owned']=bytes(self.wire[wire_start:])==b'hello\x1b[Az0'
      terminator=r.get('terminator',b'\x1b[4i')
      if r.get('fragment'):
       for value in terminator:self.send(bytes([value]));time.sleep(.12)
      else:self.send(terminator)
    self.query();self.checks['actual_postcontroller_cursor_DSR']=True
    if r.get('keyboard')=='escape':self.checks['exactly_one_keyboard_Escape_forwarded']=bytes(self.wire[wire_start:])==b'\x1b'+f'\x1b[{CURSOR[0]};{CURSOR[1]}R'.encode()+b'\x1b[0n'
    self.marker(b'm3')
    if r.get('active') or r.get('capture'):
     self.send(b'\x1b[15;1HPOSTCONTROLLER\x1b[2K'+f'\x1b[{CURSOR[0]};{CURSOR[1]}H'.encode());self.query();self.checks['postcontroller_owner_probe']=True
    self.marker(b'ready');self.query();self.checks['actual_later_keyboard_DSR']=True
  except EOFError:
   if r.get('keyboard')=='exit':self.checks['actual_AltX_closed_serial']=True
   elif not self.stop.is_set():self.errors.append('Unexpected serial EOF')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()
def run_case(r,a):
 out=OUT/a.label/r['name'];out.mkdir(parents=True,exist_ok=False);peer=ControllerPeer(r,out);peer.thread.start();rows,colors=layout()
 for stem,src in [('SNAP',SAMPLER),('META',META)]:
  (out/(stem+'.asm')).write_text(src);subprocess.run(['nasm','-fbin',str(out/(stem+'.asm')),'-o',str(out/(stem+'.COM'))],check=True)
 keys=['p1500']
 if r.get('capture'):
  keys+=['a-f1','p300']+list('D:\\OTHER.LOG')+['enter','p300']
  if r.get('hold'):keys+=['a-f2','p300']
 if r.get('active'):keys+=['a-l','p300']
 keys+=['m','1','p1000','m','2']
 if r.get('keyboard')=='exit':keys+=['p1500','a-x']
 else:
  if r.get('keyboard')=='escape':keys+=['p1000','escape','p300','escape']
  if r.get('keyboard')=='ordinary':keys+=['p300','h','e','l','l','o','up','a-g','a-f1','a-r','a-s','a-1','z','0']
  keys+=['p4000' if r.get('timeout') else 'p2200','m','3','p1000']
  if r.get('active'):keys+=['a-l','p400']
  if r.get('capture'):keys+=['a-f1','p400']
  keys+=['r','e','a','d','y','p500','a-x']
 parallel='disabled' if r.get('disabled') else f'file append:{out}/PRINTER.RAW'
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[parallel]\nparallel1={parallel}\nparallel2=disabled\nparallel3=disabled\n[serial]\nserial1=nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1\nserial2=disabled\nserial3=disabled\nserial4=disabled\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{out}"\nd:\nSNAP B\nADDKEY {' '.join(keys)}\nC:\\TERMINAL COM1 38400 8N1 HARD\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nMETA\nSNAP S\nSNAP A\nexit\n'''
 (out/'dosbox.conf').write_text(conf);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256;started=time.monotonic()
 with (out/'dosbox.log').open('w') as log:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=70).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.server.close();peer.thread.join(2)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 expected=b'' if r.get('disabled') else r.get('expected',filtered(r.get('data',RAW)))
 if r.get('active'):expected=b''.join(rows)+expected+b'POSTCONTROLLER'
 checks=dict(peer.checks);checks.update(actual_ready=bool(peer.checks.get('actual_terminal_ready')),required_precontroller_cursor=bool(peer.checks.get('actual_precontroller_cursor_DSR')),DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),runtime_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,no_peer_errors=not peer.errors,exact_raw_PRN_bytes=read('PRINTER.RAW')==expected)
 if r.get('keyboard')=='exit':checks['required_actual_AltX_closed_serial']=bool(peer.checks.get('actual_AltX_closed_serial'))
 else:checks.update(required_postcontroller_cursor=bool(peer.checks.get('actual_postcontroller_cursor_DSR')),required_later_keyboard=bool(peer.checks.get('actual_later_keyboard_DSR')))
 if r.get('capture'):checks['capture_bypassed_and_resumed']=read('OTHER.LOG')==(b'' if r.get('hold') else b''.join(rows)+b'POSTCONTROLLER') and (out/'OTHER.LOG').exists()
 if r.get('keyboard')=='ordinary':checks['ordinary_bindings_forwarded']=b'hello\x1b[A' in peer.wire
 if r.get('keyboard')=='escape':checks['doubleEscape_only_first_forwarded']=bool(peer.checks.get('exactly_one_keyboard_Escape_forwarded'))
 screen=read('SCREEN.BIN');grid=b''.join(row.ljust(80,b' ') for row in rows);checks['screen_top23_rows_preserved']=len(screen)==4000 and screen[:23*160:2]==grid[:23*80]
 bios=read('BIOS.BIN');checks['BIOS_cursor_geometry_preserved']=len(bios)==7 and bios[:2]==bytes([CURSOR[1]-1,CURSOR[0]-1]) and bios[4:]==bytes([3,80,0])
 allowed={'SNAP.asm','SNAP.COM','META.asm','META.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','BIOS.BIN','PRINTER.RAW'}|({'OTHER.LOG'} if r.get('capture') else set());checks['no_unexpected_files']=not [p.name for p in out.iterdir() if p.name not in allowed]
 for name,data in [('expected-printer.bin',expected),('serial.bin',peer.wire),('peer.bin',peer.sent)]:(out/name).write_bytes(data)
 (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n');(out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 result=dict(passed=all(checks.values()),case=r['name'],checks=checks,errors=peer.errors,binary_sha256=a.sha256,seconds=round(time.monotonic()-started,3),keys=' '.join(keys),expected_bytes=len(expected),scope='ActualDOS CSI5i dedicated rawcontroller with file-only virtualPRN, realUART/BIOS/parser/driver and independent rawbytes/grammar oracle. No physicalprinter, hostile-driver timing or complete originalprofile/UI claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def self_check():
 assert filtered(RAW)==b'AB\r\n\x0c\x1a\x14\xffEND'
 assert filtered(RAW).count(b'\x14')==1
 assert len(filtered(bytes(range(256))))==254
 assert b'\x1b' in filtered(bytes(range(256))) and b'\xff' in filtered(bytes(range(256)))
 cases=recipes();assert len(cases)==14 and len({r['name'] for r in cases})==14
 assert next(r for r in cases if r.get('timeout'))['expected']==b'\x1b[12X'
 print('Independent controller binary/filter/DC4/prefix fixture checks PASS; no runtime executed')
def main():
 if '--self-check' in __import__('sys').argv:self_check();return 0
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--case',action='append',default=[]);a=p.parse_args();assert a.label.replace('-','').replace('_','').isalnum();assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Explicit frozen runtime required';OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);rows=[run_case(r,a) for r in recipes() if not a.case or r['name'] in a.case]
 assert rows;result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows);(OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
