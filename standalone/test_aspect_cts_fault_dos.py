#!/usr/bin/env python3
"""Actual DOS long CTS hold, transmit expiry/cancellation and parent return."""
import argparse,json,re,shutil,struct
from pathlib import Path
import test_aspect_cts_dos as cts
flow=cts.flow;ROOT=cts.ROOT;sha=cts.sha;ESC=b'\x1b'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/aspect-cts-fault-dos'/a.label;out.mkdir(parents=True,exist_ok=False);inputs={}
    for directory,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/directory;m=json.loads((base/'manifest.json').read_text());assert sha(base/leaf)==m['binary_sha256'];inputs.update(m['sources'])
        for f in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(f.relative_to(ROOT))]=sha(f)
    for f in (Path(__file__),Path(cts.__file__),Path(flow.__file__),Path(flow.connection.__file__),Path(flow.renderer.__file__),Path(flow.window.__file__)):
        inputs[str(f.relative_to(ROOT))]=sha(f)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    compiled=cts.observer(out);rows=[]
    source='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\nwaitfor "GO" 5\n'+('transmit "0123456789ABCDEF"\n'*128)+'fopen 5 "CTS.OK" "wb"\nfputs 5 "RESUMED"\nfclose 5\nendproc\n'
    for mode in ('resume','timeout','cancel'):
      for soft in (0,1):
        name=mode+('-both' if soft else '-hard');folder=out/name;folder.mkdir();events=[];peer=cts.adapter(out,events,resume_after=4)
        shutil.copy2(ROOT/'build/terminal/TERMINAL.EXE',folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        directory=bytearray(flow.directory(profile=4));directory[302:311]=b'LOGIN\0\0\0\0'
        files={'LOGIN.ASP':source.encode(),'LOGIN.ASX':flow.renderer.compile_source(source),'ASPECT.EXE':(ROOT/'build/aspect-runner/ASPECT.EXE').read_bytes(),'RENDER.COM':compiled}
        status=0 if mode=='resume' else 14 if mode=='timeout' else 13
        keys=('p1800 q escape p4200' if mode=='cancel' else 'p6000')+' r e a d y p900 a-x'
        try:
            r=peer.run(name,'success',keys,directory=bytes(directory),prm=flow.prm(soft=soft,hard=1),profile=4,files=files,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',working_drive='d',observer='RENDER',
                environment={'PCPLUS_TXWAIT':'2' if mode=='timeout' else '30'},
                banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0cLOGIN:')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);state=struct.unpack('<4H',raw[-8:])
        wire=(folder/'serial.bin').read_bytes();control=b'\x13\x11' if soft else b''
        reply=ESC+(b'[1;24R' if mode=='resume' else b'[5;1R' if mode=='timeout' else b'[4;1R')
        expected=b'ATZ\rATDCaseTest:23\r'+control+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+(flow.PAYLOAD if mode=='resume' else b'')+control+(b'q' if mode=='cancel' else b'')+b'ready'+reply+b'+++ATH\r'
        low=next(e['time'] for e in events if e['kind']=='cts-low-go');high=next(e['time'] for e in events if e['kind']=='cts-high')
        blocked=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and low<e['time']<high)
        checks=dict(r['checks'],native_exit=head[:4]==(0x524e,1,1,1) and head[6]==status,
            JFT_restored=raw[14:34]==raw[34:54],owners_restored=raw[54:470]==raw[470:886],hardware_owner_observed=state[3]>(60 if mode=='resume' else 8),
            software_pause_not_used=state[0]==state[2]==0,parent_return=state[1]>18,long_CTS_hold=4<=high-low<5,
            no_payload_during_hold=not bytes(c for c in blocked if c not in (17,19)),full_wire_exact=wire==expected,
            marker=((folder/'CTS.OK').is_file() and (folder/'CTS.OK').read_bytes()==b'RESUMED')==(mode=='resume'),
            peer_stream_matches=wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive'))
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,child_exit=head[6],observations=list(state),CTS_low_seconds=high-low,
            wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],checks=checks,child_exit=head[6],observations=list(state))),flush=True)
    report=dict(passed=all(r['passed'] for r in rows),cases=rows,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),emulator_source=cts.SOURCE_URL,
        scope=__doc__+' Six actual8086 HARD/BOTH cases with four-second CTS hold through pinned nullmodem control framing. No peer XOFF. Cancel retains ordinary q. Complete wire and hardware/JFT/file-owner restoration checked. No physical UART, sustained RTS/RX or full application acceptance.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']


if __name__=='__main__':main()
