#!/usr/bin/env python3
"""Build native FIND/SWITCH/CASE source units and OMF without original inputs."""
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-find-case'
BASELINE=ROOT/'standalone/fixtures/aspect_find_case_native_units.json'
HELPERS=[
 ('upper','reconstruction/directory_dial/uppercase.asm',[],0x9128,0x9146),
 ('strlen','reconstruction/program_exec/strlen.asm',[],0x8d18,0x8d33),
 ('strcpy','reconstruction/program_exec/strcpy.asm',[],0x8268,0x829a),
 ('strcmpi','reconstruction/program_exec/strcmpi.asm',[],0x93de,0x9420),
 ('strcmp','src/aspect/string_services.asm',['-DASPECT_STRING_SERVICES_FLAT','-DASPECT_STRING_SERVICES_UNIT=1'],0x9476,0x94a1),
 ('flow','src/aspect/control_flow.asm',['-DASPECT_FLOW_FLAT','-DASPECT_FLOW_UNIT=3'],0xd2d6,0xd372),
 ('dispatch','src/aspect/dispatch.asm',['-DASPECT_DISPATCH_FLAT'],0x4b1f,0x4bff),
 ('set_bool','src/aspect/set_commands.asm',['-DASPECT_SET_FLAT','-DASPECT_SET_UNIT=2'],0xe6bb,0xe6dd),
 ('set_find','src/aspect/set_commands.asm',['-DASPECT_SET_FLAT','-DASPECT_SET_UNIT=5'],0xea1c,0xea24),
 ('set_case','src/aspect/set_commands.asm',['-DASPECT_SET_FLAT','-DASPECT_SET_UNIT=9'],0xec77,0xec7f),
]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 OUT.mkdir(parents=True,exist_ok=True);baseline=json.loads(BASELINE.read_text());units=[];sources={}
 inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 for unit in baseline['units']:
  module=unit['module'];source=ROOT/'src/aspect'/(module+'.asm');sources[str(source.relative_to(ROOT))]=sha(source)
  macro='ASPECT_FIND' if module=='find_commands' else 'ASPECT_CASE'
  output=OUT/(module+'-'+str(unit['unit'])+'.bin')
  subprocess.run(['nasm','-fbin',inc,'-D'+macro+'_FLAT','-D'+macro+'_UNIT='+str(unit['unit']),str(source),'-o',str(output)],check=True)
  assert output.stat().st_size==unit['length'] and sha(output)==unit['sha256'],output
  units.append(dict(unit,file=output.name))
 for module in ['find_commands','case_commands']:
  subprocess.run(['nasm','-fobj',inc,str(Path('src/aspect')/(module+'.asm')),'-o',str(OUT/(module+'.obj'))],cwd=ROOT,check=True)
 helpers=[]
 for name,path,defines,start,end in HELPERS:
  source=ROOT/path;output=OUT/(name+'.bin');sources[path]=sha(source)
  subprocess.run(['nasm','-fbin',inc,*defines,str(source),'-o',str(output)],check=True)
  assert output.stat().st_size==end-start,(name,output.stat().st_size,end-start)
  helpers.append(dict(name=name,file=output.name,start=start,end=end,sha256=sha(output)))
 for p in [BASELINE,Path(__file__),ROOT/'reconstruction/uart/encodings.inc']:
  sources[str(p.relative_to(ROOT))]=sha(p)
 report=dict(original_inputs=[],native_bytes=sum(u['length'] for u in units),units=units,helpers=helpers,
             sources=sources,objects={m+'.obj':sha(OUT/(m+'.obj')) for m in ['find_commands','case_commands']},
             scope='401exactnativebytes in6sourceunits plus real CRT/flow/SET/dispatcher source composition. No original executable or initialized data input; near allocator and operand/FILE/platform boundaries remain external.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built401native FIND/CASE bytes, OMF and source-only helper composition')

if __name__=='__main__':main()
