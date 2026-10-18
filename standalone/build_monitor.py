#!/usr/bin/env python3
"""Source-only native raw monitor/resolver/Y-N prompt with explicit fixtures."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/monitor';MODULE=ROOT/'reconstruction/monitor'
def main():
 OUT.mkdir(parents=True,exist_ok=True);proof=json.loads((MODULE/'provenance.json').read_text())
 for u in proof['units']:
  out=OUT/(Path(u['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/u['source']),'-o',str(out)],check=True)
  raw=out.read_bytes();assert len(raw)==u['bytes'] and hashlib.sha256(raw).hexdigest()==u['sha256']
 sources=[MODULE/u['source'] for u in proof['units']]+[ROOT/p for p in proof['reused_sources']]+[ROOT/'standalone/monitor_host.asm'];objects=[]
 for i,path in enumerate(sources):
  obj=OUT/f'{i:02d}-{path.stem}.obj';objects.append(str(obj));subprocess.run(['nasm','-fobj','-DMONITOR_OMF','-DPROGRAM_EXEC_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
 (OUT/'main.c').write_text('#include <stdio.h>\nunsigned __cdecl monitor_dos_test(void);int main(void){unsigned r=monitor_dos_test();if(!r)puts("MONITOR PASS");return r;}\n')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=monitor.map','-fe=MONITOR.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
 result={'binary_sha256':hashlib.sha256((OUT/'MONITOR.EXE').read_bytes()).hexdigest(),'exact_monitor_bytes':sum(u['bytes'] for u in proof['units']),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'Exact native modal monitor/resolver/Y-N prompt and reused native strings. Explicit memory UART/CRT/render/keyboard/window/UI boundaries; no liveUART,actualFILEorphysicaldump.'}
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built MONITOR.EXE',result['exact_monitor_bytes'],'exact new bytes')
if __name__=='__main__':main()
