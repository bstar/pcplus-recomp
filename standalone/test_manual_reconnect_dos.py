#!/usr/bin/env python3
"""Actual DOS Alt-H under peer XOFF, DTR disconnect and Alt-D retry."""
import argparse,inspect,json,re,shutil,struct,types
from pathlib import Path
import test_modem_reconnect_dos as reconnect
ROOT=reconnect.ROOT;sha=reconnect.sha;ESC=b'\x1b'


def adapter(out,events,gap):
    text=inspect.getsource(reconnect.adapter)
    text=text.replace('def adapter(out,events,gap):','def build(out,events,gap):')
    text=text.replace('now-ready>=1:', 'False:') # The client, not the BBS, must hang up.
    text=text.replace("b'KEYREADY'", "b'arm'")
    text=text.replace("b'ready\\x1b[1;25R'", "b'ready\\x1b[1;16R'")
    text=text.replace('if not block:break',"if not block:\n       if session==1:event('first-DTR-close',session=session);checks['first_peer_carrier_drop']=True\n       break")
    text=text.replace("'attempts==2'","'attempts==(1 if EXPECT_GAP else 2)'")
    module=types.ModuleType('manual_hangup_modem');module.__dict__.update(reconnect.__dict__)
    exec(compile(text,__file__,'exec'),module.__dict__);return module.build(out,events,gap)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--expect-gap',action='store_true');a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/manual-reconnect-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
    binary=ROOT/'build/terminal/TERMINAL.EXE';manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256'];inputs={**manifest['sources']}
    for f in (Path(__file__),Path(reconnect.__file__),Path(reconnect.carrier.__file__),Path(reconnect.carrier.connection.__file__)):
        inputs[str(f.relative_to(ROOT))]=sha(f)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    rows=[]
    for hard in (0,1):
        name='both' if hard else 'soft';folder=out/name;folder.mkdir();events=[];peer=adapter(out,events,a.expect_gap)
        shutil.copy2(binary,folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        settings=bytearray(reconnect.prm(soft=1,hard=hard));struct.pack_into('<H',settings,10,2)
        try:
            r=peer.run(name,'success','p2400 a r m p600 a-h p4300 a-d p4500 r e a d y p700 a-x',
                directory=reconnect.directory(profile=4),prm=bytes(settings),profile=4,working_drive='d',accounting_delta=1 if a.expect_gap else 2,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',
                banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0c')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        checks=dict(r['checks'])
        if a.expect_gap:checks.pop('manual_query_sent',None)
        log=(folder/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log)
        dial=(folder/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode();prefix=ESC+b'[1;16R'+ESC+b'[?62;2c'
        wire=(folder/'serial.bin').read_bytes();expected=prefix+b'arm'+(b'' if a.expect_gap else prefix+b'ready'+ESC+b'[1;16R')
        closed=[e for e in events if e['kind']=='first-DTR-close'];paused=[e for e in events if e['kind']=='xoff'];connections=[e for e in events if e['kind']=='connected']
        checks.update(only_owned_DTR_disconnect=len(closed)==len(paused)==1 and not any(e['kind']=='first-hangup' for e in events),
            bounded_hangup=(1.5<closed[0]['time']-paused[0]['time']<4 if closed and paused else False),
            expected_connections=len(connections)==(1 if a.expect_gap else 2),commands_exact=commands==(['ATZ','ATD'+dial]*(1 if a.expect_gap else 2)),
            no_modem_ERROR='Modem response: ERROR' not in log,whole_wire_exact=wire==expected,
            peer_stream_matches=wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive'))
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,commands=commands,connections=len(connections),wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],checks=checks,connections=len(connections),commands=commands)),flush=True)
    result=dict(passed=all(r['passed'] for r in rows),gap_reproduced=a.expect_gap,compatibility_accepted=not a.expect_gap,cases=rows,parent_sha256=sha(binary),inputs=inputs,
        scope=__doc__+' Two actual8086 SOFT/BOTH virtual-modem cases. Remote XOFF after manual arm; Alt-H sender times out then configured DTR pulse closes the first BBS socket. BBS never sends XON or initiates that close. Baseline cannot send second init; corrected parent must redial and answer manual query. Exact streams and hardware/accounting cleanup checked. No actual canceled-initialization or physical timing/full application claim.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
