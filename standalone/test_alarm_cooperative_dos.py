#!/usr/bin/env python3
"""Actual DOS8086 native alert with serviced callbacks, faults and cleanup."""
import argparse,json,os,re,subprocess
from pathlib import Path
from build_context_help import ROOT,sha

C=r'''
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "alarm_cooperative.h"
#define DAY 1573040UL
static unsigned checks,failures,cases,current;
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL case%u check%u\n",current,checks);}}
static unsigned flags(void);
#pragma aux flags = "pushf" "pop ax" value [ax] modify exact [ax];
static unsigned dseg(void);
#pragma aux dseg = "mov ax,ds" value [ax] modify exact [ax];
static unsigned sseg(void);
#pragma aux sseg = "mov ax,ss" value [ax] modify exact [ax];
typedef struct model {
 unsigned valid,services,step,key_after,key_value,reads,starts,polls,stops,owned,active;
 unsigned service_error,poll_error,stop_error,busy,invalid_seconds,invalid_ticks,lose_context,reentry,reentered;
 unsigned long ticks,started,received;
} model;
static alarm_coop_ops ops;
static void reset(model *m){memset(m,0,sizeof(*m));m->valid=m->step=1;m->key_after=65535U;m->key_value=0x011b;}
static unsigned ALARM_CALL context(void *p){model *m=p;return m->valid&&dseg()==sseg()&&(flags()&0x200);}
static unsigned ALARM_CALL service(void *p){
 model *m=p;++m->services;m->received+=7;
 if(m->lose_context&&m->services==m->lose_context)m->valid=0;
 if(m->reentry&&!m->reentered){m->reentered=1;ck(alarm_coop_run(&ops,m,1,1,1000UL)==ALARM_COOP_BUSY);ck(alarm_coop_recover()==ALARM_COOP_BUSY);}
 m->ticks=(m->ticks+m->step)%DAY;return m->service_error&&m->services==m->service_error;
}
static unsigned long ALARM_CALL ticks(void *p){model *m=p;return m->invalid_ticks?DAY:m->ticks;}
static unsigned ALARM_CALL seconds(void *p){model *m=p;return m->invalid_seconds?60:(unsigned)(m->ticks/18UL)%60;}
static unsigned ALARM_CALL peek(void *p){model *m=p;return m->services>=m->key_after;}
static unsigned ALARM_CALL read_key(void *p){model *m=p;ck(m->services>=m->key_after);++m->reads;m->key_after=65535U;return m->key_value;}
static unsigned ALARM_CALL start(void *p,unsigned frequency,unsigned duration){
 model *m=p;++m->starts;ck(frequency==880&&duration==3);
 if(m->busy)return 1;
 ck(!m->owned);m->owned=m->active=1;m->started=m->ticks;return 0;
}
static unsigned ALARM_CALL poll(void *p){
 model *m=p;unsigned long elapsed=m->ticks>=m->started?m->ticks-m->started:m->ticks+DAY-m->started;
 ++m->polls;ck(m->owned);if(m->poll_error)return 2;
 if(elapsed<3)return 1;m->active=0;return 0;
}
static unsigned ALARM_CALL stop(void *p){
 model *m=p;++m->stops;ck(m->owned);
 if(m->stop_error){--m->stop_error;return 1;}
 m->owned=m->active=0;return 0;
}
static unsigned run(model *m,unsigned duration,unsigned sound,unsigned long budget){
 alarm_coop_report r;unsigned result,old_flags=flags();
 void (__interrupt __far *v0)(void)=_dos_getvect(0);
 void (__interrupt __far *v16)(void)=_dos_getvect(0x16);
 void (__interrupt __far *v21)(void)=_dos_getvect(0x21);
 current=++cases;result=alarm_coop_run(&ops,m,duration,sound,budget);alarm_coop_result(&r);
 ck(result==r.status);ck(r.service_calls==m->services);ck(m->received==7UL*m->services);
 ck(r.key_consumed==m->reads);if(m->reads)ck(r.key_word==m->key_value);
 ck((flags()&0x600)==(old_flags&0x600)&&dseg()==sseg());
 ck(_dos_getvect(0)==v0&&_dos_getvect(0x16)==v16&&_dos_getvect(0x21)==v21);
 if(result!=ALARM_COOP_CLEANUP)ck(!alarm_coop_active()&&!m->owned&&!m->active);
 return result;
}
int main(void){
 model m;alarm_coop_ops bad;alarm_coop_report r;unsigned d,s,k,n,result;
 static const unsigned keys[]={0x011b,0x1e61,0x3b00,0x0100};
 ops.context=context;ops.service=service;ops.ticks=ticks;ops.seconds=seconds;
 ops.peek=peek;ops.read=read_key;ops.tone_start=start;ops.tone_poll=poll;ops.tone_stop=stop;
 for(d=0;d<4;++d)for(s=0;s<2;++s)for(k=0;k<5;++k){
  reset(&m);if(k<4){m.key_after=k+1;m.key_value=keys[k];}
  ck(run(&m,d,s,10000UL)==ALARM_COOP_OK);
  if(!s||!d)ck(!m.starts&&!m.stops);if(k<4)ck(m.reads==((d||k<2)?1:0));
 }
 reset(&m);m.key_after=2;ck(run(&m,0,0,1000UL)==ALARM_COOP_OK);ck(m.services==2&&m.reads==1);
 reset(&m);m.ticks=DAY-2;ck(run(&m,2,1,10000UL)==ALARM_COOP_OK);ck(m.starts>0);
 for(n=1;n<=40;++n){reset(&m);m.service_error=n;ck(run(&m,3,1,10000UL)==ALARM_COOP_SERVICE);ck(!m.reads);}
 for(s=0;s<2;++s){reset(&m);m.step=0;ck(run(&m,3,s,20UL)==ALARM_COOP_BUDGET);ck(m.services==20&&!m.reads);}
 reset(&m);m.poll_error=1;ck(run(&m,2,1,1000UL)==ALARM_COOP_SOUND);ck(m.starts==1&&m.stops==1&&!m.reads);
 reset(&m);m.busy=1;ck(run(&m,2,1,1000UL)==ALARM_COOP_SOUND);ck(m.starts==1&&!m.stops&&!m.reads);
 reset(&m);m.invalid_ticks=1;ck(run(&m,2,1,1000UL)==ALARM_COOP_CLOCK);ck(m.starts==1&&m.stops==1);
 reset(&m);m.invalid_seconds=1;ck(run(&m,2,1,1000UL)==ALARM_COOP_CLOCK);ck(!m.services&&!m.starts);
 reset(&m);m.valid=0;ck(run(&m,2,1,1000UL)==ALARM_COOP_CONTEXT);ck(!m.services&&!m.starts);
 reset(&m);m.reentry=1;ck(run(&m,1,1,1000UL)==ALARM_COOP_OK);ck(m.reentered);
 reset(&m);m.stop_error=1;result=run(&m,2,1,1000UL);
 ck(result==ALARM_COOP_CLEANUP&&alarm_coop_active()&&m.owned&&m.stops==1);
 ck(alarm_coop_run(&ops,&m,1,1,1000UL)==ALARM_COOP_BUSY);ck(m.stops==1);
 ck(alarm_coop_recover()==ALARM_COOP_CLEANUP);ck(!alarm_coop_active()&&!m.owned&&m.stops==2);
 reset(&m);m.lose_context=3;result=run(&m,2,1,1000UL);
 ck(result==ALARM_COOP_CLEANUP&&alarm_coop_active()&&m.owned&&!m.stops);
 alarm_coop_result(&r);ck(r.cause==ALARM_COOP_CONTEXT&&!r.key_consumed);
 m.valid=1;ck(alarm_coop_recover()==ALARM_COOP_CONTEXT);ck(!alarm_coop_active()&&!m.owned&&m.stops==1);
 reset(&m);m.key_after=1;ck(run(&m,65535U,1,1000UL)==ALARM_COOP_OK);ck(m.reads==1&&!m.starts);
 current=++cases;bad=ops;bad.service=0;
 ck(alarm_coop_run(&bad,&m,1,0,1000UL)==ALARM_COOP_ARGUMENT);ck(!alarm_coop_active());
 ck(alarm_coop_run(0,&m,1,0,1000UL)==ALARM_COOP_ARGUMENT);
 ck(alarm_coop_run(&ops,&m,1,0,0)==ALARM_COOP_ARGUMENT);
 printf("ALARM_COOP %u cases %u checks %u failures\n",cases,checks,failures);return failures?1:0;
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 names=['src/aspect/alarm_native.asm','src/aspect/alarm_cooperative.c','src/aspect/alarm_cooperative.h','src/aspect/alarm_cooperative_bridge.asm','standalone/test_alarm_cooperative_dos.py','reconstruction/uart/encodings.inc','standalone/build_context_help.py']
 sources={n:sha(ROOT/n) for n in names};source=out/'harness.c';source.write_text(C);objects=[]
 for name,file in [('native','src/aspect/alarm_native.asm'),('bridge','src/aspect/alarm_cooperative_bridge.asm')]:
  obj=out/(name+'.obj');subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/file),'-o',str(obj)],check=True);objects.append(str(obj))
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-i='+str(ROOT/'src/aspect'),'-fm='+str(out/'ALARM.map'),'-fe='+str(out/'ALARM.EXE'),str(source),str(ROOT/'src/aspect/alarm_cooperative.c'),*objects],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nALARM >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 text=(out/'RESULT.TXT').read_text() if (out/'RESULT.TXT').exists() else '';match=re.search(r'ALARM_COOP (\d+) cases (\d+) checks 0 failures',text)
 passed=bool(match and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists())
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 report=dict(passed=passed,cases=int(match[1]) if match else 0,checks=int(match[2]) if match else 0,output=text,sources=sources,original_inputs=[],artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},scope=__doc__+' Recovered native93-byte alert actually executes on DOS8086 through C/RET2/RET4 bridge. Context/transport/clock/key/speaker callbacks modeled; no actual UART/PIT/acoustic or parent/VM binding. Key completion, bounded frozen clocks, service failures, busy/failed sound and retained cleanup recovery tested. No script cancellation is invented from an ordinary alert key.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(text);return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
