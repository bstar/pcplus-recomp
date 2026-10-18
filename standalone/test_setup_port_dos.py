#!/usr/bin/env python3
"""Actual production-editor COM changes, independent multiport timer and peers."""
import hashlib,json,os,shutil,socket,struct,subprocess,threading,time
from pathlib import Path
from test_terminal import SAMPLER
from check_setup_model import image
from check_directory_live import word
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/setup-port-dos'
BINARY=ROOT/'build/terminal/TERMINAL.EXE';EDITOR=ROOT/'build/setup/PRMEDIT.EXE'
BASES=[0x3f8,0x2f8,0x3e8,0x2e8]

def run(name,source,target,*,accept=True,missing=False,combined=False):
 folder=OUT/name
 if folder.exists():shutil.rmtree(folder)
 folder.mkdir(parents=True)
 raw=word(image(),0,source-1);wanted=word(raw,0,target-1)
 (folder/'TEST.PRM').write_bytes(raw)
 for binary in [BINARY,EDITOR]:shutil.copyfile(binary,folder/binary.name)
 for index,base in enumerate(BASES,1):
  sampler=SAMPLER.replace('BEFORE.BIN',f'BEFORE{index}.BIN').replace('AFTER.BIN',f'AFTER{index}.BIN')
  for offset in [0,1,3,4]:sampler=sampler.replace(hex(0x3f8+offset),hex(base+offset))
  (folder/f'snap{index}.asm').write_text(sampler)
  subprocess.run(['nasm','-f','bin',str(folder/f'snap{index}.asm'),'-o',str(folder/f'SNAP{index}.COM')],check=True)
 subprocess.run(['nasm','-f','bin',str(ROOT/'standalone/port_watch.asm'),'-o',str(folder/'WATCH.COM')],check=True)
 reservations=[];ports=[]
 for _ in range(3):
  sock=socket.socket();sock.bind(('127.0.0.1',0));ports.append(sock.getsockname()[1]);reservations.append(sock)
 selected=target if accept and not missing else source
 keys=f'p1500 a-f10 p300 home del {target}'
 if combined:
  keys+=' tab home del del del del 1 9 2 0 0 pgdown home del 6'
  wanted=word(word(wanted,2,5),0x194,6)
 keys+=' f10 escape '+('y' if accept else 'n')+(' y' if combined else '')+(' space' if missing else '')
 keys+=' p6500 r e a d y p1800 a-x'
 schedule='ADDKEY p750 '+' p120 '.join(keys.split())
 serial='\n'.join(f'serial{i}='+ (f'nullmodem port:{ports[i-1]} transparent:1 nonlocal:0 rxdelay:200 txdelay:1' if i<=3 else 'disabled') for i in range(1,5))
 before='\n'.join(f'SNAP{i} B' for i in range(1,5));after='\n'.join(f'SNAP{i} A' for i in range(1,5))
 config=f'''[sdl]
output=surface
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
mount d "{folder}"
d:
WATCH T
{before}
{schedule}
TERMINAL @TEST.PRM
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
SNAP1 S
{after}
WATCH
exit
'''
 (folder/'dosbox.conf').write_text(config)
 stop=threading.Event();wire=bytearray();checks={};errors=[]
 def peer():
  # No TCP carrier during the settings choices. Establish it only after the
  # expected handoff, then prove the actual enabled UART through DSR/CPR/DA.
  if stop.wait(9):return
  try:
   with socket.create_connection(('127.0.0.1',ports[selected-1]),timeout=1) as conn:
    conn.settimeout(.05);next_probe=0;banner=False;post=False
    while not stop.is_set():
     if not banner and time.monotonic()>=next_probe:conn.sendall(b'\x1b[5n');next_probe=time.monotonic()+.3
     try:block=conn.recv(4096)
     except socket.timeout:continue
     if not block:break
     wire.extend(block)
     if not banner and b'\x1b[0n' in wire:
      checks['selected_UART_answers_DSR']=True
      conn.sendall(b'\x1b[2J\x1b[HPORT READY\x1b[6n\x1b[0c');banner=True
     if b'\x1b[1;11R' in wire:checks['selected_UART_renders_and_answers_CPR']=True
     if (b'\x1b[?1;2c' if combined else b'\x1b[?62;2c') in wire:checks['expected_profile_answers_DA']=True
     if not post and b'ready' in wire:
      checks['ordinary_keyboard_data_reaches_selected_UART']=True;conn.sendall(b' LIVE\x1b[6n');post=True
     if b'\x1b[1;16R' in wire:checks['duplex_receive_continues_after_keyboard_output']=True
  except OSError as error:
   if not stop.is_set():errors.append(str(error))
 thread=threading.Thread(target=peer,daemon=True)
 for sock in reservations:sock.close()
 thread.start()
 try:
  with (folder/'dosbox.log').open('w') as log:
   proc=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=folder,stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=25)
 finally:stop.set();thread.join(1)
 (folder/'serial.bin').write_bytes(wire)
 checks['DOS_exit_success']=proc.returncode==0 and (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
 checks['all_peer_checks_seen']=len(checks)==6 # five peer checks plus DOS exit
 checks['no_peer_errors']=not errors
 checks['exact_saved_PRM_including_opaque_bytes']=(folder/'TEST.PRM').read_bytes()==wanted
 checks['no_editor_recovery_files']=not any((folder/n).exists() for n in ['PRMEDIT.BAK','PRMEDIT.$$$'])
 checks['all_four_UART_PIC_and_IRQ_snapshots_restored']=all(len((folder/f'BEFORE{i}.BIN').read_bytes())==42 and (folder/f'BEFORE{i}.BIN').read_bytes()==(folder/f'AFTER{i}.BIN').read_bytes() for i in range(1,5))
 samples=struct.unpack('<18H',(folder/'WATCH.BIN').read_bytes())
 observations=[dict(active_ticks=samples[2+i*4],divisor_bitmap=samples[3+i*4],last_divisor=samples[4+i*4],line_bitmap=samples[5+i*4]) for i in range(4)]
 checks['independent_timer_active']=samples[0]==0x5043 and samples[1]>0 and observations[source-1]['active_ticks']>0
 for i,observed in enumerate(observations,1):
  if i==selected:checks[f'COM{i}_actual_enabled_format_and_rate']=observed['active_ticks']>0 and observed['line_bitmap']==1 and observed['divisor_bitmap']==(4 if combined else 1)
  elif i==source:checks[f'COM{i}_original_active_rate_observed']=observed['active_ticks']>0 and observed['divisor_bitmap']==1 and observed['line_bitmap']==1
  else:checks[f'COM{i}_never_enabled']=observed['active_ticks']==0
 screen=(folder/'SCREEN.BIN').read_bytes()
 checks['actual_video_matches_resumed_remote_output']=screen[:30:2]==b'PORT READY LIVE'
 result=dict(case=name,passed=all(checks.values()),checks=checks,source=source,target=target,selected=selected,observations=observations,peer_errors=errors,
  terminal_sha256=hashlib.sha256((folder/'TERMINAL.EXE').read_bytes()).hexdigest(),editor_sha256=hashlib.sha256((folder/'PRMEDIT.EXE').read_bytes()).hexdigest())
 (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 assert result['passed'],result
 print(name,'passed',flush=True);return result

def main():
 runtime=hashlib.sha256(BINARY.read_bytes()).hexdigest();editor=hashlib.sha256(EDITOR.read_bytes()).hexdigest()
 cases=[run('move-1-to-2',1,2),run('move-2-to-1',2,1),run('move-1-to-3-shared-IRQ',1,3),
  run('decline-1-to-2',1,2,accept=False),run('reject-missing-COM4',1,4,missing=True),run('move-baud-profile',1,2,combined=True)]
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==runtime and hashlib.sha256(EDITOR.read_bytes()).hexdigest()==editor
 assert all(c['terminal_sha256']==runtime and c['editor_sha256']==editor for c in cases)
 report=dict(passed=True,cases=cases,terminal_sha256=runtime,editor_sha256=editor,
  sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/test_setup_port_dos.py','standalone/port_watch.asm','standalone/test_terminal.py']},
  scope='Actual DOS production PRMEDIT via AltF10; COM1/2 in both directions, shared IRQ4 COM1/3, decline, absent BIOS COM4 and combined baud/profile change. Independent INT1C samples each UART, four before/after UART/PIC/IRQ snapshots match, and late loopback peers prove fresh DSR/DA/CPR, typed payload and video. No physical UART/Wi-Fi firmware or stock BBS claim.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
