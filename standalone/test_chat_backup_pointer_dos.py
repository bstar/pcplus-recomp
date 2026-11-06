#!/usr/bin/env python3
"""Check actual parent Chat backup pointer and contents, including API0104 control."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
from build_path_session import ROOT,sha
HOST=r'''
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/presentation.h"
#include "parent.h"
typedef struct invocation {unsigned ds,sp,off,seg,ax,count,args[8],result,flags;} invocation;
extern unsigned __cdecl chat_parent_invoke(invocation *);
static invocation call;static unsigned segment,errors;
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned largest(void){unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
#define PTR(n) MK_FP(segment+n##_SEG,n##_OFF)
#define WORD(n) (*(unsigned __far *)PTR(n))
#define CHECK(c) do{if(!(c)){++errors;printf("FAIL %u\n",__LINE__);}}while(0)
static unsigned run(unsigned off,unsigned seg,unsigned ax)
{call.ds=segment+PARENT_DS;call.sp=PARENT_SP-4096;call.off=off;call.seg=segment+seg;call.ax=ax;call.count=0;return chat_parent_invoke(&call);}
#define RUN(n,ax) run(n##_OFF,n##_SEG,ax)
int main(void)
{
 unsigned initial=largest(),i,free_after;union REGS in,out;struct SREGS sr;struct{unsigned load,reloc;}block;
 chat_word __far *video=MK_FP(0xb800,0),__far *backup;
 chat_session __far *s;chat_presentation __far *p;
 if(_dos_allocmem(PARENT_PARAS,&segment))return 2;
 for(i=0;i<PARENT_PARAS;i+=1024){unsigned n=PARENT_PARAS-i;if(n>1024)n=1024;_fmemset(MK_FP(segment+i,0),0,n*16);}
 block.load=block.reloc=segment;memset(&in,0,sizeof(in));segread(&sr);in.x.ax=0x4b03;in.x.dx=(unsigned)"PARENT.EXE";sr.es=sr.ss;in.x.bx=(unsigned)&block;intdosx(&in,&out,&sr);if(out.x.cflag)return 3;
 free_after=largest();WORD(PSP)=psp();WORD(MODE)=1;s=(chat_session __far *)((unsigned char __far *)PTR(FROZEN)+12288);
 for(i=0;i<2000;++i)video[i]=0x1741+(i%26);
 RUN(KEYFRONT,0x1800);CHECK(WORD(OWNER)==2&&s->presentation);
 if(!s->presentation)return 4;p=s->presentation;backup=PTR(FRAME);
 CHECK(p->backup==backup&&FP_SEG(p->backup)==segment+FRAME_SEG&&FP_OFF(p->backup)==FRAME_OFF);
 for(i=0;i<2000;++i)CHECK(backup[i]==0x1741+(i%26));
 RUN(FRONTSTOP,0);CHECK(WORD(OWNER)==0&&!s->presentation);
 for(i=0;i<2000;++i)CHECK(video[i]==0x1741+(i%26));
 CHECK(largest()==free_after);CHECK(_dos_freemem(segment)==0&&largest()==initial);
 printf("POINTER errors=%u frame_cells=2000\n",errors);return errors?1:0;
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary,out=a.terminal.resolve(),a.output.resolve();assert not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_foreground_text'] and sha(binary)==m['binary_sha256']
 listing=binary.with_name('terminal.map').read_text();symbols={n:(int(off,16),int(seg,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 constants=dict(PARENT_DS=int(re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I)[1],16),PARENT_SP=symbols['terminal_stack_top'][0],PARENT_PARAS=(m['memory_layout']['minimum_allocated_module_bytes']+15)//16)
 for label,n in dict(KEYFRONT='terminal_chat_key_far',FRONTSTOP='terminal_chat_stop_far',OWNER='_redisplay_active',FROZEN='redisplay_snapshot',FRAME='redisplay_view',PSP='process_psp',MODE='modes_value_1d1a').items():constants[label+'_OFF'],constants[label+'_SEG']=symbols[n]
 sources={**m['sources'],'standalone/test_chat_backup_pointer_dos.py':sha(Path(__file__)),'standalone/chat_parent_invoke.asm':sha(ROOT/'standalone/chat_parent_invoke.asm')}
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);drive=out/'drive';drive.mkdir();(drive/'pointer.c').write_text(HOST.replace('../src/chat/presentation.h',str(ROOT/'src/chat/presentation.h')))
 (drive/'parent.h').write_text(''.join('#define '+k+' '+str(v)+'\n' for k,v in constants.items()))
 shutil.copyfile(binary,drive/'PARENT.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',drive/'PCCHAT.OVL')
 subprocess.run(['nasm','-fobj',str(ROOT/'standalone/chat_parent_invoke.asm'),'-o','invoke.obj'],cwd=drive,check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-k4096','-dCHAT_PRESENTATION','-dCHAT_TEXT','-dCHAT_TIMING','-dCHAT_FOREGROUND_TEXT',*(['-dCHAT_REDISPLAY'] if m['experimental_chat_redisplay'] else []),'-fe=POINTER.EXE','pointer.c','invoke.obj'],cwd=drive,check=True)
 (out/'dosbox.conf').write_text('[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nPOINTER >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=45)
 text=(drive/'RESULT.TXT').read_text();passed=r.returncode==0 and 'POINTER errors=0 frame_cells=2000' in text and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists()
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 report=dict(passed=passed,binary_sha256=sha(binary),module_sha256=sha(drive/'PCCHAT.OVL'),api=m['chat_loader']['module']['api_version'],sources=sources,constants=constants,output=text,scope=__doc__+' Real DOS parent/module on parent DS=SS. Pointer equality, all saved cells, restored cells and arena lifetime; no ordinary main or physical hardware.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(text);assert passed
if __name__=='__main__':main()
