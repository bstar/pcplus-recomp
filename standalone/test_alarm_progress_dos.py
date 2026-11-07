#!/usr/bin/env python3
"""DOS8086 ALARM progress watchdog: full modeled32767 counts and frozen clocks."""
import json
import re
import sys
from pathlib import Path
import test_alarm_cooperative_dos as legacy
from build_context_help import ROOT, sha


def main():
    # Retain the existing independent ABI/vector/receive accounting and modeled
    # speaker owner, widening counters so the long test cannot fabricate a key.
    text = legacy.C.split('int main(void){')[0]
    text = text.replace('static unsigned checks,failures,cases,current;',
                        'static unsigned long checks;\nstatic unsigned failures,cases,current;')
    text = text.replace('check%u', 'check%lu')
    text = text.replace('unsigned valid,services,step,key_after,key_value,reads,starts,polls,stops,owned,active;',
                        'unsigned valid,step,key_value,reads,owned,active;\n unsigned long services,key_after,starts,polls,stops,clock_ticks;\n unsigned freeze_seconds,freeze_ticks,tick_period,second_period;')
    text = text.replace('m->valid=m->step=1;', 'm->valid=m->step=m->tick_period=1;m->second_period=18;')
    text = text.replace('m->key_after=65535U', 'm->key_after=0xffffffffUL')
    text = text.replace('m->ticks=(m->ticks+m->step)%DAY;',
                        'if(!m->freeze_ticks&&m->services%m->tick_period==0)m->ticks=(m->ticks+m->step)%DAY;\n if(!m->freeze_seconds)m->clock_ticks+=m->step;')
    text = text.replace('(m->ticks/18UL)%60', '(m->clock_ticks/m->second_period)%60')
    text = text.replace('static alarm_coop_ops ops;', 'static alarm_coop_ops ops;\nstatic unsigned progress_mode;')
    text = text.replace('result=alarm_coop_run(&ops,m,duration,sound,budget);',
                        'result=progress_mode?alarm_coop_run_progress(&ops,m,duration,sound,budget):alarm_coop_run(&ops,m,duration,sound,budget);')
    assert 'result=progress_mode?' in text
    text += r'''
int main(void){
 model m;alarm_coop_report r;unsigned i,s,result;
 static const unsigned durations[]={0,1,4,59,60,32767};
 ops.context=context;ops.service=service;ops.ticks=ticks;ops.seconds=seconds;
 ops.peek=peek;ops.read=read_key;ops.tone_start=start;ops.tone_poll=poll;ops.tone_stop=stop;
 /* The old total budget really fails despite ordinary advancing clocks. */
 reset(&m);ck(run(&m,4,0,64UL)==ALARM_COOP_BUDGET);ck(m.services==64);
 progress_mode=1;
 for(i=0;i<6;++i)for(s=0;s<2;++s){
  reset(&m);ck(run(&m,durations[i],s,64UL)==ALARM_COOP_OK);
  ck(!m.reads&&m.starts==m.stops);
  if(durations[i]>=4)ck(m.services>64UL);
  printf("PROGRESS duration%u sound%u services%lu\n",durations[i],s,m.services);
 }
 /* Same clock ratio, four polls per BIOS tick: the production total limit
  * fails before32767 counts. Progress policy completes beyond that total. */
 progress_mode=0;reset(&m);m.tick_period=4;m.second_period=72;
 ck(run(&m,32767,0,2000000UL)==ALARM_COOP_BUDGET);ck(m.services==2000000UL);
 printf("TOTAL_LIMIT services%lu\n",m.services);
 progress_mode=1;
 for(s=0;s<2;++s){reset(&m);m.tick_period=4;m.second_period=72;
  ck(run(&m,32767,s,512UL)==ALARM_COOP_OK);ck(m.services>2000000UL&&!m.reads);
  printf("FAST sound%u services%lu\n",s,m.services);
 }
 /* DOS second rollover and BIOS day rollover are independent clocks. */
 for(s=0;s<2;++s){reset(&m);m.ticks=DAY-2;m.clock_ticks=59UL*18;
  ck(run(&m,4,s,64UL)==ALARM_COOP_OK);ck(!m.reads);}
 for(s=0;s<2;++s){
  reset(&m);m.freeze_seconds=m.freeze_ticks=1;
  ck(run(&m,32767,s,64UL)==ALARM_COOP_BUDGET);ck(m.services==64&&!m.reads);
  reset(&m);m.freeze_seconds=1;
  ck(run(&m,32767,s,64UL)==ALARM_COOP_BUDGET);ck(m.services==64&&!m.reads);
 }
 reset(&m);m.freeze_ticks=1;
 ck(run(&m,32767,1,64UL)==ALARM_COOP_BUDGET);ck(m.services==64&&m.starts==m.stops);
 for(s=0;s<2;++s){
  reset(&m);m.freeze_seconds=1;m.key_after=64;
  ck(run(&m,32767,s,64UL)==ALARM_COOP_OK);ck(m.services==64&&m.reads==1);
  reset(&m);m.freeze_seconds=1;m.key_after=65;
  ck(run(&m,32767,s,64UL)==ALARM_COOP_BUDGET);ck(m.services==64&&!m.reads);
 }
 reset(&m);m.service_error=63;
 ck(run(&m,32767,1,64UL)==ALARM_COOP_SERVICE);ck(m.services==63&&!m.reads);
 reset(&m);m.reentry=1;ck(run(&m,4,1,64UL)==ALARM_COOP_OK);ck(m.reentered);
 reset(&m);m.stop_error=1;result=run(&m,4,1,64UL);
 ck(result==ALARM_COOP_CLEANUP&&alarm_coop_active()&&m.owned);
 ck(alarm_coop_run_progress(&ops,&m,1,1,64UL)==ALARM_COOP_BUSY);
 ck(alarm_coop_recover()==ALARM_COOP_CLEANUP);ck(!alarm_coop_active()&&!m.owned);
 reset(&m);m.invalid_seconds=1;
 ck(run(&m,4,1,64UL)==ALARM_COOP_CLOCK);ck(!m.services&&!m.starts);
 reset(&m);m.invalid_ticks=1;
 ck(run(&m,4,1,64UL)==ALARM_COOP_CLOCK);ck(m.starts==m.stops);
 reset(&m);m.lose_context=3;result=run(&m,4,1,64UL);
 ck(result==ALARM_COOP_CLEANUP&&alarm_coop_active()&&m.owned);
 m.valid=1;ck(alarm_coop_recover()==ALARM_COOP_CONTEXT);ck(!alarm_coop_active()&&!m.owned);
 alarm_coop_result(&r);ck(r.cause==ALARM_COOP_CONTEXT);
 printf("ALARM_COOP %u cases %lu checks %u failures\n",cases,checks,failures);return failures?1:0;
}
'''
    legacy.C = text
    status = legacy.main()
    assert status == 0
    folder = Path(sys.argv[sys.argv.index('--output') + 1]).resolve()
    path = folder / 'result.json'
    result = json.loads(path.read_text())
    durations = [tuple(map(int, m)) for m in re.findall(r'PROGRESS duration(\d+) sound(\d+) services(\d+)', result['output'])]
    assert [(d,s) for d,s,n in durations] == [(d,s) for d in (0,1,4,59,60,32767) for s in (0,1)]
    assert all(n > 500000 for d,s,n in durations if d == 32767)
    fast = [tuple(map(int, m)) for m in re.findall(r'FAST sound(\d+) services(\d+)', result['output'])]
    assert [s for s,n in fast] == [0,1] and all(n > 2000000 for s,n in fast)
    assert 'TOTAL_LIMIT services2000000' in result['output']
    result['sources']['standalone/test_alarm_progress_dos.py'] = sha(Path(__file__))
    result['modeled_duration_cases'] = [dict(duration=d, sound=s, service_calls=n) for d,s,n in durations]
    result['modeled_fast_clock_cases'] = [dict(duration=32767,sound=s,service_calls=n) for s,n in fast]
    result['scope'] = __doc__ + ' Actual recovered native controller and C watchdog execute in DOS8086. Clocks advance per modeled callback, not wall time; keys/speaker/receive are explicit models. Original total-budget mode is a negative control. This is not nine physical hours, real PIT/UART or VM/parent acceptance.'
    path.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS full modeled duration watchdog')


if __name__ == '__main__':
    main()
