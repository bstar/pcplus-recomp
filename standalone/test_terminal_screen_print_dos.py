#!/usr/bin/env python3
"""Actual DOS CSI media-copy with independent fixed-width screen/PRN oracle.

Synthetic owned media, file-only virtual parallel port, real BIOS/UART/PRN.
No product callbacks, terminal replies or physical printer are simulated.
"""
import argparse,fcntl,hashlib,json,os,socket,subprocess,time
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_snapshot_dos import META,CURSOR,wire_layout,snapshot,SnapshotPeer
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-screen-print-dos';BINARY=ROOT/'build/terminal/TERMINAL.EXE'
def layout():
 rows=[b'']*25;rows[0]=b'   LEADING  INNER  TRAILING   ';rows[2]=b'SCREEN PRINT KEEPS ALL 80 COLUMNS';rows[4]=b'FULLWIDTH'+b'X'*71;rows[6]=b'CURRENT ROW 7';rows[8]=b'CP437:\x82\xb3\xdb';rows[20]=b'LAST VISIBLE TEXT   '
 return rows,{4:31}
def recipes():
 return [dict(name='default-full25-FF',command=b'\x1b[i'),dict(name='explicit0-full25-FF',command=b'\x1b[0i'),dict(name='current-row-noFF',command=b'\x1b[1i',current=True),dict(name='region-inclusive-FF',command=b'\x1b[0i',region=True),dict(name='full-FF-disabled',command=b'\x1b[0i',noff=True),dict(name='multiple-parameters0-1',command=b'\x1b[0;1i',multi=True),dict(name='active-copy-owner-preserved',command=b'\x1b[0i',active=True),dict(name='private5-4-copy-control',command=b'\x1b[1i',active=True,remote=True,current=True),dict(name='disabled-PRN-nonfatal',command=b'\x1b[0i',disabled=True),dict(name='capture-active-snapshot-preserved',command=b'\x1b[0i',capture=True,snapshot=True),dict(name='capture-held-snapshot-preserved',command=b'\x1b[1i',capture=True,hold=True,current=True,snapshot=True)]
def print_bytes(rows,r):
 if r.get('current'):selected=rows[CURSOR[0]-1:CURSOR[0]]
 elif r.get('region'):selected=rows[4:10]
 else:selected=rows
 out=b''.join(row.ljust(80,b' ')+b'\r\n' for row in selected)
 if not r.get('current') and not r.get('noff'):out+=b'\x0c'
 if r.get('multi'):out+=rows[CURSOR[0]-1].ljust(80,b' ')+b'\r\n'
 return out
class ScreenPrintPeer(SnapshotPeer):
 def run(self):
  r=self.recipe;rows,colors=layout()
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready();self.wait_marker(b'm1')
    if r.get('region'):self.send(b'\x1b[5;10r\x1b[19l')
    if r.get('noff'):self.send(b'\x1b[18l')
    if r.get('remote'):self.send(b'\x1b[?5i')
    self.send(wire_layout(rows,colors));self.query();self.checks['actual_before_print_cursor_DSR']=True
    self.wait_marker(b'm2');self.send(r['command']);self.query();self.checks['actual_after_print_cursor_DSR']=True
    self.wait_marker(b'm3')
    if r.get('active') or r.get('capture'):
     # New received characters prove the preexisting owner survives the print.
     self.send(b'\x1b[15;1HAFTERPRINT\x1b[2K'+f'\x1b[{CURSOR[0]};{CURSOR[1]}H'.encode());self.query();self.checks['actual_postprint_owner_probe']=True
    if r.get('remote'):
     self.send(b'\x1b[?4i\x1b[15;1HNOTCOPY\x1b[2K'+f'\x1b[{CURSOR[0]};{CURSOR[1]}H'.encode());self.query();self.checks['private4_closed_copy_before_later_text']=True
    self.wait_marker(b'ready');self.query();self.checks['actual_later_keyboard_DSR']=True
  except EOFError:
   if not self.stop.is_set():self.errors.append('Unexpected serial EOF')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()
def run_case(r,a):
 out=OUT/a.label/r['name'];out.mkdir(parents=True,exist_ok=False);rows,colors=layout();peer=ScreenPrintPeer(r,out);peer.thread.start()
 for stem,src in [('SNAP',SAMPLER),('META',META)]:
  (out/(stem+'.asm')).write_text(src);subprocess.run(['nasm','-fbin',str(out/(stem+'.asm')),'-o',str(out/(stem+'.COM'))],check=True)
 keys=['p1500']
 if r.get('capture'):
  keys+=['a-f1','p300']+list('D:\\OTHER.LOG')+['enter','p300']
  if r.get('hold'):keys+=['a-f2','p300']
 if r.get('active') and not r.get('remote'):keys+=['a-l','p300']
 keys+=['m','1','p1200','m','2','p2200']
 if r.get('snapshot'):keys+=['a-g','p500']
 keys+=['m','3','p1200']
 if r.get('active') and not r.get('remote'):keys+=['a-l','p500']
 if r.get('capture'):keys+=['a-f1','p500']
 keys+=['r','e','a','d','y','p500','a-x']
 parallel='disabled' if r.get('disabled') else f'file append:{out}/PRINTER.RAW'
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[parallel]\nparallel1={parallel}\nparallel2=disabled\nparallel3=disabled\n[serial]\nserial1=nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1\nserial2=disabled\nserial3=disabled\nserial4=disabled\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{out}"\nd:\nSNAP B\nADDKEY {' '.join(keys)}\nC:\\TERMINAL COM1 38400 8N1 HARD\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nMETA\nSNAP S\nSNAP A\nexit\n'''
 (out/'dosbox.conf').write_text(config);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256;started=time.monotonic()
 with (out/'dosbox.log').open('w') as log:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=70).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.server.close();peer.thread.join(2)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 expected=b'' if r.get('disabled') else print_bytes(rows,r)
 if r.get('active'):expected=b''.join(rows)+expected+b'AFTERPRINT'
 checks=dict(peer.checks);checks.update(actual_ready=bool(peer.checks.get('actual_terminal_ready')),required_preprint_cursor=bool(peer.checks.get('actual_before_print_cursor_DSR')),required_postprint_cursor=bool(peer.checks.get('actual_after_print_cursor_DSR')),required_later_keyboard=bool(peer.checks.get('actual_later_keyboard_DSR')),DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),runtime_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,no_peer_errors=not peer.errors,exact_fixedwidth_PRN=read('PRINTER.RAW')==expected)
 if r.get('capture'):checks['capture_owner_bytes_preserved']=read('OTHER.LOG')==(b'' if r.get('hold') else b''.join(rows)+b'AFTERPRINT') and (out/'OTHER.LOG').exists()
 if r.get('snapshot'):checks['snapshot_owner_exact_independent']=read('PCPLUS.SCR')==snapshot(rows) and (out/'PCPLUS.SCR').exists()
 final_rows=list(rows)
 if r.get('active') or r.get('capture'):final_rows[14]=b'' # probe uses EL2 after writing; its text is logged, its row is cleared.
 screen=read('SCREEN.BIN');grid=b''.join(row.ljust(80,b' ') for row in final_rows);checks['screen_top23_rows_preserved']=len(screen)==4000 and screen[:23*160:2]==grid[:23*80]
 bios=read('BIOS.BIN');checks['BIOS_cursor_geometry_preserved']=len(bios)==7 and bios[:2]==bytes([CURSOR[1]-1,CURSOR[0]-1]) and bios[4:]==bytes([3,80,0])
 allowed={'SNAP.asm','SNAP.COM','META.asm','META.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','BIOS.BIN','PRINTER.RAW'}|({'OTHER.LOG'} if r.get('capture') else set())|({'PCPLUS.SCR'} if r.get('snapshot') else set());checks['no_unexpected_files']=not [p.name for p in out.iterdir() if p.name not in allowed]
 for name,data in [('expected-printer.bin',expected),('serial.bin',peer.wire),('peer.bin',peer.sent)]:(out/name).write_bytes(data)
 (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n');(out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 result=dict(passed=all(checks.values()),case=r['name'],checks=checks,errors=peer.errors,binary_sha256=a.sha256,seconds=round(time.monotonic()-started,3),keys=' '.join(keys),expected_bytes=len(expected),expected_sha256=hashlib.sha256(expected).hexdigest(),scope='ActualDOS CSI media-copy through realUART/parser/nativevideo/PRN file-only virtualparallel. Independent80column rows+CRLF/FF oracle, realCPR/DSR/keyboard, activecopy/capture/snapshot ownership andhardware samples. No physicalprinter, literalNUL/SUBvideo injection or driverfaultclaim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def self_check():
 rows,_=layout();cases={r['name']:r for r in recipes()}
 assert len(rows)==25 and len(rows[4])==80
 assert len(print_bytes(rows,cases['default-full25-FF']))==25*82+1
 assert print_bytes(rows,cases['current-row-noFF'])==rows[6].ljust(80,b' ')+b'\r\n'
 assert len(print_bytes(rows,cases['region-inclusive-FF']))==6*82+1
 assert len(print_bytes(rows,cases['full-FF-disabled']))==25*82
 assert print_bytes(rows,cases['multiple-parameters0-1'])==print_bytes(rows,cases['default-full25-FF'])+print_bytes(rows,cases['current-row-noFF'])
 assert print_bytes(rows,cases['default-full25-FF']).startswith(rows[0].ljust(80,b' ')+b'\r\n')
 print('Independent fixed80column/CRLF/FF/current/region/multiple screen-print oracle checks passed; no terminal executed')
def main():
 if '--self-check' in __import__('sys').argv:self_check();return 0
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--case',action='append',default=[]);a=p.parse_args();assert a.label.replace('-','').replace('_','').isalnum();assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Explicitmatching runtimefreeze required';OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);rows=[run_case(r,a) for r in recipes() if not a.case or r['name'] in a.case]
 assert rows;result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows);(OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
