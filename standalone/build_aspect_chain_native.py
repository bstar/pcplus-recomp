#!/usr/bin/env python3
"""Build exact native EXECUTE/per-file/final source owners without originals."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-chain-native';FIXTURE=ROOT/'standalone/fixtures/aspect_chain_native_units.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);units=json.loads(FIXTURE.read_text())['units'];source='src/aspect/chain_command.asm';sources={source:sha(ROOT/source)}
 for u in units:
  out=OUT/(u['name']+'.bin');u['file']=out.name
  subprocess.run(['nasm','-fbin','-Ireconstruction/uart/','-DASPECT_CHAIN_FLAT','-DASPECT_CHAIN_UNIT='+str(u['unit']),source,'-o',str(out)],cwd=ROOT,check=True)
  assert out.stat().st_size==u['length'] and sha(out)==u['sha256'],(u,out.read_bytes().hex())
 obj=OUT/'chain_command.obj';subprocess.run(['nasm','-fobj','-Ireconstruction/uart/',source,'-o',str(obj)],cwd=ROOT,check=True)
 helpers=[]
 for name,path,defs,start,end,base in [
  ('scratch','src/aspect/string_operands.asm',['-DASPECT_STRING_FLAT','-DASPECT_STRING_UNIT=1'],0xdfc7,0xdfea,0xdf04),
  ('strcpy','reconstruction/program_exec/strcpy.asm',[],0x8268,0x829a,0x8268),
  ('dispatch','src/aspect/dispatch.asm',['-DASPECT_DISPATCH_FLAT'],0x4b1f,0x4bff,0x4b1f)]:
  sources[path]=sha(ROOT/path);full=OUT/(name+'-full.bin');subprocess.run(['nasm','-fbin','-Ireconstruction/uart/',*defs,path,'-o',str(full)],cwd=ROOT,check=True)
  out=OUT/(name+'.bin');out.write_bytes(full.read_bytes()[start-base:end-base]);assert out.stat().st_size==end-start
  helpers.append(dict(name=name,start=start,end=end,file=out.name,sha256=sha(out)))
 for p in [FIXTURE,Path(__file__),ROOT/'reconstruction/uart/encodings.inc']:sources[str(p.relative_to(ROOT))]=sha(p)
 (OUT/'manifest.json').write_text(json.dumps(dict(original_inputs=[],native_bytes=sum(u['length'] for u in units),units=units,helpers=helpers,objects={obj.name:sha(obj)},sources=sources),indent=2)+'\n');print('Built',sum(u['length'] for u in units),'nativeCHAINownerbytes + actualscratch/strcpy/dispatcher')
if __name__=='__main__':main()
