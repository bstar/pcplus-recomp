#!/usr/bin/env python3
"""Actual parent/module Help-key admission under external BIOS geometry faults."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('terminal','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--rows',type=int,choices=(25,28,43,50),default=25);p.add_argument('--fault',type=int,choices=(0,1,2),default=0)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_help'] and sha(binary)==m['binary_sha256']
 names=['standalone/test_chat_help_geometry.py','standalone/chat_help_geometry_host.c','standalone/chat_parent_invoke.asm','src/chat/loader.h','src/chat/presentation.h']
 sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 listing=binary.with_name('terminal.map').read_text();symbols={n:(int(o,16),int(s,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 ds=int(re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I)[1],16)
 constants=dict(PARENT_DS=ds,PARENT_SP=symbols['terminal_stack_top'][0],PARENT_PARAS=(m['memory_layout']['minimum_allocated_module_bytes']+15)//16)
 entries=dict(ROWSET='_native_display_rows_set',LAYOUT='_terminal_row_status_layout',UIROWS='ui_window_rows',HIDDEN='ui_flow_suppressed',FLOWCELLS='ui_flow_region_cells',FLOWVIDEO='ui_flow_video_base',FLOWCOORD='ui_flow_coordinate_base',CSIROWS='csi_row_count',CSILAST='csi_last_row',KEYFRONT='terminal_chat_key_far',FRONTSTOP='terminal_chat_stop_far',OWNER='_redisplay_active',FROZEN='redisplay_snapshot',VALID='_chat_module_image_valid',PSP='process_psp',MODE='modes_value_1d1a',PENDING='terminal_program_pending',ACTIVE='terminal_program_active',KIND='terminal_program_kind',DISPLAY='_program_display_save',DISPLAYREADY='_program_display_ready')
 for label,n in entries.items():constants[label+'_OFF'],constants[label+'_SEG']=symbols[n]
 drive=out/'drive';drive.mkdir()
 for n,h in sources.items():
  target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
 (drive/'parent.h').write_text(''.join('#define '+n+' '+str(v)+'\n' for n,v in constants.items()))
 shutil.copyfile(binary,drive/'PARENT.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',drive/'PCCHAT.OVL')
 subprocess.run(['nasm','-fobj',str(ROOT/'standalone/chat_parent_invoke.asm'),'-o','invoke.obj'],cwd=drive,check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-k4096','-dCHAT_PRESENTATION','-dCHAT_TEXT','-dCHAT_TIMING','-dCHAT_FOREGROUND_TEXT','-dCHAT_REDISPLAY','-dTEST_ROWS='+str(a.rows),'-dTEST_FAULT='+str(a.fault),'-i='+str(drive),'-fe=HELPGEO.EXE','-fm=HELPGEO.MAP',str(ROOT/'standalone/chat_help_geometry_host.c'),'invoke.obj'],cwd=drive,check=True)
 listing=(drive/'HELPGEO.MAP').read_text();assert '_chat_module_dispatch' not in listing and '_chat_front_event' not in listing
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nHELPGEO >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 timeout=False
 with (out/'dosbox.log').open('w') as log:
  try:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=120)
  except subprocess.TimeoutExpired:timeout=True;r=None
 text=(drive/'RESULT.TXT').read_text() if (drive/'RESULT.TXT').exists() else '';match=re.search(r'HELPGEOM rows=\d+ fault=\d+ checks=(\d+) errors=(\d+)',text)
 passed=not timeout and r.returncode==0 and bool(match) and match[2]=='0' and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists()
 for n,h in sources.items():assert sha(ROOT/n)==sha(out/'sources'/n)==h,n
 report=dict(passed=passed,rows=a.rows,fault=a.fault,timed_out=timeout,checks=int(match[1]) if match else 0,errors=int(match[2]) if match else None,output=text,binary_sha256=sha(binary),module_sha256=sha(drive/'PCCHAT.OVL'),sources=sources,constants=constants,original_inputs=[],scope='Component calls to exact loaded parent/module far entries on parent DS=SS/stack; real BIOS row/page/graphics changes, full guarded video, pending Help and retained input checks. Canonical initial layout supplied by fixture. Valid Help queued but no DOS EXEC/main/serial acceptance. Restoration permits normal underlay retirement, not reconstruction of externally erased live Chat pixels.',artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and 'sources' not in p.parts})
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(text);return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
