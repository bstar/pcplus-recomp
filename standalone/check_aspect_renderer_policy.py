#!/usr/bin/env python3
"""Source-only compiled policy/DOS matrix and zero policyDATA inspection."""
import json,os,re,subprocess
from pathlib import Path
from build_aspect_renderer_policy import ROOT,OUT,sha


def cpu_matrix():
 import struct
 from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_INTR
 from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES,UC_X86_REG_SP,UC_X86_REG_IP
 symbols={}
 for line in (OUT/'POLICY.MAP').read_text().splitlines():
  m=re.match(r'^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4,8})[*+]?\s+(\w+)',line)
  if m:symbols[m[3]]=(int(m[1],16),int(m[2],16))
 group=re.search(r'DGROUP\s+([0-9A-Fa-f]{4}):', (OUT/'POLICY.MAP').read_text())
 load=0x2000;ds=load+int(group[1],16)
 raw=(OUT/'POLICY.EXE').read_bytes();header=struct.unpack_from('<14H',raw);body=bytearray(raw[header[4]*16:])
 for i in range(header[3]):
  off,seg=struct.unpack_from('<HH',raw,header[12]+4*i);at=seg*16+off
  struct.pack_into('<H',body,at,(struct.unpack_from('<H',body,at)[0]+load)&65535)
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,2*1024*1024);u.mem_write(load*16,bytes(body))
 checking=False;outside=[];visited=set()
 def address(name):seg,off=symbols[name];return (load+seg)*16+off
 def word(name,value):u.mem_write(address(name),struct.pack('<H',value))
 def hook(cpu,at,size,_):
  if cpu.reg_read(UC_X86_REG_IP)==0xf000:cpu.emu_stop()
  elif checking:visited.add(at)
 def write(cpu,access,at,size,value,_):
  if checking and not(ds*16+0xe000<=at and at+size<=ds*16+0x10000):outside.append((at,size,value))
 u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,write)
 def intr(cpu,num,_):raise AssertionError(('Forbidden IO interrupt',num))
 u.hook_add(UC_HOOK_INTR,intr)
 def invoke(name,arg=None,pure=True):
  nonlocal checking
  for reg,value in [(UC_X86_REG_CS,load),(UC_X86_REG_DS,ds),(UC_X86_REG_SS,ds),(UC_X86_REG_ES,ds),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0x1357),(UC_X86_REG_SI,0x2468),(UC_X86_REG_DI,0x369a)]:u.reg_write(reg,value)
  u.mem_write(ds*16+0xf000,struct.pack('<H',0xf000))
  if arg is not None:u.mem_write(ds*16+0xf002,struct.pack('<H',arg))
  checking=pure;u.emu_start(address(name),0,count=1000000);checking=False
  assert u.reg_read(UC_X86_REG_IP)==0xf000
  assert u.reg_read(UC_X86_REG_SP)==0xf002
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==ds
  for reg,value in [(UC_X86_REG_BP,0x1357),(UC_X86_REG_SI,0x2468),(UC_X86_REG_DI,0x369a)]:assert u.reg_read(reg)==value
  assert not outside,outside
  return u.reg_read(UC_X86_REG_AX)
 def valid():
  invoke('_fixture_valid',pure=False)
  u.mem_write(0x449,b'\x03\x50\0');u.mem_write(0x462,b'\0');u.mem_write(0x484,b'\x18')
 records=[]
 valid()
 history_seg,history_off=symbols['terminal_history_buffer']
 assert load+history_seg!=ds
 actual_pointer=struct.unpack('<2H',u.mem_read(address('terminal_history_pointer'),4))
 assert actual_pointer==(history_off,load+history_seg),('History far qualifier lost',actual_pointer,history_seg,history_off,ds)
 assert invoke('_aspect_render_admit')==0
 records.append(dict(kind='independent_far_history_layout',history_segment=load+history_seg,parent_DS=ds,history_offset=history_off,result=0))
 for at,value,expected in [(0x449,3,0),(0x449,7,3),(0x44a,79,3),(0x44b,1,3),(0x462,1,3),(0x484,43,3),(0x484,0,0),(0x484,24,0)]:
  valid();u.mem_write(at,bytes([value]));actual=invoke('_aspect_render_admit');assert actual==expected
  records.append(dict(kind='BDA',address=at,value=value,result=actual))
 for field,value,expected in [('screen_attributes_base',65535,3),('erase_attribute_values_base',65535,3),('terminal_history_start',65535,3),('erase_shadow_offset',65535,3),('screen_video_offset',2,3),('csi_terminal_id',4,0)]:
  valid();word(field,value);actual=invoke('_aspect_render_admit');assert actual==expected;records.append(dict(kind='pointer_geometry',field=field,result=actual))
 for depth in [0,1,2,16,17,65535]:
  valid();word('terminal_aspect_active',1);word('terminal_parser_active',depth)
  actual=invoke('_aspect_render_preflight_control',65);assert actual==(0 if 1<=depth<=16 else 3)
  records.append(dict(kind='parser_depth',depth=depth,result=actual))
 # Independently seed wide state; this does not call the generated C matrix.
 for rows,hidden,pane in [(1,0,1),(24,0,0),(25,1,1),(25,0,0)]:
  valid()
  for field,value in dict(screen_attribute_row_bytes=132,csi_column_count=132,csi_last_column=131,csi_row_count=rows,csi_last_row=rows-1,screen_last_row=rows-1,csi_origin_bottom=rows-1,erase_cell_count=rows*132,screen_viewport_enabled=1,screen_viewport_left=52,screen_viewport_right=79,screen_viewport_active=pane,screen_viewport_offset=0 if pane else 52,screen_cursor_column=0 if pane else 52,screen_attribute_offset=0 if pane else 52,ui_flow_suppressed=hidden,ui_flow_region_cells=80,ui_flow_video_base=3840,ui_flow_coordinate_base=0x1800,screen_cursor_wrap=1,screen_attribute_checks=1,erase_protection_mode=1,attributes_color_mode=1).items():word(field,value)
  result=invoke('_aspect_render_admit');assert result==(3 if rows==25 and not hidden else 0)
  records.append(dict(kind='independent_wide_geometry',rows=rows,hidden=hidden,pane=pane,result=result))
  if result:continue
  word('terminal_aspect_active',1);word('terminal_parser_active',1)
  for command in ['J','K','P']:
   word('ansi_command',ord(command));actual=invoke('_aspect_render_preflight_command');assert actual==(0 if command=='P'else 3)
   records.append(dict(kind='independent_field_command',rows=rows,pane=pane,command=command,result=actual))
 return dict(passed=True,cases=records,count=len(records),visited_instruction_addresses=len(visited),no_nonstack_writes=not outside,scope='Actual relocated compiled policy; controlled BDA and fixture state, DS=SS cdecl ABI and writes restricted to caller stack. No renderer or service bridge execution.')

def main():
 manifest=json.loads((OUT/'manifest.json').read_text())
 for n,d in manifest['sources'].items():assert sha(ROOT/n)==d
 assert sha(OUT/'POLICY.EXE')==manifest['binary_sha256']
 listing=(OUT/'policy.dis').read_text();segments=re.findall(r'Segment: (\w+) .*?([0-9A-Fa-f]{8}) bytes',listing)
 assert segments and any(n=='ASPECT_CODE' and int(v,16)>0 for n,v in segments)
 assert all(int(v,16)==0 for n,v in segments if n!='ASPECT_CODE'),segments
 cpu=cpu_matrix()
 folder=OUT/f'dos-run-{len(list(OUT.glob("dos-run-*")))+1:03d}';folder.mkdir()
 import shutil
 shutil.copyfile(OUT/'POLICY.EXE',folder/'POLICY.EXE');shutil.copyfile(OUT/'manifest.json',folder/'manifest.json');shutil.copyfile(OUT/'driver.c',folder/'driver.c')
 cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{folder}"
c:
POLICY >CONSOLE.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (folder/'dosbox.conf').write_text(cfg)
 with (folder/'dosbox.log').open('w') as log:
  result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=60)
 summary=(folder/'SUMMARY.TXT').read_text().strip() if (folder/'SUMMARY.TXT').exists() else ''
 match=re.fullmatch(r'checks=(\d+) failures=(\d+)',summary)
 checks=dict(DOS_pass=result.returncode==0 and (folder/'PASS.TXT').exists() and not(folder/'FAIL.TXT').exists(),matrix_summary=bool(match) and int(match[1])>20000 and int(match[2])==0,zero_policy_DATA=all(int(v,16)==0 for n,v in segments if n!='ASPECT_CODE'),binary_unchanged=sha(folder/'POLICY.EXE')==manifest['binary_sha256'])
 report=dict(cpu=cpu,passed=all(checks.values()) and cpu['passed'],checks=checks,DOS_summary=summary,policy_segments=dict(segments),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),run_directory=str(folder.relative_to(ROOT)),original_inputs=[],scope='Actual compiled pure policy under8086DOS with synthetic parentglobals/farplanes/backendstructs and realBDAgeometry. Fulladmission, owneruncertainty,2000metadatacells,79keymapbounds,16-mode-listpositions,256controls x64flagstates, read-only snapshots. No renderer/parentbridge execution, hardware lease admission, or MCB proof.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
