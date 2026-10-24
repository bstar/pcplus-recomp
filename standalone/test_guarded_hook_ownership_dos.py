#!/usr/bin/env python3
"""Observe borrowed trap/exit state during three real kind2 helper invocations."""
import argparse,json,struct,sys
from pathlib import Path
import test_hook_apply_dos as apply
from build_guarded_helper import GUARDED
ROOT=apply.ROOT
EXTRA=[('terminal_trap_phase',26),('terminal_exit_guard_valid',2),('terminal_exit_guard_owner',10)]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--terminal',type=Path,default=ROOT/'build'/GUARDED/'TERMINAL.EXE')
 p.add_argument('--port',type=int,choices=[1,2],required=True);p.add_argument('--mode',type=int,choices=[0,1],required=True);a=p.parse_args()
 out=a.output.resolve();binary=a.terminal.resolve()
 # The existing child reads declared parent_spans without modifying them.
 # Extend only its generated map-bound observation list, retaining all of the
 # existing settings/register/UART checks and child failure/recovery behavior.
 previous=apply.FIELDS;argv=sys.argv[:];apply.FIELDS=[*previous,*EXTRA]
 try:
  sys.argv=['test_hook_apply_dos.py','--terminal',str(binary),'--online','--port',str(a.port),'--mode',str(a.mode),'--output',str(out)]
  apply.main()
 finally:apply.FIELDS=previous;sys.argv=argv
 offset=sum(size for _,size in previous);observed=[]
 for i in range(3):
  raw=(out/f'S{i}.BIN').read_bytes();trap=struct.unpack_from('<13H',raw,offset)
  valid=struct.unpack_from('<H',raw,offset+26)[0];guard=struct.unpack_from('<5H',raw,offset+28)
  assert trap[0:2]==(2,0) and trap[2]==guard[0] and trap[3] in (0,1) and trap[4]==1
  assert trap[11:]==(0,0) and valid==1 and guard[0]>=16 and guard[1]>=16
  assert guard[2:]==(0,0,65535)
  observed.append(dict(trap=list(trap),exit_valid=valid,exit_guard=list(guard)))
 assert observed[0]==observed[1]==observed[2]
 result=json.loads((out/'result.json').read_text());result.update(trap_ownership=observed,trap_fields=EXTRA,trap_offset=offset)
 result['sources']['standalone/test_guarded_hook_ownership_dos.py']=apply.sha(Path(__file__))
 result['sources']['standalone/build_guarded_helper.py']=apply.sha(ROOT/'standalone/build_guarded_helper.py')
 result['scope']+=' Map-bound raw spans observe CHILD phase, no pending event, borrowed caller vectors, child lease, trusted exit owner/floor and zero exit retention reason on all three invocations. The ordinary fixture does not inject an interrupt during the child.'
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS helper trap ownership',a.port,a.mode)
if __name__=='__main__':main()
