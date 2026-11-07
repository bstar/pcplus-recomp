#!/usr/bin/env python3
"""Compare both actual child-client response branches under declared scalar boundaries."""
import argparse,json,os,re,subprocess
from pathlib import Path
from build_context_help import ROOT,sha
FLAGS=['ASPECT_EXTERNAL_RENDER','ASPECT_EXTERNAL_UNWIND','ASPECT_SNAPSHOT_LEASE','ASPECT_ALARM_VM','ASPECT_EMULATE_VM']

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 source=ROOT/'src/aspect/resident_render.c';text=source.read_text()
 definitions=re.findall(r'^(?:unsigned|void)[^\n;{]*?\b(aspect_render_\w+)\([^\n;{]*\)\s*\{',text,re.M)
 prototypes=re.findall(r'^((?:unsigned|void)[^\n;{]*?\b(aspect_render_\w+)\([^\n;{]*\))\s*\{',text,re.M)
 names=sorted(set(definitions)|{'aspect_render_parent_entry','aspect_render_client_record'})
 decl=[]
 for prefix in ('old','new'):
  for proto,name in prototypes:decl.append(proto.replace(name,prefix+'_'+name)+';')
 objects=[]
 for prefix in ('old','new'):
  obj=out/(prefix+'.obj');flags=['-d'+n for n in FLAGS]+(['-dASPECT_RENDER_RESPONSE_LEGACY']if prefix=='old'else[])
  flags+=['-d'+n+'='+prefix+'_'+n for n in names]
  subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we',*flags,'-i='+str(ROOT/'src/aspect'),'-fo='+str(obj),str(source)],cwd=out,check=True);objects.append(str(obj))
 program=r'''
#include <stdio.h>
#include <string.h>
#include "runtime.h"
#include "serial.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
#include "when_runtime.h"
'''+ '\n'.join(decl)+r'''
unsigned aspect_serial_active,runtime_error,runtime_set_duplex_changed,runtime_serial_local_echo;
unsigned runtime_serial_break_units,runtime_keyboard_mode,runtime_serial_error;
static unsigned variant,reply,bad_callback,bad_check,nested_mode,window_value,depth;
static unsigned calls,requests,nested,nested_result,deferred,trace[64],used;
static unsigned callback(unsigned op,unsigned v){
 unsigned r=variant?new_aspect_render_callback_dispatch(op,v):old_aspect_render_callback_dispatch(op,v);
 if(used+3<=64){trace[used++]=op;trace[used++]=v;trace[used++]=r;}return r;
}
unsigned __cdecl aspect_render_client_prepare(void){return 0;}
unsigned __cdecl aspect_render_client_check(void){++calls;return bad_check&&calls==bad_check?10:0;}
unsigned __cdecl aspect_render_callback_offset(void){return 100;}
unsigned __cdecl aspect_render_code_segment(void){return 200;}
unsigned __cdecl aspect_render_request(unsigned op,unsigned value){
 unsigned i;++requests;++depth;
 if(nested_mode&&depth==1&&(op==4||op==6||op==7||op==8||op==11)){
  ++nested;nested_result=variant?new_aspect_render_emulate(4):old_aspect_render_emulate(4);
 }
 if(op==4)callback(6,350);
 if(op==7)callback(8,16);
 if(op==8){callback(9,0);if(value==0x2c00)callback(11,window_value);}
 if(op==11)callback(11,window_value);
 if(op==6)for(i=0;i<13;++i)if(!callback(7,i))break;
 if(bad_callback)callback(99,0);
 --depth;if(op==13 && !reply)return value==0?0xff01U:value==1?0xff04U:0xff00U;return reply;
}
void runtime_set_error(unsigned value){runtime_error=value;}
unsigned runtime_console_cancel_poll(void){return 0;}
unsigned runtime_receive_raw_character(unsigned value){return value?65535:65535;}
unsigned runtime_serial_poll(void){return 0;}
unsigned runtime_serial_send(unsigned value){return value>255?14:0;}
unsigned __cdecl aspect_serial_available(void){return 0;}
unsigned __cdecl aspect_serial_unread(void){return 0;}
void runtime_when_defer_begin(void){++deferred;}
void runtime_when_defer_end(void){--deferred;}
#define CALL(name,args) (variant?new_aspect_render_##name args:old_aspect_render_##name args)
typedef struct outcome{unsigned result,checks,requests,nested,nested_result,error,units,keyboard,deferred,used,trace[64],probe,duration,enabled;} outcome;
static void run(outcome *o,unsigned which,unsigned owner,unsigned serial,unsigned response,unsigned bad,unsigned check,unsigned nesting){
 unsigned i,duration=0x5555,enabled=0x6666;memset(o,0,sizeof(*o));reply=bad_callback=bad_check=nested_mode=window_value=depth=0;
 aspect_serial_active=1;runtime_error=runtime_serial_error=runtime_serial_break_units=runtime_keyboard_mode=deferred=0;
 runtime_set_duplex_changed=1;runtime_serial_local_echo=1;
 if(CALL(prepare,(1,2,3))||CALL(attach,())){puts("SETUP FAILED");o->result=65535;return;}
 if(owner==1)CALL(program_begin,(0));
 if(owner==2){window_value=1;CALL(key,(0x2c00));}
 if(owner==3)CALL(confirm,(0));
 if(owner==4)CALL(finish,());
 aspect_serial_active=serial;reply=response;bad_callback=bad;bad_check=check;nested_mode=nesting;
 calls=requests=nested=nested_result=used=0;
 switch(which){
 case 0:o->result=CALL(emit,(65));break;
 case 1:o->result=CALL(status,(65535));break;
 case 2:o->result=CALL(status,(256));break;
 case 3:o->result=CALL(break_notice,(0));break;
 case 4:o->result=CALL(break_notice,(2));break;
 case 5:o->result=CALL(emulate,(4));break;
 case 6:o->result=CALL(emulate,(256));break;
 case 7:o->result=CALL(policy_inherit,());break;
 case 8:o->result=CALL(keyboard_inherit,());break;
 case 9:o->result=CALL(key,(65));break;
 case 10:o->result=CALL(key,(0x2c00));break;
 case 11:o->result=CALL(window_service,());break;
 case 12:o->result=CALL(script_label,("D:\\CASE.ASX",65535));break;
 case 13:o->result=CALL(alarm_policy,(&duration,&enabled));break;
 case 14:o->result=CALL(alarm_policy,(0,&enabled));break;
 default:o->result=CALL(alarm_policy,(&duration,0));break;
 }
 o->duration=duration;o->enabled=enabled;
 o->checks=calls;o->requests=requests;o->nested=nested;o->nested_result=nested_result;o->error=runtime_error;
 o->units=runtime_serial_break_units;o->keyboard=runtime_keyboard_mode;o->deferred=deferred;o->used=used;
 for(i=0;i<used;++i)o->trace[i]=trace[i];
 reply=bad_callback=bad_check=nested_mode=0;aspect_serial_active=1;
 o->probe=CALL(emulate,(6));
 if(CALL(program_active,()))CALL(program_end,(0));
 CALL(finish,());
}
int main(void){
 static unsigned replies[]={0,1,3,7,10,13,14,15,65531,65534};
 unsigned which,owner,serial,r,bad,check,nesting;unsigned long count=0,failures=0;outcome a,b;
 for(which=0;which<16;++which)for(owner=0;owner<5;++owner)for(serial=0;serial<3;++serial)
 for(r=0;r<10;++r)for(bad=0;bad<2;++bad)for(check=0;check<4;++check)for(nesting=0;nesting<2;++nesting){
  variant=0;run(&a,which,owner,serial,replies[r],bad,check,nesting);
  variant=1;run(&b,which,owner,serial,replies[r],bad,check,nesting);
  if(a.result==65535||memcmp(&a,&b,sizeof(a))){
   if(failures<5)printf("MISMATCH %u %u %u %u %u %u %u old%u new%u\n",which,owner,serial,r,bad,check,nesting,a.result,b.result);
   ++failures;
  }
  ++count;
 }
 printf("RESPONSES %lu cases %lu failures\n",count,failures);return failures?1:0;
}
'''
 (out/'test.c').write_text(program)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-k8192',*['-d'+n for n in FLAGS],'-i='+str(ROOT/'src/aspect'),'-fe=RESP.EXE',str(out/'test.c'),*objects],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nRESP >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 with(out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=120)
 count=16*5*3*10*2*4*2;text=(out/'RESULT.TXT').read_text();assert (out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists() and text.strip()=='RESPONSES '+str(count)+' cases 0 failures',text
 deps={str(source.relative_to(ROOT)):sha(source),'standalone/test_render_response_equivalence_dos.py':sha(Path(__file__)),'standalone/build_context_help.py':sha(ROOT/'standalone/build_context_help.py')}
 for f in (ROOT/'src/aspect').glob('*.h'):deps[str(f.relative_to(ROOT))]=sha(f)
 r=dict(passed=True,cases=count,sources=deps,artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()},original_inputs=[],scope=__doc__+' Actual DOS8086 C clients, legacy vs shared ready/completion blocks,16 request paths,detached/PROGRAM/window/confirm owners,serial0/1/2,typed/bridge results,callback errors,pre/post client faults and nested EMULATE during synchronous callbacks. Results,call counts,callback trace,policy values and subsequent probe compared. Scalar bridge/client-check/serial/receive boundaries modeled; not actual far bridge, hardware or full ASPECT execution.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
