#!/usr/bin/env python3
"""Build exact native path commands/services and error mapping from source only."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-paths'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);proof=json.loads((ROOT/'standalone/fixtures/aspect_path_native_units.json').read_text());units=[];inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 for unit in proof['units']:
  key='ASPECT_PATH' if unit['group']=='command' else 'ASPECT_PATH_SERVICE';target=OUT/(unit['group']+str(unit['unit'])+'.bin')
  subprocess.run(['nasm','-fbin',inc,'-D'+key+'_FLAT','-D'+key+'_UNIT='+str(unit['unit']),str(ROOT/unit['source']),'-o',str(target)],check=True)
  assert target.stat().st_size==unit['bytes'] and sha(target)==unit['sha256'],unit
  units.append(dict(**unit,output=str(target.relative_to(ROOT))))
 target=OUT/'error_map.bin';subprocess.run(['nasm','-fbin','-DASPECT_PATH_MAP_FLAT',str(ROOT/'src/aspect/path_state.asm'),'-o',str(target)],check=True)
 assert list(target.read_bytes())==proof['error_map']['values'] and sha(target)==proof['error_map']['sha256']
 objects=[];sources=[ROOT/'src/aspect'/p for p in ('path_commands.asm','path_services.asm','path_state.asm')]+[ROOT/p for p in proof['reused']]
 for source in sources:
  obj=OUT/(source.stem+'.obj');subprocess.run(['nasm','-fobj',inc,*(['-DPROGRAM_EXEC_OMF'] if source.parent.name=='program_exec' else []),str(source.relative_to(ROOT)),'-o',str(obj)],cwd=ROOT,check=True);objects.append(obj)
  if source.parent.name=='program_exec':
   flat=OUT/(source.stem+'.bin');subprocess.run(['nasm','-fbin',inc,str(source),'-o',str(flat)],check=True)
   prior=json.loads((ROOT/'reconstruction/program_exec/provenance.json').read_text());u=next(u for u in prior['units'] if u['file']==str(source.relative_to(ROOT)));assert sha(flat)==u['sha256']
 report=dict(passed=True,original_inputs=[],units=units,error_map=proof['error_map'],objects={str(p.relative_to(ROOT)):sha(p) for p in objects},sources={str(p.relative_to(ROOT)):sha(p) for p in [*sources,Path(__file__),ROOT/'standalone/fixtures/aspect_path_native_units.json']},native_bytes=sum(u['bytes'] for u in units)+sum((OUT/(Path(p).stem+'.bin')).stat().st_size for p in proof['reused']),scope='Exact native path commands/helpers and reused CRT result/error instructions; OMF imports unresolved until the runtime link. Numeric error map source facts, no original input. Actual filesystem and script integration are separate.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('ASPECT paths:',report['native_bytes'],'exact instruction bytes,20 numeric error entries and OMF PASS')
if __name__=='__main__':main()
