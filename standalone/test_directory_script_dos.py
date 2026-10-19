#!/usr/bin/env python3
"""Owned modem -> actual DOS directory auto-script -> terminal resume regression.

Only synthetic directories, source scripts and PRM fixtures are used. Expected
peer traffic is fixed before DOS execution. The existing connection harness is
loaded with an isolated output-directory adapter; its reports are never edited.
"""
import argparse,hashlib,json,struct,sys,types
from pathlib import Path
import test_connection_dos as connection
import test_script_launch_dos as script_support
from directory_fixtures import directory,prm
ROOT=connection.ROOT
OUT=ROOT/'build/directory-script-dos'
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def adapter():
 source=(ROOT/'standalone/test_connection_dos.py').read_text()
 old="out=ROOT/'build/connection-dos'/name"
 assert source.count(old)==1
 module=types.ModuleType('directory_script_connection_adapter')
 module.__file__=str(ROOT/'standalone/test_connection_dos.py')
 exec(compile(source.replace(old,"out=ROOT/'build/directory-script-dos'/name"),module.__file__,'exec'),module.__dict__)
 return module

def definitions():
 # FIRST BYTE SAFE/query suffix is intentionally after the prompt consumed by
 # WAITFOR. It must be returned as raw bytes and rendered/replied to by parent.
 suffix=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'
 login=('proc main\nwaitfor "LOGIN:" 2\nif waitfor\ntransmit $D_PWORD\n'
        'transmit "^M"\nmessage "SCRIPT LIVE"\npause 1\nendif\nendproc\n')
 simple='proc main\nmessage "SCRIPT LIVE"\npause 1\nendproc\n'
 metadata=('integer n\nstring displaybuf\nproc main\n'
           'transmit $D_NAME\ntransmit "|"\ntransmit $D_PHONE\ntransmit "|"\n'
           'transmit $D_SCRIPT\ntransmit "|"\nn = $D_ENTRY\nitoa n displaybuf\ntransmit displaybuf\n'
           'transmit "^M"\n'
           'message "SCRIPT LIVE"\npause 1\nendproc\n')
 return [
  dict(name='queued-login-explicit-password',source=login,banner=b'LOGIN:'+suffix,tx=b'Synth42\r',passwords=1,bits=1),
  dict(name='no-implicit-password',source=simple,banner=suffix,tx=b'',passwords=0,bits=1),
  dict(name='entry200-default-com2',source=metadata,banner=suffix,tx=b'LAB NODE 200|CaseTest:23|LOGIN|200\r',passwords=0,bits=1,entry=200,com=2,default_port=True),
  dict(name='missing-child-resumes',source=simple,banner=suffix,tx=b'',passwords=0,bits=2,helper=False),
  dict(name='unsupported-child-resumes',source=simple,data=bytes.fromhex('00 cf fd 94'),banner=suffix,tx=b'',passwords=0,bits=2),
  dict(name='missing-script-resumes',source=simple,banner=suffix,tx=b'',passwords=0,bits=2,script=False),
  dict(name='busy-never-launches',source=login,banner=suffix,tx=b'',passwords=0,bits=0,mode='busy')]

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--terminal-sha256',required=True)
 parser.add_argument('--runner-sha256',required=True)
 parser.add_argument('--case',action='append')
 args=parser.parse_args()
 terminal=ROOT/'build/terminal/TERMINAL.EXE';runner=ROOT/'build/aspect-runner/ASPECT.EXE'
 assert sha(terminal)==args.terminal_sha256,'Terminal differs from frozen parent identity'
 assert sha(runner)==args.runner_sha256,'Runner differs from frozen parent identity'
 cases=definitions()
 if args.case:
  cases=[c for c in cases if c['name'] in args.case];assert {c['name'] for c in cases}==set(args.case)
 OUT.mkdir(parents=True,exist_ok=True)
 # All outcomes are authored before any actual DOS execution.
 expectations=[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.items()} for c in cases]
 (OUT/'expectations.json').write_text(json.dumps(expectations,indent=2)+'\n')
 script_support.OUT=OUT
 observer=script_support.watcher()
 harness=adapter();results=[]
 for case in cases:
  name=case['name'];folder=OUT/name;folder.mkdir(exist_ok=True)
  # Preserve every attempt, including failed artifacts, rather than overwrite.
  assert not (folder/'result.json').exists(),f'Archive prior run before retry: {folder}'
  for binary in ['TERMINAL.EXE','ASPECT.EXE']:(folder/binary).unlink(missing_ok=True)
  (folder/'TERMINAL.EXE').write_bytes(terminal.read_bytes())
  if case.get('helper',True):(folder/'ASPECT.EXE').write_bytes(runner.read_bytes())
  entry=case.get('entry',1);com=case.get('com',1)
  payload=bytearray(directory(entry=entry,port=0 if case.get('default_port') else com,baud=5))
  at=250+(entry-1)*114
  payload[at+52:at+61]=b'LOGIN\0\0\0\0'
  payload[at+75:at+86]=b'Synth42\0\0\0\0'
  files={'SCRIPT.COM':observer}
  files['LOGIN.ASP']=case['source'].encode('cp437')
  if case.get('script',True):files['LOGIN.ASX']=case.get('data',compile_source(case['source']))
  harness.BINARY=folder/'TERMINAL.EXE'
  mode=case.get('mode','success')
  keys='p2800 space p600 r e a d y p700 a-x' if mode=='success' else 'p4000 a-x'
  result=harness.run(name,mode,keys,directory=bytes(payload),prm=prm(port=com,baud=5),com=com,
    arguments=f'@D:\\TEST.PRM /E:D:\\TEST.DIR /N:{entry}',directory_entry=entry,
    files=files,banner=case['banner'],working_drive='d',observer='SCRIPT')
  wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
  magic,bits,ticks,_=struct.unpack('<4H',(folder/'SCRIPT.BIN').read_bytes())
  checks=result['checks']
  checks.update(observed_console=magic==0x4d43 and ticks>0 and bits==case['bits'],
   password_only_when_requested=wire.count(b'Synth42')==case['passwords'],
   one_connection_no_automatic_retry=result['commands']==['ATZ','ATDCaseTest:23'],
   selected_record_accounting_only=checks['directory_expected_updates_only'],
   frozen_binaries=sha(terminal)==args.terminal_sha256 and sha(runner)==args.runner_sha256)
  if mode=='success':checks['ordinary_keyboard_resumes']=b'ready' in wire
  if case['tx']:checks['explicit_script_metadata_exactly_once']=wire.count(case['tx'])==1
  else:checks['no_unrequested_metadata']=b'LAB NODE' not in wire
  # ANSI reply bytes already checked by harness; script command bytes are
  # asserted separately and must precede ordinary parent keyboard transmission.
  if case['tx']:checks['script_before_resumed_typing']=wire.find(case['tx'])<wire.find(b'ready')
  result.update(passed=all(checks.values()),observer_bits=bits,source_sha256=sha(folder/'LOGIN.ASP'),
   runner_sha256=args.runner_sha256,expected_tx_hex=case['tx'].hex(),synthetic_inputs_only=True)
  (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL',flush=True)
  results.append(result)
 history=[]
 for prior in sorted(OUT.glob('failed-*/checks.json')):
  old=json.loads(prior.read_text())
  history.append(dict(report=str(prior.relative_to(ROOT)),sha256=sha(prior),failed_checks={c['case']:[k for k,v in c['checks'].items() if not v] for c in old['cases'] if not c['passed']},reason='Incorrect manual-menu success prompt expectation; automatic success immediately resumes. New owned scripts pause1 after message for reliable TSR observation.'))
 report=dict(regression_history=history,passed=all(r['passed'] for r in results),cases=results,terminal_sha256=args.terminal_sha256,
  runner_sha256=args.runner_sha256,checker_sha256=sha(Path(__file__)),harness_sha256=sha(ROOT/'standalone/test_connection_dos.py'),
  expectations_sha256=sha(OUT/'expectations.json'),original_inputs=[],
  scope='Actual source-built DOS terminal and ASPECT child, directory accounting, emulated COM1/COM2 IRQ/nullmodem. Same-write CONNECT+prompt+ANSI suffix; synthetic directory/password/source only. Physical modem and original source-compiler invocation not tested.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
