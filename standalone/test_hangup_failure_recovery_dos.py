#!/usr/bin/env python3
"""DOS recovery from failed hangup through peer XON, second hangup and redial."""
import argparse,inspect,json,shutil,struct,types
from pathlib import Path
import test_hangup_retained_carrier_dos as retained
base=retained.base;ROOT=retained.ROOT


def adapter(out,events,backend):
    text=inspect.getsource(retained.adapter).replace('def adapter(out, events, backend):','def create(out, events, backend):')
    old="conn.settimeout(.03);escape=False;online=False;line=bytearray();online_data=bytearray();paused=False"
    assert text.count(old)==1
    text=text.replace(old,old+";released=False;pause_at=0;queried=False")
    old='except socket.timeout:continue';assert text.count(old)==1
    text=text.replace(old,"""except socket.timeout:
      if paused and not released and time.monotonic()-pause_at>=5.8:
       conn.sendall(b'\\x11');event('XON-recovery',b'\\x11');released=True
      continue""")
    text=text.replace("if not paused and online_data.endswith(b'arm'):", "if attempts==1 and not paused and online_data.endswith(b'arm'):")
    text=text.replace("event('XOFF-online',b'\\x13');paused=True", "event('XOFF-online',b'\\x13');paused=True;pause_at=time.monotonic()")
    old='''      # Deliberately retain online data mode and DCD across any DTR pulse.
      # AT-looking bytes here are data, never parsed as new modem commands.
      continue''';assert text.count(old)==1
    text=text.replace(old,"""      if attempts==2 and not queried and online_data.endswith(b'ready'):
       conn.sendall(b'\\x1b[6n');event('reconnected-query',b'\\x1b[6n');queried=True
      if online_data.endswith(b'+++ATH\\r'):
       assert released
       conn.sendall(b'\\xff\\x81\\r\\nOK\\r\\n');event('hangup-command-disconnect',b'\\xff\\x81');online=False;line.clear()
      continue""")
    ns=dict(retained.__dict__);exec(compile(text,__file__,'exec'),ns);return ns['create'](out,events,backend)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    binary=ROOT/'build/terminal/TERMINAL.EXE';manifest=json.loads((binary.parent/'manifest.json').read_text());assert base.sha(binary)==manifest['binary_sha256']
    inputs=dict(manifest['sources'])
    for path in (Path(__file__),Path(retained.__file__),Path(base.__file__),ROOT/'standalone/manual_cancel_watch.asm',ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/directory_fixtures.py',ROOT/'standalone/modem_fixtures.py',ROOT/'nix/patches/dosbox-dcd-control.patch',ROOT/'nix/flake.lock'):
        inputs[str(path.relative_to(ROOT))]=base.sha(path)
    for name,digest in inputs.items():
        assert base.sha(ROOT/name)==digest;dest=out/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copy2(binary,out/'admitted.EXE');shutil.copy2(binary.parent/'terminal.map',out/'admitted.map')
    compiled=retained.observer(out,binary.parent/'terminal.map');vectors=base.vectors(out);backend=(ROOT/'build/dosbox-dcd-lab/bin/dosbox-x').resolve();rows=[]
    for drop in (0,1):
        name=f'drop{drop}-both';folder=out/name;folder.mkdir();events=[];peer=adapter(out,events,backend)
        shutil.copy2(binary,folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        payload=bytearray(retained.prm(soft=1,hard=1));struct.pack_into('<H',payload,10,3);struct.pack_into('<H',payload,16,drop)
        try:
            r=peer.run(name,'success','p1800 a r m p600 a-h p5000 a-d p1600 a-h p2300 a-d p1800 r e a d y p700 a-x',directory=retained.directory(profile=4),prm=bytes(payload),profile=4,working_drive='d',observer='WATCH',files={'WATCH.COM':compiled,'VECT.COM':vectors},accounting_delta=2,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        sample=struct.unpack('<12H',(folder/'RETAIN.BIN').read_bytes());wire=(folder/'serial.bin').read_bytes();reply=b'\x1b[1;16R\x1b[?62;2c';dial=b'ATZ\rATDCaseTest:23\r'
        kinds=[e['kind'] for e in events]
        checks=dict(r['checks'],observer_valid=sample[0]==0x4847 and sample[11]==1,failed_hangup_observed=sample[3]>4 and sample[6]>4 and sample[8]>4 and sample[9]==8,
            XON_released_pause_before_retry=sample[7]==0,
            two_clean_connections=r['commands']==['ATZ','ATDCaseTest:23']*2 and kinds.count('online-CONNECT')==2,
            explicit_XON_recovery=kinds.count('XOFF-online')==kinds.count('XON-recovery')==1,
            actual_hangup_disconnect=kinds.count('hangup-command-disconnect')==2,
            manual_query_after_redial=kinds.count('reconnected-query')==1,
            whole_wire_exact=wire==dial+reply+b'arm+++ATH\r'+dial+reply+b'ready\x1b[1;16R+++ATH\r',
            observer_vectors_restored=(folder/'VECOLD.BIN').read_bytes()==(folder/'VECNEW.BIN').read_bytes() and len((folder/'VECOLD.BIN').read_bytes())==8)
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,sample=list(sample),wire_hex=wire.hex(),captures={str(f.relative_to(folder)):base.sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],sample=list(sample),failed=[k for k,v in checks.items() if not v])),flush=True)
    result=dict(passed=all(v['passed'] for v in rows),parent_sha256=base.sha(binary),inputs=inputs,cases=rows,scope=__doc__+' Explicit patched DCD lab backend; peer retains initial connection across DTR, sends timed XON, and disconnects only after actual configured hangup bytes. Two BOTH-flow DOS cases cover DTR0/1, redial/manual query/accounting/hardware/vector restoration. Physical hardware and full application remain open.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
