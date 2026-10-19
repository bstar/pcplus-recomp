#!/usr/bin/env python3
"""Build source-owned calibrated TXPACE component; no originals."""
import hashlib,json,struct,subprocess
from pathlib import Path
from omf_imports import records
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-txpace'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical_module(blob):
 # -zld suppresses checkout/time-dependent dependency comments. Canonicalize
 # only THEADR's source-name metadata; every remaining record stays exact.
 parsed=records(blob);name=b'src/aspect/txpace.c'
 payload=bytes([len(name)])+name
 head=struct.pack('<BH',0x80,len(payload)+1)+payload
 result=head+bytes([-sum(head)&255])+b''.join(raw for _,_,raw in parsed[1:])
 after=records(result)
 assert len(after)==len(parsed) and after[1:]==parsed[1:]
 assert not any(kind==0x88 and data[:2]==b'\x80\xe9' and len(data)>2 for kind,data,_ in after)
 return result
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 subprocess.run(['nasm','-f','bin','-Ireconstruction/uart/','-DASPECT_TXPACE_FLAT','src/aspect/txpace.asm','-o',str(OUT/'delay.bin')],cwd=ROOT,check=True)
 subprocess.run(['nasm','-f','obj','-Ireconstruction/uart/','src/aspect/txpace.asm','-o',str(OUT/'native.obj')],cwd=ROOT,check=True)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-zld','-fo='+str(OUT/'txpace.obj'),'src/aspect/txpace.c'],cwd=ROOT,check=True)
 obj=OUT/'txpace.obj';obj.write_bytes(canonical_module(obj.read_bytes()))
 source='''#include <stdio.h>
#include <conio.h>
#include "../../src/aspect/txpace.h"
static unsigned calls[5],cancel_phase,drop_if;
static unsigned step(unsigned phase){++calls[phase];if(drop_if==phase)aspect_txpace_restore_if(0);return phase==cancel_phase?42:0;}
int main(void){unsigned record[32],i,before,after,status,amounts[3]={0,55,999};unsigned long start,end;FILE*f;aspect_txpace_reset();record[0]=inp(0x21);record[1]=aspect_txpace_flags();status=aspect_txpace_prepare(step);record[2]=status;record[3]=aspect_txpace_count;record[4]=aspect_txpace_ready();record[5]=inp(0x21);record[6]=aspect_txpace_flags();if(status)return 10;for(i=0;i<3;++i){start=aspect_txpace_ticks();status=aspect_txpace_delay(amounts[i],step);end=aspect_txpace_ticks();record[7+i*3]=amounts[i];record[8+i*3]=(unsigned)(end>=start?end-start:end+ASPECT_TXPACE_DAY-start);record[9+i*3]=status;}aspect_txpace_reset();aspect_txpace_restore_if(0);status=aspect_txpace_prepare(step);before=aspect_txpace_flags();aspect_txpace_restore_if(512);record[16]=status;record[17]=before&512;cancel_phase=ASPECT_TXPACE_BEFORE_MEASURE;status=aspect_txpace_prepare(step);record[18]=status;record[19]=aspect_txpace_step_error;record[20]=aspect_txpace_count;cancel_phase=0;drop_if=ASPECT_TXPACE_BEFORE_MEASURE;status=aspect_txpace_prepare(step);after=aspect_txpace_flags();record[21]=status;record[22]=after&512;record[23]=aspect_txpace_count;record[24]=calls[1];record[25]=calls[2];record[26]=calls[3];record[27]=calls[4];f=fopen("RESULT.BIN","wb");if(!f)return 2;if(fwrite(record,2,28,f)!=28||fclose(f))return 3;return 0;}
''';(OUT/'diagnostic.c').write_text(source)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-fe=TXPACE.EXE','diagnostic.c','txpace.obj','native.obj'],cwd=OUT,check=True)
 files=['src/aspect/txpace.c','src/aspect/txpace.h','src/aspect/txpace.asm','standalone/build_aspect_txpace.py','standalone/omf_imports.py','reconstruction/uart/encodings.inc']
 report=dict(original_inputs=[],sources={p:sha(ROOT/p)for p in files},outputs={p:sha(OUT/p)for p in ['delay.bin','native.obj','txpace.obj','diagnostic.c','TXPACE.EXE']})
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('BuiltTXPACEsourcecomponent+actualDOSdiagnostic')
if __name__=='__main__':main()
