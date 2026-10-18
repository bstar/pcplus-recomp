#!/usr/bin/env python3
"""Source-only exact native print_controller wrappers and explicit memory-CRT fixture."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/print_controller';MODULE=ROOT/'reconstruction/print_controller'
def main():
 OUT.mkdir(parents=True,exist_ok=True);proof=json.loads((MODULE/'provenance.json').read_text())
 for u in proof['units']:
  out=OUT/(Path(u['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/u['source']),'-o',str(out)],check=True)
  raw=out.read_bytes();assert len(raw)==u['bytes'] and hashlib.sha256(raw).hexdigest()==u['sha256']
 sources=[MODULE/u['source'] for u in proof['units']]+[ROOT/p for p in proof['reused_sources']]+[ROOT/'standalone/print_controller_host.asm'];objects=[]
 for i,path in enumerate(sources):
  obj=OUT/f'{i:02d}-{path.stem}.obj';objects.append(str(obj));subprocess.run(['nasm','-fobj','-DPRINT_CONTROLLER_OMF','-DPRINTER_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
 (OUT/'main.c').write_text('#include <stdio.h>\nunsigned __cdecl print_controller_dos_test(void);int main(void){unsigned r=print_controller_dos_test();if(!r)puts("PRINTCTL PASS");return r;}\n')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=print_controller.map','-fe=PRINTCTL.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
 result={'binary_sha256':hashlib.sha256((OUT/'PRINTCTL.EXE').read_bytes()).hexdigest(),'exact_print_controller_bytes':sum(u['bytes'] for u in proof['units']),'borrowed_sources':proof['reused_sources'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'Exact native dedicated-print controller plus reused byte wrapper; explicit CRT open/putc/flush/close/status memory fixtures only. Native unsafe blocking escape buffer and unchecked FILE errors preserved; no live or physical printer support.'}
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built PRINTCTL.EXE',result['exact_print_controller_bytes'],'exact new bytes')
if __name__=='__main__':main()
