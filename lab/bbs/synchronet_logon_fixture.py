#!/usr/bin/env python3
"""Temporary owned LABUSER logon exemption; preserve/restore other account bits.

Use only for a measured probe rejected by the daily quota. This is a declared
lab precondition, not a terminal compatibility fix or stock quota test.
Run in the pinned bbs shell. Begin records before/after; end verifies restoration.
"""
import argparse,json,subprocess
from pathlib import Path
from synchronet import ROOT,RUNTIME,ENV

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['begin','end']);p.add_argument('--record',type=Path,required=True);a=p.parse_args()
 record=a.record.resolve();record.relative_to(ROOT/'build/bbs-lab')
 if a.operation=='begin':
  assert not record.exists(),'Preserve existing fixture evidence'
  body="""require('userdefs.js','UEXEMPT_LOGONS');
var n=system.matchuser('LABUSER'); if(!n) throw Error('Missing synthetic LABUSER');
var u=new User(n); var before=u.security.exemptions;var bit=UEXEMPT_LOGONS;
u.security.exemptions=before|bit;
if(u.security.exemptions!==(before|bit)) throw Error('Exemption was not applied');
print('PCPLUS_FIXTURE '+JSON.stringify({user:'LABUSER',number:n,level:u.security.level,
logons_today:u.stats.logons_today,bit:bit,before:before,active:u.security.exemptions,
restored:false,scope:'Temporary synthetic-account daily-logon exemption only; editor/server quota policy unchanged.'}));
"""
 else:
  state=json.loads(record.read_text());assert not state['restored']
  body="""var s=%s;var u=new User(s.number);
if(u.alias!==s.user) throw Error('Account identity changed');
if((u.security.exemptions & ~s.bit)!==(s.before & ~s.bit)) throw Error('Other exemption flags changed');
u.security.exemptions=s.before;
if(u.security.exemptions!==s.before) throw Error('Exemption was not restored');
s.restored=true;s.after=u.security.exemptions;
print('PCPLUS_FIXTURE '+JSON.stringify(s));
"""%json.dumps(state)
 record.parent.mkdir(parents=True,exist_ok=True);script=record.with_suffix('.'+a.operation+'.js');script.write_text(body)
 result=subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(script)],env=ENV(),capture_output=True,text=True,check=True)
 record.with_suffix('.'+a.operation+'.stdout').write_text(result.stdout)
 record.with_suffix('.'+a.operation+'.stderr').write_text(result.stderr)
 lines=[line.partition('PCPLUS_FIXTURE ')[2] for line in result.stdout.splitlines() if line.startswith('PCPLUS_FIXTURE ')]
 assert len(lines)==1,result.stdout
 state=json.loads(lines[0]);record.write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state,indent=2))
if __name__=='__main__':main()
