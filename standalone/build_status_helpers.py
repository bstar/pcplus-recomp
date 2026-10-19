#!/usr/bin/env python3
"""Build native status helpers, maintained formatter and source-only DOS proof."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/status-helpers'
BASE=ROOT/'standalone/fixtures/status_helper_units.json'
VECTORS=ROOT/'standalone/fixtures/status_formatter_vectors.json'
SOURCE=ROOT/'src/status/status_helpers.asm'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clit(b):return '"'+''.join('\\%03o'%x for x in b)+'"'
def main():
 OUT.mkdir(parents=True,exist_ok=True);units=json.loads(BASE.read_text())['units'];vectors=json.loads(VECTORS.read_text())['cases'];deps={}
 for u in units:
  p=OUT/f"unit{u['unit']}.bin";subprocess.run(['nasm','-f','bin','-Ireconstruction/uart/','-DSTATUS_HELPERS_FLAT',f"-DSTATUS_HELPERS_UNIT={u['unit']}",str(SOURCE.relative_to(ROOT)),'-o',str(p)],cwd=ROOT,check=True);assert p.stat().st_size==u['bytes']and sha(p)==u['sha256']
 objects=[]
 def asm(src,name,flags=()):
  p=OUT/(name+'.obj');subprocess.run(['nasm','-f','obj','-Ireconstruction/uart/',*flags,src,'-o',str(p)],cwd=ROOT,check=True);objects.append(p.name);deps[src]=sha(ROOT/src)
 asm('src/status/status_helpers.asm','status_helpers')
 # Exercise configurable segment and renamed imports at assembly time.
 subprocess.run(['nasm','-f','obj','-Ireconstruction/uart/','-DSTATUS_HELPERS_CONFIG','-Dstatus_sprintf=status_renamed_format','-Dui_write_string=status_renamed_write','src/status/status_helpers.asm','-o',str(OUT/'status_helpers_config.obj')],cwd=ROOT,check=True)
 for src,name,macro in [('reconstruction/ui_windows/write_string.asm','write_string','UI_WINDOWS_OMF'),('reconstruction/ui_windows/coordinate.asm','coordinate','UI_WINDOWS_OMF'),('reconstruction/ui_windows/cga_blank.asm','cga_blank','UI_WINDOWS_OMF'),('reconstruction/ui_windows/cga_unblank.asm','cga_unblank','UI_WINDOWS_OMF'),('reconstruction/terminal_reset/status_fill.asm','status_fill','TERMINAL_RESET_OMF'),('reconstruction/text/fill.asm','text_fill','TEXT_OMF'),('reconstruction/program_exec/strlen.asm','strlen','PROGRAM_EXEC_OMF')]:asm(src,name,['-D'+macro])
 asm('standalone/status_helpers_host.asm','host')
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-fo='+str(OUT/'status_formatter.obj'),'src/status/status_formatter.c'],cwd=ROOT,check=True);objects.append('status_formatter.obj')
 c=['#include <stdlib.h>','#include <stdio.h>','#include <string.h>','#include <dos.h>','#include "../../src/status/status_formatter.h"','extern int status_diag_error;','void status_diag_printf(const char *,const unsigned *);','void status_diag_message(const char *);','void status_diag_fill(unsigned,unsigned,unsigned);','void status_diag_cga_unavailable(void){exit(99);}', 'static unsigned char screen[4004];','static void clear_video(void){unsigned i;unsigned char __far *v=MK_FP(0xb800,0);for(i=0;i<4004;++i)v[i]=0xcc;}','static int dump(const char *name){unsigned i;FILE*f;unsigned char __far*v=MK_FP(0xb800,0);for(i=0;i<4004;++i)screen[i]=v[i];f=fopen(name,"wb");if(!f)return 1;if(fwrite(screen,1,4004,f)!=4004||fclose(f))return 2;return 0;}','int main(void){unsigned words[16];char out[150];int result;FILE*f;']
 composed=[]
 for i,v in enumerate(vectors):
  c.append('memset(out,0,sizeof(out));memset(words,0,sizeof(words));')
  for j,a in enumerate(v['args']):c.append('words[%d]=%s;'%(j,'(unsigned)'+clit(bytes.fromhex(a['string_hex']))if'string_hex'in a else str(a['word'])))
  c.append('result=status_format(out,%d,%s,words,%d);f=fopen("T%02d.BIN","wb");if(!f)return 1;fwrite(&result,2,1,f);fwrite(out,1,result<0?1:result+1,f);if(fclose(f))return 2;'%(v['cap'],clit(bytes.fromhex(v['format_hex'])),v['argc'],i))
  if v['name']in('normal','novel','empty','cp437','alt_empty','alt_novel','alt_cp437'):
   c.append('clear_video();status_diag_printf(%s,words);if(status_diag_error!=%d||dump("U%02d.BIN"))return 3;'%(clit(bytes.fromhex(v['format_hex'])),v['expected_result'],i));composed.append(i)
 c+=['clear_video();status_diag_message("TEST");if(dump("MESSAGE.BIN"))return 4;','clear_video();status_diag_fill(3,3842,90);if(dump("FILL.BIN"))return 5;','return 0;}'];(OUT/'diagnostic.c').write_text('\n'.join(c)+'\n')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-fe=STATUS.EXE','diagnostic.c',*objects],cwd=OUT,check=True)
 deps.update({p:sha(ROOT/p)for p in ['src/status/status_formatter.c','src/status/status_formatter.h','reconstruction/uart/encodings.inc','standalone/fixtures/status_helper_units.json','standalone/fixtures/status_formatter_vectors.json']})
 report=dict(original_inputs=[],builder_sha256=sha(Path(__file__)),source_dependencies=deps,units=units,native_bytes=175,diagnostic_sha256=sha(OUT/'STATUS.EXE'),generated_c_sha256=sha(OUT/'diagnostic.c'),objects={name:sha(OUT/name)for name in objects+['status_helpers_config.obj']},composed_vector_indices=composed)
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built175 native bytes+CONFIG formatter+STATUS.EXE')
if __name__=='__main__':main()
