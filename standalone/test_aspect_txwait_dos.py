#!/usr/bin/env python3
"""Actual DOS long XOFF stalls, configured expiry and transport cancellation."""
import argparse,json,re,shutil,struct
from pathlib import Path
import test_aspect_flow_return_dos as flow
ROOT=flow.ROOT;sha=flow.sha;ESC=b'\x1b'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/aspect-txwait-dos'/a.label;out.mkdir(parents=True,exist_ok=False);inputs={}
    for directory,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/directory;m=json.loads((base/'manifest.json').read_text());assert sha(base/leaf)==m['binary_sha256'];inputs.update(m['sources'])
        for f in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(f.relative_to(ROOT))]=sha(f)
    for f in (Path(__file__),Path(flow.__file__),Path(flow.connection.__file__),Path(flow.renderer.__file__),Path(flow.window.__file__)):
        inputs[str(f.relative_to(ROOT))]=sha(f)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    observer=flow.observer(out);rows=[]
    source='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\nwaitfor "GO" 5\n'+('transmit "0123456789ABCDEF"\n'*128)+'fopen 5 "WAIT.OK" "wb"\nfputs 5 "RESUMED"\nfclose 5\nendproc\n'
    definitions=[('default-long',None,False),('configured-long','6',False),('cancel-behind-key','30',True)]
    if not a.baseline:definitions += [('short-timeout','2',False),('maximum-long','3600',False),('cancel-long','30',True)]
    for name,seconds,cancel in definitions:
        folder=out/name;folder.mkdir();events=[];peer=flow.adapter(out,events,resume_after=4)
        shutil.copy2(ROOT/'build/terminal/TERMINAL.EXE',folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        directory=bytearray(flow.directory(profile=4));directory[302:311]=b'LOGIN\0\0\0\0'
        files={'LOGIN.ASP':source.encode(),'LOGIN.ASX':flow.renderer.compile_source(source),'ASPECT.EXE':(ROOT/'build/aspect-runner/ASPECT.EXE').read_bytes(),'RENDER.COM':observer}
        failed=a.baseline or name=='short-timeout';status=14 if a.baseline else 13 if cancel else 14 if failed else 0
        keys=('p1800 q escape p4200' if name=='cancel-behind-key' else 'p1800 escape p4200' if cancel else 'p6000')+' r e a d y p900 a-x'
        try:
            r=peer.run(name,'success',keys,directory=bytes(directory),prm=flow.prm(soft=1,hard=1),profile=4,files=files,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',working_drive='d',observer='RENDER',
                environment={'PCPLUS_TXWAIT':seconds} if seconds else {},
                banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0cLOGIN:')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);paused,returned,parent_pause=struct.unpack('<3H',raw[-6:])
        wire=(folder/'serial.bin').read_bytes();success=status==0
        tail=ESC+(b'[5;1R' if failed else b'[4;1R' if cancel else b'[1;24R')
        expected=b'ATZ\rATDCaseTest:23\r\x13\x11'+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+(flow.PAYLOAD if success else b'')+b'\x13\x11'+((b'q\x1b' if a.baseline else b'q') if name=='cancel-behind-key' else b'')+b'ready'+tail+b'+++ATH\r'
        off=next(e['time'] for e in events if e['kind']=='xoff-go');on=next(e['time'] for e in events if e['kind']=='xon')
        blocked=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and off<e['time']<on)
        checks=dict(r['checks'],native_exit=head[:4]==(0x524e,1,1,1) and head[6]==status,
            JFT_restored=raw[14:34]==raw[34:54],owners_restored=raw[54:470]==raw[470:886],pause_observed=paused>8,
            long_pause_reached=(paused>60 if success else True),parent_return=returned>18,
            no_data_during_hold=not bytes(c for c in blocked if c not in (17,19)),
            full_wire_exact=wire==expected,script_marker=((folder/'WAIT.OK').is_file() and (folder/'WAIT.OK').read_bytes()==b'RESUMED')==success,
            peer_stream_matches=wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive'))
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,configured_seconds=seconds,child_exit=head[6],
            observations=dict(child_paused_ticks=paused,parent_return_ticks=returned,parent_paused_ticks=parent_pause),
            wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],checks=checks,child_exit=head[6],paused_ticks=paused)),flush=True)
    report=dict(passed=all(r['passed'] for r in rows),gap_reproduced=a.baseline,compatibility_accepted=not a.baseline and all(r['passed'] for r in rows),
        cases=rows,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),
        scope=__doc__+' Four-second remote XOFF hold, actual8086 DOSBox-X BOTH flow with CTS high, exact2048-byte success or exact error/cancel streams, passive state and hardware/JFT/file-owner checks. Maximum3600 is configuration acceptance plus a short stall, not a one-hour wall-time test. No physical UART/CTS timing or full application claim.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']


if __name__=='__main__':main()
