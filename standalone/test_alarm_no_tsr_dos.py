#!/usr/bin/env python3
"""Actual ALARM VM/parent receive test without a resident observation program."""
import argparse,json,struct,sys,re
from pathlib import Path
import test_connection_dos as connection
from directory_fixtures import prm
from test_directory_key_bindings_dos import actions
from build_context_help import ROOT,sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('parent','child','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 parent=a.parent.resolve();child=a.child.resolve()
 source='proc main\ntransmit "ALARMSTART"\nalarm 1\ntransmit "ALARMDONE"\nendproc\n'
 files={'ASPECT.EXE':child.read_bytes(),'LOGON.ASX':compile_source(source),'ACTIONS.KEY':actions(b'D:\\LOGON.ASX',0)}
 settings=bytearray(prm(port=3,baud=5))
 for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,1),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',settings,off,value)
 label=out.name;capture=ROOT/'build/connection-dos'/label;assert not capture.exists();connection.BINARY=parent
 result=connection.run(label,'success','p900 enter p6500 a-1 p3500 enter p700 r e a d y enter p700 a-x',
  timeout=30,prm=bytes(settings),com=3,irq=5,working_drive='d',files=files,cpu='386',arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY /A:NETWORK',
  online_triggers=[(b'ALARMSTART',b'ALARM_RX\x1b[6n'),(b'ALARMDONE',b'\x1b[5n')])
 wire=(capture/'serial.bin').read_bytes();checks=dict(connection=result['passed'],actual_VM_entry=b'ALARMSTART'in wire,actual_ALARM_return=b'ALARMDONE'in wire,
  receive_query_during_ALARM=b'ALARMSTART'in wire and b'ALARMDONE'in wire and bool(re.search(rb'\x1b\[\d+;\d+R',wire.split(b'ALARMSTART',1)[1].split(b'ALARMDONE',1)[0])),
  parser_after_ALARM=b'ALARMDONE'in wire and b'\x1b[0n'in wire.split(b'ALARMDONE',1)[1],parent_keys_after_ALARM=b'ready'in wire)
 report=dict(passed=all(checks.values()),checks=checks,products=dict(parent=sha(parent),child=sha(child)),source=source,connection=result,
  artifacts={str(f.relative_to(ROOT)):sha(f)for f in capture.iterdir()if f.is_file()},scope=__doc__+' Real parent, script wrapper, DOS clock/BIOS/PIT, native WHEN/receive/ANSI renderer. Owned raw modem peer, no TSR or injected parser response. Physical modem, full flow/WHEN/error/capacity and sound remain separate.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS'if report['passed']else'FAIL',checks);return 0 if report['passed']else 1
if __name__=='__main__':raise SystemExit(main())
