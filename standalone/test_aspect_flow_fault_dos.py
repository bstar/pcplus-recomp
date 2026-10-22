#!/usr/bin/env python3
"""Observe real XOFF timeout/cancel handback while the peer still holds TX."""
import argparse,json,re,shutil,struct
from pathlib import Path
import test_aspect_flow_return_dos as flow
from directory_fixtures import directory,prm
ROOT=flow.ROOT;sha=flow.sha;ESC=b'\x1b'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--expect-gap',action='store_true');a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/aspect-flow-fault-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
    inputs={}
    for directory_,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/directory_;manifest=json.loads((base/'manifest.json').read_text());assert manifest['binary_sha256']==sha(base/leaf)
        inputs.update(manifest['sources'])
        for file in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(file.relative_to(ROOT))]=sha(file)
    for file in (Path(__file__),Path(flow.__file__),Path(flow.renderer.__file__),Path(flow.connection.__file__),Path(flow.window.__file__)):
        inputs[str(file.relative_to(ROOT))]=sha(file)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    compiled=flow.observer(out);rows=[]
    script='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\nwaitfor "GO" 5\ntransmit "MUSTNOTSEND"\nfopen 5 "BAD.OK" "wb"\nfputs 5 "BAD"\nfclose 5\nendproc\n'
    for mode in ('timeout','cancel'):
      for hard in (0,1):
        name=mode+('-both' if hard else '-soft');folder=out/name;folder.mkdir();events=[];peer=flow.adapter(out,events,resume_after=4)
        shutil.copy2(ROOT/'build/terminal/TERMINAL.EXE',folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        payload=bytearray(directory(profile=4));payload[302:311]=b'LOGIN\0\0\0\0'
        files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':flow.renderer.compile_source(script),'ASPECT.EXE':(ROOT/'build/aspect-runner/ASPECT.EXE').read_bytes(),'RENDER.COM':compiled}
        keys=('p1800 escape p1200' if mode=='cancel' else 'p3000')+' r e a d y p2300 a-x'
        try:
            r=peer.run(name,'success',keys,directory=bytes(payload),prm=prm(soft=1,hard=hard),
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,profile=4,working_drive='d',observer='RENDER',environment={'PCPLUS_TXWAIT':'2'},
                banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0cLOGIN:')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw);state=dict(zip(flow.FIELDS,struct.unpack('<3H',raw[-6:])))
        wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()[::2]
        off=next(e['time'] for e in events if e['kind']=='xoff-go');on=next(e['time'] for e in events if e['kind']=='xon')
        leaks=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and off<e['time']<on)
        leaked_app=bytes(c for c in leaks if c not in (17,19))
        checks=dict(r['checks']);checks.pop('no_data_during_XOFF')
        checks.update(actual_child_exit=header[:4]==(0x524e,1,1,1) and header[6]==(13 if mode=='cancel' else 14),
            JFT_restored=raw[14:34]==raw[34:54],owners_restored=raw[54:470]==raw[470:886],child_XOFF_observed=state['child_paused_ticks']>8,
            parent_return_observed=state['parent_return_ticks']>18,no_script_data=b'MUSTNOTSEND' not in wire and not (folder/'BAD.OK').exists(),
            error_visible=(b'cancelled' in screen if mode=='cancel' else b'serial 7' in screen),
            exact_received_wire=wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive'))
        desired=dict(parent_retains_pause=state['parent_paused_after_return']>8,no_data_before_XON=not leaked_app)
        gap=all(not v for v in desired.values())
        passed=all(checks.values()) and (gap if a.expect_gap else all(desired.values()))
        rows.append(dict(case=name,passed=passed,checks=checks,desired_checks=desired,observations=state,application_before_XON_hex=leaked_app.hex(),
                         wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=passed,checks=checks,desired_checks=desired,observations=state,application_before_XON_hex=leaked_app.hex())),flush=True)
    report=dict(passed=all(r['passed'] for r in rows),gap_reproduced=a.expect_gap,compatibility_accepted=not a.expect_gap and all(r['passed'] for r in rows),
        cases=rows,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),
        scope=__doc__+' Actual DOSBox-X8086, SOFT/BOTH with CTS always high; passive timer and independent peer. No injected product/ISR/UART status.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']


if __name__=='__main__':main()
