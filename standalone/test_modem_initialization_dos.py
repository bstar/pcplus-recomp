#!/usr/bin/env python3
"""Observe initialization replies and readiness before dialing in actual DOS."""
import argparse,inspect,json,shutil,types
from pathlib import Path
import test_connection_dos as base
from modem_fixtures import fixture
from audit_aspect_transmit_wait import ROOT,sha


def adapter(out,events,policy):
    source=inspect.getsource(base.run).replace("out=ROOT/'build/connection-dos'/name",'out=CASE_OUT/name')
    start=source.index(' def peer():');end=source.index(' thread=threading.Thread',start)
    peer=r''' def event(kind,data=b'',**values):
  events.append(dict(kind=kind,time=time.monotonic(),hex=data.hex(),**values))
 def peer():
  nonlocal attempts
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(.02);line=bytearray();online=False;ready=False;started_ready=False;reply_at=None
    def response(data):conn.sendall(data);event('response',data)
    while not stop.is_set():
     if reply_at is not None and time.monotonic()>=reply_at:
      ready=True;reply_at=None;response(b'\r\nOK\r\n');event('initialization-ready')
     try:block=conn.recv(4096)
     except socket.timeout:continue
     if not block:break
     wire.extend(block);event('receive',block)
     for value in block:
      if online:
       line.append(value)
       if line.endswith(b'+++ATH\r'):
        checks['configured_hangup_reached_wire']=True;response(b'\r\nOK\r\n');line.clear();online=False
       continue
      if value==27:line.clear();checks['configured_abort_reached_wire']=True;event('abort',bytes([value]));continue
      if not line and value!=13:started_ready=ready;event('command-start',bytes([value]),ready=ready)
      if value!=13:line.append(value);continue
      command=bytes(line);line.clear()
      if not command:continue
      commands.append(command.decode('ascii','replace'));event('command',command,started_ready=started_ready,ready_now=ready)
      if command==b'ATZ':
       if POLICY=='error':response(b'\r\nERROR\r\n')
       elif POLICY=='quiet':ready=True;event('quiet-ready')
       elif POLICY=='delayed':reply_at=time.monotonic()+.75;event('initialization-pending',delay=.75)
       else:ready=True;response(b'\r\nOK\r\n');event('initialization-ready')
      elif command==b'ATD'+target:
       attempts+=1
       if not started_ready:
        event('dial-before-ready',command);response(b'\r\nNO CARRIER\r\n');continue
       online=True;response(b'CONNECT\r\n\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c')
      else:checks['unexpected_modem_command']=True
  except OSError as error:
   if not stop.is_set():errors.append(str(error))
'''
    source=source[:start]+peer+source[end:];source=source.replace('cputype=386','cputype=8086')
    module=types.ModuleType('initialization_peer');module.__dict__.update(base.__dict__);module.__dict__.update(CASE_OUT=out,events=events,POLICY=policy)
    exec(compile(source,__file__,'exec'),module.__dict__);return module


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    product=ROOT/'build/terminal';binary=product/'TERMINAL.EXE';manifest=json.loads((product/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
    inputs=dict(manifest['sources'])
    for path in (Path(__file__),Path(base.__file__),ROOT/'standalone/modem_fixtures.py',ROOT/'standalone/test_terminal.py'):
        inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;dest=out/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copy2(binary,out/'admitted.EXE');shutil.copy2(product/'terminal.map',out/'admitted.map');rows=[]
    for policy in ('OK','quiet','error','delayed'):
        folder=out/policy;folder.mkdir();shutil.copy2(binary,folder/'TERMINAL.EXE');events=[];peer=adapter(out,events,policy);peer.BINARY=folder/'TERMINAL.EXE'
        try:r=peer.run(policy,'success' if policy in ('OK','quiet') else 'busy','p4500 a-x',prm=fixture(timeout=3),profile=6)
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        commands=[e for e in events if e['kind']=='command'];early=[e for e in events if e['kind']=='dial-before-ready']
        checks=dict(r['checks'],exact_commands=[e['hex'] for e in commands]==[b'ATZ'.hex(),b'ATDCaseTest:23'.hex()],
            declared_peer_readiness=bool(early)==(policy in ('error','delayed')),
            no_initialization_rewrite=(folder/'TEST.PRM').read_bytes()[0x18:0x47].split(b'\0',1)[0]==b'ATZ^M')
        wire=(folder/'serial.bin').read_bytes();expected=b'ATZ\rATDCaseTest:23\r'+(b'\x1b[1;16R\x1b[?1;2c+++ATH\r' if policy in ('OK','quiet') else b'\x1b')
        checks['whole_wire_exact']=wire==expected
        rows.append(dict(policy=policy,passed=all(checks.values()),checks=checks,gap_reproduced=policy in ('error','delayed'),quiet_profile_compatible=policy=='quiet',wire_hex=wire.hex(),events=events,captures={str(path.relative_to(folder)):sha(path) for path in folder.rglob('*') if path.is_file()}))
        print(json.dumps(dict(policy=policy,passed=rows[-1]['passed'],failed=[k for k,v in checks.items() if not v])),flush=True)
    result=dict(passed=all(row['passed'] for row in rows),initialization_policy_gap_reproduced=True,initialization_policy_accepted=False,parent_sha256=sha(binary),inputs=inputs,cases=rows,checker_sha256=sha(Path(__file__)),
        scope=__doc__+' Four actual8086 DOS controller/sender/IRQ sessions against an owned serial peer: immediate OK, explicit quiet-ready profile, initialization ERROR and750ms delayed readiness. ERROR/delayed peers reject ATD started before ready. Passing reproduces the gap while preserving the valid no-reply control; no physical Boca timing or correction is claimed. Exact commands/responses/wire and UART restoration retained.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
