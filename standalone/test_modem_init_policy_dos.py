#!/usr/bin/env python3
"""Actual DOS configurable initialization acknowledgements with an owned peer."""
import argparse,inspect,json,shutil,struct,types
from pathlib import Path
import test_modem_initialization_dos as baseline
from modem_fixtures import fixture
from audit_aspect_transmit_wait import ROOT,sha


def adapter(out,events,policy,commands):
    text=inspect.getsource(baseline.adapter).replace('def adapter(out,events,policy):','def create(out,events,policy,expected):')
    text=text.replace("module.__dict__.update(CASE_OUT=out,events=events,POLICY=policy)","module.__dict__.update(CASE_OUT=out,events=events,POLICY=policy,EXPECTED=expected)")
    needle="    source=source[:start]+peer+source[end:];source=source.replace('cputype=386','cputype=8086')"
    assert text.count(needle)==1
    text=text.replace(needle,needle+"\n    source=source.replace(\"commands[:2]==['ATZ',('ATD'+target.decode('ascii'))]\",\"commands==EXPECTED\")")
    if policy=='numeric-error':
        text=text.replace("POLICY=='error'","POLICY=='numeric-error'").replace("response(b'\\r\\nERROR\\r\\n')","response(b'\\r\\n4\\r\\n')")
    if policy=='numeric-OK':
        text=text.replace("else:ready=True;response(b'\\r\\nOK\\r\\n');event('initialization-ready')","else:ready=True;response(b'\\r\\n0\\r\\n');event('initialization-ready')")
    if policy=='echo':
        text=text.replace("else:ready=True;response(b'\\r\\nOK\\r\\n');event('initialization-ready')","else:ready=True;response(b'ATZ\\r\\nBOOK\\r\\n OK \\r\\n');event('initialization-ready')")
    if policy=='multi':
        text=text.replace("elif command==b'ATD'+target:","elif command==b'ATE0':ready=False;reply_at=time.monotonic()+.4;event('second-initialization-pending',delay=.4)\n      elif command==b'ATD'+target:")
    namespace=dict(baseline.__dict__);exec(compile(text,__file__,'exec'),namespace);return namespace['create'](out,events,policy,commands)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--terminal',type=Path,default=ROOT/'build/terminal/TERMINAL.EXE');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    binary=a.terminal.resolve();assert binary.is_relative_to(ROOT/'build') and binary.name=='TERMINAL.EXE';product=binary.parent;manifest=json.loads((product/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256'];inputs=dict(manifest['sources'])
    for path in (Path(__file__),Path(baseline.__file__),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/modem_fixtures.py',ROOT/'standalone/test_terminal.py'):
        inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;dest=out/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copy2(binary,out/'admitted.EXE');shutil.copy2(product/'terminal.map',out/'admitted.map');rows=[]
    cases=[('OK',3,True),('delayed',3,True),('error',3,False),('quiet',0,True),('quiet',1,False),('numeric-OK',3,True),('numeric-error',3,False),('multi',3,True),('echo',3,True)]
    for policy,seconds,connected in cases:
        name=policy+'-'+str(seconds);folder=out/name;folder.mkdir();shutil.copy2(binary,folder/'TERMINAL.EXE');events=[]
        commands=['ATZ']+(['ATE0'] if policy=='multi' else [])+(['ATDCaseTest:23'] if connected else [])
        peer=adapter(out,events,policy,commands);peer.BINARY=folder/'TERMINAL.EXE'
        payload=bytearray(fixture(timeout=3))
        if manifest.get('experimental_mouse'):struct.pack_into('<HH',payload,0x4e4,8,4)
        if policy=='multi':payload[0x18:0x47]=b'ATZ^MATE0^M'.ljust(47,b'\0')
        try:r=peer.run(name,'success' if connected else 'busy','p4500 a-x',prm=bytes(payload),profile=6,arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:'+str(seconds))
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        wire=(folder/'serial.bin').read_bytes();prefix=b'ATZ\r'+(b'ATE0\r' if policy=='multi' else b'')
        expected=prefix+(b'ATDCaseTest:23\r\x1b[1;16R\x1b[?1;2c+++ATH\r' if connected else b'\x1b')
        checks=dict(r['checks'],no_dial_before_peer_ready=not any(e['kind']=='dial-before-ready' for e in events),whole_wire_exact=wire==expected,
            exact_initialization_unchanged=(folder/'TEST.PRM').read_bytes()==bytes(payload))
        rows.append(dict(case=name,policy=policy,wait_seconds=seconds,connected=connected,passed=all(checks.values()),checks=checks,wire_hex=wire.hex(),events=events,captures={str(path.relative_to(folder)):sha(path) for path in folder.rglob('*') if path.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],failed=[k for k,v in checks.items() if not v])),flush=True)
    r=dict(passed=all(row['passed'] for row in rows),selected_initialization_policy_accepted=all(row['passed'] for row in rows),parent_sha256=sha(binary),inputs=inputs,cases=rows,mouse_scales=[8,4] if manifest.get('experimental_mouse') else None,checker_sha256=sha(Path(__file__)),
        scope=__doc__+' Nine actual8086 DOS cases: immediate/delayed/ERROR, legacy quiet and explicit quiet timeout, numeric0/4, two configured commands with delayed second ACK, and echo/unrelated lines. Exact UART/modem commands, actual ANSI replies on connected cases, no pre-ready ATD, normal exit and42-byte UART restoration. Not physical Boca timing, SIP/audio, retry/flow-pressure or full F03 acceptance.')
    (out/'checks.json').write_text(json.dumps(r,indent=2)+'\n');assert r['passed']


if __name__=='__main__':main()
