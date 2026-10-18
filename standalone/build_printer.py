#!/usr/bin/env python3
"""Source-only exact native printer wrappers and explicit memory-CRT fixture."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/printer';MODULE=ROOT/'reconstruction/printer'
def main():
 OUT.mkdir(parents=True,exist_ok=True);proof=json.loads((MODULE/'provenance.json').read_text())
 for u in proof['units']:
  out=OUT/(Path(u['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/u['source']),'-o',str(out)],check=True)
  raw=out.read_bytes();assert len(raw)==u['bytes'] and hashlib.sha256(raw).hexdigest()==u['sha256']
 sources=[MODULE/u['source'] for u in proof['units']]+[ROOT/p for p in proof['reused_sources']]+[ROOT/'standalone/printer_host.asm'];objects=[]
 for i,path in enumerate(sources):
  obj=OUT/f'{i:02d}-{path.stem}.obj';objects.append(str(obj));subprocess.run(['nasm','-fobj','-DPRINTER_OMF','-DINPUT_DISPATCH_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
 (OUT/'main.c').write_text('#include <stdio.h>\nunsigned __cdecl printer_dos_test(void);int main(void){unsigned r=printer_dos_test();if(!r)puts("PRINTER PASS");return r;}\n')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=printer.map','-fe=PRINTER.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
 result={'binary_sha256':hashlib.sha256((OUT/'PRINTER.EXE').read_bytes()).hexdigest(),'exact_printer_bytes':sum(u['bytes'] for u in proof['units']),'borrowed_logger_bytes':132,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'Exact native printer byte/toggle plus existing logger; explicit CRT open/putc/flush/close/status memory fixtures only. Native null-open flag and ignored errors are preserved, no live/physicalPRN support.'}
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built PRINTER.EXE',result['exact_printer_bytes'],'exact new bytes')
if __name__=='__main__':main()
