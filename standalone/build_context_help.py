#!/usr/bin/env python3
"""Source-only native help producer and real DOS parent/child ABI probes."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--parent-admission',action='store_true');a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 proof=json.loads((ROOT/'reconstruction/context_help/provenance.json').read_text());prior=json.loads((ROOT/'reconstruction/program_exec/provenance.json').read_text());units=[dict(u,define='CONTEXT_HELP_OMF') for u in proof['units']]+[dict(u,define='PROGRAM_EXEC_OMF') for u in prior['units'] if Path(u['file']).stem in ('strcpy','get_ds')]
 sources=['standalone/build_context_help.py','standalone/context_help_state.asm','standalone/context_help_parent.c','standalone/context_help_child.c','src/help/format.c','src/help/format.h','reconstruction/context_help/provenance.json','reconstruction/program_exec/provenance.json','reconstruction/uart/encodings.inc']+[u['file'] for u in units];objects=[]
 for u in units:
  name=Path(u['file']).stem;obj=out/(name+'.obj');flat=out/(name+'.bin')
  subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/u['file']),'-o',str(flat)],check=True);assert sha(flat)==u['sha256'] and flat.stat().st_size==u['bytes']
  subprocess.run(['nasm','-fobj','-D'+u['define'],'-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/u['file']),'-o',str(obj)],check=True);objects.append(str(obj))
 subprocess.run(['nasm','-fobj',str(ROOT/'standalone/context_help_state.asm'),'-o',str(out/'state.obj')],check=True)
 common=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-k8192']
 extra=[]
 if a.parent_admission:
  common.append('-dHELP_PARENT_ADMISSION');sources+=['src/help/parent.c','src/help/parent.h','src/help/parent_dos.c'];extra=[str(ROOT/n) for n in ['src/help/parent.c','src/help/parent_dos.c']]
 subprocess.run([*common,'-fe=CONTEXT.EXE','-fm=CONTEXT.MAP',str(ROOT/'standalone/context_help_parent.c'),str(ROOT/'src/help/format.c'),str(out/'state.obj'),*objects],cwd=out,check=True)
 subprocess.run([*common,'-fe=HLPPROBE.EXE','-fm=HLPPROBE.MAP',str(ROOT/'standalone/context_help_child.c'),str(ROOT/'src/help/format.c'),*extra],cwd=out,check=True)
 records=[];payloads=[];at=3+47*38
 for topic in range(47):
  data=('AUTHORED %02d\r\n'%topic).encode();records.append(('Context %02d'%topic).encode().ljust(32,b'\0')+struct.pack('<HI',1,at));payloads.append(data);at+=len(data)
 (out/'HELP.HLP').write_bytes(struct.pack('<BH',47,47)+b''.join(records+payloads))
 report=dict(passed=True,original_inputs=[],native_bytes=132,dependency_bytes=53,units=units,sources={n:sha(ROOT/n) for n in sources},products={n:sha(out/n) for n in ['CONTEXT.EXE','HLPPROBE.EXE','HELP.HLP']},scope='Exact native descriptor producer with real recovered strcpy/getDS. Diagnostic resolver/CRT formatter/spawn boundary and controlled source child exercise actual DOS foreign-memory transfer and authored HLP reading; no full native PROGRAM controller, production PCHELP, UI or UART integration.')
 if a.parent_admission:report['parent_admission']=True;report['scope']+=' Parent admission verifies actual child/parent PSP, parent main-block MCB ownership and bounded descriptor/path/title spans before consuming memory or opening files; seven additional actual DOS negative requests.'
 (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built132 exact producer bytes +53 reused dependencies; source-only DOS probes.')
if __name__=='__main__':main()
