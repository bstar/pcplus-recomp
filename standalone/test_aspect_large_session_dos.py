#!/usr/bin/env python3
"""Actual DOS main-loop/ASPECT rendering at diagnostic-selected text heights.
Owned synthetic modem peer, timer observer and BIOS key events; no BBS/SIP/physical acceptance.
"""
import argparse,hashlib,json,struct,sys,types,shutil,subprocess
from pathlib import Path
import test_aspect_renderer_dos as renderer
from directory_fixtures import directory,prm
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ESC=b'\x1b';QUERY=ESC+b'[6n';DA=ESC+b'[0c'
def adapter(out):
 p=ROOT/'standalone/test_connection_dos.py';source=p.read_text()
 replacements={"out=ROOT/'build/connection-dos'/name":"out=SESSION_OUT/name",'len(screen)==4000':'len(screen)==8000',
 "\n       line.append(byte)\n":"\n       line.append(byte)\n\n       if SESSION_POST and not checks.get('session_post_sent') and b'ready' in line:\n        conn.sendall(SESSION_POST);checks['session_post_sent']=True\n"}
 for old,new in replacements.items():assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
 assert source.count('cycles=fixed 6000')==1;source=source.replace('cycles=fixed 6000','cycles=fixed 12000')
 m=types.ModuleType('large_session_connection');m.__file__=str(p);m.SESSION_OUT=out;m.SESSION_POST=b'';exec(compile(source,str(p),'exec'),m.__dict__)
 assert m.SAMPLER.count('mov cx,4000')==1;m.SAMPLER=m.SAMPLER.replace('mov cx,4000','mov cx,8000')
 return m
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--runner',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--nested',choices=['save','noclear-graphics','noclear-text']);p.add_argument('--profile',type=int,choices=[4,6],default=6);p.add_argument('--rows',type=int,action='append',choices=[25,28,43,50]);p.add_argument('--case',action='append',choices=['queries','RIS','window']);a=p.parse_args()
 assert not a.nested or not a.case or a.case==['queries'],'Nested cases use the query/return workflow'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 runner=a.runner.resolve();rm=json.loads((runner.parent/'manifest.json').read_text());assert sha(runner)==rm['binary_sha256'] and rm['experimental_parent_render'] and rm['experimental_custom_irq'] and not rm['original_inputs']
 for n,h in rm['sources'].items():assert sha(ROOT/n)==h,n
 sys.path.insert(0,str(ROOT/'src/aspect'));from compiler import compile_source
 import test_aspect_script_window_dos as window
 cases=[];manifests={}
 for physical in a.rows or [25,28,43,50]:
  terminal=(a.build/str(physical)/'TERMINAL.EXE').resolve();tm=json.loads((terminal.parent/'manifest.json').read_text());assert sha(terminal)==tm['binary_sha256'] and tm['diagnostic_session_rows_probe']==physical and tm['experimental_aspect_row_owner']
  for n,h in tm['sources'].items():assert sha(ROOT/n)==h,n
  manifests[str(physical)]={'path':str(terminal.relative_to(ROOT)),'sha256':sha(terminal),'manifest_sha256':sha(terminal.parent/'manifest.json')}
  for kind in a.case or (['queries'] if a.nested else ['queries','RIS','window']):
   name=f'{physical}-{a.profile}-{kind}'+('-'+a.nested if a.nested else '');group=out/name;group.mkdir();renderer.OUT=group
   passive=window.make_observer(renderer.observer,window.symbols(terminal.parent/'terminal.map'),window.symbols(runner.parent/'ASPECT.map'),render_progress=True)
   observed,modes,policy_pairs,snapshots=passive(renderer.map_offsets(terminal.parent/'terminal.map'))
   # Schedule literal BIOS keys from real EXEC lifecycle events, rather than
   # guessing a wall-clock delay for dialing, script return or slow CPU models.
   asm=group/'observer.asm';text=asm.read_text();anchor='timer:\n save\n cld\n';assert text.count(anchor)==1
   automatic='''
 cmp word [cs:exec_seen],1
 jne .keys_done
 cmp word [cs:exec_done],1
 je .after_child
 inc word [cs:child_ticks]
 cmp word [cs:open_window],1
 jne .keys_done
 cmp word [cs:child_ticks],36
 jne .keys_done
 mov cx,0x2c00
 mov ah,5
 int 0x16
 jmp .keys_done
.after_child:
 inc word [cs:return_ticks]
 cmp word [cs:return_ticks],36
 jne .exit_key
 mov si,ready_keys
 mov di,5
.ready_key:
 mov cx,[cs:si]
 mov ah,5
 int 0x16
 add si,2
 dec di
 jnz .ready_key
.exit_key:
 cmp word [cs:return_ticks],72
 jne .keys_done
 mov cx,0x2d00
 mov ah,5
 int 0x16
.keys_done:
'''
   if a.nested:
    # Count the ASPECT exit only, not its nested DOS children.
    old=' cmp word [cs:exec_done],0\n jne .chain\n mov al,[ss:bp+16]'
    new=' cmp word [cs:exec_done],0\n jne .chain\n mov ah,0x62\n int 0x21\n mov es,bx\n mov ax,[es:0x16]\n cmp ax,[cs:parent_psp]\n jne .chain\n mov al,[ss:bp+16]'
    assert text.count(old)==1;text=text.replace(old,new)
   text=text.replace(anchor,anchor+automatic)
   text=text.replace('resident_end:\nstart:',('child_ticks: dw 0\nreturn_ticks: dw 0\nopen_window: dw '+str(int(kind=='window'))+'\nready_keys: dw 0x1372,0x1265,0x1e61,0x2064,0x1579\nresident_end:\nstart:'))
   asm.write_text(text);subprocess.run(['nasm','-fbin',str(asm),'-o',str(group/'RENDER.COM')],check=True);observed=(group/'RENDER.COM').read_bytes()
   application=group/'application';application.mkdir();shutil.copyfile(terminal,application/'TERMINAL.EXE');shutil.copyfile(runner,application/'ASPECT.EXE')
   harness=adapter(group);harness.BINARY=application/'TERMINAL.EXE'
   logical=physical-1;lower=(f'LOWER-{physical}').encode();header=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+DA+ESC+f'[{logical};1H'.encode()+lower+QUERY
   if kind=='RIS':header+=ESC+b'c';lower=b''
   header+=ESC+b'[1;1H'+ESC+b'[KFIRST BYTE SAFE'+QUERY+b'LOGIN:'
   source='proc main\nwaitfor "LOGIN:" 5\nif waitfor\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'
   updates=();triggers=();keys='p30000 a-x';post_reply=ESC+b'[1;22R';bottom=lower;early=ESC+f'[{logical};{len(lower)+1}R'.encode()
   if kind=='window':
    source='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\nwaitfor "END" 20\nif waitfor\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'
    triggers=((b'KEYREADY',((3.0,ESC+f'[{logical};1H'.encode()+b'UPDATED'+QUERY),(5.0,b'END'))),)
    keys='p30000 a-x';post_reply=ESC+f'[{logical};11R'.encode();bottom=b'UPDATEDEND'
   payload=bytearray(directory(port=0,profile=a.profile));payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
   settings=bytearray(prm(port=3));struct.pack_into('<H',settings,0x188,5);struct.pack_into('<HH',settings,0x4e4,8,4);struct.pack_into('<H',settings,0x196,0);struct.pack_into('<HH',settings,0x1bc,0,0);struct.pack_into('<H',settings,0x1e4,0)
   nested_files={};nested_code=None
   if a.nested:
    nested_code='R' if a.nested=='noclear-text' else 'G';option='' if a.nested=='save' else ' NOCLEAR'
    command='run "D:\\NESTED.COM '+nested_code+'"'+option+'\nrun "D:\\GEOM.COM" NOCLEAR\n'
    source=source.replace('transmit $D_PWORD',command+'transmit $D_PWORD',1)
    subprocess.run(['nasm','-fbin','-DPORT=0x3e8','-DVECTOR=13','-DIRQBIT=32',str(ROOT/'standalone/aspect_parent_child.asm'),'-o',str(group/'NESTED.COM')],check=True)
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/text_geometry_child.asm'),'-o',str(group/'GEOM.COM')],check=True)
    nested_files={'NESTED.COM':(group/'NESTED.COM').read_bytes(),'GEOM.COM':(group/'GEOM.COM').read_bytes(),'CHILD.LOG':b''}
    if a.nested=='noclear-graphics':bottom=b''
   files={'LOGIN.ASP':source.encode(),'LOGIN.ASX':compile_source(source),'ASPECT.EXE':runner.read_bytes(),'RENDER.COM':observed}
   files.update(nested_files)
   harness.SESSION_POST=QUERY+ESC+b'[18t'
   result=harness.run('run','success',keys,directory=bytes(payload),prm=bytes(settings),arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /I:3',files=files,banner=header,working_drive='d',observer='RENDER',online_updates=updates,online_triggers=triggers,cpu='8086',com=3,irq=5,profile=a.profile,timeout=60)
   folder=group/'run';wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes();raw=(folder/'RENDER.BIN').read_bytes();h=struct.unpack_from('<7H',raw)
   checks=result['checks'];checks.update(real_child_exit0=h[:4]==(0x524e,1,1,1) and h[6]==0,
    JFT_unchanged=raw[14:34]==raw[34:54],sink_owners_unchanged=raw[54:470]==raw[470:886],
    actual_bottom_row_CPR=early in wire if kind!='RIS' else True,
    parent_keyboard_after_child=b'ready' in wire,post_query_after_keyboard=bool(checks.get('session_post_sent')) and wire.find(b'ready')<wire.rfind(post_reply),
    accepted_logical_size=(ESC+f'[8;{logical};80t'.encode()) in wire,
    password_once=wire.count(b'Synth42\r')==1,
    bottom_content=screen[(logical-1)*160:(logical-1)*160+len(bottom)*2:2]==bottom,
    actual_physical_status=screen[logical*160:(logical+1)*160:2].startswith(b' Disconnected' if physical==25 else b' Alt-Z FOR HELP'),
    frozen_inputs=sha(terminal)==tm['binary_sha256'] and sha(runner)==rm['binary_sha256'])
   if a.nested:
    checks.pop('fixture_unchanged_CHILD.LOG');checks['nested_child_executed_once']=(folder/'CHILD.LOG').read_bytes()==nested_code.encode()
    geometry=struct.unpack('<5H',(folder/'GEOM.BIN').read_bytes());checks['independent_returned_geometry']=geometry==(3,80,physical,14 if physical==28 else 8 if physical in (43,50) else 16,0)
    if a.nested=='noclear-graphics':
     checks['immediate_banner_not_dropped']=early in wire and b'\x1b[1;16R' in wire
     checks['NOCLEAR_graphics_clears_bottom']=screen[(logical-1)*160:logical*160:2]==b' '*80
    if a.nested=='noclear-text':checks['NOCLEAR_raw247_keeps_child_text']=screen[20*160:20*160+2]==b'C\x4f'
   if kind=='RIS':checks['RIS_cleared_bottom']=screen[(logical-1)*160:logical*160:2]==b' '*80
   if kind=='window':
    first,advanced,seen,help_seen,ticks,rx,menu=struct.unpack('<7H',raw[-14:]);checks.update(window_observed=seen==1,window_kept_open=ticks>18,renderer_advances_while_open=advanced==1,live_bottom_query=(ESC+f'[{logical};8R'.encode()) in wire)
   result.update(passed=all(checks.values()),physical_rows=physical,logical_rows=logical,profile=a.profile,kind=kind,nested=a.nested,runner_sha256=sha(runner),observer_source_sha256=sha(group/'observer.asm'),observer_sha256=sha(group/'RENDER.COM'),artifacts={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file() and f.name!='result.json'})
   (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');cases.append(result);print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL '+str([n for n,v in checks.items() if not v]),flush=True)
   assert result['passed'],name
  for n,h in tm['sources'].items():assert sha(ROOT/n)==h,n
 for n,h in rm['sources'].items():assert sha(ROOT/n)==h,n
 from package_connection_test import stage
 for physical in a.rows or [25,28,43,50]:
  try:stage(out/('must-not-package-'+str(physical)),{'TERMINAL.EXE':(a.build/str(physical)/'TERMINAL.EXE').resolve()})
  except AssertionError as e:assert 'Startup diagnostic' in str(e)
  else:raise AssertionError('Session diagnostic packaged')
 sources=['standalone/test_aspect_large_session_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_aspect_script_window_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/package_connection_test.py']+(['standalone/aspect_parent_child.asm','standalone/text_geometry_child.asm'] if a.nested else [])
 report=dict(passed=True,cases=cases,images=manifests,runner_sha256=sha(runner),runner_manifest_sha256=sha(runner.parent/'manifest.json'),diagnostic_package_rejected=True,sources={n:sha(ROOT/n) for n in sources},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
