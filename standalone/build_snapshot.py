#!/usr/bin/env python3
"""Source-only native screen snapshot with memory-FILE/UI fixture."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/snapshot';MODULE=ROOT/'reconstruction/snapshot'
DRIVER=r'''
#include <string.h>
#include <i86.h>
extern unsigned __cdecl snapshot_copy_c(unsigned,unsigned,unsigned,char *);
extern unsigned __cdecl snapshot_row_c(unsigned,char *);
extern void __cdecl snapshot_writer_c(unsigned);
extern void __cdecl snapshot_keyboard_c(void);
extern unsigned char fixture_cells[],fixture_destination[],fixture_output[];
extern unsigned __cdecl snapshot_shadow_segment,fixture_output_count,fixture_write_calls;
extern unsigned fixture_open_calls,fixture_close_calls,fixture_status_calls;
extern unsigned fixture_wait_calls,fixture_keyboard_calls,fixture_error_calls;
extern unsigned fixture_open_result;
int main(void)
{
 struct SREGS regs;segread(&regs);snapshot_shadow_segment=regs.ds;
 if(snapshot_copy_c(5,(unsigned)fixture_cells,regs.ds,(char *)fixture_destination)!=4)return 1;
 if(memcmp(fixture_destination," A B ",5) || fixture_destination[5])return 2;
 if(snapshot_row_c(1,(char *)fixture_destination)!=0)return 3;
 snapshot_writer_c(0);
 if(fixture_output_count!=12 || memcmp(fixture_output," A B\r\n\r\nZ \r\n",12))return 4;
 if(fixture_write_calls!=3 || fixture_close_calls!=1 || fixture_status_calls || fixture_wait_calls)return 5;
 snapshot_keyboard_c();
 if(fixture_output_count!=24 || memcmp(fixture_output+12,fixture_output,12))return 6;
 if(fixture_status_calls!=1 || fixture_wait_calls!=1 || fixture_keyboard_calls!=2)return 7;
 fixture_open_result=0;snapshot_writer_c(1);
 if(fixture_error_calls!=1 || fixture_close_calls!=2 || fixture_output_count!=24)return 8;
 return 0;
}
'''
def main():
 OUT.mkdir(parents=True,exist_ok=True);proof=json.loads((MODULE/'provenance.json').read_text())
 for unit in proof['units']:
  out=OUT/(Path(unit['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/unit['source']),'-o',str(out)],check=True)
  data=out.read_bytes();assert len(data)==unit['bytes'] and hashlib.sha256(data).hexdigest()==unit['sha256']
 sources=[MODULE/u['source'] for u in proof['units']]+[ROOT/p for p in proof['reused_sources']]+[ROOT/'standalone/snapshot_host.asm'];objects=[]
 for i,path in enumerate(sources):
  obj=OUT/f'{i:02d}-{path.stem}.obj';objects.append(str(obj));subprocess.run(['nasm','-fobj','-DSNAPSHOT_OMF','-DPROGRAM_EXEC_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
 (OUT/'main.c').write_text(DRIVER)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=snapshot.map','-fe=SNAPSHOT.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
 result={'binary_sha256':hashlib.sha256((OUT/'SNAPSHOT.EXE').read_bytes()).hexdigest(),'exact_snapshot_bytes':sum(u['bytes'] for u in proof['units']),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'Actual native snapshot row/video/copy/writer instructions, original reused CRT string copies; explicit memory-FILE and UI callbacks, not live capture integration or real snapshot file ownership.'}
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built SNAPSHOT.EXE',result['exact_snapshot_bytes'],'exact bytes')
if __name__=='__main__':main()
