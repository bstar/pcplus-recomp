#!/usr/bin/env python3
"""Build recovered WHEN source units and relocatable OMF, without originals."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-when';SOURCE=ROOT/'src/aspect/when.asm'
HELPERS=[('copy','reconstruction/erase/move_bytes.asm',[],0x85b4,0x85fc),('upper','reconstruction/directory_dial/uppercase.asm',[],0x9128,0x9146),('decode','src/aspect/console_commands.asm',['-DASPECT_CONSOLE_FLAT','-DASPECT_CONSOLE_UNIT=4'],0x4934,0x498b)]
UNITS=[(1,0xe8c9,0xe9f5,55728),(2,0x534e,0x53c2,0x1200),(3,0x53c2,0x5431,0x1200),(4,0x4de9,0x4e34,0x1200)]
# Source components used by the independent full-flow replay; no installed app input.
COMPOSITION=[('exit','src/aspect/console_commands.asm','ASPECT_CONSOLE',1,0x4eb5,0x4ebc),('dispatch','src/aspect/dispatch.asm','ASPECT_DISPATCH',None,0x4b1f,0x4bff),
 ('stack','src/aspect/value_stack.asm','ASPECT_STACK',None,0xd0d0,0xd195)]
COMPOSITION += [('flow'+str(n),'src/aspect/control_flow.asm','ASPECT_FLOW',n,a,b) for n,a,b in [(1,0xd1f2,0xd20d),(2,0xd27d,0xd2a0),(3,0xd2d6,0xd372),(4,0xe129,0xe199)]]
COMPOSITION += [('operands'+str(n),'src/aspect/numeric_operands.asm','ASPECT_OPERANDS',n,a,b) for n,a,b in [(1,0xd19e,0xd1b0),(2,0xdb10,0xdb65),(3,0xdc48,0xdd26),(4,0xe0f1,0xe129)]]
COMPOSITION += [('strings'+str(n),'src/aspect/string_operands.asm','ASPECT_STRING',n,a,b) for n,a,b in [(1,0xdf04,0xe0cc),(2,0xdd68,0xdd9c),(4,0xe0e4,0xe0f1)]]
COMPOSITION += [('expression4','src/aspect/expression_support.asm','ASPECT_EXPR',4,0xde4d,0xdf04)]
COMPOSITION += [('serial'+str(n),'src/aspect/serial_commands.asm','ASPECT_SERIAL_COMMANDS',n,a,b) for n,a,b in [(1,0x5176,0x517f),(2,0x5188,0x52d0),(3,0x48cc,0x4934),(4,0xe9f5,0xea1d),(5,0x8252,0x8268)]]
COMPOSITION += [('receive'+str(n),'src/aspect/receive_commands.asm','ASPECT_RECEIVE_COMMANDS',n,a,b) for n,a,b in [(1,0x5431,0x5458),(4,0x4c4f,0x4c74)]]
COMPOSITION += [('policy'+str(n),'src/aspect/receive_policy.asm','ASPECT_RECEIVE_POLICY',n,a,b) for n,a,b in [(1,0x4c3c,0x4c4f),(2,0x4c74,0x4cb4)]]
ENTRIES=dict(cancel=0xe8c9,register=0xe8fc,slot=0xe9df,monitor=0x534e,trigger=0x53c2,service=0x4de9)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);parts=[];inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 for n,a,b,base in UNITS:
  target=OUT/f'unit{n}.bin';subprocess.run(['nasm','-f','bin',inc,'-DASPECT_WHEN_FLAT',f'-DASPECT_WHEN_UNIT={n}',str(SOURCE),'-o',str(target)],check=True)
  assert target.stat().st_size==b-a,(n,target.stat().st_size,b-a)
  parts.append(dict(unit=n,start=a,end_exclusive=b,file_base=base,sha256=sha(target.read_bytes())))
 subprocess.run(['nasm','-f','obj',inc,str(SOURCE),'-o',str(OUT/'when.obj')],check=True)
 helpers=[]
 for name,relative,defs,a,b in HELPERS:
  source=ROOT/relative;target=OUT/(name+'.bin')
  subprocess.run(['nasm','-f','bin',inc,*defs,str(source),'-o',str(target)],check=True);assert target.stat().st_size==b-a
  helpers.append(dict(name=name,start=a,end_exclusive=b,source=relative,source_sha256=sha(source.read_bytes()),sha256=sha(target.read_bytes())))
 composition=[]
 for name,relative,macro,n,a,b in COMPOSITION:
  source=ROOT/relative;target=OUT/(name+'.bin');defs=['-D'+macro+'_FLAT']+([] if n is None else ['-D'+macro+'_UNIT='+str(n)])
  subprocess.run(['nasm','-f','bin',inc,*defs,str(source),'-o',str(target)],check=True);assert target.stat().st_size==b-a,(name,target.stat().st_size,b-a)
  composition.append(dict(name=name,start=a,end_exclusive=b,source=relative,source_sha256=sha(source.read_bytes()),sha256=sha(target.read_bytes())))
 dependencies={p:sha((ROOT/p).read_bytes()) for p in ['reconstruction/uart/encodings.inc','reconstruction/translation/receive.asm']}
 report=dict(source_dependencies=dependencies,composition=composition,helpers=helpers,original_inputs=[],source_sha256=sha(SOURCE.read_bytes()),builder_sha256=sha(Path(__file__).read_bytes()),units=parts,object_sha256=sha((OUT/'when.obj').read_bytes()),native_bytes=sum(b-a for _,a,b,_ in UNITS))
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built',report['native_bytes'],'WHEN bytes + OMF')
if __name__=='__main__':main()
