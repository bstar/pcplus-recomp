#!/usr/bin/env python3
"""Source-only exact native print_screen wrappers and explicit memory-CRT fixture."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/print_screen';MODULE=ROOT/'reconstruction/print_screen'
def main():
 OUT.mkdir(parents=True,exist_ok=True);proof=json.loads((MODULE/'provenance.json').read_text())
 for u in proof['units']:
  out=OUT/(Path(u['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/u['source']),'-o',str(out)],check=True)
  raw=out.read_bytes();assert len(raw)==u['bytes'] and hashlib.sha256(raw).hexdigest()==u['sha256']
 sources=[MODULE/u['source'] for u in proof['units']]+[ROOT/p for p in proof['reused_sources']]+[ROOT/'standalone/print_screen_host.asm'];objects=[]
 for i,path in enumerate(sources):
  obj=OUT/f'{i:02d}-{path.stem}.obj';objects.append(str(obj));subprocess.run(['nasm','-fobj','-DPRINT_SCREEN_OMF','-DPRINTER_OMF','-DUI_WINDOWS_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
 (OUT/'main.c').write_text('#include <stdio.h>\nunsigned __cdecl print_screen_dos_test(void);int main(void){unsigned r=print_screen_dos_test();if(!r)puts("PRINTSCREEN PASS");return r;}\n')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=print_screen.map','-fe=PRINTSCR.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
 result={'binary_sha256':hashlib.sha256((OUT/'PRINTSCR.EXE').read_bytes()).hexdigest(),'exact_print_screen_bytes':sum(u['bytes'] for u in proof['units']),'borrowed_sources':proof['reused_sources'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'Exact native print_screen byte/toggle plus reused byte/toggle/video helpers; explicit CRT open/putc/flush/close/status memory fixtures only. Native unsafe shared FILE lifecycle preserved; no live or physical printer support.'}
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built PRINTSCR.EXE',result['exact_print_screen_bytes'],'exact new bytes')
if __name__=='__main__':main()
