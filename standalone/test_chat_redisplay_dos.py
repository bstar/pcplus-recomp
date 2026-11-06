#!/usr/bin/env python3
"""Real DOS parent/module/viewer arena, input, RX and retirement composition.

Calls exact parent far entries on its declared DS=SS/stack after DOS overlay
loading. Main, real keyboard dequeue, UART delivery and physical hardware are
separate gates. Neither product Chat nor viewer code is linked into the host.
"""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();binary,out=a.terminal.resolve(),a.output.resolve()
 assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text())
 assert m['experimental_chat_redisplay'] and m['chat_loader']['module']['api_version']==0x105
 assert sha(binary)==m['binary_sha256']
 sources=dict(m['sources'])
 for n in ['standalone/test_chat_redisplay_dos.py','standalone/chat_redisplay_host.c','standalone/chat_parent_invoke.asm']:sources[n]=sha(ROOT/n)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 listing=binary.with_name('terminal.map').read_text()
 symbols={n:(int(off,16),int(seg,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 group=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert group
 constants=dict(PARENT_DS=int(group[1],16),PARENT_SP=symbols['terminal_stack_top'][0],PARENT_PARAS=(m['memory_layout']['minimum_allocated_module_bytes']+15)//16)
 entries=dict(BINDING='_chat_front_view_binding',KEY='terminal_redisplay_key_far',BEFORE='terminal_redisplay_before_far',IDLE='terminal_redisplay_idle_far',OWNER='_redisplay_active',FROZEN='redisplay_snapshot',VIEW='_chat_view_active',SNAPSHOTSEG='redisplay_snapshot_segment',KEYFRONT='terminal_chat_key_far',RXHOLD='terminal_chat_receive_hold_far',RX='terminal_chat_receive_far',FRONTSTOP='terminal_chat_stop_far',VALID='_chat_module_image_valid',PSP='process_psp',MODE='modes_value_1d1a',HISTORY='terminal_history_buffer',HISTORYPTR='terminal_history_pointer',HISTORYSTART='terminal_history_start',HISTORYEND='terminal_history_end',HISTORYWRAPPED='terminal_history_wrapped',TXCOUNT='terminal_tx_count',TXHEAD='terminal_tx_head',TXTAIL='terminal_tx_tail',TXBUFFER='terminal_tx_buffer',CONNECTION='connection_state')
 for label,n in entries.items():constants[label+'_OFF'],constants[label+'_SEG']=symbols[n]
 out.mkdir();drive=out/'drive';drive.mkdir()
 for n,h in sources.items():
  target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
 (drive/'parent.h').write_text(''.join('#define '+k+' '+str(v)+'\n' for k,v in constants.items()))
 shutil.copyfile(binary,drive/'PARENT.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',drive/'PCCHAT.OVL')
 subprocess.run(['nasm','-fobj',str(ROOT/'standalone/chat_parent_invoke.asm'),'-o','invoke.obj'],cwd=drive,check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-k4096','-dCHAT_PRESENTATION','-dCHAT_TEXT','-dCHAT_TIMING','-dCHAT_FOREGROUND_TEXT','-dCHAT_REDISPLAY','-i='+str(drive),'-fe=VIEWTEST.EXE','-fm=VIEWTEST.MAP',str(ROOT/'standalone/chat_redisplay_host.c'),'invoke.obj'],cwd=drive,check=True)
 host_map=(drive/'VIEWTEST.MAP').read_text();assert '_chat_module_dispatch' not in host_map and '_redisplay_event_impl' not in host_map
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nVIEWTEST >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 timed_out=False
 with (out/'dosbox.log').open('w') as log:
  try:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=120)
  except subprocess.TimeoutExpired:timed_out=True;r=None
 text=(drive/'RESULT.TXT').read_text() if (drive/'RESULT.TXT').exists() else ''
 match=re.search(r'REDISPLAY checks=(\d+) errors=(\d+) sessions=5 wrapped_bytes=63000 low_memory=1 export=1 RX=1',text)
 passed=not timed_out and r.returncode==0 and bool(match) and match[2]=='0' and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists()
 for n,h in sources.items():assert sha(ROOT/n)==sha(out/'sources'/n)==h,n
 report=dict(passed=passed,timed_out=timed_out,checks=int(match[1]) if match else 0,output=text,binary_sha256=sha(binary),module_sha256=sha(drive/'PCCHAT.OVL'),sources=sources,constants=constants,original_inputs=[],scope=__doc__,artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and 'sources' not in p.parts})
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(text);print('PASS' if passed else 'FAIL');assert passed

if __name__=='__main__':main()
